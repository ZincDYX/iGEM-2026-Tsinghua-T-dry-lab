import json
import mimetypes
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from uuid import uuid4

import pandas as pd

from CatalystOptimizationSystem.core.optimizer import Optimizer, Columns
from CatalystOptimizationSystem.core.constraints import (
    load_constraints,
    normalize_value_unit,
    validate_cross_relations,
    compute_confidence,
)

ASCII_ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_ROOT = BASE_DIR / 'ui'
ASSETS_ROOT = STATIC_ROOT / 'assets'
UPLOAD_ROOT = BASE_DIR / 'uploads'
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
JOB_LOCK = threading.Lock()
JOBS = {}

def _normalize_metric_name(name: str) -> str:
    name = (name or '').strip().replace(' ', '_')
    return ''.join(ch for ch in name if ch in ASCII_ALLOWED).lower()


def _ensure_english_identifiers(names):
    out = []
    for n in names:
        n2 = _normalize_metric_name(n)
        if not n2 or any((ord(c) > 127) for c in n):
            raise ValueError(f"metrics ????????????: {n}")
        out.append(n2)
    return out

class Handler(BaseHTTPRequestHandler):
    _constraints = load_constraints()
    _static_root = STATIC_ROOT
    _assets_root = ASSETS_ROOT
    _upload_root = UPLOAD_ROOT

    def _send(self, code: int, payload: dict):
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/health':
            self._send(200, {'status': 'ok'})
        elif parsed.path == '/jobs':
            with JOB_LOCK:
                jobs = list(JOBS.values())
            self._send(200, {'jobs': jobs})
        elif parsed.path.startswith('/jobs/'):
            job_id = parsed.path.rsplit('/', 1)[-1]
            with JOB_LOCK:
                job = JOBS.get(job_id)
            if not job:
                self._send(404, {'error': 'job not found'})
            else:
                self._send(200, job)
        else:
            self._serve_static(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get('Content-Length', '0') or '0')
        raw = self.rfile.read(length) if length > 0 else b''

        if parsed.path == '/upload':
            self._handle_upload(parsed, raw)
            return

        try:
            req = json.loads(raw.decode('utf-8')) if raw else {}
        except Exception:
            self._send(400, {'error': 'invalid json'})
            return

        try:
            if parsed.path == '/suggest':
                self._handle_suggest(req)
            elif parsed.path == '/extract':
                self._handle_extract(req)
            elif parsed.path == '/clean':
                self._handle_clean(req)
            elif parsed.path == '/impute/evaluate':
                self._handle_impute_evaluate(req)
            elif parsed.path == '/impute/apply':
                self._handle_impute_apply(req)
            elif parsed.path == '/record':
                self._handle_record(req)
            elif parsed.path == '/correct':
                self._handle_correct(req)
            else:
                self._send(404, {'error': 'not found'})
        except ValueError as ve:
            self._send(400, {'error': str(ve)})

    def _handle_suggest(self, req: dict):
        csv_path = req.get('csv_path')
        cols = req.get('columns', {})
        top_k = int(req.get('top_k', 5))
        n_candidates = int(req.get('n_candidates', 2000))
        if not csv_path:
            self._send(400, {'error': 'csv_path required'})
            return
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            self._send(400, {'error': f'failed to read csv: {e}'})
            return

        # ???????
        for k, v in cols.items():
            if v and (not v.isascii()):
                raise ValueError(f"???????????: {k} -> {v}")

        c = Columns(
            T=cols.get('T', 'final_reaction_temp'),
            P=cols.get('P', 'final_pressure'),
            conv=cols.get('conv', 'final_co2_conversion'),
            sel=cols.get('sel', 'final_methanol_selectivity'),
            yld=cols.get('yld', 'final_methanol_yield'),
        )
        # ???????????
        weights = req.get('weights') or {}
        w_sel = float(weights.get('sel', 0.8))
        w_conv = float(weights.get('conv', 0.2))
        w_yld = float(weights.get('yld', 0.0))
        objective = req.get('objective')
        try:
            opt = Optimizer(df, cols=c, w_syn=w_sel, w_conv=w_conv, w_yld=w_yld, objective=objective)
            res = opt.suggest(n_candidates=n_candidates, top_k=top_k)
        except Exception as e:
            self._send(500, {'error': f'optimization failed: {e}'})
            return

        self._send(200, {'suggestions': res.to_dict(orient='records')})

    def _handle_extract(self, req: dict):
        from CatalystOptimizationSystem.core.extractor import extract_dataset
        elsevier_key = req.get('elsevier_key')
        keyword = req.get('keyword')
        count = int(req.get('count', 25))
        metrics = req.get('metrics')
        icl = req.get('icl_path')
        inst = req.get('elsevier_insttoken')
        llm_key = req.get('llm_key')
        llm_base = req.get('llm_base')
        llm_model = req.get('llm_model')
        constraints = req.get('constraints_path')
        schema = req.get('schema_path')
        icl_bank = req.get('icl_bank_path')
        icl_top_k = int(req.get('icl_top_k', 3))
        domain = req.get('domain')
        workers = int(req.get('workers', 1))
        resume = bool(req.get('resume', True))
        background = bool(req.get('background', False))
        chunk_chars = int(req.get('chunk_chars', 14000))
        chunk_overlap = int(req.get('chunk_overlap', 1000))
        max_chunks = int(req.get('max_chunks', 8))
        out = req.get('out')
        if not elsevier_key or not keyword:
            self._send(400, {'error': 'elsevier_key and keyword are required'})
            return
        # ??????
        if metrics:
            metrics = _ensure_english_identifiers(metrics)

        def run_extract():
            out_csv = extract_dataset(
                elsevier_api_key=elsevier_key,
                keyword=keyword,
                count=count,
                metrics=metrics,
                icl_json_path=icl,
                elsevier_inst_token=inst,
                llm_api_key=llm_key,
                llm_api_base=llm_base,
                llm_model=llm_model,
                out_csv=out,
                constraints_path=constraints,
                schema_path=schema,
                icl_bank_path=icl_bank,
                icl_top_k=icl_top_k,
                domain=domain,
                workers=workers,
                resume=resume,
                chunk_chars=chunk_chars,
                chunk_overlap=chunk_overlap,
                max_chunks=max_chunks,
            )
            return out_csv

        if background:
            job_id = uuid4().hex[:12]
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            with JOB_LOCK:
                JOBS[job_id] = {
                    'job_id': job_id,
                    'status': 'running',
                    'created_at': now,
                    'updated_at': now,
                    'keyword': keyword,
                    'count': count,
                    'workers': workers,
                    'out': out,
                    'output_csv': None,
                    'error': None,
                }

            def worker():
                try:
                    output_csv = run_extract()
                    status = 'completed'
                    error = None
                except Exception as ex:
                    output_csv = None
                    status = 'failed'
                    error = f'extraction failed: {ex}'
                with JOB_LOCK:
                    if job_id in JOBS:
                        JOBS[job_id].update({
                            'status': status,
                            'updated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'output_csv': output_csv,
                            'error': error,
                        })

            threading.Thread(target=worker, daemon=True).start()
            self._send(202, {'job_id': job_id, 'status': 'running'})
            return

        try:
            out_csv = run_extract()
        except Exception as ex:
            self._send(500, {'error': f'extraction failed: {ex}'})
            return
        self._send(200, {'output_csv': out_csv})

    def _json_safe(self, obj):
        if isinstance(obj, dict):
            return {k: self._json_safe(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._json_safe(v) for v in obj]
        try:
            if pd.isna(obj):
                return None
        except Exception:
            pass
        return obj

    def _list_or_none(self, value):
        if value is None:
            return None
        if isinstance(value, list):
            return value or None
        if isinstance(value, str):
            items = [x for x in value.replace(',', ' ').split() if x]
            return items or None
        return None

    def _make_output_path(self, csv_path: str, prefix: str) -> str:
        src = Path(csv_path)
        ts = time.strftime('%Y%m%d-%H%M%S')
        parent = src.parent if src.parent else Path('.')
        return str(parent / f'{prefix}_{ts}.csv')

    def _numeric_frame_from_request(self, req: dict):
        from CatalystOptimizationSystem.core.imputer import load_numeric_block

        csv_path = req.get('csv_path')
        use_columns = self._list_or_none(req.get('use_columns'))
        if not csv_path:
            raise ValueError('csv_path required')
        df = pd.read_csv(csv_path, encoding='utf-8')
        if use_columns:
            missing = [c for c in use_columns if c not in df.columns]
            if missing:
                raise ValueError(f'use_columns not found: {missing}')
            df_num = df[use_columns].apply(pd.to_numeric, errors='coerce')
        else:
            try:
                df_num = load_numeric_block(csv_path)
            except Exception:
                df_num = df.select_dtypes(include='number').copy()
        if df_num.empty:
            raise ValueError('no numeric columns for imputation')
        return df, df_num

    def _handle_clean(self, req: dict):
        from CatalystOptimizationSystem.core.validator import clean_catalyst_data

        csv_path = req.get('csv_path')
        if not csv_path:
            self._send(400, {'error': 'csv_path required'})
            return
        out = req.get('out') or self._make_output_path(csv_path, 'cleaned_database')
        df_clean = clean_catalyst_data(
            csv_path,
            grouping_keys=self._list_or_none(req.get('grouping')),
            key_value_columns=self._list_or_none(req.get('keys')),
            required_columns=self._list_or_none(req.get('required')),
            nonzero_columns=self._list_or_none(req.get('nonzero')),
        )
        try:
            df_clean.to_csv(out, index=False, encoding='utf-8', lineterminator='\n')
        except Exception as ex:
            self._send(500, {'error': f'failed to write cleaned csv: {ex}'})
            return
        self._send(200, {
            'rows': int(len(df_clean)),
            'columns': df_clean.columns.tolist(),
            'output_csv': out,
        })

    def _handle_impute_evaluate(self, req: dict):
        from CatalystOptimizationSystem.core.imputation_workflow import (
            EvalConfig,
            ask_llm_candidates,
            evaluate_method,
        )

        csv_path = req.get('csv_path')
        if not csv_path:
            self._send(400, {'error': 'csv_path required'})
            return
        try:
            _, df_num = self._numeric_frame_from_request(req)
            cfg = EvalConfig(
                mask_frac=float(req.get('mask_frac', 0.1)),
                repeats=int(req.get('repeats', 3)),
                seed=int(req.get('seed', 42)),
            )
            suggestions = {
                'median': {},
                'knn': [{'n_neighbors': 5, 'weights': 'distance', 'metric': 'nan_euclidean'}],
                'mice': [{'max_iter': 20, 'sample_posterior': False, 'random_state': 0}],
            }
            llm_key = req.get('llm_key')
            if llm_key:
                try:
                    suggestions = ask_llm_candidates(
                        df_num,
                        llm_key,
                        req.get('llm_base') or 'https://api.deepseek.com/v1/chat/completions',
                        req.get('llm_model') or 'deepseek-chat',
                    )
                except Exception:
                    pass
            report = [evaluate_method(df_num, 'median', {}, cfg)]
            for cand in suggestions.get('knn', [])[:5]:
                report.append(evaluate_method(df_num, 'knn', cand, cfg))
            for cand in suggestions.get('mice', [])[:5]:
                report.append(evaluate_method(df_num, 'mice', cand, cfg))
            report_sorted = sorted(report, key=lambda x: (x['score'],), reverse=True)

            summary_path = self._make_output_path(csv_path, 'imputation_eval_summary')
            summary = pd.DataFrame([
                {
                    'method': item.get('method'),
                    'params': json.dumps(item.get('params', {}), ensure_ascii=False),
                    'overall_nrmse': item.get('overall_nrmse'),
                    'score': item.get('score'),
                }
                for item in report_sorted
            ])
            summary.to_csv(summary_path, index=False, encoding='utf-8', lineterminator='\n')
            missing_rate = df_num.isna().mean(axis=1)
            payload = {
                'report': report_sorted,
                'summary_csv': summary_path,
                'columns': df_num.columns.tolist(),
                'missingness': {
                    'mean': float(missing_rate.mean()),
                    'median': float(missing_rate.median()),
                    'p90': float(missing_rate.quantile(0.9)),
                },
            }
            self._send(200, self._json_safe(payload))
        except ValueError as ex:
            self._send(400, {'error': str(ex)})
        except Exception as ex:
            self._send(500, {'error': f'imputation evaluation failed: {ex}'})

    def _handle_impute_apply(self, req: dict):
        from CatalystOptimizationSystem.core.imputation_workflow import _apply_imputation

        csv_path = req.get('csv_path')
        method = req.get('method') or 'median'
        params_raw = req.get('params') or {}
        if not csv_path:
            self._send(400, {'error': 'csv_path required'})
            return
        try:
            params = json.loads(params_raw) if isinstance(params_raw, str) else params_raw
            if not isinstance(params, dict):
                raise ValueError('params must be a JSON object')
            df, df_num = self._numeric_frame_from_request(req)
            imputed = _apply_imputation(df_num, method, params)
            out_df = df.copy()
            for col in imputed.columns:
                out_df[col] = imputed[col]
            out = req.get('out') or self._make_output_path(csv_path, f'imputed_{method}')
            out_df.to_csv(out, index=False, encoding='utf-8', lineterminator='\n')
            self._send(200, {
                'rows': int(len(out_df)),
                'columns': out_df.columns.tolist(),
                'output_csv': out,
            })
        except ValueError as ex:
            self._send(400, {'error': str(ex)})
        except Exception as ex:
            self._send(500, {'error': f'imputation apply failed: {ex}'})

    def _serve_static(self, path: str):
        rel = path.lstrip('/')
        if not rel:
            rel = 'index.html'
        target = (self._static_root / rel).resolve()
        try:
            target.relative_to(self._static_root)
        except ValueError:
            self._send(404, {'error': 'not found'})
            return
        if not target.exists() or not target.is_file():
            self._send(404, {'error': 'not found'})
            return
        mime, _ = mimetypes.guess_type(str(target))
        mime = mime or 'application/octet-stream'
        try:
            data = target.read_bytes()
        except Exception as ex:
            self._send(500, {'error': f'failed to read static file: {ex}'})
            return
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _handle_upload(self, parsed, body: bytes):
        content_type = self.headers.get('Content-Type', '')
        filename = 'upload.bin'
        file_bytes = body

        if 'multipart/form-data' in content_type:
            bound_token = ''
            for part in content_type.split(';'):
                part = part.strip()
                if part.startswith('boundary='):
                    bound_token = part.split('=', 1)[1]
                    break
            if bound_token:
                boundary = ('--' + bound_token).encode('utf-8')
                segments = body.split(boundary)
                for seg in segments:
                    if not seg or seg in (b'--', b'--\r\n'):
                        continue
                    if seg.startswith(b'\r\n'):
                        seg = seg[2:]
                    header_end = seg.find(b'\r\n\r\n')
                    if header_end == -1:
                        continue
                    header_block = seg[:header_end].decode('utf-8', errors='ignore')
                    payload = seg[header_end+4:]
                    if payload.endswith(b'\r\n'):
                        payload = payload[:-2]
                    if 'filename=' in header_block:
                        for line in header_block.split('\r\n'):
                            if 'filename=' in line:
                                try:
                                    fname = line.split('filename=',1)[1].strip().strip('"')
                                    if fname:
                                        filename = fname
                                except Exception:
                                    pass
                        file_bytes = payload
                        break

        safe = self._safe_filename(filename)
        dest = self._upload_root / safe
        base, ext = os.path.splitext(safe)
        counter = 1
        while dest.exists():
            dest = self._upload_root / f"{base}_{counter}{ext}"
            counter += 1
        try:
            with open(dest, 'wb') as f:
                f.write(file_bytes or b'')
        except Exception as ex:
            self._send(500, {'error': f'failed to save file: {ex}'})
            return
        self._send(200, {'path': str(dest)})

    def _safe_filename(self, name: str) -> str:
        name = name or 'upload.bin'
        cleaned = ''.join(ch if ch.isalnum() or ch in ('-', '_', '.') else '_' for ch in name)
        cleaned = cleaned.strip('._') or 'upload.bin'
        return cleaned

    def _handle_record(self, req: dict):
        csv_path = req.get('csv_path')
        if not csv_path:
            self._send(400, {'error': 'csv_path required'})
            return
        try:
            row_index = int(req.get('row_index', 0))
        except Exception:
            self._send(400, {'error': 'row_index must be int'})
            return
        try:
            df = pd.read_csv(csv_path)
        except Exception as ex:
            self._send(400, {'error': f'failed to read csv: {ex}'})
            return
        total = len(df)
        if total == 0:
            self._send(400, {'error': 'csv has no rows'})
            return
        if row_index < 0 or row_index >= total:
            self._send(400, {'error': f'row_index {row_index} out of range (total {total})'})
            return
        row = df.iloc[row_index]
        row_dict = {}
        for k, v in row.to_dict().items():
            if pd.isna(v):
                row_dict[k] = None
            else:
                row_dict[k] = v
        self._send(200, {
            'row_index': row_index,
            'total_rows': total,
            'columns': df.columns.tolist(),
            'row': row_dict,
        })

    def _handle_correct(self, req: dict):
        csv_path = req.get('csv_path')
        metric_raw = req.get('metric')
        value = req.get('value')
        unit = req.get('unit')
        doi = req.get('doi')
        note = req.get('note')
        row_index = req.get('row_index')
        if not csv_path or not metric_raw:
            self._send(400, {'error': 'csv_path and metric are required'})
            return
        metric = _normalize_metric_name(metric_raw)
        if not metric:
            self._send(400, {'error': 'invalid metric'})
            return
        try:
            df = pd.read_csv(csv_path)
        except Exception as ex:
            self._send(400, {'error': f'failed to read csv: {ex}'})
            return

        target_idx = None
        if row_index is not None:
            try:
                idx = int(row_index)
            except Exception:
                self._send(400, {'error': 'row_index must be int'})
                return
            target_idx = idx
        elif doi:
            if 'doi' not in df.columns:
                self._send(400, {'error': 'column doi not found; provide row_index instead'})
                return
            matches = df.index[df['doi'].astype(str) == doi].tolist()
            if not matches:
                self._send(400, {'error': f'doi {doi} not found'})
                return
            target_idx = matches[0]
        else:
            self._send(400, {'error': 'provide row_index or doi'})
            return

        if target_idx < 0 or target_idx >= len(df):
            self._send(400, {'error': f'row_index {target_idx} out of range'})
            return

        constraints = self._constraints
        norm_value, norm_unit, violations = normalize_value_unit(metric, value, unit, constraints)
        value_col = f"{metric}_value"
        unit_col = f"{metric}_unit"
        norm_val_col = f"{metric}_norm_value"
        norm_unit_col = f"{metric}_norm_unit"
        viol_col = f"{metric}_violations"
        if value_col not in df.columns or unit_col not in df.columns:
            self._send(400, {'error': f'metric columns not found for {metric}'})
            return

        df.at[target_idx, value_col] = value
        df.at[target_idx, unit_col] = unit
        if norm_val_col in df.columns:
            df.at[target_idx, norm_val_col] = norm_value
        if norm_unit_col in df.columns:
            df.at[target_idx, norm_unit_col] = norm_unit
        if viol_col in df.columns:
            df.at[target_idx, viol_col] = ",".join(violations) if violations else ""

        if note:
            df.at[target_idx, 'correction_note'] = note

        metrics_present = sorted({c[:-11] for c in df.columns if c.endswith('_norm_value')})
        row_norm_map = {}
        for name in metrics_present:
            nv_col = f"{name}_norm_value"
            nu_col = f"{name}_norm_unit"
            nv = df.at[target_idx, nv_col] if nv_col in df.columns else None
            nu = df.at[target_idx, nu_col] if nu_col in df.columns else None
            nv = None if (nv is not None and pd.isna(nv)) else nv
            row_norm_map[name] = (nv, nu)

        cross_vios = validate_cross_relations(row_norm_map)
        metric_violations_all = []
        for name in metrics_present:
            viol_col = f"{name}_violations"
            val = df.at[target_idx, viol_col] if viol_col in df.columns else None
            if isinstance(val, str) and val.strip():
                metric_violations_all.extend([f"{name}:{t.strip()}" for t in val.split(',') if t.strip()])

        corr_col = 'corrected_rounds'
        corrected_rounds = 0
        if corr_col in df.columns:
            prev = df.at[target_idx, corr_col]
            if pd.notna(prev):
                try:
                    corrected_rounds = int(prev)
                except Exception:
                    corrected_rounds = 0
        corrected_rounds += 1
        df.at[target_idx, corr_col] = corrected_rounds

        conf = compute_confidence(metric_violations_all, cross_vios, corrected_rounds)
        if 'confidence' in df.columns:
            df.at[target_idx, 'confidence'] = conf
        for name in metrics_present:
            conf_col = f"{name}_confidence"
            if conf_col in df.columns:
                df.at[target_idx, conf_col] = conf

        try:
            df.to_csv(csv_path, index=False, encoding='utf-8', lineterminator='\n')
        except Exception as ex:
            self._send(500, {'error': f'failed to write csv: {ex}'})
            return

        row = df.iloc[target_idx].to_dict()
        sanitized = {k: (None if pd.isna(v) else v) for k, v in row.items()}
        self._send(200, {
            'message': 'correction applied',
            'row_index': target_idx,
            'violations': violations,
            'cross_violations': cross_vios,
            'confidence': conf,
            'row': sanitized,
            'output_csv': csv_path,
        })


def run(host: str = '127.0.0.1', port: int = 8080):
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f'API listening on http://{host}:{port} (GET /health, /jobs/<id>; POST /extract, /clean, /impute/evaluate, /impute/apply, /suggest)')
    httpd.serve_forever()


if __name__ == '__main__':
    host = '127.0.0.1'
    port = 8080
    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        port = int(sys.argv[2])
    run(host, port)
