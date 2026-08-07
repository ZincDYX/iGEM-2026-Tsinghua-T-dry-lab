import os
import json
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Iterable
from urllib.parse import quote
import requests
import pandas as pd
import xml.etree.ElementTree as ET

from CatalystOptimizationSystem.utils.logger import get_logger
from CatalystOptimizationSystem.utils.config import (
    ELSEVIER_SEARCH_ENDPOINT,
    ELSEVIER_ARTICLE_ENDPOINT,
    DEFAULT_LLM_BASE,
    DEFAULT_LLM_MODEL,
    DEFAULT_ICL_JSON,
    DEFAULT_SCHEMA_JSON,
    DEFAULT_ICL_BANK,
)

logger = get_logger(__name__)
from CatalystOptimizationSystem.core.constraints import load_constraints, normalize_value_unit, validate_cross_relations, compute_confidence
from CatalystOptimizationSystem.core.icl_selector import load_icl_bank, select_icl_examples
from CatalystOptimizationSystem.core.schema_config import (
    load_schema,
    schema_constraints,
    schema_metric_names,
    schema_prompt,
    normalize_value_unit_from_schema,
    validate_cross_relations_from_schema,
)

# allowed ascii for identifiers
ASCII_ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
DEFAULT_METRICS = ['glabridin_titer', 'substrate_conversion', 'glabridin_yield', 'glabridin_selectivity']

# ---- ???? ----
def _get_headers_elsevier(api_key: str, inst_token: Optional[str] = None) -> Dict[str, str]:
    headers = {"X-ELS-APIKey": api_key, "Accept": "application/json"}
    if inst_token:
        headers["X-ELS-Insttoken"] = inst_token
    return headers


def _strip_namespaces(root: ET.Element):
    for el in root.iter():
        if isinstance(el.tag, str) and '}' in el.tag:
            el.tag = el.tag.split('}', 1)[1]


def _extract_pii_doi(entry: dict) -> Tuple[Optional[str], Optional[str]]:
    pii = entry.get("pii")
    doi = entry.get("prism:doi") or entry.get("dc:identifier")
    if not (pii or doi):
        for link in entry.get("link", []):
            href = link.get("@href", "")
            if link.get("@ref") == "self" and "/pii/" in href:
                return href.split("/pii/")[1], doi
    return pii, doi


def _http_get(url: str, *, headers: Dict[str, str], params: Optional[Dict[str, Any]] = None,
              timeout: int = 30, retries: int = 3, backoff: float = 0.8):
    for i in range(max(1, retries)):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=timeout)
            if resp.status_code >= 500 and i < retries - 1:
                time.sleep(backoff * (2 ** i))
                continue
            resp.raise_for_status()
            return resp
        except Exception:
            if i >= retries - 1:
                raise
            time.sleep(backoff * (2 ** i))


# ---- Elsevier ??????? ----
def scidir_search(keyword: str, count: int, api_key: str, inst_token: Optional[str] = None) -> List[dict]:
    headers = _get_headers_elsevier(api_key, inst_token)
    all_entries: List[dict] = []
    start = 0
    page = 25
    while len(all_entries) < int(count):
        take = min(page, int(count) - len(all_entries))
        params = {"query": keyword, "count": take, "start": start}
        resp = _http_get(ELSEVIER_SEARCH_ENDPOINT, headers=headers, params=params, timeout=30, retries=3)
        js = resp.json()
        search_results = js.get('search-results', {})
        entries = search_results.get('entry', []) or []
        if not entries:
            break
        all_entries.extend(entries)
        start += len(entries)
        if len(entries) < take:
            break
    return all_entries[:int(count)]


def fetch_fulltext_xml(pii: Optional[str], doi: Optional[str], api_key: str, inst_token: Optional[str] = None) -> Optional[bytes]:
    if not (pii or doi):
        return None
    identifier, id_type = (pii, 'pii') if pii else (doi, 'doi')
    url = ELSEVIER_ARTICLE_ENDPOINT.format(id_type=id_type, identifier=quote(str(identifier), safe=''))
    headers = _get_headers_elsevier(api_key, inst_token)
    headers['Accept'] = 'application/xml'
    try:
        resp = _http_get(url, headers=headers, timeout=60, retries=2)
        return resp.content
    except Exception as ex:
        logger.warning("Fetch fulltext failed %s %s: %s", id_type, identifier, ex)
        return None


def extract_text_from_xml(xml_bytes: bytes) -> str:
    try:
        root = ET.fromstring(xml_bytes)
        _strip_namespaces(root)
        texts = []
        para_tags = ["abstract", "section", "para", "p", "simple-para"]
        for tag in para_tags:
            for el in root.findall(f".//{tag}"):
                t = " ".join("".join(el.itertext()).split())
                if t:
                    texts.append(t)
        txt = "\n".join(t for t in texts if t)
        return txt
    except Exception:
        return ""


def chunk_text(text: str, max_chars: int = 14000, overlap: int = 1000, max_chunks: int = 8) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    max_chars = max(4000, int(max_chars or 14000))
    overlap = max(0, min(int(overlap or 0), max_chars // 2))
    max_chunks = max(1, int(max_chunks or 1))
    if len(text) <= max_chars:
        return [text]

    chunks: List[str] = []
    start = 0
    while start < len(text) and len(chunks) < max_chunks:
        end = min(len(text), start + max_chars)
        if end < len(text):
            boundary = max(text.rfind("\n", start, end), text.rfind(". ", start, end))
            if boundary > start + int(max_chars * 0.65):
                end = boundary + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [chunk for chunk in chunks if chunk]


# ---- LLM ?? ----
def load_icl_examples(path: Optional[str]) -> List[dict]:
    p = path or DEFAULT_ICL_BANK or DEFAULT_ICL_JSON
    try:
        if str(p).lower().endswith('.jsonl'):
            return load_icl_bank(p)
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        logger.warning("Load ICL examples failed, use empty context: %s", p)
        return []


def build_prompt(examples: List[dict], text: str, metrics: List[str], schema: Optional[Dict[str, Any]] = None) -> str:
    parts = [
        "You are an information extraction assistant.",
        "Extract experimental records, not just article-level summaries.",
        "A record corresponds to one enzyme or mutant, one substrate, one reaction system, one set of reaction conditions, and one set of results.",
        "Split records when enzyme, mutant, substrate, temperature, pH, time, LLPS state, or reaction system differs.",
        "Requested metrics (return null if missing in a record): " + ", ".join(metrics),
    ]
    sp = schema_prompt(schema, metrics)
    if sp:
        parts.append(sp)
    if examples:
        instructions = []
        for ex in examples[:3]:
            inst = str(ex.get('instruction', '')).strip()
            if inst and inst not in instructions:
                instructions.append(inst)
        if instructions:
            parts.append("Task instructions:\n" + "\n".join(f"- {inst}" for inst in instructions))
        parts.append("Examples:")
        for ex in examples[:3]:
            inst = str(ex.get('instruction', '')).strip()
            if inst:
                parts.append("Instruction:\n" + inst)
            parts.append("Context:\n" + str(ex.get('context', '')))
            parts.append("Expected JSON:\n" + json.dumps({"records": [ex.get('output', {})]}, ensure_ascii=False))
    parts.append("Text:\n" + text)
    parts.append(
        "Return JSON only as {\"records\": [<record>, ...]}. "
        "Each record must use keys exactly matching metric names. "
        "Each metric value is an object: {\"value\": <string_or_number|null>, \"unit\": <string|null>, \"evidence\": <string|null>}. "
        "If the article contains no extractable experimental record, return {\"records\": []}."
    )
    return "\n\n".join(parts)


def _retry_after_seconds(resp) -> Optional[float]:
    value = resp.headers.get("Retry-After") if resp is not None else None
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        return None


def call_llm_openai(api_key: str, api_base: str, model: str, prompt: str,
                    retries: int = 6, backoff: float = 2.0) -> str:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You extract structured information as JSON only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
    }
    retries = max(1, int(retries or 1))
    retry_status = {429, 500, 502, 503, 504}
    last_error: Optional[Exception] = None
    for attempt in range(max(1, int(retries or 1))):
        try:
            resp = requests.post(api_base, headers=headers, json=payload, timeout=180)
            if resp.status_code in retry_status and attempt < retries - 1:
                wait = _retry_after_seconds(resp)
                if wait is None:
                    wait = backoff * (2 ** attempt) + random.uniform(0, 0.75)
                logger.warning("LLM temporary error %s, retry %d/%d after %.1fs", resp.status_code, attempt + 1, retries, wait)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            break
        except requests.RequestException as ex:
            last_error = ex
            if attempt >= retries - 1:
                raise
            wait = backoff * (2 ** attempt) + random.uniform(0, 0.75)
            logger.warning("LLM request failed, retry %d/%d after %.1fs: %s", attempt + 1, retries, wait, ex)
            time.sleep(wait)
    else:
        if last_error:
            raise last_error
        raise RuntimeError("LLM request failed without response")
    js = resp.json()
    content = js.get('choices', [{}])[0].get('message', {}).get('content', '')
    return content


def _extract_json_block(s: str) -> Optional[str]:
    if not s:
        return None
    s2 = s.strip()
    if s2.startswith('```') and s2.endswith('```'):
        s2 = s2.strip('`')
    i = s2.find('{')
    j = s2.rfind('}')
    if i != -1 and j != -1 and j > i:
        return s2[i:j+1]
    return None


def parse_metrics_json(s: str) -> Dict[str, Any]:
    try:
        block = _extract_json_block(s) or s
        js = json.loads(block)
        return js if isinstance(js, dict) else {}
    except Exception:
        return {}


def _as_records(parsed: Dict[str, Any], metrics: List[str]) -> List[Dict[str, Any]]:
    if not isinstance(parsed, dict):
        return []
    records = parsed.get("records")
    if isinstance(records, list):
        return [r for r in records if isinstance(r, dict)]
    if any(k in parsed for k in metrics):
        return [parsed]
    return []


def _record_signature(record: Dict[str, Any], metrics: List[str]) -> str:
    pieces = []
    for metric in metrics:
        obj = record.get(metric, {}) if isinstance(record, dict) else {}
        if isinstance(obj, dict):
            pieces.append((
                metric,
                str(obj.get("value", "")).strip().lower(),
                str(obj.get("unit", "")).strip().lower(),
                str(obj.get("evidence", ""))[:160].strip().lower(),
            ))
    return json.dumps(pieces, ensure_ascii=False, sort_keys=True)


def _dedupe_records(records: List[Dict[str, Any]], metrics: List[str]) -> List[Dict[str, Any]]:
    seen: set[str] = set()
    out: List[Dict[str, Any]] = []
    for record in records:
        sig = _record_signature(record, metrics)
        if sig in seen:
            continue
        seen.add(sig)
        out.append(record)
    return out


# ---- ????? ----
def _normalize_metric_name(name: str) -> str:
    name = (name or '').strip().replace(' ', '_')
    return ''.join(ch for ch in name if ch in ASCII_ALLOWED).lower()


def _ensure_english_identifiers(names: Iterable[str], field: str) -> List[str]:
    out = []
    for n in names:
        n2 = _normalize_metric_name(n)
        if not n2 or any((ord(c) > 127) for c in n):
            raise ValueError(f"{field} ????????????: {n}")
        out.append(n2)
    return out


def _article_key(pii: Optional[str], doi: Optional[str], title: str = "") -> str:
    if doi:
        return "doi:" + str(doi).lower().strip()
    if pii:
        return "pii:" + str(pii).lower().strip()
    return "title:" + str(title).lower().strip()[:160]


def _existing_article_keys(path: str) -> set[str]:
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return set()
    try:
        df = pd.read_csv(p, usecols=["article_key"])
        return set(str(x) for x in df["article_key"].dropna().unique())
    except Exception:
        return set()


def _output_columns(metrics: List[str]) -> List[str]:
    cols = [
        "article_key", "doi", "pii", "title", "keyword", "schema_id",
        "selected_icl_ids", "text_chars", "chunk_count", "processed_chunks",
        "record_index", "record_count",
        "extraction_status", "error", "corrected_rounds", "confidence",
    ]
    for metric in metrics:
        cols.extend([
            f"{metric}_value",
            f"{metric}_unit",
            f"{metric}_evidence",
            f"{metric}_norm_value",
            f"{metric}_norm_unit",
            f"{metric}_violations",
            f"{metric}_confidence",
        ])
    return cols


def _normalize_records(records, metrics, constraints, schema):
    norm_maps = []
    metric_violations_all: List[str] = []
    cross_violations_all: List[str] = []
    for idx, record in enumerate(records):
        norm_map = {}
        for metric in metrics:
            obj = record.get(metric, {}) if isinstance(record, dict) else {}
            value = obj.get("value") if isinstance(obj, dict) else None
            unit = obj.get("unit") if isinstance(obj, dict) else None
            if schema:
                nv, nu, vios = normalize_value_unit_from_schema(metric, value, unit, constraints)
            else:
                nv, nu, vios = normalize_value_unit(metric, value, unit, constraints)
            norm_map[metric] = (nv, nu, vios)
            metric_violations_all.extend([f"record_{idx + 1}.{metric}:{vio}" for vio in vios])
        cross_vios = validate_cross_relations_from_schema(norm_map, schema) if schema else validate_cross_relations(norm_map)
        cross_violations_all.extend([f"record_{idx + 1}:{vio}" for vio in cross_vios])
        norm_maps.append(norm_map)
    return norm_maps, metric_violations_all, cross_violations_all


def _status_row(*, pii, doi, title, keyword, schema, selected_examples=None, status, error,
                text_chars: int = 0, chunk_count: int = 0, processed_chunks: int = 0):
    return {
        "article_key": _article_key(pii, doi, title),
        "doi": doi,
        "pii": pii,
        "title": title,
        "keyword": keyword,
        "schema_id": (schema or {}).get("schema_id"),
        "selected_icl_ids": ",".join(str(ex.get("id", "")) for ex in (selected_examples or [])),
        "text_chars": text_chars,
        "chunk_count": chunk_count,
        "processed_chunks": processed_chunks,
        "record_index": 0,
        "record_count": 0,
        "extraction_status": status,
        "error": error,
        "corrected_rounds": 0,
        "confidence": 0.0,
    }


def _flatten_record_rows(*, records, norm_maps, metrics, pii, doi, title, keyword, schema,
                         selected_examples, corrected_rounds, confidence,
                         text_chars: int = 0, chunk_count: int = 0, processed_chunks: int = 0):
    rows = []
    total = len(records)
    for idx, record in enumerate(records, start=1):
        row = {
            "article_key": _article_key(pii, doi, title),
            "doi": doi,
            "pii": pii,
            "title": title,
            "keyword": keyword,
            "schema_id": (schema or {}).get("schema_id"),
            "selected_icl_ids": ",".join(str(ex.get("id", "")) for ex in selected_examples),
            "text_chars": text_chars,
            "chunk_count": chunk_count,
            "processed_chunks": processed_chunks,
            "record_index": idx,
            "record_count": total,
            "extraction_status": "ok",
            "error": None,
            "corrected_rounds": corrected_rounds,
            "confidence": confidence,
        }
        norm_map = norm_maps[idx - 1] if idx - 1 < len(norm_maps) else {}
        for metric in metrics:
            obj = record.get(metric, {}) if isinstance(record, dict) else {}
            value = obj.get("value") if isinstance(obj, dict) else None
            unit = obj.get("unit") if isinstance(obj, dict) else None
            evidence = obj.get("evidence") if isinstance(obj, dict) else None
            nv, nu, vios = norm_map.get(metric, (None, None, []))
            row[f"{metric}_value"] = value
            row[f"{metric}_unit"] = unit
            row[f"{metric}_evidence"] = evidence
            row[f"{metric}_norm_value"] = nv
            row[f"{metric}_norm_unit"] = nu
            row[f"{metric}_violations"] = ",".join(vios) if vios else None
            row[f"{metric}_confidence"] = confidence
        rows.append(row)
    return rows


def _append_rows(path: str, rows: List[Dict[str, Any]], columns: List[str], lock: threading.Lock):
    if not rows:
        return
    with lock:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        header = not p.exists() or p.stat().st_size == 0
        pd.DataFrame(rows, columns=columns).to_csv(
            p,
            mode="a",
            header=header,
            index=False,
            encoding="utf-8",
            lineterminator="\n",
        )


def _process_entry(e: dict, *, keyword: str, metrics: List[str], examples: List[dict],
                   schema: Optional[Dict[str, Any]], constraints: Dict[str, Dict[str, Any]],
                   elsevier_api_key: str, elsevier_inst_token: Optional[str],
                   llm_api_key: Optional[str], llm_api_base: Optional[str],
                   llm_model: Optional[str], icl_top_k: int, domain: Optional[str],
                   chunk_chars: int, chunk_overlap: int, max_chunks: int):
    pii, doi = _extract_pii_doi(e)
    title = e.get('dc:title') or ''
    selected_examples: List[dict] = []
    try:
        xml_bytes = fetch_fulltext_xml(pii, doi, elsevier_api_key, elsevier_inst_token)
        if not xml_bytes:
            return [_status_row(pii=pii, doi=doi, title=title, keyword=keyword, schema=schema, status="fetch_failed", error="fulltext xml unavailable")]
        text = extract_text_from_xml(xml_bytes)
        if not text:
            return [_status_row(pii=pii, doi=doi, title=title, keyword=keyword, schema=schema, status="empty_text", error="fulltext text extraction returned empty")]
        chunks = chunk_text(text, max_chars=chunk_chars, overlap=chunk_overlap, max_chunks=max_chunks)
        if not chunks:
            return [_status_row(pii=pii, doi=doi, title=title, keyword=keyword, schema=schema, status="empty_text", error="fulltext chunking returned empty", text_chars=len(text))]
        if not llm_api_key:
            return [_status_row(pii=pii, doi=doi, title=title, keyword=keyword, schema=schema, selected_examples=selected_examples, status="llm_key_missing", error="llm key not provided", text_chars=len(text), chunk_count=len(chunks))]

        api_base = llm_api_base or DEFAULT_LLM_BASE
        model = llm_model or DEFAULT_LLM_MODEL
        records: List[Dict[str, Any]] = []
        selected_by_id: Dict[str, dict] = {}
        corrected_rounds = 0
        processed_chunks = 0

        for chunk_index, chunk in enumerate(chunks, start=1):
            chunk_examples = select_icl_examples(
                examples,
                chunk,
                metrics,
                domain=domain or (schema or {}).get('domain'),
                k=int(icl_top_k or 3),
            )
            for ex in chunk_examples:
                selected_by_id[str(ex.get("id", ""))] = ex
            prompt = build_prompt(chunk_examples, chunk, metrics, schema=schema)
            parsed = parse_metrics_json(call_llm_openai(llm_api_key, api_base, model, prompt))
            chunk_records = _as_records(parsed, metrics)
            processed_chunks += 1
            if not chunk_records:
                continue

            norm_maps, metric_vios, cross_vios = _normalize_records(chunk_records, metrics, constraints, schema)
            if metric_vios or cross_vios:
                err_text = "\n".join(metric_vios + cross_vios)[:1500]
                corr_prompt = prompt + "\n\nThe previous extraction violated validation rules:\n" + err_text + "\nReturn corrected JSON only in the same {\"records\": [...]} format."
                try:
                    parsed2 = parse_metrics_json(call_llm_openai(llm_api_key, api_base, model, corr_prompt))
                    records2 = _as_records(parsed2, metrics)
                    if records2:
                        chunk_records = records2
                        corrected_rounds += 1
                except Exception as ex:
                    logger.warning("corrective round failed for %s chunk %d: %s", doi or pii, chunk_index, ex)
            records.extend(chunk_records)

        selected_examples = list(selected_by_id.values())
        records = _dedupe_records(records, metrics)
        if not records:
            return [_status_row(pii=pii, doi=doi, title=title, keyword=keyword, schema=schema, selected_examples=selected_examples, status="no_records", error="LLM returned no records", text_chars=len(text), chunk_count=len(chunks), processed_chunks=processed_chunks)]

        norm_maps, metric_vios, cross_vios = _normalize_records(records, metrics, constraints, schema)
        confidence = compute_confidence(metric_vios, cross_vios, corrected_rounds)
        return _flatten_record_rows(
            records=records,
            norm_maps=norm_maps,
            metrics=metrics,
            pii=pii,
            doi=doi,
            title=title,
            keyword=keyword,
            schema=schema,
            selected_examples=selected_examples,
            corrected_rounds=corrected_rounds,
            confidence=confidence,
            text_chars=len(text),
            chunk_count=len(chunks),
            processed_chunks=processed_chunks,
        )
    except Exception as ex:
        logger.warning("entry extraction failed %s: %s", doi or pii or title, ex)
        return [_status_row(pii=pii, doi=doi, title=title, keyword=keyword, schema=schema, selected_examples=selected_examples, status="error", error=str(ex))]


# ---- ??? ----
def extract_dataset(
    elsevier_api_key: str,
    keyword: str,
    count: int,
    metrics: Optional[List[str]],
    icl_json_path: Optional[str] = None,
    elsevier_inst_token: Optional[str] = None,
    llm_api_key: Optional[str] = None,
    llm_api_base: Optional[str] = None,
    llm_model: Optional[str] = None,
    out_csv: Optional[str] = None,
    constraints_path: Optional[str] = None,
    schema_path: Optional[str] = None,
    icl_bank_path: Optional[str] = None,
    icl_top_k: int = 3,
    domain: Optional[str] = None,
    workers: int = 1,
    resume: bool = True,
    chunk_chars: int = 14000,
    chunk_overlap: int = 1000,
    max_chunks: int = 8,
) -> str:
    schema = load_schema(schema_path)
    if schema and not metrics:
        metrics = schema_metric_names(schema)
    elif not metrics:
        metrics = DEFAULT_METRICS
    metrics = _ensure_english_identifiers(metrics, 'metrics')
    constraints = schema_constraints(schema) if schema else load_constraints(constraints_path)
    examples = load_icl_examples(icl_bank_path or icl_json_path)
    ts = time.strftime('%Y%m%d-%H%M%S')
    out = out_csv or f"extracted_dataset_{ts}.csv"
    columns = _output_columns(metrics)
    done_keys = _existing_article_keys(out) if resume else set()
    entries = scidir_search(keyword, count, elsevier_api_key, elsevier_inst_token)

    work_entries = []
    for entry in entries:
        pii, doi = _extract_pii_doi(entry)
        key = _article_key(pii, doi, entry.get('dc:title') or '')
        if key in done_keys:
            logger.info("Skip completed article: %s", key)
            continue
        work_entries.append(entry)

    lock = threading.Lock()
    max_workers = max(1, int(workers or 1))
    written_rows = 0
    logger.info("Start extraction: entries=%d pending=%d workers=%d resume=%s out=%s", len(entries), len(work_entries), max_workers, resume, out)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [
            pool.submit(
                _process_entry,
                entry,
                keyword=keyword,
                metrics=metrics,
                examples=examples,
                schema=schema,
                constraints=constraints,
                elsevier_api_key=elsevier_api_key,
                elsevier_inst_token=elsevier_inst_token,
                llm_api_key=llm_api_key,
                llm_api_base=llm_api_base,
                llm_model=llm_model,
                icl_top_k=icl_top_k,
                domain=domain,
                chunk_chars=chunk_chars,
                chunk_overlap=chunk_overlap,
                max_chunks=max_chunks,
            )
            for entry in work_entries
        ]
        for future in as_completed(futures):
            rows = future.result()
            _append_rows(out, rows, columns, lock)
            written_rows += len(rows)
            if rows:
                logger.info("Wrote %d rows for %s status=%s", len(rows), rows[0].get("article_key"), rows[0].get("extraction_status"))

    logger.info("Saved extracted dataset: %s (+%d rows)", out, written_rows)
    return out


def main():
    import argparse
    p = argparse.ArgumentParser(description='???????API/???/??/??/ICL??????')
    p.add_argument('--elsevier-key', required=True, help='Elsevier API Key')
    p.add_argument('--keyword', required=True, help='?????')
    p.add_argument('--count', type=int, default=25, help='????')
    p.add_argument('--metrics', nargs='+', default=None, help='??????????????????')
    p.add_argument('--icl', default=None, help='ICL ??JSON??????')
    p.add_argument('--schema', default=None, help='Schema JSON path for schema-first extraction')
    p.add_argument('--icl-bank', default=None, help='ICL bank JSONL/JSON path for dynamic ICL selection')
    p.add_argument('--icl-top-k', type=int, default=3, help='Number of dynamic ICL examples')
    p.add_argument('--domain', default=None, help='Domain label used by dynamic ICL selection')
    p.add_argument('--workers', type=int, default=1, help='Number of concurrent article workers')
    p.add_argument('--no-resume', action='store_true', help='Disable resume; process articles even if output CSV already contains them')
    p.add_argument('--chunk-chars', type=int, default=14000, help='Maximum characters per LLM extraction chunk')
    p.add_argument('--chunk-overlap', type=int, default=1000, help='Character overlap between adjacent chunks')
    p.add_argument('--max-chunks', type=int, default=8, help='Maximum chunks processed per article')
    p.add_argument('--elsevier-insttoken', default=None, help='Elsevier InstToken????')
    p.add_argument('--llm-key', default=None, help='LLM/OpenAI??API?Key????')
    p.add_argument('--llm-base', default=None, help='LLM API Base?????????')
    p.add_argument('--llm-model', default=None, help='LLM????????????')
    p.add_argument('--out', default=None, help='??CSV??????')
    args = p.parse_args()

    extract_dataset(
        elsevier_api_key=args.elsevier_key,
        keyword=args.keyword,
        count=args.count,
        metrics=args.metrics,
        icl_json_path=args.icl,
        elsevier_inst_token=args.elsevier_insttoken,
        llm_api_key=args.llm_key,
        llm_api_base=args.llm_base,
        llm_model=args.llm_model,
        out_csv=args.out,
        schema_path=args.schema,
        icl_bank_path=args.icl_bank,
        icl_top_k=args.icl_top_k,
        domain=args.domain,
        workers=args.workers,
        resume=not args.no_resume,
        chunk_chars=args.chunk_chars,
        chunk_overlap=args.chunk_overlap,
        max_chunks=args.max_chunks,
    )


if __name__ == '__main__':
    main()
