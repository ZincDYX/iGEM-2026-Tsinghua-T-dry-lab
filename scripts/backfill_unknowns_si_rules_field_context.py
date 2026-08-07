# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import fulltext_pro_field_completion as ft


ROOT = ft.ROOT
SRC = ft.DEFAULT_OUTPUT
OUT = ROOT / "essay" / "optimized_experimental_database_with_supplementary_expanded160_union_evidence_aware_fulltext_pro_completed_si_rule_fieldbackfilled.csv"
SUMMARY = ROOT / "essay" / "si_rule_fieldbackfill_summary.json"
SUPP_AGG = ROOT / "essay" / "supplementary_current" / "aggregated_supplementary_current_database.csv"

UNKNOWN = {"", "unknown", "none", "null", "nan", "n/a", "na", "not specified", "not available", "unidentified"}
TEXT_CACHE_LIMIT = 160_000


PRODUCT_LEXICON: list[tuple[str, str, str]] = [
    ("8-prenylnaringenin", "8-prenylnaringenin", "prenylflavonoid"),
    ("prenylflavonoid", "prenylflavonoid", "prenylflavonoid"),
    ("glabridin", "glabridin", "isoflavonoid"),
    ("genistein", "genistein", "isoflavonoid"),
    ("daidzein", "daidzein", "isoflavonoid"),
    ("glycitein", "glycitein", "isoflavonoid"),
    ("isoflavone", "isoflavone", "isoflavonoid"),
    ("isoflavonoid", "isoflavonoid", "isoflavonoid"),
    ("naringenin", "naringenin", "flavonoid"),
    ("pinocembrin", "pinocembrin", "flavonoid"),
    ("liquiritigenin", "liquiritigenin", "flavonoid"),
    ("taxifolin", "taxifolin", "flavonoid"),
    ("kaempferol", "kaempferol", "flavonoid"),
    ("apigenin", "apigenin", "flavonoid"),
    ("quercetin", "quercetin", "flavonoid"),
    ("luteolin", "luteolin", "flavonoid"),
    ("chrysin", "chrysin", "flavonoid"),
    ("flavanone", "flavanone", "flavonoid"),
    ("flavonoid", "flavonoid", "flavonoid"),
    ("resveratrol", "resveratrol", "stilbene"),
    ("piceatannol", "piceatannol", "stilbene"),
    ("stilbene", "stilbene", "stilbene"),
    ("lycopene", "lycopene", "isoprenoid"),
    ("astaxanthin", "astaxanthin", "isoprenoid"),
    ("carotene", "carotene", "isoprenoid"),
    ("carotenoid", "carotenoid", "isoprenoid"),
    ("isoprenoid", "isoprenoid", "isoprenoid"),
    ("limonene", "limonene", "terpenoid"),
    ("taxadiene", "taxadiene", "terpenoid"),
    ("artemisinic acid", "artemisinic acid", "terpenoid"),
    ("amorpha-4,11-diene", "amorpha-4,11-diene", "terpenoid"),
    ("amorphadiene", "amorphadiene", "terpenoid"),
    ("squalene", "squalene", "terpenoid"),
    ("patchoulol", "patchoulol", "terpenoid"),
    ("valencene", "valencene", "terpenoid"),
    ("friedelin", "friedelin", "terpenoid"),
    ("lupeol", "lupeol", "terpenoid"),
    ("triterpenoid", "triterpenoid", "terpenoid"),
    ("terpenoid", "terpenoid", "terpenoid"),
    ("menaquinone-7", "menaquinone-7", "isoprenoid"),
    ("mk-7", "menaquinone-7", "isoprenoid"),
    ("ginsenoside", "ginsenoside", "natural_product"),
    ("alkaloid", "alkaloid", "natural_product"),
    ("polyketide", "polyketide", "natural_product"),
    ("natural product", "natural product", "natural_product"),
]


HOST_LEXICON: list[tuple[str, str, str]] = [
    ("saccharomyces cerevisiae", "Saccharomyces cerevisiae", "yeast"),
    ("s. cerevisiae", "Saccharomyces cerevisiae", "yeast"),
    ("yeast", "yeast", "yeast"),
    ("yarrowia lipolytica", "Yarrowia lipolytica", "yeast"),
    ("pichia pastoris", "Pichia pastoris", "yeast"),
    ("komagataella phaffii", "Komagataella phaffii", "yeast"),
    ("escherichia coli", "Escherichia coli", "bacteria"),
    ("e. coli", "Escherichia coli", "bacteria"),
    ("bacillus subtilis", "Bacillus subtilis", "bacteria"),
    ("corynebacterium glutamicum", "Corynebacterium glutamicum", "bacteria"),
    ("streptomyces", "Streptomyces", "bacteria"),
    ("pseudomonas", "Pseudomonas", "bacteria"),
    ("cyanobacter", "cyanobacteria", "cyanobacteria"),
    ("synechocystis", "Synechocystis", "cyanobacteria"),
    ("synechococcus", "Synechococcus", "cyanobacteria"),
    ("nicotiana benthamiana", "Nicotiana benthamiana", "plant"),
    ("arabidopsis", "Arabidopsis", "plant"),
    ("plant", "plant", "plant"),
    ("hela", "HeLa", "mammalian"),
    ("hek293", "HEK293", "mammalian"),
    ("cho cell", "CHO cells", "mammalian"),
    ("mammalian", "mammalian cells", "mammalian"),
    ("cell-free", "cell-free system", "cell_free"),
    ("cell free", "cell-free system", "cell_free"),
]

SUBSTRATE_LEXICON: list[tuple[str, str]] = [
    ("p-coumaric acid", "p-coumaric acid"),
    ("coumaric acid", "p-coumaric acid"),
    ("cinnamic acid", "cinnamic acid"),
    ("ferulic acid", "ferulic acid"),
    ("caffeic acid", "caffeic acid"),
    ("malonyl-coa", "malonyl-CoA"),
    ("malonyl coa", "malonyl-CoA"),
    ("acetyl-coa", "acetyl-CoA"),
    ("acetyl coa", "acetyl-CoA"),
    ("farnesyl diphosphate", "farnesyl diphosphate"),
    ("fpp", "farnesyl diphosphate"),
    ("geranyl diphosphate", "geranyl diphosphate"),
    ("gpp", "geranyl diphosphate"),
    ("dimethylallyl diphosphate", "dimethylallyl diphosphate"),
    ("dmapp", "dimethylallyl diphosphate"),
    ("isopentenyl diphosphate", "isopentenyl diphosphate"),
    ("ipp", "isopentenyl diphosphate"),
    ("naringenin", "naringenin"),
    ("liquiritigenin", "liquiritigenin"),
    ("pinocembrin", "pinocembrin"),
    ("glucose", "glucose"),
    ("acetate", "acetate"),
    ("tyrosine", "tyrosine"),
    ("phenylalanine", "phenylalanine"),
]


def compact(value: Any) -> str:
    return " ".join(str(value or "").replace("\u00a0", " ").strip().split())


def lower(value: Any) -> str:
    return compact(value).lower()


def is_unknown(value: Any) -> bool:
    return lower(value) in UNKNOWN


def parse_float(value: Any) -> float | None:
    text = compact(value).replace("−", "-")
    nums = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
    if not nums:
        return None
    vals = [float(n) for n in nums]
    return sum(vals) / len(vals)


def short_evidence(text: str, term: str | None = None, limit: int = 360) -> str:
    text = compact(text)
    if term:
        i = text.lower().find(term.lower())
        if i >= 0:
            start = max(0, i - 130)
            end = min(len(text), i + 230)
            text = text[start:end]
    return text[:limit]


def choose_consensus(values: list[str], min_count: int = 2, dominance: float = 0.70) -> str:
    vals = [compact(v) for v in values if not is_unknown(v)]
    if not vals:
        return ""
    counts = Counter(vals)
    top, n = counts.most_common(1)[0]
    if n >= min_count and n / len(vals) >= dominance:
        return top
    if len(counts) == 1 and n >= 1:
        return top
    return ""


def detect_product(text: str) -> tuple[str, str, str]:
    hay = lower(text)
    for term, canonical, family in PRODUCT_LEXICON:
        if re.search(rf"(?<![A-Za-z0-9-]){re.escape(term)}(?![A-Za-z0-9-])", hay):
            return canonical, family, term
    return "", "", ""


def detect_host(text: str) -> tuple[str, str, str]:
    hay = lower(text)
    for term, canonical, group in HOST_LEXICON:
        if re.search(rf"(?<![A-Za-z0-9-]){re.escape(term)}(?![A-Za-z0-9-])", hay):
            return canonical, group, term
    return "", "", ""


def detect_system(text: str) -> tuple[str, str]:
    hay = lower(text)
    patterns = [
        ("whole-cell biotransformation", "whole-cell"),
        ("whole cell biotransformation", "whole-cell"),
        ("whole-cell", "whole-cell"),
        ("whole cell", "whole-cell"),
        ("cell-free", "cell-free"),
        ("cell free", "cell-free"),
        ("purified enzyme", "purified enzyme"),
        ("in vitro", "in vitro"),
        ("in vivo", "in vivo"),
        ("fermentation", "fermentation"),
    ]
    for term, value in patterns:
        if term in hay:
            return value, term
    return "", ""


def detect_substrate(text: str) -> tuple[str, str]:
    # Prefer explicit substrate context rather than any appearance in a title.
    for term, canonical in SUBSTRATE_LEXICON:
        pattern = rf"(?i)(?:substrate|fed|feeding|added|supplied|converted|biotransformed|from|using|precursor)[^.{{}}]{{0,90}}(?<![A-Za-z0-9-]){re.escape(term)}(?![A-Za-z0-9-])"
        if re.search(pattern, text):
            return canonical, term
    return "", ""


def set_label(row: dict[str, str], field: str, value: str, source: str, evidence: str, changes: Counter[str]) -> bool:
    if not value or not is_unknown(row.get(field)):
        return False
    row[field] = value
    src_field = f"{field}_source"
    if src_field in row:
        row[src_field] = source
    row["si_rule_backfill_status"] = "updated"
    row["si_rule_backfill_evidence"] = append_evidence(row.get("si_rule_backfill_evidence", ""), field, evidence)
    changes[field] += 1
    return True


def set_best_value(row: dict[str, str], base_field: str, value: str, unit: str, evidence: str, source: str, changes: Counter[str]) -> bool:
    value_field = f"best_{base_field}_value"
    if value_field not in row or not is_unknown(row.get(value_field)):
        return False
    row[value_field] = value
    for suffix, val in [("_unit", unit), ("_evidence", evidence), ("_source", source)]:
        key = f"best_{base_field}{suffix}"
        if key in row and (suffix == "_source" or is_unknown(row.get(key))):
            row[key] = val
    row["si_rule_backfill_status"] = "updated"
    row["si_rule_backfill_evidence"] = append_evidence(row.get("si_rule_backfill_evidence", ""), base_field, evidence)
    changes[value_field] += 1
    return True


def append_evidence(old: str, field: str, evidence: str) -> str:
    piece = f"{field}: {compact(evidence)[:260]}"
    if not old:
        return piece
    if piece in old:
        return old
    return (old + " || " + piece)[:1200]


def row_text(row: dict[str, str]) -> str:
    keys = [
        "title_clean", "title", "primary_result_evidence", "source_keywords", "best_main_product_name_value",
        "main_product_name_value", "best_substrate_name_value", "substrate_name_value", "best_expression_host_value",
        "expression_host_value", "best_enzyme_name_value", "enzyme_name_value",
    ]
    return " ".join(compact(row.get(k)) for k in keys)


def row_llps_relevant(row: dict[str, str]) -> bool:
    text = " ".join([
        row_text(row),
        compact(row.get("clean_level")),
        compact(row.get("source_keywords")),
        compact(row.get("database_tier")),
        compact(row.get("best_product_family")),
    ]).lower()
    terms = ["llps", "liquid-liquid phase separation", "phase separation", "biomolecular condensate", "protein condensate", "condensate", "membraneless organelle", "llps_system"]
    if any(term in text for term in terms):
        return True
    return any(not is_unknown(row.get(f)) for f in ["best_llps_component_value", "best_llps_state_value", "best_llps_trigger_value"])


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames: list[str] = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_doi_consensus(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        doi = lower(row.get("doi"))
        if doi:
            grouped[doi].append(row)
    out: dict[str, dict[str, str]] = {}
    for doi, items in grouped.items():
        entry: dict[str, str] = {}
        for field in ["best_product_family", "best_canonical_product", "best_host_group", "best_canonical_host"]:
            val = choose_consensus([r.get(field, "") for r in items], min_count=2, dominance=0.80)
            if val:
                entry[field] = val
        for field in ["expression_host", "reaction_system_type", "is_whole_cell"]:
            val = choose_consensus([r.get(f"best_{field}_value", "") for r in items], min_count=2, dominance=0.80)
            if val:
                entry[f"best_{field}_value"] = val
        if entry:
            out[doi] = entry
    return out


def build_supplementary_consensus() -> dict[str, dict[str, str]]:
    if not SUPP_AGG.exists():
        return {}
    rows = read_csv(SUPP_AGG)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        doi = lower(row.get("doi"))
        if doi:
            grouped[doi].append(row)
    out: dict[str, dict[str, str]] = {}
    for doi, items in grouped.items():
        text_blob = " ".join(row_text(r) for r in items[:80])
        product, family, pterm = detect_product(text_blob)
        host, hgroup, hterm = detect_host(text_blob)
        system, sterm = detect_system(text_blob)
        entry: dict[str, str] = {}
        if product:
            entry["best_canonical_product"] = product
            entry["best_product_family"] = family
            entry["product_evidence"] = short_evidence(text_blob, pterm)
        if host:
            entry["best_canonical_host"] = host
            entry["best_host_group"] = hgroup
            entry["host_evidence"] = short_evidence(text_blob, hterm)
        if system:
            entry["best_reaction_system_type_value"] = system
            entry["system_evidence"] = short_evidence(text_blob, sterm)
        for field in ["enzyme_name", "enzyme_source_species", "expression_host", "substrate_name", "main_product_name"]:
            val = choose_consensus([r.get(f"{field}_value", "") for r in items], min_count=2, dominance=0.80)
            if val:
                entry[f"best_{field}_value"] = val
                entry[f"{field}_evidence"] = short_evidence(" ".join(compact(r.get(f"{field}_evidence")) for r in items if compact(r.get(f"{field}_value")) == val))
        if entry:
            out[doi] = entry
    return out


def read_text_files(files: list[str]) -> str:
    chunks: list[str] = []
    total = 0
    for file in files[:10]:
        path = Path(file)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if not text.strip():
            continue
        text = text[:TEXT_CACHE_LIMIT]
        chunks.append(text)
        total += len(text)
        if total >= TEXT_CACHE_LIMIT * 2:
            break
    return "\n".join(chunks)


def context_candidates(text: str) -> dict[str, tuple[str, str, str]]:
    out: dict[str, tuple[str, str, str]] = {}
    compact_text = compact(text)
    low_text = compact_text.lower()
    product, family, pterm = detect_product(compact_text[:80_000])
    if product:
        out["best_canonical_product"] = (product, "", short_evidence(compact_text, pterm))
        out["best_product_family"] = (family, "", short_evidence(compact_text, pterm))
        out["best_main_product_name_value"] = (product, "", short_evidence(compact_text, pterm))
    host, hgroup, hterm = detect_host(compact_text[:80_000])
    if host:
        out["best_canonical_host"] = (host, "", short_evidence(compact_text, hterm))
        out["best_host_group"] = (hgroup, "", short_evidence(compact_text, hterm))
        out["best_expression_host_value"] = (host, "", short_evidence(compact_text, hterm))
    system, sterm = detect_system(compact_text[:80_000])
    if system:
        out["best_reaction_system_type_value"] = (system, "", short_evidence(compact_text, sterm))
        out["best_is_whole_cell_value"] = ("yes" if "whole" in system or system in {"in vivo", "fermentation"} else "no", "", short_evidence(compact_text, sterm))
    substrate, subterm = detect_substrate(compact_text[:80_000])
    if substrate:
        out["best_substrate_name_value"] = (substrate, "", short_evidence(compact_text, subterm))

    temp_hits = []
    for m in re.finditer(r"(?i)(?:at|temperature|incubat(?:ed|ion)|cultivated|fermented|grown)[^.]{0,80}?(\d{1,2}(?:\.\d+)?)\s*(?:°\s*c|deg\s*c|degrees?\s*c|celsius|\bc\b)", compact_text):
        val = float(m.group(1))
        if 10 <= val <= 80:
            temp_hits.append((val, short_evidence(compact_text[max(0, m.start() - 120):m.end() + 160])))
    temp = dominant_numeric(temp_hits, tolerance=0.6, min_count=2)
    if temp:
        out["best_reaction_temperature_value"] = (format_num(temp[0]), "deg C", temp[1])

    ph_hits = []
    for m in re.finditer(r"(?i)\bpH\s*(?:of|=|at|was|is|:)?\s*(\d{1,2}(?:\.\d+)?)", compact_text):
        val = float(m.group(1))
        if 1 <= val <= 14:
            ph_hits.append((val, short_evidence(compact_text[max(0, m.start() - 120):m.end() + 160])))
    ph = dominant_numeric(ph_hits, tolerance=0.15, min_count=2)
    if ph:
        out["best_reaction_ph_value"] = (format_num(ph[0]), "", ph[1])

    time_hits = []
    for m in re.finditer(r"(?i)(?:for|after|incubat(?:ed|ion)|ferment(?:ed|ation)|cultivated|grown)[^.]{0,70}?(\d+(?:\.\d+)?)\s*(h|hr|hrs|hour|hours|min|mins|minute|minutes|day|days|d)\b", compact_text):
        val = float(m.group(1))
        unit = m.group(2)
        if 0 < val <= 10000:
            time_hits.append((val, unit, short_evidence(compact_text[max(0, m.start() - 120):m.end() + 160])))
    time = dominant_time(time_hits, min_count=2)
    if time:
        out["best_reaction_time_value"] = (format_num(time[0]), time[1], time[2])

    od_hits = []
    for m in re.finditer(r"(?i)\bOD\s*600\s*(?:of|=|at|was|is|~|approximately|around|to)?\s*(\d+(?:\.\d+)?)", compact_text):
        val = float(m.group(1))
        if 0.01 <= val <= 200:
            od_hits.append((val, short_evidence(compact_text[max(0, m.start() - 140):m.end() + 140])))
    od = dominant_numeric(od_hits, tolerance=0.1, min_count=2)
    if od:
        out["best_cell_density_od600_value"] = (format_num(od[0]), "OD600", od[1])

    substrate_hits = []
    for m in re.finditer(r"(?i)(?:substrate|p-coumaric acid|coumaric acid|naringenin|glucose|acetate)[^.]{0,90}?(\d+(?:\.\d+)?)\s*(mM|uM|μM|µM|mg/L|g/L)", compact_text):
        val = float(m.group(1))
        unit = m.group(2)
        if 0 < val <= 100000:
            substrate_hits.append((val, unit, short_evidence(compact_text[max(0, m.start() - 140):m.end() + 140])))
    conc = dominant_time(substrate_hits, min_count=2)
    if conc:
        out["best_substrate_concentration_value"] = (format_num(conc[0]), conc[1], conc[2])

    llps_terms = ["liquid-liquid phase separation", "phase separation", "llps", "biomolecular condensate", "protein condensate", "condensate", "membraneless organelle"]
    has_llps_context = any(term in low_text for term in llps_terms)
    for term in llps_terms:
        if term in low_text:
            out["best_llps_state_value"] = ("phase-separated" if term in {"liquid-liquid phase separation", "phase separation", "llps", "biomolecular condensate", "protein condensate", "condensate"} else term, "", short_evidence(compact_text, term))
            break
    trigger_patterns = [
        ("glucose starvation", "glucose starvation"),
        ("glucose deprivation", "glucose deprivation"),
        ("galactose induction", "galactose induction"),
        ("salt", "salt concentration"),
        ("nacl", "salt concentration"),
        ("peg", "PEG/crowding"),
        ("calcium", "calcium"),
        ("ca2+", "calcium"),
        ("mms", "DNA damage"),
        ("zeocin", "DNA damage"),
        ("hydrogen peroxide", "oxidative stress"),
        ("overexpression", "overexpression"),
    ]
    if has_llps_context:
        for term, value in trigger_patterns:
            if trigger_near_llps(compact_text, term, llps_terms):
                out["best_llps_trigger_value"] = (value, "", short_evidence(compact_text, term))
                break
    return out


def trigger_near_llps(text: str, trigger: str, llps_terms: list[str], window: int = 700) -> bool:
    hay = text.lower()
    for m in re.finditer(re.escape(trigger.lower()), hay):
        start = max(0, m.start() - window)
        end = min(len(hay), m.end() + window)
        segment = hay[start:end]
        if any(term in segment for term in llps_terms):
            return True
    return False


def dominant_numeric(hits: list[tuple[float, str]], tolerance: float = 0.5, min_count: int = 2) -> tuple[float, str] | None:
    if not hits:
        return None
    rounded = Counter(round(v / tolerance) * tolerance for v, _ in hits)
    top, count = rounded.most_common(1)[0]
    if count >= min_count and count / len(hits) >= 0.45:
        for v, ev in hits:
            if abs(v - top) <= tolerance:
                return v, ev
    return None


def dominant_time(hits: list[tuple[float, str, str]], min_count: int = 2) -> tuple[float, str, str] | None:
    if not hits:
        return None
    normalized = Counter((round(v, 3), unit) for v, unit, _ in hits)
    (v, unit), count = normalized.most_common(1)[0]
    if count >= min_count and count / len(hits) >= 0.40:
        for hv, hu, ev in hits:
            if round(hv, 3) == v and hu == unit:
                return hv, hu, ev
    return None


def format_num(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.4g}"


def ensure_extra_columns(rows: list[dict[str, str]]) -> None:
    for row in rows:
        row.setdefault("si_rule_backfill_status", "")
        row.setdefault("si_rule_backfill_evidence", "")
        row.setdefault("si_rule_backfill_methods", "")


def unknown_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    fields = [
        "best_product_family", "best_canonical_product", "best_host_group", "best_canonical_host",
        "best_enzyme_name_value", "best_enzyme_source_species_value", "best_expression_host_value",
        "best_substrate_name_value", "best_main_product_name_value", "best_reaction_system_type_value",
        "best_is_whole_cell_value", "best_llps_state_value", "best_llps_trigger_value",
        "best_reaction_temperature_value", "best_reaction_ph_value", "best_reaction_time_value",
        "best_substrate_concentration_value", "best_cell_density_od600_value",
    ]
    return {f: sum(1 for r in rows if is_unknown(r.get(f))) for f in fields if f in rows[0]}


def main() -> None:
    rows = read_csv(SRC)
    before = unknown_counts(rows)
    ensure_extra_columns(rows)
    text_map = ft.load_text_manifests(ROOT)
    doi_consensus = build_doi_consensus(rows)
    supp_consensus = build_supplementary_consensus()
    text_context_cache: dict[str, dict[str, tuple[str, str, str]]] = {}
    changes: Counter[str] = Counter()
    method_changes: Counter[str] = Counter()

    for row in rows:
        methods: set[str] = set()
        text = row_text(row)
        product, family, pterm = detect_product(text)
        if product:
            if set_label(row, "best_canonical_product", product, "rule_lexicon", short_evidence(text, pterm), changes):
                methods.add("rule_lexicon")
            if set_label(row, "best_product_family", family, "rule_lexicon", short_evidence(text, pterm), changes):
                methods.add("rule_lexicon")
            if set_best_value(row, "main_product_name", product, "", short_evidence(text, pterm), "rule_lexicon", changes):
                methods.add("rule_lexicon")
        host, hgroup, hterm = detect_host(text)
        if host:
            if set_label(row, "best_canonical_host", host, "rule_lexicon", short_evidence(text, hterm), changes):
                methods.add("rule_lexicon")
            if set_label(row, "best_host_group", hgroup, "rule_lexicon", short_evidence(text, hterm), changes):
                methods.add("rule_lexicon")
            if set_best_value(row, "expression_host", host, "", short_evidence(text, hterm), "rule_lexicon", changes):
                methods.add("rule_lexicon")
        system, sterm = detect_system(text)
        if system and set_best_value(row, "reaction_system_type", system, "", short_evidence(text, sterm), "rule_lexicon", changes):
            methods.add("rule_lexicon")
        substrate, subterm = detect_substrate(text)
        if substrate and set_best_value(row, "substrate_name", substrate, "", short_evidence(text, subterm), "rule_lexicon", changes):
            methods.add("rule_lexicon")

        doi = lower(row.get("doi"))
        for source_name, consensus in [("doi_consensus", doi_consensus.get(doi, {})), ("supplementary_consensus", supp_consensus.get(doi, {}))]:
            if not consensus:
                continue
            for field in ["best_canonical_product", "best_product_family", "best_canonical_host", "best_host_group"]:
                if field in consensus and set_label(row, field, consensus[field], source_name, consensus.get("product_evidence") or consensus.get("host_evidence") or f"DOI-level consensus for {doi}", changes):
                    methods.add(source_name)
            for best_field in [
                "best_enzyme_name_value", "best_enzyme_source_species_value", "best_expression_host_value",
                "best_substrate_name_value", "best_main_product_name_value", "best_reaction_system_type_value", "best_is_whole_cell_value",
            ]:
                if best_field in consensus and best_field in row and is_unknown(row.get(best_field)):
                    row[best_field] = consensus[best_field]
                    src = best_field.replace("_value", "_source")
                    ev = best_field.replace("best_", "").replace("_value", "_evidence")
                    if src in row:
                        row[src] = source_name
                    if ev in consensus:
                        evidence = consensus[ev]
                    else:
                        evidence = consensus.get("system_evidence") or f"DOI-level supplementary consensus for {doi}"
                    evidence_field = best_field.replace("_value", "_evidence")
                    if evidence_field in row and is_unknown(row.get(evidence_field)):
                        row[evidence_field] = evidence
                    row["si_rule_backfill_status"] = "updated"
                    row["si_rule_backfill_evidence"] = append_evidence(row.get("si_rule_backfill_evidence", ""), best_field, evidence)
                    changes[best_field] += 1
                    methods.add(source_name)

        if doi and doi in text_map and any(is_unknown(row.get(f)) for f in [
            "best_reaction_temperature_value", "best_reaction_ph_value", "best_reaction_time_value",
            "best_substrate_concentration_value", "best_cell_density_od600_value",
            "best_llps_state_value", "best_llps_trigger_value", "best_reaction_system_type_value",
            "best_expression_host_value", "best_product_family", "best_host_group",
        ]):
            if doi not in text_context_cache:
                text_context_cache[doi] = context_candidates(read_text_files(text_map[doi]))
            candidates = text_context_cache[doi]
            for field, (value, unit, evidence) in candidates.items():
                if field in {"best_llps_state_value", "best_llps_trigger_value"} and not row_llps_relevant(row):
                    continue
                if field in ["best_canonical_product", "best_product_family", "best_canonical_host", "best_host_group"]:
                    if set_label(row, field, value, "field_context_search", evidence, changes):
                        methods.add("field_context_search")
                elif field.startswith("best_") and field.endswith("_value") and field in row and is_unknown(row.get(field)):
                    base_field = field[len("best_"):-len("_value")]
                    if set_best_value(row, base_field, value, unit, evidence, "field_context_search", changes):
                        methods.add("field_context_search")

        if methods:
            existing_methods = set(filter(None, compact(row.get("si_rule_backfill_methods")).split(";")))
            row["si_rule_backfill_methods"] = ";".join(sorted(existing_methods | methods))
            for m in methods:
                method_changes[m] += 1

    after = unknown_counts(rows)
    write_csv(OUT, rows)
    summary = {
        "input": str(SRC),
        "output": str(OUT),
        "rows": len(rows),
        "text_mapped_dois": len(text_map),
        "supplementary_consensus_dois": len(supp_consensus),
        "doi_consensus_dois": len(doi_consensus),
        "changed_rows": sum(1 for r in rows if r.get("si_rule_backfill_status") == "updated"),
        "changes_by_field": dict(changes.most_common()),
        "changes_by_method_rows": dict(method_changes.most_common()),
        "unknown_before": before,
        "unknown_after": after,
        "unknown_reduction": {k: before.get(k, 0) - after.get(k, 0) for k in before},
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Wrote: {OUT}")
    print(f"Wrote: {SUMMARY}")


if __name__ == "__main__":
    main()
