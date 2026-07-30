from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .schema import ExtractionSchema


VALUE_UNIT_RE = re.compile(
    r"(?P<value>[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:\s*(?:-|to|/)\s*[+-]?(?:\d+(?:\.\d+)?|\.\d+))?)"
    r"\s*(?P<unit>%|percent|fold|x|mg\s*/\s*l|g\s*/\s*l|ug\s*/\s*l|ng\s*/\s*l|"
    r"mg/l|g/l|ug/l|ng/l|u\s*/\s*mg|U\s*/\s*mg|U/mg|U\s*/\s*ml|U/ml|"
    r"h|hr|hrs|min|s|day|days|c|degc|degree\s*c|mM|uM|nM|um|nm|od600)(?=\W|$)",
    re.IGNORECASE,
)

SIGNAL_TERMS = (
    "activity",
    "specific activity",
    "relative activity",
    "conversion",
    "yield",
    "titer",
    "titre",
    "production",
    "concentration",
    "substrate",
    "product",
    "reaction",
    "assay",
    "fermentation",
    "glabridin",
    "vestitol",
    "preglabridin",
    "phase separation",
    "condensate",
    "droplet",
    "frap",
    "scaffold",
)

NEGATIVE_TERMS = (
    "copyright",
    "creative commons",
    "license",
    "doi.org",
    "references",
    "bibliography",
    "correspondence",
)

RESULT_METRICS = {
    "substrate_conversion",
    "glabridin_titer",
    "leakage_ratio",
    "kcat",
    "km",
    "llps_state",
}

CONDITION_METRICS = {
    "reaction_temperature",
    "reaction_ph",
    "reaction_time",
    "substrate_concentration",
    "cofactor",
    "llps_trigger",
}


@dataclass(frozen=True)
class CandidateArticle:
    article_id: str
    title: str = ""
    doi: str = ""
    pii: str = ""
    text_file: Path | None = None
    text: str | None = None
    rank: int | None = None
    source: str = ""


@dataclass(frozen=True)
class EvidenceCandidate:
    evidence_id: str
    article_id: str
    title: str
    doi: str
    pii: str
    metric_hint: str
    value_text: str
    unit_text: str
    score: int
    evidence: str
    text_file: str = ""


def read_manifest(path: Path) -> list[CandidateArticle]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [candidate_from_row(row, base_dir=path.parent) for row in csv.DictReader(handle)]


def candidate_from_row(row: dict[str, str], *, base_dir: Path) -> CandidateArticle:
    text_file = _optional_path(row.get("text_file", ""), base_dir)
    return CandidateArticle(
        article_id=_first_nonempty(row, "article_id", "candidate_id", "doi", "pii", "title"),
        title=_norm(row.get("title", "")),
        doi=_norm(row.get("doi", "")),
        pii=_norm(row.get("pii", "")),
        text_file=text_file,
        rank=_parse_int(row.get("rank", "")),
        source=_norm(row.get("source", "")),
    )


def mine_numeric_evidence(
    articles: Iterable[CandidateArticle],
    *,
    max_per_paper: int = 8,
    max_contexts_per_paper: int = 160,
) -> list[EvidenceCandidate]:
    candidates: list[EvidenceCandidate] = []
    for article in articles:
        text = _article_text(article)
        if not text:
            continue
        mined = _mine_article(article, text, max_per_paper=max_per_paper, max_contexts=max_contexts_per_paper)
        candidates.extend(mined)
    candidates.sort(key=lambda item: (item.score, item.doi, item.evidence_id), reverse=True)
    return candidates


def structure_evidence_rows(evidence_rows: Iterable[EvidenceCandidate], schema: ExtractionSchema) -> list[dict[str, str]]:
    metrics = list(schema.metrics)
    rows: list[dict[str, str]] = []
    for evidence in evidence_rows:
        target_metric = map_hint_to_metric(evidence.metric_hint, metrics)
        row = _empty_structured_row(metrics)
        row.update(
            {
                "article_id": evidence.article_id,
                "doi": evidence.doi,
                "pii": evidence.pii,
                "title": evidence.title,
                "schema_id": schema.schema_id,
                "structured_metric": target_metric,
                "quality_label": _quality_label(evidence.score),
                "source_score": str(evidence.score),
                "data_source_type_value": "numeric_evidence_mining",
                "data_source_type_evidence": evidence.evidence,
            }
        )
        _put_metric(row, target_metric, evidence.value_text, evidence.unit_text, evidence.evidence)
        rows.append(row)
    return rows


def aggregate_records(rows: Iterable[dict[str, str]], schema: ExtractionSchema) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    metrics = list(schema.metrics)
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(_evidence_group_key(row), []).append(row)

    clean: list[dict[str, str]] = []
    excluded: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for group_rows in grouped.values():
        for result_metric in _result_metrics_for_group(group_rows, metrics):
            out = _base_aggregate_row(group_rows[0], schema)
            _copy_best_context(out, group_rows, metrics)
            result_row = _best_row(group_rows, result_metric)
            if result_row is not None:
                value, unit, evidence = _metric_triplet(result_row, result_metric)
                _put_metric(out, result_metric, value, unit, evidence)
                out["primary_result_metric"] = result_metric
                out["primary_result_value"] = value
                out["primary_result_unit"] = unit
                out["primary_result_evidence"] = evidence
            out["source_row_count"] = str(len(group_rows))
            out["source_scores"] = "; ".join(sorted({_norm(row.get("source_score", "")) for row in group_rows}, reverse=True))
            out["aggregate_record_id"] = _stable_record_id(out)
            clean_level, reason = _clean_level(out)
            out["clean_level"] = clean_level
            out["exclude_reason"] = reason
            if not clean_level:
                excluded.append(out)
                continue
            if out["aggregate_record_id"] in seen_ids:
                out["exclude_reason"] = "duplicate_after_aggregation"
                excluded.append(out)
                continue
            seen_ids.add(out["aggregate_record_id"])
            clean.append(out)
    return clean, excluded


def build_database_from_manifest(
    *,
    manifest: Path,
    schema: ExtractionSchema,
    output_dir: Path,
    max_per_paper: int = 8,
    max_contexts_per_paper: int = 160,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    articles = read_manifest(manifest)
    evidence = mine_numeric_evidence(
        articles,
        max_per_paper=max_per_paper,
        max_contexts_per_paper=max_contexts_per_paper,
    )
    structured = structure_evidence_rows(evidence, schema)
    clean, excluded = aggregate_records(structured, schema)

    evidence_csv = output_dir / "numeric_evidence.csv"
    structured_csv = output_dir / "structured_records.csv"
    clean_csv = output_dir / "clean_database.csv"
    excluded_csv = output_dir / "excluded_records.csv"
    summary_json = output_dir / "summary.json"
    write_csv(evidence_csv, [candidate_to_row(item) for item in evidence])
    write_csv(structured_csv, structured)
    write_csv(clean_csv, clean)
    write_csv(excluded_csv, excluded)
    summary = {
        "manifest": str(manifest),
        "articles": len(articles),
        "numeric_evidence_rows": len(evidence),
        "structured_rows": len(structured),
        "clean_records": len(clean),
        "excluded_records": len(excluded),
        "outputs": {
            "numeric_evidence": str(evidence_csv),
            "structured_records": str(structured_csv),
            "clean_database": str(clean_csv),
            "excluded_records": str(excluded_csv),
            "summary": str(summary_json),
        },
    }
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def candidate_to_row(candidate: EvidenceCandidate) -> dict[str, Any]:
    return {
        "evidence_id": candidate.evidence_id,
        "article_id": candidate.article_id,
        "title": candidate.title,
        "doi": candidate.doi,
        "pii": candidate.pii,
        "metric_hint": candidate.metric_hint,
        "value_text": candidate.value_text,
        "unit_text": candidate.unit_text,
        "score": candidate.score,
        "evidence": candidate.evidence,
        "text_file": candidate.text_file,
    }


def map_hint_to_metric(hint: str, metrics: list[str]) -> str:
    hint = hint.lower()
    preferred = {
        "titer": "glabridin_titer",
        "yield": "substrate_conversion",
        "conversion": "substrate_conversion",
        "activity": "kcat" if "kcat" in metrics else "substrate_conversion",
        "kinetics": "kcat" if "kcat" in metrics else "km",
        "condition_time": "reaction_time",
        "condition_temperature": "reaction_temperature",
        "condition_concentration": "substrate_concentration",
        "llps": "llps_state",
    }
    metric = preferred.get(hint, "")
    if metric in metrics:
        return metric
    for fallback in ("glabridin_titer", "substrate_conversion", "reaction_time", "llps_state"):
        if fallback in metrics:
            return fallback
    return metrics[0]


def _mine_article(article: CandidateArticle, text: str, *, max_per_paper: int, max_contexts: int) -> list[EvidenceCandidate]:
    candidates: list[EvidenceCandidate] = []
    seen: set[str] = set()
    for context in _iter_contexts(text, max_contexts=max_contexts):
        if _is_negative(context):
            continue
        for match in VALUE_UNIT_RE.finditer(context):
            value = match.group("value")
            unit = (match.groupdict().get("unit") or "").replace(" ", "")
            score = _score_context(context, unit)
            if score < 8:
                continue
            evidence = context[:900]
            digest = hashlib.sha1(
                "|".join([article.doi, value, unit, evidence[:180]]).encode("utf-8", errors="ignore")
            ).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            candidates.append(
                EvidenceCandidate(
                    evidence_id=digest[:16],
                    article_id=article.article_id,
                    title=article.title,
                    doi=article.doi,
                    pii=article.pii,
                    metric_hint=_metric_hint(context, unit),
                    value_text=value,
                    unit_text=unit,
                    score=score,
                    evidence=evidence,
                    text_file=str(article.text_file or ""),
                )
            )
    candidates.sort(key=lambda item: item.score, reverse=True)
    return candidates[:max_per_paper]


def _iter_contexts(text: str, *, max_contexts: int) -> list[str]:
    text = _normalize_text(text)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
    contexts: list[str] = []
    seen: set[str] = set()

    def add(value: str) -> None:
        if len(contexts) >= max_contexts:
            return
        value = re.sub(r"\s+", " ", value).strip()
        if not value or value in seen:
            return
        low = value.lower()
        if VALUE_UNIT_RE.search(value) or any(term in low for term in SIGNAL_TERMS):
            seen.add(value)
            contexts.append(value[:1200])

    for index, line in enumerate(lines):
        low = line.lower()
        if VALUE_UNIT_RE.search(line) or any(term in low for term in SIGNAL_TERMS):
            add(" ".join(lines[max(0, index - 1) : min(len(lines), index + 2)]))
    if len(contexts) < max_contexts:
        for paragraph in re.split(r"\n\s*\n+", text):
            add(paragraph)
            if len(contexts) >= max_contexts:
                break
    return contexts


def _metric_hint(context: str, unit: str) -> str:
    low = context.lower()
    unit_low = unit.lower()
    if unit_low in {"h", "hr", "hrs", "min", "s", "day", "days"}:
        return "condition_time"
    if unit_low in {"c", "degc", "degreec"}:
        return "condition_temperature"
    if unit_low in {"mm", "um", "nm", "mmol", "mm", "um", "nm"}:
        return "condition_concentration"
    if any(term in low for term in ("kcat", "km", "vmax")):
        return "kinetics"
    if any(term in low for term in ("titer", "titre", "production", "produced")):
        return "titer"
    if "yield" in low:
        return "yield"
    if "conversion" in low:
        return "conversion"
    if "activity" in low:
        return "activity"
    if any(term in low for term in ("phase separation", "condensate", "droplet", "frap")):
        return "llps"
    return "numeric_experimental"


def _score_context(context: str, unit: str) -> int:
    low = context.lower()
    score = 8 if VALUE_UNIT_RE.search(context) else 0
    score += 4 if unit else 0
    score += 3 * sum(1 for term in SIGNAL_TERMS if term in low)
    score -= 8 * sum(1 for term in NEGATIVE_TERMS if term in low)
    return score


def _is_negative(context: str) -> bool:
    low = context.lower()
    return len(context) < 25 or low.count("http") > 0 or sum(term in low for term in NEGATIVE_TERMS) >= 2


def _empty_structured_row(metrics: list[str]) -> dict[str, str]:
    row = {
        "article_id": "",
        "doi": "",
        "pii": "",
        "title": "",
        "schema_id": "",
        "structured_metric": "",
        "quality_label": "",
        "source_score": "",
    }
    for metric in metrics:
        row[f"{metric}_value"] = ""
        row[f"{metric}_unit"] = ""
        row[f"{metric}_evidence"] = ""
    return row


def _put_metric(row: dict[str, str], metric: str, value: str, unit: str, evidence: str) -> None:
    row[f"{metric}_value"] = _norm(value)
    row[f"{metric}_unit"] = _norm(unit)
    row[f"{metric}_evidence"] = _norm(evidence)


def _metric_triplet(row: dict[str, str], metric: str) -> tuple[str, str, str]:
    return (
        _norm(row.get(f"{metric}_value", "")),
        _norm(row.get(f"{metric}_unit", "")),
        _norm(row.get(f"{metric}_evidence", "")),
    )


def _has_metric(row: dict[str, str], metric: str) -> bool:
    return any(_metric_triplet(row, metric))


def _best_row(rows: list[dict[str, str]], metric: str) -> dict[str, str] | None:
    candidates = [row for row in rows if _has_metric(row, metric)]
    if not candidates:
        return None
    return max(candidates, key=lambda row: (_parse_int(row.get("source_score", "")) or 0, len(_metric_triplet(row, metric)[2])))


def _copy_best_context(out: dict[str, str], rows: list[dict[str, str]], metrics: list[str]) -> None:
    for metric in metrics:
        if metric in RESULT_METRICS:
            continue
        best = _best_row(rows, metric)
        if best is None:
            continue
        value, unit, evidence = _metric_triplet(best, metric)
        _put_metric(out, metric, value, unit, evidence)


def _result_metrics_for_group(rows: list[dict[str, str]], metrics: list[str]) -> list[str]:
    results = []
    for metric in metrics:
        if metric in RESULT_METRICS and any(_has_metric(row, metric) for row in rows):
            results.append(metric)
    return results


def _base_aggregate_row(row: dict[str, str], schema: ExtractionSchema) -> dict[str, str]:
    out = _empty_structured_row(list(schema.metrics))
    out.update(
        {
            "aggregate_record_id": "",
            "article_id": _norm(row.get("article_id", "")),
            "doi": _norm(row.get("doi", "")),
            "pii": _norm(row.get("pii", "")),
            "title": _norm(row.get("title", "")),
            "schema_id": schema.schema_id,
            "source_row_count": "",
            "source_scores": "",
            "primary_result_metric": "",
            "primary_result_value": "",
            "primary_result_unit": "",
            "primary_result_evidence": "",
            "clean_level": "",
            "exclude_reason": "",
        }
    )
    return out


def _clean_level(row: dict[str, str]) -> tuple[str, str]:
    metric = _norm(row.get("primary_result_metric", ""))
    value = _norm(row.get("primary_result_value", ""))
    unit = _norm(row.get("primary_result_unit", ""))
    evidence = _norm(row.get("primary_result_evidence", ""))
    if not metric:
        return "", "no_primary_result_metric"
    if metric != "llps_state" and not re.search(r"\d", value):
        return "", "primary_result_has_no_numeric_value"
    if metric in {"glabridin_titer", "kcat", "km"} and not unit:
        return "", "primary_result_missing_unit"
    if len(evidence) < 25:
        return "", "short_primary_evidence"
    if metric in {"llps_state"}:
        return "A_llps", ""
    if any(_has_metric(row, item) for item in CONDITION_METRICS):
        return "A_result_with_condition", ""
    return "B_result_only", ""


def _stable_record_id(row: dict[str, str]) -> str:
    raw = "|".join(
        [
            _norm(row.get("doi", "")).lower(),
            _norm(row.get("primary_result_metric", "")).lower(),
            _norm(row.get("primary_result_value", "")).lower(),
            _norm(row.get("primary_result_unit", "")).lower(),
            _norm(row.get("primary_result_evidence", ""))[:300].lower(),
        ]
    )
    return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _evidence_group_key(row: dict[str, str]) -> str:
    evidence = ""
    structured_metric = _norm(row.get("structured_metric", ""))
    if structured_metric:
        evidence = _metric_triplet(row, structured_metric)[2]
    if not evidence:
        evidence = _norm(row.get("title", ""))
    digest = hashlib.sha1(evidence[:1200].lower().encode("utf-8", errors="ignore")).hexdigest()[:16]
    return f"{_norm(row.get('doi', '')).lower()}|{digest}"


def _quality_label(score: int) -> str:
    if score >= 30:
        return "high"
    if score >= 18:
        return "medium"
    return "candidate"


def _article_text(article: CandidateArticle) -> str:
    if article.text:
        return article.text
    if article.text_file and article.text_file.exists():
        return article.text_file.read_text(encoding="utf-8", errors="ignore")
    return ""


def _optional_path(value: str, base_dir: Path) -> Path | None:
    value = _norm(value)
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else base_dir / path


def _first_nonempty(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = _norm(row.get(key, ""))
        if value:
            return value
    return hashlib.sha1(json.dumps(row, sort_keys=True).encode("utf-8", errors="ignore")).hexdigest()[:16]


def _normalize_text(text: str) -> str:
    replacements = {"\u00b5": "u", "\u03bc": "u", "\uff05": "%", "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u00b0": "deg"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _parse_int(value: str) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()
