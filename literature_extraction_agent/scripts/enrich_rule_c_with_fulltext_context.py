from __future__ import annotations

import argparse
import csv
import json
import re
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULE = ROOT / "essay" / "rule_strict_tiered_database.csv"
DEFAULT_MANIFEST = ROOT / "essay" / "pdf_text_cache_20000_direct_manifest.csv"
DEFAULT_OUT = ROOT / "essay" / "rule_c_fulltext_context.csv"
DEFAULT_SUMMARY = ROOT / "essay" / "rule_c_fulltext_context_summary.json"


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def safe_path(value: str) -> Path:
    p = Path(value)
    if not p.is_absolute():
        p = ROOT / p
    return p


def metric_value(row: dict[str, str], metric: str) -> tuple[str, str, str]:
    return norm(row.get(f"{metric}_value", "")), norm(row.get(f"{metric}_unit", "")), norm(row.get(f"{metric}_evidence", ""))


def read_manifest(path: Path) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            doi = norm(row.get("doi", "")).lower()
            if doi and row.get("status") == "cached" and doi not in out:
                out[doi] = row
    return out


def locate_context(text: str, evidence: str, *, window: int) -> tuple[str, str, float]:
    text_one = re.sub(r"\s+", " ", text)
    evidence_one = norm(evidence)
    if not text_one or not evidence_one:
        return "", "empty", 0.0
    idx = text_one.lower().find(evidence_one[:180].lower())
    if idx < 0:
        anchor = evidence_one[:80].lower()
        idx = text_one.lower().find(anchor)
    if idx >= 0:
        start = max(0, idx - window)
        end = min(len(text_one), idx + len(evidence_one) + window)
        return text_one[start:end], "exact_or_anchor", 1.0

    # Fallback: scan chunks using the most distinctive evidence words.
    evidence_words = [w for w in re.findall(r"[A-Za-z0-9_.+-]+", evidence_one.lower()) if len(w) > 3]
    evidence_words = evidence_words[:80]
    best = (0.0, 0, "")
    step = max(1000, window // 2)
    size = max(2500, window * 2)
    for start in range(0, len(text_one), step):
        chunk = text_one[start:start + size]
        if not chunk:
            continue
        word_hits = sum(1 for w in evidence_words if w in chunk.lower())
        ratio = SequenceMatcher(None, evidence_one[:500].lower(), chunk[:1200].lower()).ratio()
        score = ratio + min(0.5, word_hits / 80)
        if score > best[0]:
            best = (score, start, chunk)
    if best[2]:
        start = max(0, best[1] - window // 2)
        end = min(len(text_one), best[1] + size + window // 2)
        return text_one[start:end], "fuzzy", round(best[0], 4)
    return "", "not_found", 0.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rule", type=Path, default=DEFAULT_RULE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--window", type=int, default=2600)
    args = parser.parse_args()

    manifest = read_manifest(args.manifest)
    rows_out: list[dict[str, str]] = []
    fieldnames: list[str] = []
    located_counts: dict[str, int] = {}
    missing_text = 0
    with args.rule.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        extra = ["text_file", "fulltext_context", "context_location_method", "context_match_score", "context_chars"]
        out_fields = fieldnames + [x for x in extra if x not in fieldnames]
        for row in reader:
            tier = norm(row.get("rule_strict_tier", ""))
            if not tier.startswith("strict_C"):
                continue
            doi = norm(row.get("doi", "")).lower()
            metric = norm(row.get("structured_metric", ""))
            _, _, evidence = metric_value(row, metric)
            manifest_row = manifest.get(doi)
            out_row = dict(row)
            if not manifest_row:
                out_row["text_file"] = ""
                out_row["fulltext_context"] = ""
                out_row["context_location_method"] = "missing_manifest"
                out_row["context_match_score"] = "0"
                out_row["context_chars"] = "0"
                missing_text += 1
                rows_out.append(out_row)
                continue
            text_file = manifest_row.get("text_file", "")
            text_path = safe_path(text_file)
            out_row["text_file"] = text_file
            if not text_path.exists():
                out_row["fulltext_context"] = ""
                out_row["context_location_method"] = "missing_text_file"
                out_row["context_match_score"] = "0"
                out_row["context_chars"] = "0"
                missing_text += 1
                rows_out.append(out_row)
                continue
            text = text_path.read_text(encoding="utf-8", errors="ignore")
            context, method, score = locate_context(text, evidence, window=args.window)
            out_row["fulltext_context"] = context
            out_row["context_location_method"] = method
            out_row["context_match_score"] = str(score)
            out_row["context_chars"] = str(len(context))
            located_counts[method] = located_counts.get(method, 0) + 1
            rows_out.append(out_row)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows_out)

    by_tier: dict[str, int] = {}
    by_metric: dict[str, int] = {}
    dois: set[str] = set()
    for row in rows_out:
        by_tier[row.get("rule_strict_tier", "")] = by_tier.get(row.get("rule_strict_tier", ""), 0) + 1
        by_metric[row.get("structured_metric", "")] = by_metric.get(row.get("structured_metric", ""), 0) + 1
        doi = norm(row.get("doi", "")).lower()
        if doi:
            dois.add(doi)
    summary = {
        "rule_c_rows": len(rows_out),
        "unique_dois": len(dois),
        "missing_text": missing_text,
        "by_location_method": dict(sorted(located_counts.items())),
        "by_rule_strict_tier": dict(sorted(by_tier.items())),
        "by_structured_metric": dict(sorted(by_metric.items())),
        "output": str(args.out),
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
