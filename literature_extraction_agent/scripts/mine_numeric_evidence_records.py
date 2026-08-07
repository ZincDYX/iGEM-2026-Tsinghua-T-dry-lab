from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "essay" / "pdf_text_cache_20000_direct_manifest.csv"
DEFAULT_OUT = ROOT / "essay" / "high_recall_numeric_experimental_evidence.csv"
DEFAULT_SUMMARY = ROOT / "essay" / "high_recall_numeric_experimental_evidence_summary.json"


VALUE_UNIT_RE = re.compile(
    r"(?P<value>[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:\s*(?:-|to|/)\s*[+-]?(?:\d+(?:\.\d+)?|\.\d+))?)"
    r"\s*(?P<unit>%|percent|fold|x|mg\s*/\s*l|g\s*/\s*l|ug\s*/\s*l|ng\s*/\s*l|"
    r"mg/l|g/l|ug/l|ng/l|mg\s*/\s*g|mg/g|g/kg|mg/kg|"
    r"um|mu\s*m|mm|nm|pm|mM|uM|nM|"
    r"u\s*/\s*mg|U\s*/\s*mg|U/mg|U\s*/\s*ml|U/ml|"
    r"h|hr|hrs|min|s|day|days|"
    r"c|degc|degree\s*c|mol\s*%|wt\s*%|v/v|w/v|od600|nm|rpm|"
    r"cells/ml|cfu/ml|g\s*dcw/l|gdcw/l)\b",
    re.IGNORECASE,
)

BARE_VALUE_RE = re.compile(
    r"\b(?P<value>[+-]?(?:\d+(?:\.\d+)?|\.\d+))\b"
)

SIGNAL_TERMS = [
    "activity", "specific activity", "relative activity", "enzyme", "catalase",
    "conversion", "yield", "titer", "titre", "production", "produced",
    "productivity", "concentration", "dose", "threshold", "bistable",
    "response", "fold", "increase", "decrease", "mutant", "variant",
    "substrate", "product", "fermentation", "culture", "medium",
    "strain", "engineered", "heterologous", "biosynthesis", "pathway",
    "metabolic", "bioreactor", "glabridin", "flavonoid", "isoflavonoid",
    "isoprenoid", "terpenoid", "naringenin", "liquiritigenin",
    "phase separation", "condensate", "droplet", "puncta", "foci",
    "granule", "aggregate", "scaffold", "channeling", "partitioning",
    "frap", "recovery", "microscopy", "table", "figure", "supplementary",
    "pH", "temperature", "incubated", "reaction", "assay",
]

NEGATIVE_TERMS = [
    "received", "accepted", "published", "copyright", "creative commons",
    "license", "doi.org", "http://", "https://", "email", "correspondence",
    "department", "university", "references", "bibliography",
]

METRIC_HINTS = [
    ("titer", ["mg/l", "g/l", "titer", "titre", "production"]),
    ("yield", ["yield", "%", "percent", "mol %"]),
    ("conversion", ["conversion"]),
    ("activity", ["activity", "u/mg", "u/ml", "enzyme"]),
    ("kinetics", ["kcat", "km", "vmax"]),
    ("condition", ["ph", "temperature", "incubated", "reaction", "assay", "min", " h", "hr"]),
    ("llps", ["phase separation", "condensate", "droplet", "frap", "puncta", "foci"]),
    ("expression_or_fermentation", ["strain", "culture", "fermentation", "bioreactor", "od600", "dcw"]),
]


def norm_text(text: str) -> str:
    replacements = {
        "\u00b5": "u",
        "\u03bc": "u",
        "\uff05": "%",
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u00b0": "deg",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def safe_abs(root: Path, value: str) -> Path:
    p = Path(value)
    if not p.is_absolute():
        p = root / p
    return p


def split_units(paragraph: str) -> list[str]:
    text = re.sub(r"\s+", " ", paragraph).strip()
    if not text:
        return []
    pieces = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(])", text)
    out: list[str] = []
    for piece in pieces:
        piece = piece.strip()
        if len(piece) <= 700:
            out.append(piece)
            continue
        clauses = re.split(r";\s+|,\s+(?=(?:whereas|while|and|but|with|under|at)\b)", piece)
        out.extend(c.strip() for c in clauses if c.strip())
    return out


def section_hint(context: str) -> str:
    low = context.lower()
    if "supplementary" in low or "supplemental" in low:
        return "supplementary"
    if "table" in low:
        return "table"
    if "figure" in low or "fig." in low:
        return "figure"
    if "method" in low or "assay" in low or "reaction" in low:
        return "methods_or_assay"
    if "result" in low or "production" in low or "yield" in low:
        return "results"
    return "text"


def metric_hint(context: str, unit: str) -> str:
    low = context.lower()
    unit_low = unit.lower()
    if unit_low in {"h", "hr", "hrs", "min", "s", "day", "days", "rpm"}:
        return "condition"
    if unit_low in {"c", "degc", "degreec"}:
        return "condition"
    if unit_low in {"um", "nm", "pm"} and ("bar =" in low or "scale bar" in low):
        return "microscopy_scale"
    if unit_low in {"um", "mm", "nm", "pm", "mm"} and any(t in low for t in ["concentration", "substrate", "iptg", "atp", "nadh", "nadph", "medium", "buffer"]):
        return "condition"
    if unit_low in {"mg/l", "g/l", "ug/l", "ng/l", "gdcw/l"} and any(t in low for t in ["titer", "titre", "production", "produced", "reached"]):
        return "titer"
    if unit_low in {"%", "percent", "mol%", "wt%", "v/v", "w/v"}:
        if "conversion" in low:
            return "conversion"
        if "yield" in low:
            return "yield"
    for name, terms in METRIC_HINTS:
        for term in terms:
            if term in low or term in unit_low:
                return name
    return "numeric_experimental"


def score_context(context: str, unit: str) -> int:
    low = context.lower()
    score = 0
    for term in SIGNAL_TERMS:
        if term.lower() in low:
            score += 3
    if VALUE_UNIT_RE.search(context):
        score += 8
    if re.search(r"\b(table|fig\.|figure|supplementary)\b", low):
        score += 6
    if re.search(r"\b\d+(?:\.\d+)?\s*(?:%|fold|mg/l|g/l|u/mg|u/ml|um|mm|nm)\b", low):
        score += 10
    if unit:
        score += 4
    for term in NEGATIVE_TERMS:
        if term in low:
            score -= 8
    return score


def is_negative(context: str) -> bool:
    low = context.lower()
    if len(context) < 25:
        return True
    if sum(term in low for term in NEGATIVE_TERMS) >= 2:
        return True
    if low.count("http") > 0:
        return True
    if re.fullmatch(r"[\d\s,.;:()/-]+", context):
        return True
    return False


def iter_contexts(text: str) -> list[str]:
    text = norm_text(text)
    paras = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
    contexts: list[str] = []
    for para in paras:
        lines = [re.sub(r"\s+", " ", line).strip() for line in para.splitlines() if line.strip()]
        if len(lines) >= 3:
            for i, line in enumerate(lines):
                if VALUE_UNIT_RE.search(line) or any(t.lower() in line.lower() for t in SIGNAL_TERMS):
                    start = max(0, i - 1)
                    end = min(len(lines), i + 2)
                    contexts.append(" ".join(lines[start:end]))
        contexts.extend(split_units(para))
    return contexts


def iter_fast_contexts(text: str, *, max_contexts: int) -> list[str]:
    text = norm_text(text)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
    contexts: list[str] = []
    seen: set[str] = set()

    def add(context: str) -> None:
        if len(contexts) >= max_contexts:
            return
        context = re.sub(r"\s+", " ", context).strip()
        if not context or context in seen:
            return
        low = context.lower()
        if VALUE_UNIT_RE.search(context) or any(term.lower() in low for term in SIGNAL_TERMS):
            seen.add(context)
            contexts.append(context[:1200])

    for i, line in enumerate(lines):
        low = line.lower()
        if VALUE_UNIT_RE.search(line) or any(term.lower() in low for term in SIGNAL_TERMS):
            add(" ".join(lines[max(0, i - 1): min(len(lines), i + 2)]))
        if len(contexts) >= max_contexts:
            break

    if len(contexts) < max_contexts:
        paras = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
        for para in paras:
            para_one = re.sub(r"\s+", " ", para).strip()
            low = para_one.lower()
            if VALUE_UNIT_RE.search(para_one) or any(term.lower() in low for term in SIGNAL_TERMS):
                if len(para_one) <= 1200:
                    add(para_one)
                else:
                    for piece in split_units(para_one):
                        add(piece)
                        if len(contexts) >= max_contexts:
                            break
            if len(contexts) >= max_contexts:
                break
    return contexts


def mine_article(row: dict[str, str], *, max_per_paper: int, max_contexts: int) -> list[dict[str, str]]:
    text_path = safe_abs(ROOT, row.get("text_file", ""))
    if not text_path.exists():
        return []
    text = text_path.read_text(encoding="utf-8", errors="ignore")
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()
    for context in iter_fast_contexts(text, max_contexts=max_contexts):
        if is_negative(context):
            continue
        low = context.lower()
        if not any(term.lower() in low for term in SIGNAL_TERMS) and not VALUE_UNIT_RE.search(context):
            continue
        matches = list(VALUE_UNIT_RE.finditer(context))
        if not matches and any(term.lower() in low for term in SIGNAL_TERMS):
            matches = list(BARE_VALUE_RE.finditer(context))
        for m in matches:
            value = m.group("value")
            unit = (m.groupdict().get("unit") or "").replace(" ", "")
            near_left = context[max(0, m.start() - 30): m.start()].lower()
            if re.search(r"(?:scale\s+)?bar\s*=\s*$", near_left):
                continue
            score = score_context(context, unit)
            if score < 8:
                continue
            evidence = context[:900]
            key = hashlib.sha1((row.get("doi", "") + value + unit + evidence[:180]).encode("utf-8", errors="ignore")).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            candidates.append({
                "evidence_id": key[:16],
                "rank": row.get("rank", ""),
                "candidate_id": row.get("candidate_id", ""),
                "doi": row.get("doi", ""),
                "title": row.get("title", ""),
                "metric_hint": metric_hint(context, unit),
                "value_text": value,
                "unit_text": unit,
                "section_hint": section_hint(context),
                "score": str(score),
                "evidence": evidence,
                "text_file": row.get("text_file", ""),
            })
            if len(candidates) > max_per_paper * 12:
                candidates.sort(key=lambda r: int(r["score"]), reverse=True)
                candidates = candidates[: max_per_paper * 6]
    candidates.sort(key=lambda r: int(r["score"]), reverse=True)
    return candidates[:max_per_paper]


FIELDNAMES = [
    "evidence_id", "rank", "candidate_id", "doi", "title", "metric_hint",
    "value_text", "unit_text", "section_hint", "score", "evidence", "text_file",
]


def row_key(row: dict[str, str]) -> str:
    return (row.get("text_file") or row.get("doi") or row.get("title") or "").strip()


def load_done_state(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {str(x) for x in data.get("done_text_files", [])}
    except Exception:
        return set()


def save_done_state(path: Path, done: set[str]) -> None:
    payload = {"done_count": len(done), "done_text_files": sorted(done)}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--max-per-paper", type=int, default=8)
    parser.add_argument("--max-contexts-per-paper", type=int, default=160)
    parser.add_argument("--target-rows", type=int, default=10000)
    parser.add_argument("--work-out", type=Path, default=None)
    parser.add_argument("--state", type=Path, default=None)
    parser.add_argument("--fresh", action="store_true", help="Ignore and overwrite previous incremental work files.")
    args = parser.parse_args()
    if args.work_out is None:
        args.work_out = args.out.with_name(args.out.stem + ".work.csv")
    if args.state is None:
        args.state = args.out.with_name(args.out.stem + ".state.json")

    with args.manifest.open("r", encoding="utf-8-sig", newline="") as f:
        manifest_rows = [r for r in csv.DictReader(f) if r.get("status") == "cached"]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.work_out.parent.mkdir(parents=True, exist_ok=True)
    if args.fresh:
        if args.work_out.exists():
            args.work_out.unlink()
        if args.state.exists():
            args.state.unlink()

    done = load_done_state(args.state)
    write_header = not args.work_out.exists() or args.work_out.stat().st_size == 0
    rows_written_this_run = 0
    processed_this_run = 0
    with args.work_out.open("a", encoding="utf-8-sig", newline="") as wf:
        writer = csv.DictWriter(wf, fieldnames=FIELDNAMES, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        for i, row in enumerate(manifest_rows, start=1):
            key = row_key(row)
            if key in done:
                continue
            mined = mine_article(
                row,
                max_per_paper=max(1, args.max_per_paper),
                max_contexts=max(20, args.max_contexts_per_paper),
            )
            if mined:
                writer.writerows(mined)
                rows_written_this_run += len(mined)
            processed_this_run += 1
            done.add(key)
            if processed_this_run % 25 == 0:
                wf.flush()
                save_done_state(args.state, done)
            if processed_this_run % 100 == 0:
                print(f"processed_this_run={processed_this_run} done_total={len(done)}/{len(manifest_rows)} rows_this_run={rows_written_this_run}", flush=True)
        wf.flush()
    save_done_state(args.state, done)

    all_rows: list[dict[str, str]] = []
    if args.work_out.exists():
        with args.work_out.open("r", encoding="utf-8-sig", newline="") as f:
            all_rows = list(csv.DictReader(f))

    all_rows.sort(key=lambda r: (int(r["score"]), r["doi"]), reverse=True)
    if args.target_rows > 0:
        all_rows = all_rows[: args.target_rows]

    with args.out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    by_metric: dict[str, int] = {}
    by_section: dict[str, int] = {}
    doi_set = set()
    text_files_with_rows = set()
    for row in all_rows:
        by_metric[row["metric_hint"]] = by_metric.get(row["metric_hint"], 0) + 1
        by_section[row["section_hint"]] = by_section.get(row["section_hint"], 0) + 1
        if row.get("doi"):
            doi_set.add(row["doi"].lower())
        if row.get("text_file"):
            text_files_with_rows.add(row["text_file"])
    summary = {
        "cached_papers_scanned": len(manifest_rows),
        "cached_papers_done_state": len(done),
        "processed_this_run": processed_this_run,
        "rows_written_this_run_to_work_file": rows_written_this_run,
        "papers_with_candidate_evidence_before_top_cut": len(text_files_with_rows),
        "rows_written": len(all_rows),
        "unique_dois_written": len(doi_set),
        "max_per_paper": args.max_per_paper,
        "target_rows": args.target_rows,
        "by_metric_hint": dict(sorted(by_metric.items())),
        "by_section_hint": dict(sorted(by_section.items())),
        "output": str(args.out),
        "work_output": str(args.work_out),
        "state": str(args.state),
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
