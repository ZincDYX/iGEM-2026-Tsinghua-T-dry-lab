# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import html
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

try:
    import fulltext_pro_field_completion as ft

    ROOT = ft.ROOT
    SRC = ft.DEFAULT_OUTPUT
except Exception:
    ROOT = Path.cwd()
    SRC = ROOT / "essay" / "optimized_experimental_database_with_supplementary_expanded160_union_evidence_aware_fulltext_pro_completed.csv"

OUT = ROOT / "essay" / "known_information_visualization_report_en.html"
SUMMARY_OUT = ROOT / "essay" / "known_information_visualization_report_en_summary.json"

UNKNOWN = {
    "",
    "unknown",
    "none",
    "null",
    "nan",
    "n/a",
    "na",
    "not specified",
    "not available",
    "unidentified",
    "not reported",
}

STOPWORDS = {
    "the", "and", "for", "with", "from", "into", "that", "this", "were", "was", "are", "has", "have", "had",
    "using", "use", "used", "via", "through", "between", "within", "under", "over", "after", "before", "than",
    "study", "analysis", "effect", "effects", "based", "data", "result", "results", "table", "figure", "supplementary",
    "cell", "cells", "protein", "proteins", "enzyme", "enzymes", "reaction", "reactions", "metabolic", "metabolism",
    "biosynthesis", "activity", "expression", "production", "product", "products",
}

PRODUCT_FAMILY_LABELS = {
    "flavonoid": "Flavonoids",
    "isoflavonoid": "Isoflavonoids",
    "isoprenoid": "Isoprenoids",
    "terpenoid": "Terpenoids",
    "llps_system": "LLPS systems",
    "natural_product": "Natural products",
    "phenylpropanoid": "Phenylpropanoids",
    "prenylflavonoid": "Prenylflavonoids",
    "stilbene": "Stilbenes",
    "other": "Other known families",
}

HOST_LABELS = {
    "yeast": "Yeast",
    "bacteria": "Bacteria",
    "plant": "Plant",
    "mammalian": "Mammalian cells",
    "cell_free": "Cell-free system",
    "cyanobacteria": "Cyanobacteria",
    "other": "Other known hosts",
}

TIER_LABELS = {
    "core": "Core",
    "llps_core": "LLPS core",
    "silver": "Silver",
    "review": "Review-level",
}

CLEAN_LABELS = {
    "A_complete": "A: complete record",
    "A_llps": "A: LLPS core",
    "B_product_condition": "B: product and condition",
    "C_llps_candidate": "C: LLPS candidate",
    "C_partial_context": "C: partial context",
    "D_result_only": "D: result only",
}

METRIC_LABELS = {
    "glabridin_yield": "Glabridin yield",
    "glabridin_titer": "Glabridin titer",
    "glabridin_concentration": "Glabridin concentration",
    "glabridin_selectivity": "Glabridin selectivity",
    "enzyme_activity": "Enzyme activity",
    "specific_activity": "Specific activity",
    "relative_activity": "Relative activity",
    "substrate_conversion": "Substrate conversion",
    "kinetic_efficiency": "Kinetic efficiency",
    "regioselectivity": "Regioselectivity",
    "critical_phase_concentration": "Critical phase concentration",
    "phase_regulation_direction": "Phase regulation",
    "catalytic_efficiency_fold_change": "Catalytic efficiency fold-change",
    "frap_half_time": "FRAP half-time",
    "droplet_dissolution_time": "Droplet dissolution time",
    "kcat": "kcat",
    "km": "Km",
    "llps_state": "LLPS state",
}

SERIES = ["#2f6fbb", "#31a354", "#f39c12", "#b65fcf", "#d95f5f", "#1f9fb4", "#6c7a89", "#8d6e63"]


def norm(value: object) -> str:
    return " ".join(str(value or "").replace("\u00a0", " ").strip().split())


def key(value: object) -> str:
    return norm(value).lower()


def is_unknown(value: object) -> bool:
    return key(value) in UNKNOWN


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def labelize(value: object, mapping: dict[str, str] | None = None) -> str:
    raw = norm(value)
    k = raw.lower()
    if mapping and k in mapping:
        return mapping[k]
    if not raw:
        return "Unlabeled"
    return raw.replace("_", " ").replace("-", " ").title()


def short_label(value: str, limit: int = 24) -> str:
    value = norm(value)
    return value if len(value) <= limit else value[: limit - 1] + "..."


def pct(value: int, total: int) -> str:
    return f"{100 * value / total:.1f}%" if total else "0.0%"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def counter_for(rows: list[dict[str, str]], field: str, mapping: dict[str, str] | None = None, drop_other: bool = False) -> Counter:
    counter: Counter[str] = Counter()
    for row in rows:
        value = row.get(field, "")
        if is_unknown(value):
            continue
        if drop_other and key(value) == "other":
            continue
        counter[labelize(value, mapping)] += 1
    return counter


def known_count(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if not is_unknown(row.get(field, "")))


def metric_name(row: dict[str, str]) -> str:
    metric = row.get("primary_result_metric") or row.get("schema_id") or ""
    if is_unknown(metric):
        return ""
    return labelize(metric, METRIC_LABELS)


def top(counter: Counter, n: int) -> list[tuple[str, int]]:
    return [(name, count) for name, count in counter.most_common(n) if count > 0]


def svg_bar(items: list[tuple[str, int]], title: str, color: str = SERIES[0], width: int = 980, bar_h: int = 28) -> str:
    if not items:
        return empty_chart("No known records available for this chart.")
    left = 220
    right = 80
    top_pad = 28
    row_gap = 10
    height = top_pad + len(items) * (bar_h + row_gap) + 26
    max_v = max(v for _, v in items) or 1
    plot_w = width - left - right
    parts = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">']
    parts.append(f'<title>{esc(title)}</title>')
    for i, (name, value) in enumerate(items):
        y = top_pad + i * (bar_h + row_gap)
        w = max(2, plot_w * value / max_v)
        parts.append(f'<text class="axis-label" x="{left - 12}" y="{y + bar_h * 0.68}" text-anchor="end">{esc(short_label(name, 28))}</text>')
        parts.append(f'<rect class="bar" x="{left}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="3" fill="{color}"></rect>')
        parts.append(f'<text class="value-label" x="{left + w + 8:.1f}" y="{y + bar_h * 0.68}">{value:,}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def coverage_chart(items: list[dict[str, object]], width: int = 980) -> str:
    left = 250
    right = 80
    bar_h = 24
    row_gap = 9
    top_pad = 20
    height = top_pad + len(items) * (bar_h + row_gap) + 22
    plot_w = width - left - right
    parts = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="Known field coverage">']
    parts.append("<title>Known field coverage</title>")
    for i, item in enumerate(items):
        label = str(item["label"])
        known = int(item["known"])
        total = int(item["total"])
        unknown = total - known
        y = top_pad + i * (bar_h + row_gap)
        w_known = plot_w * known / total if total else 0
        w_unknown = plot_w - w_known
        parts.append(f'<text class="axis-label" x="{left - 12}" y="{y + bar_h * 0.68}" text-anchor="end">{esc(label)}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{plot_w}" height="{bar_h}" rx="3" fill="#e6e9ef"></rect>')
        parts.append(f'<rect x="{left}" y="{y}" width="{w_known:.1f}" height="{bar_h}" rx="3" fill="{SERIES[1]}"></rect>')
        if w_unknown > 0:
            parts.append(f'<rect x="{left + w_known:.1f}" y="{y}" width="{w_unknown:.1f}" height="{bar_h}" rx="3" fill="#c7ccd6"></rect>')
        parts.append(f'<text class="value-label" x="{left + plot_w + 8}" y="{y + bar_h * 0.68}">{known:,} known / {unknown:,} unknown</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def bubble_chart(rows: list[dict[str, str]], width: int = 980, height: int = 560) -> str:
    fams = [name for name, _ in top(counter_for(rows, "best_product_family", PRODUCT_FAMILY_LABELS, drop_other=True), 8)]
    hosts = [name for name, _ in top(counter_for(rows, "best_host_group", HOST_LABELS, drop_other=True), 7)]
    if not fams or not hosts:
        return empty_chart("No known product-host intersections available.")
    pairs: Counter[tuple[str, str]] = Counter()
    for row in rows:
        fam = labelize(row.get("best_product_family"), PRODUCT_FAMILY_LABELS)
        host = labelize(row.get("best_host_group"), HOST_LABELS)
        if fam in fams and host in hosts:
            pairs[(fam, host)] += 1
    left, right, top_pad, bottom = 150, 40, 30, 115
    plot_w = width - left - right
    plot_h = height - top_pad - bottom
    max_v = max(pairs.values()) if pairs else 1
    x_step = plot_w / max(1, len(fams) - 1)
    y_step = plot_h / max(1, len(hosts) - 1)
    parts = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="Product family by host group bubble chart">']
    parts.append("<title>Known product family by host group</title>")
    for i, host in enumerate(hosts):
        y = top_pad + i * y_step
        parts.append(f'<line class="grid" x1="{left}" x2="{width-right}" y1="{y:.1f}" y2="{y:.1f}"></line>')
        parts.append(f'<text class="axis-label" x="{left - 12}" y="{y + 4:.1f}" text-anchor="end">{esc(host)}</text>')
    for i, fam in enumerate(fams):
        x = left + i * x_step
        parts.append(f'<line class="grid" y1="{top_pad}" y2="{height-bottom}" x1="{x:.1f}" x2="{x:.1f}"></line>')
        parts.append(f'<text class="axis-label rotate-label" transform="translate({x:.1f},{height - bottom + 18}) rotate(35)">{esc(short_label(fam, 18))}</text>')
    for (fam, host), value in pairs.items():
        x = left + fams.index(fam) * x_step
        y = top_pad + hosts.index(host) * y_step
        r = 5 + 30 * math.sqrt(value / max_v)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{SERIES[0]}" opacity="0.72"><title>{esc(fam)} / {esc(host)}: {value:,} records</title></circle>')
        if value == max_v:
            parts.append(f'<text class="value-label" x="{x:.1f}" y="{y + 4:.1f}" text-anchor="middle">{value:,}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def upset_chart(rows: list[dict[str, str]], width: int = 980) -> str:
    sets = [
        ("Product", lambda r: not is_unknown(r.get("best_canonical_product")) or not is_unknown(r.get("best_product_family"))),
        ("Host", lambda r: not is_unknown(r.get("best_canonical_host")) or not is_unknown(r.get("best_host_group"))),
        ("Enzyme", lambda r: not is_unknown(r.get("best_enzyme_name_value"))),
        ("Substrate", lambda r: not is_unknown(r.get("best_substrate_name_value"))),
        ("Main product", lambda r: not is_unknown(r.get("best_main_product_name_value"))),
        ("Conditions", lambda r: any(not is_unknown(r.get(f)) for f in ["best_reaction_temperature_value", "best_reaction_ph_value", "best_reaction_time_value", "best_substrate_concentration_value"])),
        ("LLPS", lambda r: any(not is_unknown(r.get(f)) for f in ["best_llps_component_value", "best_llps_state_value", "best_llps_trigger_value"])),
    ]
    combos: Counter[tuple[int, ...]] = Counter()
    for row in rows:
        combo = tuple(1 if fn(row) else 0 for _, fn in sets)
        if any(combo):
            combos[combo] += 1
    items = combos.most_common(12)
    left = 150
    bar_left = 410
    top_pad = 35
    row_h = 30
    height = top_pad + len(items) * row_h + 40
    max_v = max((v for _, v in items), default=1)
    plot_w = width - bar_left - 90
    parts = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="UpSet plot of known field combinations">']
    parts.append("<title>Known field combinations</title>")
    for j, (name, _) in enumerate(sets):
        x = left + j * 34
        parts.append(f'<text class="axis-label rotate-label" transform="translate({x},{top_pad - 12}) rotate(-35)">{esc(name)}</text>')
    for i, (combo, value) in enumerate(items):
        y = top_pad + i * row_h
        active_x = []
        for j, bit in enumerate(combo):
            x = left + j * 34
            fill = SERIES[1] if bit else "#d8dde6"
            parts.append(f'<circle cx="{x}" cy="{y}" r="7" fill="{fill}"></circle>')
            if bit:
                active_x.append(x)
        if len(active_x) > 1:
            parts.append(f'<line x1="{min(active_x)}" x2="{max(active_x)}" y1="{y}" y2="{y}" stroke="{SERIES[1]}" stroke-width="3" opacity="0.8"></line>')
        w = max(2, plot_w * value / max_v)
        parts.append(f'<rect class="bar" x="{bar_left}" y="{y - 10}" width="{w:.1f}" height="20" rx="3" fill="{SERIES[2]}"></rect>')
        parts.append(f'<text class="value-label" x="{bar_left + w + 8:.1f}" y="{y + 5}">{value:,}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def sankey_chart(rows: list[dict[str, str]], width: int = 1040, height: int = 620) -> str:
    columns = [
        ("Source mode", "source_mode", None),
        ("Product family", "best_product_family", PRODUCT_FAMILY_LABELS),
        ("Host group", "best_host_group", HOST_LABELS),
        ("Result metric", "__metric__", METRIC_LABELS),
    ]
    top_allowed: list[set[str]] = []
    for title, field, mapping in columns:
        if field == "__metric__":
            cnt = Counter(metric_name(r) for r in rows if metric_name(r))
        else:
            cnt = counter_for(rows, field, mapping)
        top_allowed.append({name for name, _ in cnt.most_common(8)})
    paths: Counter[tuple[str, str, str, str]] = Counter()
    for row in rows:
        source = labelize(row.get("source_mode"))
        family = labelize(row.get("best_product_family"), PRODUCT_FAMILY_LABELS)
        host = labelize(row.get("best_host_group"), HOST_LABELS)
        metric = metric_name(row)
        values = [source, family, host, metric]
        if not all(values):
            continue
        values = [v if v in top_allowed[i] else "Other known" for i, v in enumerate(values)]
        if "Other known" in values[1:3]:
            continue
        paths[tuple(values)] += 1
    if not paths:
        return empty_chart("No complete known source-product-host-metric paths available.")
    node_counts = [Counter() for _ in columns]
    link_counts: list[Counter[tuple[str, str]]] = [Counter(), Counter(), Counter()]
    for path, count in paths.items():
        for i, value in enumerate(path):
            node_counts[i][value] += count
        for i in range(3):
            link_counts[i][(path[i], path[i + 1])] += count
    x_positions = [70, 360, 650, 910]
    node_pos: list[dict[str, tuple[float, float, float]]] = []
    for c, counts in enumerate(node_counts):
        items = counts.most_common(9)
        total = sum(v for _, v in items) or 1
        gap = 10
        usable = height - 80 - gap * (len(items) - 1)
        y = 54
        pos = {}
        for name, value in items:
            h = max(20, usable * value / total)
            pos[name] = (x_positions[c], y, h)
            y += h + gap
        node_pos.append(pos)
    max_link = max((v for cnt in link_counts for v in cnt.values()), default=1)
    parts = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="Known information Sankey flow">']
    parts.append("<title>Known information flow</title>")
    for i, cnt in enumerate(link_counts):
        for (a, b), value in cnt.most_common(60):
            if a not in node_pos[i] or b not in node_pos[i + 1]:
                continue
            x1, y1, h1 = node_pos[i][a]
            x2, y2, h2 = node_pos[i + 1][b]
            y_start = y1 + h1 / 2
            y_end = y2 + h2 / 2
            stroke_w = 1 + 16 * math.sqrt(value / max_link)
            color = SERIES[i % len(SERIES)]
            parts.append(f'<path d="M {x1 + 118:.1f},{y_start:.1f} C {(x1+x2)/2:.1f},{y_start:.1f} {(x1+x2)/2:.1f},{y_end:.1f} {x2:.1f},{y_end:.1f}" fill="none" stroke="{color}" stroke-width="{stroke_w:.1f}" opacity="0.24"><title>{esc(a)} to {esc(b)}: {value:,}</title></path>')
    for c, (title, _, _) in enumerate(columns):
        parts.append(f'<text class="chart-title" x="{x_positions[c]}" y="24">{esc(title)}</text>')
        for name, (x, y, h) in node_pos[c].items():
            value = node_counts[c][name]
            parts.append(f'<rect x="{x}" y="{y:.1f}" width="118" height="{h:.1f}" rx="4" fill="{SERIES[c % len(SERIES)]}" opacity="0.78"></rect>')
            parts.append(f'<text class="node-label" x="{x + 8}" y="{y + min(18, h * 0.55):.1f}">{esc(short_label(name, 16))}</text>')
            if h > 34:
                parts.append(f'<text class="node-count" x="{x + 8}" y="{y + min(35, h - 6):.1f}">{value:,}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def chord_chart(rows: list[dict[str, str]], width: int = 800, height: int = 620) -> str:
    fams = [name for name, _ in top(counter_for(rows, "best_product_family", PRODUCT_FAMILY_LABELS, drop_other=True), 6)]
    hosts = [name for name, _ in top(counter_for(rows, "best_host_group", HOST_LABELS, drop_other=True), 6)]
    nodes = fams + hosts
    if len(nodes) < 3:
        return empty_chart("No known product-host chord relationships available.")
    edges: Counter[tuple[str, str]] = Counter()
    for row in rows:
        fam = labelize(row.get("best_product_family"), PRODUCT_FAMILY_LABELS)
        host = labelize(row.get("best_host_group"), HOST_LABELS)
        if fam in fams and host in hosts:
            edges[(fam, host)] += 1
    cx, cy = width / 2, height / 2
    radius = min(width, height) * 0.35
    angles = {}
    for i, node in enumerate(nodes):
        angle = -math.pi / 2 + 2 * math.pi * i / len(nodes)
        angles[node] = angle
    max_edge = max(edges.values()) if edges else 1
    parts = [f'<svg class="chart chord" viewBox="0 0 {width} {height}" role="img" aria-label="Chord diagram of product families and host groups">']
    parts.append("<title>Product family and host group chord diagram</title>")
    for (fam, host), value in edges.most_common(50):
        a1, a2 = angles[fam], angles[host]
        x1, y1 = cx + radius * math.cos(a1), cy + radius * math.sin(a1)
        x2, y2 = cx + radius * math.cos(a2), cy + radius * math.sin(a2)
        sw = 1 + 14 * math.sqrt(value / max_edge)
        parts.append(f'<path d="M {x1:.1f},{y1:.1f} Q {cx:.1f},{cy:.1f} {x2:.1f},{y2:.1f}" fill="none" stroke="{SERIES[0]}" stroke-width="{sw:.1f}" opacity="0.22"><title>{esc(fam)} / {esc(host)}: {value:,}</title></path>')
    for i, node in enumerate(nodes):
        angle = angles[node]
        x, y = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
        fill = SERIES[1] if node in fams else SERIES[2]
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="17" fill="{fill}" opacity="0.88"></circle>')
        label_x = cx + (radius + 35) * math.cos(angle)
        label_y = cy + (radius + 35) * math.sin(angle)
        anchor = "start" if math.cos(angle) >= 0 else "end"
        parts.append(f'<text class="axis-label" x="{label_x:.1f}" y="{label_y:.1f}" text-anchor="{anchor}">{esc(short_label(node, 18))}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def network_chart(rows: list[dict[str, str]], width: int = 980, height: int = 560) -> str:
    fams = [name for name, _ in top(counter_for(rows, "best_product_family", PRODUCT_FAMILY_LABELS, drop_other=True), 6)]
    hosts = [name for name, _ in top(counter_for(rows, "best_host_group", HOST_LABELS, drop_other=True), 6)]
    metrics = [name for name, _ in Counter(metric_name(r) for r in rows if metric_name(r)).most_common(6)]
    if not fams or not hosts:
        return empty_chart("No known network relationships available.")
    edge_fh: Counter[tuple[str, str]] = Counter()
    edge_hm: Counter[tuple[str, str]] = Counter()
    for row in rows:
        fam = labelize(row.get("best_product_family"), PRODUCT_FAMILY_LABELS)
        host = labelize(row.get("best_host_group"), HOST_LABELS)
        metric = metric_name(row)
        if fam in fams and host in hosts:
            edge_fh[(fam, host)] += 1
        if host in hosts and metric in metrics:
            edge_hm[(host, metric)] += 1
    positions = {}
    for i, name in enumerate(fams):
        positions[name] = (150, 80 + i * 70, SERIES[1])
    for i, name in enumerate(hosts):
        positions[name] = (490, 80 + i * 70, SERIES[2])
    for i, name in enumerate(metrics):
        positions[name] = (830, 80 + i * 70, SERIES[3])
    max_edge = max([1] + list(edge_fh.values()) + list(edge_hm.values()))
    parts = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="Known database network chart">']
    parts.append("<title>Known database network</title>")
    for edge_counter in [edge_fh, edge_hm]:
        for (a, b), value in edge_counter.most_common(50):
            if a not in positions or b not in positions:
                continue
            x1, y1, _ = positions[a]
            x2, y2, _ = positions[b]
            sw = 1 + 8 * math.sqrt(value / max_edge)
            parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#6b7280" stroke-width="{sw:.1f}" opacity="0.22"><title>{esc(a)} to {esc(b)}: {value:,}</title></line>')
    for name, (x, y, fill) in positions.items():
        parts.append(f'<circle cx="{x}" cy="{y}" r="18" fill="{fill}" opacity="0.9"></circle>')
        parts.append(f'<text class="node-text" x="{x + 26}" y="{y + 5}">{esc(short_label(name, 24))}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def sunburst_chart(rows: list[dict[str, str]], width: int = 760, height: int = 680) -> str:
    fam_counts = counter_for(rows, "best_product_family", PRODUCT_FAMILY_LABELS, drop_other=True)
    fams = [name for name, _ in fam_counts.most_common(7)]
    if not fams:
        return empty_chart("No known hierarchy available.")
    tree: dict[str, Counter[str]] = {fam: Counter() for fam in fams}
    for row in rows:
        fam = labelize(row.get("best_product_family"), PRODUCT_FAMILY_LABELS)
        host = labelize(row.get("best_host_group"), HOST_LABELS)
        if fam in tree and not is_unknown(row.get("best_host_group")):
            tree[fam][host] += 1
    cx, cy = width / 2, height / 2
    total = sum(fam_counts[fam] for fam in fams)
    start = -math.pi / 2
    parts = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="Sunburst chart of product families and host groups">']
    parts.append("<title>Known product-host hierarchy</title>")
    for i, fam in enumerate(fams):
        value = fam_counts[fam]
        end = start + 2 * math.pi * value / total
        color = SERIES[i % len(SERIES)]
        parts.append(arc_path(cx, cy, 80, 170, start, end, color, f"{fam}: {value:,} records", 0.84))
        host_total = sum(tree[fam].values()) or 1
        h_start = start
        for j, (host, h_value) in enumerate(tree[fam].most_common(5)):
            h_end = h_start + (end - start) * h_value / host_total
            parts.append(arc_path(cx, cy, 180, 270, h_start, h_end, SERIES[(i + j + 1) % len(SERIES)], f"{fam} / {host}: {h_value:,}", 0.66))
            h_start = h_end
        mid = (start + end) / 2
        lx, ly = cx + 310 * math.cos(mid), cy + 310 * math.sin(mid)
        anchor = "start" if math.cos(mid) >= 0 else "end"
        parts.append(f'<text class="axis-label" x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}">{esc(short_label(fam, 17))}</text>')
        start = end
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="62" fill="#f5f7fb" stroke="#d8dde6"></circle>')
    parts.append(f'<text class="center-label" x="{cx}" y="{cy - 4}" text-anchor="middle">Known</text>')
    parts.append(f'<text class="center-label small" x="{cx}" y="{cy + 18}" text-anchor="middle">records</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def arc_path(cx: float, cy: float, r0: float, r1: float, a0: float, a1: float, color: str, title: str, opacity: float) -> str:
    if a1 - a0 <= 0.001:
        return ""
    large = 1 if a1 - a0 > math.pi else 0
    x0, y0 = cx + r1 * math.cos(a0), cy + r1 * math.sin(a0)
    x1, y1 = cx + r1 * math.cos(a1), cy + r1 * math.sin(a1)
    x2, y2 = cx + r0 * math.cos(a1), cy + r0 * math.sin(a1)
    x3, y3 = cx + r0 * math.cos(a0), cy + r0 * math.sin(a0)
    d = f"M {x0:.1f},{y0:.1f} A {r1},{r1} 0 {large} 1 {x1:.1f},{y1:.1f} L {x2:.1f},{y2:.1f} A {r0},{r0} 0 {large} 0 {x3:.1f},{y3:.1f} Z"
    return f'<path d="{d}" fill="{color}" opacity="{opacity}"><title>{esc(title)}</title></path>'


def treemap_html(items: list[tuple[str, int]], title: str) -> str:
    if not items:
        return empty_chart("No known records available for this treemap.")
    max_v = max(v for _, v in items)
    parts = [f'<div class="treemap" role="img" aria-label="{esc(title)}">']
    for i, (name, value) in enumerate(items[:18]):
        basis = 13 + 42 * value / max_v
        parts.append(f'<div class="tile" style="flex-basis:{basis:.1f}%; background:{SERIES[i % len(SERIES)]};"><strong>{esc(short_label(name, 28))}</strong><span>{value:,} records</span></div>')
    parts.append("</div>")
    return "\n".join(parts)


def word_cloud(rows: list[dict[str, str]], width: int = 980, height: int = 430) -> str:
    text_fields = [
        "title_clean", "title", "best_main_product_name_value", "best_substrate_name_value",
        "best_enzyme_name_value", "best_llps_component_value", "primary_result_metric",
    ]
    words: Counter[str] = Counter()
    for row in rows:
        blob = " ".join(row.get(f, "") for f in text_fields)
        for word in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", blob):
            w = word.lower().strip("-")
            if w in STOPWORDS or len(w) < 3:
                continue
            words[w] += 1
    items = words.most_common(80)
    if not items:
        return empty_chart("No text terms available.")
    max_v = items[0][1]
    x, y = 24, 52
    line_h = 48
    parts = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="Keyword cloud from known database records">']
    parts.append("<title>Keyword cloud</title>")
    for i, (word, value) in enumerate(items):
        size = 13 + 28 * math.sqrt(value / max_v)
        label = word.title() if word not in {"llps", "frap", "od600", "kcat"} else word.upper()
        approx = len(label) * size * 0.58 + 22
        if x + approx > width - 24:
            x = 24 + (i % 3) * 12
            y += line_h
        if y > height - 24:
            break
        color = SERIES[i % len(SERIES)]
        parts.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size:.1f}" fill="{color}" opacity="0.9">{esc(label)}<title>{esc(label)}: {value:,}</title></text>')
        x += approx
    parts.append("</svg>")
    return "\n".join(parts)


def empty_chart(message: str) -> str:
    return f'<div class="empty-chart">{esc(message)}</div>'


def table_html(headers: list[str], rows: list[list[object]]) -> str:
    out = ["<div class=\"table-wrap\"><table>", "<thead><tr>"]
    for h in headers:
        out.append(f"<th>{esc(h)}</th>")
    out.append("</tr></thead><tbody>")
    for row in rows:
        out.append("<tr>")
        for cell in row:
            out.append(f"<td>{esc(cell)}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def build_report(rows: list[dict[str, str]]) -> tuple[str, dict[str, object]]:
    total = len(rows)
    dois = {key(r.get("doi")) for r in rows if not is_unknown(r.get("doi"))}
    titles = {key(r.get("title_clean") or r.get("title")) for r in rows if not is_unknown(r.get("title_clean") or r.get("title"))}
    product_family_counter = counter_for(rows, "best_product_family", PRODUCT_FAMILY_LABELS)
    host_counter = counter_for(rows, "best_host_group", HOST_LABELS)
    product_counter = counter_for(rows, "best_canonical_product")
    host_name_counter = counter_for(rows, "best_canonical_host")
    metric_counter = Counter(metric_name(r) for r in rows if metric_name(r))
    tier_counter = counter_for(rows, "database_tier", TIER_LABELS)
    clean_counter = counter_for(rows, "clean_level", CLEAN_LABELS)
    fulltext_counter = counter_for(rows, "fulltext_pro_status")

    coverage_fields = [
        ("Product family", "best_product_family"),
        ("Canonical product", "best_canonical_product"),
        ("Host group", "best_host_group"),
        ("Canonical host", "best_canonical_host"),
        ("Main product name", "best_main_product_name_value"),
        ("Substrate name", "best_substrate_name_value"),
        ("Enzyme name", "best_enzyme_name_value"),
        ("Enzyme source species", "best_enzyme_source_species_value"),
        ("Expression host", "best_expression_host_value"),
        ("Reaction system type", "best_reaction_system_type_value"),
        ("Whole-cell flag", "best_is_whole_cell_value"),
        ("Reaction temperature", "best_reaction_temperature_value"),
        ("Reaction pH", "best_reaction_ph_value"),
        ("Reaction time", "best_reaction_time_value"),
        ("Substrate concentration", "best_substrate_concentration_value"),
        ("LLPS component", "best_llps_component_value"),
        ("LLPS state", "best_llps_state_value"),
        ("LLPS trigger", "best_llps_trigger_value"),
    ]
    coverage = [{"label": label, "known": known_count(rows, field), "total": total} for label, field in coverage_fields]

    both_product_host = sum(1 for r in rows if not is_unknown(r.get("best_product_family")) and not is_unknown(r.get("best_host_group")))
    full_conditions = sum(
        1
        for r in rows
        if all(
            not is_unknown(r.get(field))
            for field in ["best_reaction_temperature_value", "best_reaction_ph_value", "best_reaction_time_value"]
        )
    )
    llps_known = sum(
        1
        for r in rows
        if any(not is_unknown(r.get(field)) for field in ["best_llps_component_value", "best_llps_state_value", "best_llps_trigger_value"])
    )

    source_edges = [
        ("Unique DOI records", len(dois), "Experimental records", total),
        ("Experimental records", total, "Fulltext Pro accepted", fulltext_counter.get("Accepted", 0)),
        ("Experimental records", total, "Low-confidence retained", fulltext_counter.get("Low Confidence", 0)),
        ("Experimental records", total, "No direct update", fulltext_counter.get("No Update", 0)),
        ("Experimental records", total, "Product-host labeled", both_product_host),
    ]

    summary = {
        "total_records": total,
        "unique_dois": len(dois),
        "unique_titles": len(titles),
        "known_product_family": known_count(rows, "best_product_family"),
        "known_canonical_product": known_count(rows, "best_canonical_product"),
        "known_host_group": known_count(rows, "best_host_group"),
        "known_canonical_host": known_count(rows, "best_canonical_host"),
        "product_host_labeled_records": both_product_host,
        "full_reaction_condition_records": full_conditions,
        "llps_evidence_records": llps_known,
    }

    html_parts = [
        "<!doctype html>",
        "<html lang=\"en\">",
        "<head>",
        "<meta charset=\"utf-8\">",
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
        "<title>Known Information Atlas for the iGEM Literature-Derived Experimental Database</title>",
        css(),
        "</head>",
        "<body>",
        "<main>",
        "<section class=\"hero\">",
        "<p class=\"eyebrow\">Literature-derived experimental database</p>",
        "<h1>Known Information Atlas</h1>",
        "<p class=\"lead\">This English report visualizes the records with recognized product, host, experimental, and evidence fields after rule-based cleaning, LLM quality control, and full-text or supplementary-material completion.</p>",
        "<div class=\"stats\">",
        stat_card("Structured records", f"{total:,}", "Rows in the current curated database"),
        stat_card("Unique DOI sources", f"{len(dois):,}", "Traceable literature identifiers"),
        stat_card("Known product families", f"{known_count(rows, 'best_product_family'):,}", pct(known_count(rows, 'best_product_family'), total)),
        stat_card("Known host groups", f"{known_count(rows, 'best_host_group'):,}", pct(known_count(rows, 'best_host_group'), total)),
        "</div>",
        "</section>",
        section("Field Coverage After Full-Text Completion", coverage_chart(coverage), "Known coverage is strongest for host labels and product-family labels. Highly specific wet-lab parameters remain sparse because many articles do not report them at the row level."),
        two_col(
            "Known Product Families",
            svg_bar(top(product_family_counter, 12), "Known product families", SERIES[0]),
            "The database captures a broad natural-product space, with flavonoids, terpenoids, isoprenoids, natural products, and LLPS-related systems forming the main recognizable families.",
            "Known Host Groups",
            svg_bar(top(host_counter, 10), "Known host groups", SERIES[1]),
            "Yeast is the dominant known chassis, followed by plant, bacterial, mammalian, and cell-free systems, supporting cross-host comparison for pathway and condensate design.",
        ),
        section("Known Information Flow: Source to Product, Host, and Result Metric", sankey_chart(rows), "The Sankey diagram shows how known source modes connect to recognized product families, host groups, and measured result types. Unknown labels are excluded so the visible flow represents directly usable evidence."),
        section("Product Family and Host Group Matrix", bubble_chart(rows), "Bubble size represents the number of structured records for each known product-family and host-group intersection. This view highlights where the database is dense enough for comparative analysis."),
        section("Known Field Combination Landscape", upset_chart(rows), "The UpSet-style plot shows which information fields tend to co-occur in the same record. Product-host labeling is common, while LLPS-specific evidence appears in a smaller but biologically important subset."),
        two_col(
            "Chord Diagram: Product Families and Hosts",
            chord_chart(rows),
            "The chord diagram emphasizes repeated pairings between product families and host systems. Thick connections indicate high-frequency evidence pairs.",
            "Network Chart: Product, Host, and Metric",
            network_chart(rows),
            "The network view links the most frequent product families, host groups, and result metrics, revealing which experimental outcomes can be compared across biological systems.",
        ),
        two_col(
            "Sunburst: Known Product-Host Hierarchy",
            sunburst_chart(rows),
            "The sunburst organizes recognized records from product families into host groups, providing a compact hierarchy for project storytelling.",
            "Treemap: Database Tiers",
            treemap_html(top(tier_counter, 12), "Database tier treemap"),
            "The treemap summarizes how known records are distributed across curation tiers, separating high-confidence experimental entries from broader review-level evidence.",
        ),
        section("Keyword Cloud From Known Records", word_cloud(rows), "The word cloud is generated from titles and known extracted fields. Larger words represent concepts that appear more often in the recognized portion of the database."),
        two_col(
            "Result Metrics",
            svg_bar(top(metric_counter, 12), "Known result metrics", SERIES[3]),
            "The result-metric distribution shows what the database can quantify, including enzyme activity, conversion, titer, yield, kinetic parameters, and phase-related measurements.",
            "Evidence Quality Levels",
            svg_bar(top(clean_counter, 10), "Evidence quality levels", SERIES[4]),
            "Clean-level labels indicate whether records contain complete product-condition evidence, partial context, LLPS-specific evidence, or result-only evidence.",
        ),
        section(
            "Top Known Entities",
            table_html(
                ["Rank", "Canonical product", "Records", "Canonical host", "Records"],
                [
                    [
                        i + 1,
                        top(product_counter, 15)[i][0] if i < len(top(product_counter, 15)) else "",
                        f"{top(product_counter, 15)[i][1]:,}" if i < len(top(product_counter, 15)) else "",
                        top(host_name_counter, 15)[i][0] if i < len(top(host_name_counter, 15)) else "",
                        f"{top(host_name_counter, 15)[i][1]:,}" if i < len(top(host_name_counter, 15)) else "",
                    ]
                    for i in range(15)
                ],
            ),
            "This table lists the most frequent recognized products and host names. It is useful for selecting representative case studies in a project presentation.",
        ),
        section(
            "Evidence Chain Summary",
            evidence_chain(source_edges),
            "Each database row remains traceable to literature identifiers and extraction status. The chain shows how source literature is transformed into structured experimental records and then into product-host-labeled evidence.",
        ),
        "<footer>",
        "<p>Generated from the current full-text-completed database. Charts emphasize known values; unknown or unsupported fields are retained in the database but excluded from most analytical figures.</p>",
        "</footer>",
        "</main>",
        "</body>",
        "</html>",
    ]
    return "\n".join(html_parts), summary


def stat_card(label: str, value: str, note: str) -> str:
    return f'<div class="stat"><span>{esc(label)}</span><strong>{esc(value)}</strong><em>{esc(note)}</em></div>'


def section(title: str, visual: str, caption: str) -> str:
    return f'<section class="panel"><h2>{esc(title)}</h2>{visual}<p class="caption">{esc(caption)}</p></section>'


def two_col(title_a: str, visual_a: str, cap_a: str, title_b: str, visual_b: str, cap_b: str) -> str:
    return (
        '<section class="grid-two">'
        f'<article class="panel"><h2>{esc(title_a)}</h2>{visual_a}<p class="caption">{esc(cap_a)}</p></article>'
        f'<article class="panel"><h2>{esc(title_b)}</h2>{visual_b}<p class="caption">{esc(cap_b)}</p></article>'
        '</section>'
    )


def evidence_chain(edges: list[tuple[str, int, str, int]]) -> str:
    nodes = []
    seen = set()
    for a, av, b, bv in edges:
        if a not in seen:
            nodes.append((a, av))
            seen.add(a)
        if b not in seen:
            nodes.append((b, bv))
            seen.add(b)
    width, height = 980, 300
    max_v = max(v for _, v in nodes) or 1
    x_positions = [80, 300, 540, 760, 760]
    y_positions = [145, 145, 80, 145, 220]
    pos = {}
    parts = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="Evidence chain summary">']
    parts.append("<title>Evidence chain summary</title>")
    for i, (name, value) in enumerate(nodes):
        x = x_positions[min(i, len(x_positions) - 1)]
        y = y_positions[min(i, len(y_positions) - 1)]
        pos[name] = (x, y)
        r = 20 + 34 * math.sqrt(value / max_v)
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="{SERIES[i % len(SERIES)]}" opacity="0.82"></circle>')
        parts.append(f'<text class="node-text middle" x="{x}" y="{y - 4}" text-anchor="middle">{esc(short_label(name, 22))}</text>')
        parts.append(f'<text class="node-count middle" x="{x}" y="{y + 18}" text-anchor="middle">{value:,}</text>')
    max_edge = max((min(a, b) for _, a, _, b in edges), default=1)
    for a, av, b, bv in edges:
        if a not in pos or b not in pos:
            continue
        x1, y1 = pos[a]
        x2, y2 = pos[b]
        sw = 2 + 12 * math.sqrt(min(av, bv) / max_edge)
        parts.insert(2, f'<path d="M {x1},{y1} C {(x1+x2)/2},{y1} {(x1+x2)/2},{y2} {x2},{y2}" fill="none" stroke="#6b7280" stroke-width="{sw:.1f}" opacity="0.28"></path>')
    parts.append("</svg>")
    return "\n".join(parts)


def css() -> str:
    return """
<style>
:root {
  color-scheme: light;
  --bg: #f3f6fb;
  --ink: #1e293b;
  --muted: #667085;
  --panel: #ffffff;
  --line: #d9e1ec;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: Arial, Helvetica, sans-serif;
}
main {
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
  padding: 32px 0 48px;
}
.hero {
  padding: 34px;
  border-radius: 14px;
  background: linear-gradient(135deg, #ffffff 0%, #eef4ff 100%);
  border: 1px solid var(--line);
}
.eyebrow {
  margin: 0 0 10px;
  color: #2f6fbb;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  font-size: 12px;
}
h1 {
  margin: 0;
  font-size: 42px;
  line-height: 1.08;
}
.lead {
  max-width: 900px;
  margin: 14px 0 0;
  color: var(--muted);
  font-size: 17px;
  line-height: 1.6;
}
.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-top: 26px;
}
.stat, .panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 14px;
  box-shadow: 0 8px 24px rgba(30, 41, 59, .06);
}
.stat {
  padding: 16px;
}
.stat span, .stat em {
  display: block;
  color: var(--muted);
  font-style: normal;
  font-size: 13px;
}
.stat strong {
  display: block;
  margin: 8px 0 4px;
  font-size: 30px;
}
.panel {
  margin-top: 18px;
  padding: 22px;
}
.grid-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}
.grid-two .panel {
  margin-top: 18px;
}
h2 {
  margin: 0 0 14px;
  font-size: 22px;
  line-height: 1.25;
}
.caption {
  color: var(--muted);
  line-height: 1.55;
  margin: 14px 0 0;
}
.chart {
  width: 100%;
  height: auto;
  display: block;
}
.axis-label, .value-label, .node-label, .node-count, .node-text, .chart-title, .center-label {
  font-family: Arial, Helvetica, sans-serif;
  fill: var(--ink);
}
.axis-label { font-size: 13px; fill: #475467; }
.value-label { font-size: 13px; font-weight: 700; }
.node-label { font-size: 12px; fill: #ffffff; font-weight: 700; }
.node-count { font-size: 12px; fill: #ffffff; }
.node-text { font-size: 13px; fill: var(--ink); font-weight: 700; }
.node-text.middle, .node-count.middle { fill: #ffffff; }
.chart-title { font-size: 14px; font-weight: 700; fill: #334155; }
.center-label { font-size: 18px; font-weight: 700; }
.center-label.small { font-size: 13px; font-weight: 400; fill: #667085; }
.grid { stroke: #d9e1ec; stroke-width: 1; }
.bar { opacity: .86; }
.rotate-label { dominant-baseline: central; }
.treemap {
  display: flex;
  flex-wrap: wrap;
  align-content: stretch;
  min-height: 360px;
  gap: 8px;
}
.tile {
  min-width: 145px;
  min-height: 88px;
  border-radius: 10px;
  padding: 12px;
  color: #ffffff;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.tile strong {
  font-size: 15px;
}
.tile span {
  font-size: 13px;
  opacity: .92;
}
.table-wrap {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
th, td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
}
th {
  color: #334155;
  background: #f7f9fc;
}
.empty-chart {
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
  border: 1px dashed var(--line);
  border-radius: 12px;
}
footer {
  color: var(--muted);
  margin-top: 24px;
  line-height: 1.55;
}
@media (max-width: 860px) {
  .stats, .grid-two { grid-template-columns: 1fr; }
  h1 { font-size: 34px; }
  .hero, .panel { padding: 18px; }
}
</style>
"""


def main() -> None:
    rows = read_rows(SRC)
    report, summary = build_report(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(report, encoding="utf-8")
    SUMMARY_OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote: {OUT}")
    print(f"Wrote: {SUMMARY_OUT}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
