# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import html
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "essay" / "optimized_experimental_database_with_supplementary_expanded160_union_evidence_aware_fulltext_pro_completed.csv"
OUT = ROOT / "essay" / "experimental_database_visualization_report.html"
FRAG = Path(r"C:\Users\zhaol\.codex\visualizations\2026\07\16\019f696f-fb3d-7970-9980-d2136f604864\experimental-database-visuals.html")


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def norm(value: object) -> str:
    return " ".join(str(value or "").strip().split())


rows = list(csv.DictReader(SRC.open("r", encoding="utf-8-sig", newline="")))
N = len(rows)
unique_dois = len({norm(r.get("doi")).lower() for r in rows if norm(r.get("doi"))})

METRIC_LABEL = {
    "glabridin_yield": "产率/得率",
    "glabridin_titer": "产物滴度",
    "enzyme_activity": "酶活",
    "substrate_conversion": "底物转化率",
    "llps_state": "LLPS状态/阈值",
    "specific_activity": "比活力",
    "km": "Km",
    "kinetic_efficiency": "催化效率",
    "relative_activity": "相对活性",
    "critical_phase_concentration": "相分离临界浓度",
    "kcat": "kcat",
}
TIER_LABEL = {"core": "核心库", "llps_core": "LLPS核心", "silver": "银层", "review": "待复核"}
CLEAN_LABEL = {
    "A_complete": "A 完整记录",
    "A_llps": "A LLPS核心",
    "B_product_condition": "B 产物+条件",
    "C_llps_candidate": "C LLPS候选",
    "C_partial_context": "C 部分上下文",
    "D_result_only": "D 仅结果",
}
FAMILY_LABEL = {
    "flavonoid": "黄酮",
    "isoflavonoid": "异黄酮",
    "isoprenoid": "类异戊二烯",
    "terpenoid": "萜类",
    "llps_system": "LLPS体系",
    "natural_product": "天然产物",
    "phenylpropanoid": "苯丙烷类",
    "prenylflavonoid": "异戊烯基黄酮",
    "stilbene": "二苯乙烯",
    "other": "其他",
    "unknown": "未识别",
}
HOST_LABEL = {"yeast": "酵母", "bacteria": "细菌", "plant": "植物", "mammalian": "哺乳动物/细胞", "cell_free": "无细胞体系", "cyanobacteria": "蓝藻", "other": "其他", "unknown": "未识别"}
PALETTE = [
    "var(--viz-series-1, #3b82f6)",
    "var(--viz-series-2, #10b981)",
    "var(--viz-series-3, #f59e0b)",
    "var(--viz-series-4, #ef4444)",
    "var(--viz-series-5, #8b5cf6)",
    "var(--viz-series-6, #06b6d4)",
]


def pct(value: int, total: int = N) -> str:
    return f"{100 * value / total:.1f}%" if total else "0.0%"


FIELD_ALIASES = {
    "product_family": ["best_product_family", "final_product_family", "product_family"],
    "canonical_product": ["best_canonical_product", "final_canonical_product", "canonical_product"],
    "host_group": ["best_host_group", "final_host_group", "host_group"],
    "canonical_host": ["best_canonical_host", "final_canonical_host", "canonical_host"],
}


def row_value(row: dict[str, str], field: str) -> str:
    for key in FIELD_ALIASES.get(field, [field]):
        value = norm(row.get(key))
        if value and value.lower() not in {"unknown", "none", "null", "nan", "n/a", "na", "not specified"}:
            return value
    return "unknown"


def counter(field: str) -> Counter[str]:
    return Counter(row_value(r, field) for r in rows)


def ordered_items(c: Counter[str], labels: dict[str, str] | None = None, order: list[str] | None = None, limit: int | None = None):
    labels = labels or {}
    if order:
        items = [(k, c[k]) for k in order if c[k]]
        items += sorted([(k, v) for k, v in c.items() if k not in set(order)], key=lambda kv: -kv[1])
    else:
        items = sorted(c.items(), key=lambda kv: -kv[1])
    if limit:
        items = items[:limit]
    return [(labels.get(k, k), v, k) for k, v in items if v]


def hbar_svg(items, title: str, width=900, left=190, right=120, row_h=34, bar_h=18) -> str:
    maxv = max((v for _, v, _ in items), default=1)
    plot_w = width - left - right
    height = 34 + len(items) * row_h + 22
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，使用水平条形图展示各类别记录数。</desc>",
    ]
    out.append(f'<line x1="{left}" y1="22" x2="{left + plot_w}" y2="22" class="axis-line" />')
    for i, (label, value, _) in enumerate(items):
        y = 44 + i * row_h
        w = max(2, plot_w * value / maxv)
        color = PALETTE[i % len(PALETTE)] if len(items) <= 8 else PALETTE[0]
        out.append(f'<text x="{left - 12}" y="{y + bar_h - 4}" text-anchor="end" class="axis-label">{esc(label)}</text>')
        out.append(f'<rect x="{left}" y="{y}" width="{w:.2f}" height="{bar_h}" rx="3" fill="{color}" opacity="0.78" />')
        out.append(f'<text x="{min(left + w + 8, left + plot_w + 4):.2f}" y="{y + bar_h - 4}" class="value-label">{value:,} ({pct(value)})</text>')
    out.append("</svg>")
    return "\n".join(out)


def method_transfer_table() -> str:
    rows_html = [
        ("总体流程图", "文献检索、过滤、抽取、清洗、数据库、交互式 Agent", "文献候选库、PDF/SI 抽取、ICL/Prompt、结构化数据库、证据链与前端查询"),
        ("Prompt 结构图", "任务描述、抽取字段、格式示例、通用约束", "schema 字段、必填/非零/单位约束、动态 ICL、JSON 输出骨架"),
        ("数据库概览", "记录保留率、唯一配方数、数据字段覆盖", "证据记录、聚合实验记录、DOI 覆盖、质量层级、上下文字段覆盖"),
        ("质量验证图", "自动抽取与人工/已有数据库对比的误差分布", "无人工金标准时改用完整度、相关性、source quality 与 evidence coverage 作为质量代理"),
        ("统计分析组图", "组分类型、性质分布、高频组分/配方、数据缺口", "产物家族、宿主底盘、主结果指标、条件字段、Top 产物-宿主系统和数值分布"),
        ("时间/频率演化", "高频 DES 配方在应用领域中的累计研究频次", "当前库缺少年份字段，改为 Top DOI/Top 系统的累计记录贡献曲线，并标注后续需补 publication_year"),
        ("Agent 查询链", "自然语言问题转图数据库查询并追溯来源", "以 DOI、Evidence、Record、Host、Product、Metric、Tier 组织 graph-ready 证据链"),
    ]
    body = "\n".join(
        f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in rows_html
    )
    return f"""
<div class="table-responsive">
  <table class="method-table">
    <thead><tr><th>参考文献方法</th><th>DES 论文中的用途</th><th>迁移到本数据库后的实现</th></tr></thead>
    <tbody>{body}</tbody>
  </table>
</div>
"""


def pipeline_workflow_svg(title: str, width=1120, height=470) -> str:
    stages = [
        ("候选文献库", "Scopus / WOS / DOI", "20,000 级候选"),
        ("全文与附件", "PDF / SI / 表格", "PDF、xlsx、docx、zip"),
        ("证据抽取", "LLM + 规则 + ICL", "145,892 条证据"),
        ("结构化清洗", "schema / 单位 / 去重", "143,208 条清洗证据"),
        ("实验记录库", "聚合 / 分层 / 溯源", "11,181 条记录"),
        ("可查询知识库", "Graph-ready / HTML", "DOI 到证据链"),
    ]
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，展示从文献搜索到结构化实验数据库和可查询知识库的流程。</desc>",
    ]
    y = 105
    box_w = 150
    gap = 32
    for i, (name, detail, count) in enumerate(stages):
        x = 36 + i * (box_w + gap)
        out.append(f'<rect x="{x}" y="{y}" width="{box_w}" height="112" rx="8" class="node-fill" />')
        out.append(f'<text x="{x + box_w/2}" y="{y + 32}" text-anchor="middle" class="section-label">{esc(name)}</text>')
        out.append(f'<text x="{x + box_w/2}" y="{y + 58}" text-anchor="middle" class="axis-label">{esc(detail)}</text>')
        out.append(f'<text x="{x + box_w/2}" y="{y + 86}" text-anchor="middle" class="value-label">{esc(count)}</text>')
        if i < len(stages) - 1:
            sx = x + box_w
            tx = x + box_w + gap
            out.append(f'<path d="M {sx},{y + 56} C {sx + 16},{y + 56} {tx - 16},{y + 56} {tx},{y + 56}" class="chain-line" />')
    bottom_items = [
        ("动态 ICL", "按 schema 和相似证据匹配示例"),
        ("领域规则", "单位、非零、必填字段约束"),
        ("断点续跑", "缓存全文、work 文件、state 文件"),
        ("质量分层", "core / silver / review"),
    ]
    for i, (name, detail) in enumerate(bottom_items):
        x = 110 + i * 250
        yy = 300
        out.append(f'<rect x="{x}" y="{yy}" width="190" height="72" rx="8" class="soft-node" />')
        out.append(f'<text x="{x + 95}" y="{yy + 28}" text-anchor="middle" class="section-label">{esc(name)}</text>')
        out.append(f'<text x="{x + 95}" y="{yy + 52}" text-anchor="middle" class="axis-label">{esc(detail)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def prompt_structure_svg(title: str, width=1120, height=430) -> str:
    modules = [
        ("任务描述", "只抽取可追溯实验记录"),
        ("抽取字段", "宿主、产物、底物、条件、结果"),
        ("动态 ICL", "相似文献/相似指标示例"),
        ("领域规则", "单位换算、必填列、非零列"),
        ("输出 JSON", "records 数组 + evidence"),
    ]
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，复刻参考文献的模块化 prompt 结构。</desc>",
    ]
    for i, (name, detail) in enumerate(modules):
        x = 72 + i * 205
        y = 116
        out.append(f'<rect x="{x}" y="{y}" width="160" height="120" rx="8" class="node-fill" />')
        out.append(f'<text x="{x + 80}" y="{y + 34}" text-anchor="middle" class="section-label">{esc(name)}</text>')
        out.append(f'<text x="{x + 80}" y="{y + 64}" text-anchor="middle" class="axis-label">{esc(detail)}</text>')
        if i < len(modules) - 1:
            out.append(f'<path d="M {x + 160},{y + 60} C {x + 180},{y + 60} {x + 185},{y + 60} {x + 205},{y + 60}" class="chain-line" />')
    out.append(f'<rect x="250" y="300" width="620" height="54" rx="8" class="soft-node" />')
    out.append(f'<text x="560" y="333" text-anchor="middle" class="value-label">本项目对应：schema_config + icl_examples + build_prompt + constraints + JSON parser</text>')
    out.append("</svg>")
    return "\n".join(out)


def graph_rag_schema_svg(title: str, width=1120, height=520) -> str:
    nodes = [
        ("Literature", "文献 DOI / 标题", 115, 120),
        ("Evidence", "原文/表格证据", 360, 120),
        ("ExperimentRecord", "结构化实验记录", 610, 120),
        ("Metric", "滴度/产率/酶活", 865, 95),
        ("QualityTier", "core/silver/review", 865, 190),
        ("Host", "宿主底盘", 360, 330),
        ("Product", "产物家族", 610, 330),
        ("QueryAgent", "自然语言查询", 865, 330),
    ]
    links = [
        (0, 1, "has evidence"),
        (1, 2, "supports"),
        (2, 3, "has result"),
        (2, 4, "assigned to"),
        (2, 5, "uses host"),
        (2, 6, "produces"),
        (7, 2, "retrieves"),
        (7, 0, "traces source"),
    ]
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，展示数据库可转为图检索结构的节点和边。</desc>",
    ]
    for a, b, label in links:
        x1, y1 = nodes[a][2] + 80, nodes[a][3] + 30
        x2, y2 = nodes[b][2], nodes[b][3] + 30
        if x2 < x1:
            x1 = nodes[a][2]
            x2 = nodes[b][2] + 160
        out.append(f'<path d="M {x1},{y1} C {(x1+x2)/2},{y1} {(x1+x2)/2},{y2} {x2},{y2}" class="chain-line"><title>{esc(label)}</title></path>')
        out.append(f'<text x="{(x1+x2)/2}" y="{(y1+y2)/2 - 6}" text-anchor="middle" class="axis-label">{esc(label)}</text>')
    for name, detail, x, y in nodes:
        out.append(f'<rect x="{x}" y="{y}" width="160" height="64" rx="8" class="node-fill" />')
        out.append(f'<text x="{x + 80}" y="{y + 26}" text-anchor="middle" class="section-label">{esc(name)}</text>')
        out.append(f'<text x="{x + 80}" y="{y + 48}" text-anchor="middle" class="axis-label">{esc(detail)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def availability_panel_svg(title: str, width=1120, height=470) -> str:
    checks = [
        ("DOI", lambda r: bool(norm(r.get("doi")))),
        ("标题", lambda r: bool(norm(r.get("title_clean") or r.get("title")))),
        ("证据文本", lambda r: bool(norm(r.get("primary_result_evidence")))),
        ("产物", lambda r: norm(r.get("canonical_product")).lower() != "unknown"),
        ("宿主", lambda r: norm(r.get("canonical_host")).lower() != "unknown"),
        ("实验条件", lambda r: any(norm(r.get(f"{m}_value")) for m in ["reaction_time", "reaction_temperature", "reaction_ph", "substrate_concentration", "cell_density_od600"])),
        ("单位", lambda r: bool(norm(r.get("primary_result_unit")))),
        ("归一化数值", lambda r: bool(norm(r.get("primary_result_numeric_normalized")))),
    ]
    values = [(name, sum(1 for row in rows if fn(row))) for name, fn in checks]
    maxv = N
    left = 160
    plot_w = 790
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，展示关键字段的数据可用性。</desc>",
    ]
    for i, (name, value) in enumerate(values):
        y = 62 + i * 44
        w = plot_w * value / maxv
        out.append(f'<text x="{left - 14}" y="{y + 18}" text-anchor="end" class="axis-label">{esc(name)}</text>')
        out.append(f'<rect x="{left}" y="{y}" width="{plot_w}" height="22" rx="4" fill="var(--border, #d8deea)" opacity="0.28" />')
        out.append(f'<rect x="{left}" y="{y}" width="{w:.2f}" height="22" rx="4" fill="var(--viz-series-1, #3b82f6)" opacity="0.72" />')
        out.append(f'<text x="{left + plot_w + 12}" y="{y + 17}" class="value-label">{value:,} ({pct(value)})</text>')
    out.append("</svg>")
    return "\n".join(out)


def quality_proxy_svg(title: str, width=1120, height=460) -> str:
    bins = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 101)]
    comp = Counter()
    rel = Counter()
    for row in rows:
        try:
            c = int(float(row.get("completeness_score") or 0))
        except ValueError:
            c = 0
        try:
            r = int(float(row.get("project_relevance_score") or 0))
        except ValueError:
            r = 0
        comp[next(i for i, (a, b) in enumerate(bins) if a <= c < b)] += 1
        rel[min(4, r // 3)] += 1
    qual = counter("aggregation_quality")
    x0 = 90
    bar_w = 64
    baseline = 250
    maxv = max(max(comp.values(), default=1), max(rel.values(), default=1))
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，使用完整度、项目相关性和抽取质量标签作为无人工金标准情况下的质量代理分析。</desc>",
        '<text x="210" y="38" text-anchor="middle" class="section-label">完整度分布</text>',
        '<text x="550" y="38" text-anchor="middle" class="section-label">项目相关性分布</text>',
        '<text x="890" y="38" text-anchor="middle" class="section-label">抽取质量标签</text>',
    ]
    for i, (a, b) in enumerate(bins):
        v = comp[i]
        h = 170 * v / maxv
        x = x0 + i * (bar_w + 10)
        label = f"{a}-{b-1}" if b < 101 else "80-100"
        out.append(f'<rect x="{x}" y="{baseline - h:.2f}" width="{bar_w}" height="{h:.2f}" rx="4" fill="var(--viz-series-1, #3b82f6)" opacity="0.72" />')
        out.append(f'<text x="{x + bar_w/2}" y="{baseline + 22}" text-anchor="middle" class="axis-label">{label}</text>')
    for i in range(5):
        v = rel[i]
        h = 170 * v / maxv
        x = 430 + i * (bar_w + 10)
        out.append(f'<rect x="{x}" y="{baseline - h:.2f}" width="{bar_w}" height="{h:.2f}" rx="4" fill="var(--viz-series-2, #10b981)" opacity="0.72" />')
        out.append(f'<text x="{x + bar_w/2}" y="{baseline + 22}" text-anchor="middle" class="axis-label">{i*3}-{i*3+2}</text>')
    q_items = ordered_items(qual, None, ["high", "medium", "candidate", "llm"])
    maxq = max((v for _, v, _ in q_items), default=1)
    for i, (label, v, _) in enumerate(q_items[:4]):
        y = 82 + i * 54
        w = 220 * v / maxq
        out.append(f'<text x="790" y="{y + 18}" text-anchor="end" class="axis-label">{esc(label)}</text>')
        out.append(f'<rect x="805" y="{y}" width="{w:.2f}" height="22" rx="4" fill="var(--viz-series-3, #f59e0b)" opacity="0.72" />')
        out.append(f'<text x="{815 + w:.2f}" y="{y + 17}" class="value-label">{v:,}</text>')
    out.append('<text x="560" y="375" text-anchor="middle" class="axis-label">说明：这里复刻参考文献的“质量验证图”思路，但当前库尚无人工金标准，因此显示质量代理，而非人工误差。</text>')
    out.append("</svg>")
    return "\n".join(out)


def fig4_database_source_overview_svg(title: str, width=1120, height=620) -> str:
    source_mode_counts = counter("source_mode")
    data_type_counts = counter("data_source_type_value")
    source_quality_counts = counter("aggregation_quality")
    stages = [
        ("候选 DOI", 5275),
        ("可读附件", 1594),
        ("高召回证据", 145892),
        ("清洗证据", 143208),
        ("聚合候选", 20587),
        ("最终记录", N),
    ]
    left = 58
    top = 62
    bar_w = 126
    max_stage = max(v for _, v in stages)
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，复刻参考文献 Fig. 4 的数据库来源与保留概览。</desc>",
        '<text x="58" y="30" class="section-label">a 数据来源与保留链路</text>',
    ]
    baseline = 250
    for i, (label, value) in enumerate(stages):
        x = left + i * 168
        h = max(8, 168 * math.sqrt(value / max_stage))
        out.append(f'<rect x="{x}" y="{baseline - h:.2f}" width="{bar_w}" height="{h:.2f}" rx="6" fill="{PALETTE[i % len(PALETTE)]}" opacity="0.72"><title>{esc(label)}: {value:,}</title></rect>')
        out.append(f'<text x="{x + bar_w/2}" y="{baseline + 24}" text-anchor="middle" class="axis-label">{esc(label)}</text>')
        out.append(f'<text x="{x + bar_w/2}" y="{baseline - h - 8:.2f}" text-anchor="middle" class="value-label">{value:,}</text>')
        if i < len(stages) - 1:
            out.append(f'<path d="M {x + bar_w + 8},{baseline - h/2:.2f} C {x + bar_w + 28},{baseline - h/2:.2f} {x + 144},{baseline - h/2:.2f} {x + 160},{baseline - h/2:.2f}" class="axis-line" />')

    def panel_bars(items, x0, y0, panel_title, labels=None, max_items=5):
        labels = labels or {}
        top_items = sorted(items.items(), key=lambda kv: -kv[1])[:max_items]
        maxv = max((v for _, v in top_items), default=1)
        out.append(f'<text x="{x0}" y="{y0}" class="section-label">{esc(panel_title)}</text>')
        for j, (key, value) in enumerate(top_items):
            y = y0 + 30 + j * 38
            w = 250 * value / maxv
            label = labels.get(key, key) if key else "未标注"
            if len(label) > 26:
                label = label[:24] + "..."
            out.append(f'<text x="{x0 + 92}" y="{y + 16}" text-anchor="end" class="axis-label">{esc(label)}</text>')
            out.append(f'<rect x="{x0 + 104}" y="{y}" width="{w:.2f}" height="20" rx="4" fill="var(--viz-series-1, #3b82f6)" opacity="0.68" />')
            out.append(f'<text x="{x0 + 112 + w:.2f}" y="{y + 16}" class="value-label">{value:,}</text>')

    panel_bars(source_mode_counts, 70, 330, "b 数据来源模式", {
        "aggregated_high_recall_evidence_group": "全文/SI 高召回聚合",
        "llm_completed_d_result_only_fulltext": "LLM 补全 D 级记录",
        "llm_or_existing_multi_metric": "LLM 多指标记录",
    })
    panel_bars(data_type_counts, 430, 330, "c 证据类型", {"table": "表格", "text": "正文", "method": "方法", "figure": "图/图注", "unknown": "未识别"})
    panel_bars(source_quality_counts, 790, 330, "d 抽取质量标签", {"high": "高", "medium": "中", "candidate": "候选", "llm": "LLM 补全"})
    out.append("</svg>")
    return "\n".join(out)


def fig4_research_comparison_svg(title: str, width=1120, height=560) -> str:
    strict_old = 7339
    strict_new = N
    broad = 20567
    core_silver = sum(1 for r in rows if r.get("database_tier") in {"core", "llps_core", "silver"})
    unique_products = len({norm(r.get("canonical_product")).lower() for r in rows if norm(r.get("canonical_product")).lower() not in {"", "unknown"}})
    unique_hosts = len({norm(r.get("canonical_host")).lower() for r in rows if norm(r.get("canonical_host")).lower() not in {"", "unknown"}})
    unique_systems = len({
        (norm(r.get("canonical_product")).lower(), norm(r.get("canonical_host")).lower())
        for r in rows
        if norm(r.get("canonical_product")).lower() not in {"", "unknown"}
        and norm(r.get("canonical_host")).lower() not in {"", "unknown"}
    })
    comparisons = [
        ("DES 参考库", "文献", 14602, "记录", 34027, "唯一配方", 9215),
        ("本项目严格库", "DOI", unique_dois, "记录", strict_new, "产物-宿主系统", unique_systems),
        ("本项目宽召回", "DOI", unique_dois, "记录", broad, "核心/银层", core_silver),
        ("扩量前版本", "DOI", 1362, "记录", strict_old, "核心/银层", 2763),
    ]
    maxv = max(max(a, b, c) for _, _, a, _, b, _, c in comparisons)
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，复刻参考文献 Fig. 4b 的数据库规模与研究比较。</desc>",
        '<text x="58" y="34" class="section-label">Research comparison：参考 DES 数据库 vs 本项目实验记录库</text>',
    ]
    left = 170
    y0 = 80
    row_h = 94
    plot_w = 760
    for i, (name, l1, v1, l2, v2, l3, v3) in enumerate(comparisons):
        y = y0 + i * row_h
        out.append(f'<text x="{left - 18}" y="{y + 34}" text-anchor="end" class="section-label">{esc(name)}</text>')
        for j, (label, value) in enumerate([(l1, v1), (l2, v2), (l3, v3)]):
            yy = y + j * 24
            w = plot_w * math.sqrt(value / maxv)
            out.append(f'<rect x="{left}" y="{yy}" width="{w:.2f}" height="17" rx="3" fill="{PALETTE[j]}" opacity="0.68"><title>{esc(label)}: {value:,}</title></rect>')
            out.append(f'<text x="{left + w + 8:.2f}" y="{yy + 14}" class="value-label">{esc(label)} {value:,}</text>')
    lx = 170
    for j, label in enumerate(["文献/DOI 覆盖", "结构化记录", "唯一对象/高质量子集"]):
        out.append(f'<rect x="{lx}" y="500" width="13" height="13" rx="2" fill="{PALETTE[j]}" opacity="0.68" />')
        out.append(f'<text x="{lx + 20}" y="511" class="axis-label">{esc(label)}</text>')
        lx += 210
    out.append("</svg>")
    return "\n".join(out)


def fig6_llps_enzyme_analysis_svg(title: str, width=1180, height=930) -> str:
    enzyme_metrics = {"enzyme_activity", "specific_activity", "relative_activity", "km", "kcat", "kinetic_efficiency"}
    llps_metrics = {"llps_state", "critical_phase_concentration", "frap_half_time", "droplet_dissolution_time"}
    production_metrics = {"glabridin_titer", "glabridin_yield", "substrate_conversion"}

    def is_llps(row):
        text = " ".join([row.get("primary_result_evidence", ""), row.get("title_clean", ""), row_value(row, "product_family")]).lower()
        return row.get("primary_result_metric") in llps_metrics or any(t in text for t in ["llps", "phase separation", "condensate", "droplet", "puncta"])

    def is_enzyme(row):
        text = " ".join([row.get("primary_result_evidence", ""), row.get("title_clean", "")]).lower()
        return row.get("primary_result_metric") in enzyme_metrics or "enzyme" in text

    groups = {
        "酶体系": [r for r in rows if is_enzyme(r)],
        "LLPS体系": [r for r in rows if is_llps(r)],
        "产物性能": [r for r in rows if r.get("primary_result_metric") in production_metrics],
    }
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，复刻参考文献 Fig. 6 的多面板统计分析，用于 LLPS 和酶催化体系。</desc>",
    ]

    def mini_bar(counter_obj, x, y, w, panel_title, label_map=None, topn=6):
        label_map = label_map or {}
        items = sorted(counter_obj.items(), key=lambda kv: -kv[1])[:topn]
        maxv = max((v for _, v in items), default=1)
        out.append(f'<text x="{x}" y="{y}" class="section-label">{esc(panel_title)}</text>')
        for i, (key, value) in enumerate(items):
            yy = y + 30 + i * 28
            label = label_map.get(key, key) if key else "未识别"
            if len(label) > 20:
                label = label[:18] + "..."
            bw = w * value / maxv
            out.append(f'<text x="{x + 102}" y="{yy + 14}" text-anchor="end" class="axis-label">{esc(label)}</text>')
            out.append(f'<rect x="{x + 112}" y="{yy}" width="{bw:.2f}" height="17" rx="3" fill="var(--viz-series-1, #3b82f6)" opacity="0.66" />')
            out.append(f'<text x="{x + 120 + bw:.2f}" y="{yy + 14}" class="value-label">{value:,}</text>')

    # a: system category size
    sys_counts = Counter({k: len(v) for k, v in groups.items()})
    mini_bar(sys_counts, 50, 42, 245, "a 体系类别记录数", topn=3)

    # b: metric distribution
    metric_counts = Counter(r.get("primary_result_metric") or "unknown" for r in rows if is_enzyme(r) or is_llps(r))
    mini_bar(metric_counts, 430, 42, 245, "b LLPS/酶相关指标", METRIC_LABEL, topn=7)

    # c: quality tier for LLPS/enzyme
    tier_mix = defaultdict(Counter)
    for name, subset in groups.items():
        for row in subset:
            tier_mix[name][row.get("database_tier") or "review"] += 1
    x0, y0 = 825, 42
    out.append(f'<text x="{x0}" y="{y0}" class="section-label">c 体系质量层级</text>')
    tier_keys = ["core", "llps_core", "silver", "review"]
    max_t = max((sum(c.values()) for c in tier_mix.values()), default=1)
    for i, (name, c) in enumerate(tier_mix.items()):
        y = y0 + 32 + i * 46
        x = x0 + 110
        out.append(f'<text x="{x0 + 96}" y="{y + 16}" text-anchor="end" class="axis-label">{esc(name)}</text>')
        for j, tier in enumerate(tier_keys):
            value = c[tier]
            if not value:
                continue
            bw = 270 * value / max_t
            out.append(f'<rect x="{x:.2f}" y="{y}" width="{bw:.2f}" height="20" rx="2" fill="{PALETTE[j]}" opacity="0.7"><title>{esc(name)} · {esc(TIER_LABEL.get(tier, tier))}: {value:,}</title></rect>')
            x += bw

    # d/e/f: host, product, enzyme names
    mini_bar(Counter(r.get("host_group") or "unknown" for r in rows if is_enzyme(r)), 50, 315, 245, "d 酶体系宿主类型", HOST_LABEL)
    mini_bar(Counter(r.get("product_family") or "unknown" for r in rows if is_llps(r)), 430, 315, 245, "e LLPS相关产物/体系", FAMILY_LABEL)
    enzyme_names = Counter(norm(r.get("enzyme_name_value")) or "未识别" for r in rows if is_enzyme(r))
    mini_bar(enzyme_names, 825, 315, 245, "f 高频酶名称", topn=6)

    # g: condition availability by group
    condition_fields = [
        ("温度", "reaction_temperature"),
        ("pH", "reaction_ph"),
        ("时间", "reaction_time"),
        ("底物浓度", "substrate_concentration"),
        ("OD600", "cell_density_od600"),
    ]
    xg, yg = 50, 610
    out.append(f'<text x="{xg}" y="{yg}" class="section-label">g 实验条件覆盖率</text>')
    for i, (group_name, subset) in enumerate(groups.items()):
        y = yg + 36 + i * 52
        out.append(f'<text x="{xg + 88}" y="{y + 18}" text-anchor="end" class="axis-label">{esc(group_name)}</text>')
        x = xg + 110
        denom = max(1, len(subset))
        for j, (label, field) in enumerate(condition_fields):
            value = sum(1 for r in subset if norm(r.get(f"{field}_value")))
            h = 24
            cell_w = 92
            op = 0.12 + 0.72 * value / denom
            out.append(f'<rect x="{x + j * cell_w}" y="{y}" width="82" height="{h}" rx="4" fill="{PALETTE[j % len(PALETTE)]}" opacity="{op:.3f}"><title>{esc(group_name)} · {esc(label)}: {value:,} ({100 * value / denom:.1f}%)</title></rect>')
            out.append(f'<text x="{x + j * cell_w + 41}" y="{y + 17}" text-anchor="middle" class="cell-label">{value:,}</text>')
    for j, (label, _) in enumerate(condition_fields):
        out.append(f'<text x="{160 + j * 92 + 41}" y="{yg + 206}" text-anchor="middle" class="axis-label">{esc(label)}</text>')

    # h: main numeric distribution summary
    numeric_metrics = ["enzyme_activity", "km", "critical_phase_concentration", "llps_state", "glabridin_titer", "glabridin_yield"]
    xh, yh = 650, 610
    out.append(f'<text x="{xh}" y="{yh}" class="section-label">h 关键数值中位数（正值）</text>')
    medians = []
    for metric in numeric_metrics:
        vals = []
        for row in rows:
            if row.get("primary_result_metric") != metric:
                continue
            raw = row.get("primary_result_numeric_normalized") or row.get("primary_result_numeric")
            try:
                val = float(raw)
                if math.isfinite(val) and val > 0:
                    vals.append(val)
            except (TypeError, ValueError):
                pass
        vals.sort()
        if vals:
            medians.append((metric, vals[len(vals) // 2], len(vals)))
    max_med = max((math.log10(v + 1) for _, v, _ in medians), default=1)
    for i, (metric, median, count) in enumerate(medians):
        y = yh + 34 + i * 34
        bw = 275 * math.log10(median + 1) / max_med
        out.append(f'<text x="{xh + 132}" y="{y + 15}" text-anchor="end" class="axis-label">{esc(METRIC_LABEL.get(metric, metric))}</text>')
        out.append(f'<rect x="{xh + 145}" y="{y}" width="{bw:.2f}" height="18" rx="3" fill="var(--viz-series-2, #10b981)" opacity="0.68" />')
        out.append(f'<text x="{xh + 153 + bw:.2f}" y="{y + 15}" class="value-label">{median:.3g} / n={count:,}</text>')

    out.append("</svg>")
    return "\n".join(out)


def top_system_cumulative_svg(title: str, width=1120, height=520) -> str:
    systems = Counter()
    doi_systems: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        product = row_value(row, "canonical_product")
        host = row_value(row, "canonical_host")
        if not product or product.lower() == "unknown":
            product = FAMILY_LABEL.get(row_value(row, "product_family"), "未识别")
        if not host or host.lower() == "unknown":
            host = HOST_LABEL.get(row_value(row, "host_group"), "未识别")
        system = f"{product} / {host}"
        systems[system] += 1
        doi = norm(row.get("doi")).lower()
        if doi:
            doi_systems[doi][system] += 1
    top_systems = [s for s, _ in systems.most_common(6)]
    doi_order = [doi for doi, _ in sorted(doi_systems.items(), key=lambda kv: -sum(kv[1].values()))[:220]]
    cum = {s: [] for s in top_systems}
    running = Counter()
    for rank, doi in enumerate(doi_order, start=1):
        running.update(doi_systems[doi])
        for s in top_systems:
            cum[s].append((rank, running[s]))
    left, top, plot_w, plot_h = 100, 50, 850, 360
    max_y = max((points[-1][1] for points in cum.values() if points), default=1)
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，按 DOI 记录贡献排序，展示高频产物/宿主系统的累计记录数。</desc>",
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" class="axis-line" />',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" class="axis-line" />',
    ]
    def sx(rank: int) -> float:
        return left + plot_w * (rank - 1) / max(1, len(doi_order) - 1)
    def sy(value: int) -> float:
        return top + plot_h - plot_h * value / max_y
    for i, s in enumerate(top_systems):
        points = cum[s]
        if not points:
            continue
        d = " ".join(("M" if j == 0 else "L") + f" {sx(rank):.2f},{sy(value):.2f}" for j, (rank, value) in enumerate(points))
        color = PALETTE[i % len(PALETTE)]
        out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.5" opacity="0.82"><title>{esc(s)}: {points[-1][1]:,}</title></path>')
        out.append(f'<text x="{left + plot_w + 12}" y="{sy(points[-1][1]) + 4:.2f}" class="axis-label">{esc(s[:28])} {points[-1][1]:,}</text>')
    out.append(f'<text x="{left + plot_w/2}" y="{top + plot_h + 38}" text-anchor="middle" class="axis-label">按实验记录贡献排序的 DOI 序号</text>')
    out.append(f'<text x="28" y="{top + plot_h/2}" transform="rotate(-90 28 {top + plot_h/2})" text-anchor="middle" class="axis-label">累计实验记录数</text>')
    out.append("</svg>")
    return "\n".join(out)


def agent_query_example_svg(title: str, width=1120, height=520) -> str:
    lanes = [
        ("用户问题", "哪些酵母底盘中有黄酮/异戊二烯产物的高滴度或高产率记录？", 70),
        ("意图解析", "识别 host=yeast，product_family=flavonoid/isoprenoid，metric=titer/yield", 160),
        ("图检索", "Record - Host - Product - Metric - Evidence - DOI", 250),
        ("结果组织", "返回实验记录、数值单位、证据片段、数据库层级和 DOI", 340),
        ("追溯验证", "打开原文或 SI 证据，复核 review 层记录后纳入建模", 430),
    ]
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，复刻参考文献的三轮 Agent 查询链，并迁移到当前实验数据库。</desc>",
    ]
    for i, (name, detail, y) in enumerate(lanes):
        x = 110 + i * 190
        out.append(f'<rect x="{x}" y="{y}" width="170" height="74" rx="8" class="node-fill" />')
        out.append(f'<text x="{x + 85}" y="{y + 28}" text-anchor="middle" class="section-label">{esc(name)}</text>')
        out.append(f'<text x="{x + 85}" y="{y + 52}" text-anchor="middle" class="axis-label">{esc(detail[:24])}</text>')
        if i < len(lanes) - 1:
            out.append(f'<path d="M {x + 170},{y + 37} C {x + 206},{y + 37} {x + 154},{lanes[i+1][2] + 37} {x + 190},{lanes[i+1][2] + 37}" class="chain-line" />')
    out.append('<text x="560" y="485" text-anchor="middle" class="axis-label">该图是工作流示意：当前 HTML 已具备统计和证据链展示，后续可将同一结构接入图数据库和自然语言查询。</text>')
    out.append("</svg>")
    return "\n".join(out)


def funnel_svg(stages, title: str, width=900, left=170, right=100, row_h=42) -> str:
    maxv = max(v for _, v, _ in stages)
    plot_w = width - left - right
    height = 44 + len(stages) * row_h + 18
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，展示从证据到最终数据库的记录保留过程。</desc>",
    ]
    for i, (label, value, note) in enumerate(stages):
        y = 38 + i * row_h
        w = max(3, plot_w * value / maxv)
        out.append(f'<text x="{left - 12}" y="{y + 21}" text-anchor="end" class="axis-label">{esc(label)}</text>')
        out.append(f'<rect x="{left}" y="{y}" width="{w:.2f}" height="24" rx="4" fill="{PALETTE[i % len(PALETTE)]}" opacity="0.72" />')
        out.append(f'<text x="{min(left + w + 8, left + plot_w + 4):.2f}" y="{y + 18}" class="value-label">{value:,}</text>')
        out.append(f'<text x="{left + plot_w + 78}" y="{y + 18}" class="axis-label">{esc(note)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def stacked_bar_svg(groups, series_keys, series_labels, title: str, width=900, left=180, right=90, row_h=38) -> str:
    totals = {g: sum(groups[g].get(k, 0) for k in series_keys) for g in groups}
    ordered = sorted(groups, key=lambda g: -totals[g])
    maxv = max(totals.values(), default=1)
    plot_w = width - left - right
    height = 48 + len(ordered) * row_h + 52
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，每行按数据库层级堆叠。</desc>",
    ]
    for i, g in enumerate(ordered):
        y = 40 + i * row_h
        x = left
        out.append(f'<text x="{left - 12}" y="{y + 18}" text-anchor="end" class="axis-label">{esc(METRIC_LABEL.get(g, g))}</text>')
        for j, k in enumerate(series_keys):
            v = groups[g].get(k, 0)
            if not v:
                continue
            w = plot_w * v / maxv
            out.append(f'<rect x="{x:.2f}" y="{y}" width="{max(1, w):.2f}" height="20" rx="2" fill="{PALETTE[j % len(PALETTE)]}" opacity="0.78"><title>{esc(METRIC_LABEL.get(g, g))} · {esc(series_labels[j])}: {v}</title></rect>')
            x += w
        out.append(f'<text x="{left + plot_w + 8}" y="{y + 16}" class="value-label">{totals[g]:,}</text>')
    lx = left
    ly = height - 24
    for j, label in enumerate(series_labels):
        out.append(f'<rect x="{lx}" y="{ly - 12}" width="12" height="12" rx="2" fill="{PALETTE[j % len(PALETTE)]}" opacity="0.78" />')
        out.append(f'<text x="{lx + 18}" y="{ly - 2}" class="axis-label">{esc(label)}</text>')
        lx += 110
    out.append("</svg>")
    return "\n".join(out)


def heatmap_svg(xkeys, ykeys, matrix, xlabels, ylabels, title: str, width=900, left=160, top=58, cell_w=112, cell_h=38) -> str:
    plot_w = cell_w * len(xkeys)
    height = top + cell_h * len(ykeys) + 44
    width = max(width, left + plot_w + 60)
    maxv = max((matrix.get((y, x), 0) for y in ykeys for x in xkeys), default=1)
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，颜色深浅表示记录数。</desc>",
    ]
    for xi, x in enumerate(xkeys):
        out.append(f'<text x="{left + xi * cell_w + cell_w / 2}" y="28" text-anchor="middle" class="axis-label">{esc(xlabels.get(x, x))}</text>')
    for yi, y in enumerate(ykeys):
        yy = top + yi * cell_h
        out.append(f'<text x="{left - 12}" y="{yy + 24}" text-anchor="end" class="axis-label">{esc(ylabels.get(y, y))}</text>')
        for xi, x in enumerate(xkeys):
            v = matrix.get((y, x), 0)
            op = 0.08 + 0.82 * (math.sqrt(v) / math.sqrt(maxv) if maxv else 0)
            xx = left + xi * cell_w
            out.append(f'<rect x="{xx}" y="{yy}" width="{cell_w - 4}" height="{cell_h - 4}" rx="4" fill="var(--viz-series-1, #3b82f6)" opacity="{op:.3f}"><title>{esc(ylabels.get(y, y))} · {esc(xlabels.get(x, x))}: {v}</title></rect>')
            if v:
                out.append(f'<text x="{xx + (cell_w - 4) / 2}" y="{yy + 23}" text-anchor="middle" class="cell-label">{v:,}</text>')
    out.append("</svg>")
    return "\n".join(out)


def log_box_svg(metrics, title: str, width=900, left=170, right=70, row_h=42) -> str:
    data = []
    for metric in metrics:
        vals = []
        for row in rows:
            if row.get("primary_result_metric") == metric:
                raw = row.get("primary_result_numeric_normalized") or row.get("primary_result_numeric") or ""
                try:
                    x = float(raw)
                    if math.isfinite(x) and x > 0:
                        vals.append(x)
                except ValueError:
                    pass
        vals.sort()
        if len(vals) >= 3:
            def q(p: float) -> float:
                return vals[min(len(vals) - 1, int(round((len(vals) - 1) * p)))]
            data.append((metric, len(vals), q(.05), q(.25), q(.5), q(.75), q(.95)))
    logs = [math.log10(x) for _, _, p5, q1, med, q3, p95 in data for x in [p5, q1, med, q3, p95] if x > 0]
    lo = min(logs) if logs else 0
    hi = max(logs) if logs else 1
    if hi == lo:
        hi = lo + 1
    plot_w = width - left - right
    height = 58 + len(data) * row_h + 52
    axis_y = height - 38

    def sx(value: float) -> float:
        return left + (math.log10(value) - lo) / (hi - lo) * plot_w

    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，横轴为正数值的 log10 尺度，箱线表示5%到95%范围及四分位数。</desc>",
        f'<line x1="{left}" y1="{axis_y}" x2="{left + plot_w}" y2="{axis_y}" class="axis-line" />',
    ]
    for tick in range(math.floor(lo), math.ceil(hi) + 1):
        x = left + (tick - lo) / (hi - lo) * plot_w
        if left <= x <= left + plot_w:
            label = f"10^{tick}" if abs(tick) > 2 else f"{10 ** tick:g}"
            out.append(f'<line x1="{x:.2f}" y1="{axis_y}" x2="{x:.2f}" y2="{axis_y + 5}" class="axis-line" />')
            out.append(f'<text x="{x:.2f}" y="{axis_y + 22}" text-anchor="middle" class="axis-label">{esc(label)}</text>')
    for i, (metric, count, p5, q1, med, q3, p95) in enumerate(data):
        y = 38 + i * row_h
        out.append(f'<text x="{left - 12}" y="{y + 18}" text-anchor="end" class="axis-label">{esc(METRIC_LABEL.get(metric, metric))}</text>')
        out.append(f'<line x1="{sx(p5):.2f}" y1="{y + 12}" x2="{sx(p95):.2f}" y2="{y + 12}" class="axis-line" />')
        out.append(f'<rect x="{sx(q1):.2f}" y="{y + 2}" width="{max(2, sx(q3) - sx(q1)):.2f}" height="20" rx="3" fill="var(--viz-series-2, #10b981)" opacity="0.58" />')
        out.append(f'<line x1="{sx(med):.2f}" y1="{y}" x2="{sx(med):.2f}" y2="{y + 24}" stroke="var(--foreground, #111827)" stroke-width="2" />')
        out.append(f'<text x="{left + plot_w + 8}" y="{y + 17}" class="value-label">n={count:,}</text>')
    out.append("</svg>")
    return "\n".join(out)


def quality_heatmap_svg(title: str, width=900, left=120, top=54, cell_w=88, cell_h=38) -> str:
    comp_bins = [0, 20, 40, 60, 80, 101]
    rel_bins = [0, 3, 6, 9, 12, 16]
    xlabels = ["0-19", "20-39", "40-59", "60-79", "80-100"]
    ylabels = ["0-2", "3-5", "6-8", "9-11", "12-15"]
    mat = defaultdict(int)
    for row in rows:
        try:
            comp = int(float(row.get("completeness_score") or 0))
        except ValueError:
            comp = 0
        try:
            rel = int(float(row.get("project_relevance_score") or 0))
        except ValueError:
            rel = 0
        xi = next((i for i in range(len(comp_bins) - 1) if comp_bins[i] <= comp < comp_bins[i + 1]), len(comp_bins) - 2)
        yi = next((i for i in range(len(rel_bins) - 1) if rel_bins[i] <= rel < rel_bins[i + 1]), len(rel_bins) - 2)
        mat[(yi, xi)] += 1
    maxv = max(mat.values(), default=1)
    height = top + cell_h * len(ylabels) + 52
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，横轴为完整度，纵轴为项目相关性，颜色表示记录数。</desc>",
    ]
    for xi, label in enumerate(xlabels):
        out.append(f'<text x="{left + xi * cell_w + cell_w / 2}" y="30" text-anchor="middle" class="axis-label">{esc(label)}</text>')
    for yi, label in enumerate(ylabels):
        yy = top + (len(ylabels) - 1 - yi) * cell_h
        out.append(f'<text x="{left - 10}" y="{yy + 24}" text-anchor="end" class="axis-label">{esc(label)}</text>')
        for xi, xlabel in enumerate(xlabels):
            v = mat.get((yi, xi), 0)
            op = 0.07 + 0.85 * (math.sqrt(v) / math.sqrt(maxv))
            xx = left + xi * cell_w
            out.append(f'<rect x="{xx}" y="{yy}" width="{cell_w - 4}" height="{cell_h - 4}" rx="4" fill="var(--viz-series-3, #f59e0b)" opacity="{op:.3f}"><title>相关性 {label}，完整度 {xlabel}: {v}</title></rect>')
            if v:
                out.append(f'<text x="{xx + (cell_w - 4) / 2}" y="{yy + 23}" text-anchor="middle" class="cell-label">{v:,}</text>')
    out.append("</svg>")
    return "\n".join(out)


def word_cloud_svg(title: str, width=1040, height=560) -> str:
    stop_words = {
        "the", "and", "for", "with", "from", "into", "that", "this", "were", "was", "are", "has", "have",
        "using", "used", "use", "via", "its", "their", "between", "than", "then", "also", "based",
        "study", "studies", "result", "results", "table", "figure", "fig", "supplementary", "data",
        "analysis", "effect", "effects", "different", "showed", "shown", "obtained", "respectively",
        "strain", "strains", "cell", "cells", "level", "levels", "value", "values", "unknown",
        "mg", "ml", "mm", "um", "nm", "min", "hour", "hours", "using", "production",
    }
    phrase_terms = [
        "Saccharomyces cerevisiae", "Escherichia coli", "Yarrowia lipolytica",
        "metabolic engineering", "synthetic biology", "heterologous biosynthesis",
        "enzyme activity", "substrate conversion", "phase separation",
        "liquid droplet", "protein condensate", "natural product",
        "flavonoid", "isoflavonoid", "isoprenoid", "terpenoid",
        "naringenin", "glabridin", "liquiritigenin", "quercetin",
        "astaxanthin", "lycopene", "resveratrol", "squalene",
    ]
    weights: Counter[str] = Counter()
    token_re = re.compile(r"[A-Za-z][A-Za-z0-9-]{2,}")

    def add_text(text: str, weight: int = 1) -> None:
        low = text.lower()
        for phrase in phrase_terms:
            count = low.count(phrase.lower())
            if count:
                weights[phrase] += count * weight * 5
        for token in token_re.findall(text):
            low_token = token.lower().strip("-")
            if len(low_token) < 3 or low_token in stop_words:
                continue
            if re.fullmatch(r"[a-z]*\d+[a-z]*", low_token):
                continue
            weights[low_token] += weight

    for row in rows:
        title_text = norm(row.get("title_clean") or row.get("title"))
        evidence = norm(row.get("primary_result_evidence"))[:500]
        add_text(title_text, 3)
        add_text(evidence, 1)
        product = row_value(row, "canonical_product")
        host = row_value(row, "canonical_host")
        family = row_value(row, "product_family")
        metric = norm(row.get("primary_result_metric"))
        if product and product.lower() != "unknown":
            weights[product] += 8
        if host and host.lower() != "unknown":
            weights[host] += 5
        if family and family.lower() != "unknown":
            weights[FAMILY_LABEL.get(family, family)] += 4
        if metric:
            weights[METRIC_LABEL.get(metric, metric)] += 3

    terms = [(term, value) for term, value in weights.most_common(110) if value >= 8]
    maxv = max((v for _, v in terms), default=1)
    minv = min((v for _, v in terms), default=1)
    cx, cy = width / 2, height / 2 + 12
    boxes: list[tuple[float, float, float, float]] = []
    placed = []

    def font_size(value: int) -> float:
        if maxv == minv:
            return 18
        return 13 + 26 * math.sqrt((value - minv) / (maxv - minv))

    def intersects(box: tuple[float, float, float, float]) -> bool:
        x0, y0, x1, y1 = box
        if x0 < 18 or y0 < 54 or x1 > width - 18 or y1 > height - 18:
            return True
        for bx0, by0, bx1, by1 in boxes:
            if not (x1 < bx0 or x0 > bx1 or y1 < by0 or y0 > by1):
                return True
        return False

    for i, (term, value) in enumerate(terms):
        size = font_size(value)
        label = term.replace("_", " ")
        approx_w = max(24, len(label) * size * 0.54)
        approx_h = size * 1.18
        placed_box = None
        for step in range(2600):
            angle = step * 0.37 + i * 0.19
            radius = 2.4 * math.sqrt(step)
            x = cx + math.cos(angle) * radius * 10.4
            y = cy + math.sin(angle) * radius * 6.3
            box = (x - approx_w / 2 - 4, y - approx_h / 2 - 4, x + approx_w / 2 + 4, y + approx_h / 2 + 4)
            if not intersects(box):
                placed_box = box
                boxes.append(box)
                placed.append((label, value, x, y, size))
                break
        if len(placed) >= 82:
            break

    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，词语大小表示其在标题、证据片段、产物、宿主和指标字段中的加权频次。</desc>",
        f'<text x="{width / 2}" y="28" text-anchor="middle" class="section-label">关键词词云：标题、证据、宿主、产物与指标字段</text>',
    ]
    for idx, (label, value, x, y, size) in enumerate(placed):
        opacity = 0.48 + 0.42 * math.sqrt(value / maxv)
        weight = 500 if idx < 18 else 400
        out.append(f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="middle" font-size="{size:.1f}" font-weight="{weight}" fill="var(--foreground, #111827)" opacity="{opacity:.3f}"><title>{esc(label)}: {value:,}</title>{esc(label)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def bubble_svg(title: str, width=980, left=120, top=70, cell_w=112, cell_h=72) -> str:
    host_keys = ["yeast", "bacteria", "plant", "mammalian", "cell_free", "cyanobacteria", "other", "unknown"]
    family_keys = ["flavonoid", "isoflavonoid", "isoprenoid", "terpenoid", "llps_system", "natural_product", "phenylpropanoid", "stilbene", "other", "unknown"]
    counts = defaultdict(int)
    core_counts = defaultdict(int)
    for row in rows:
        key = (row_value(row, "product_family"), row_value(row, "host_group"))
        counts[key] += 1
        if row.get("database_tier") in {"core", "llps_core", "silver"}:
            core_counts[key] += 1
    maxv = max(counts.values(), default=1)
    height = top + len(family_keys) * cell_h + 50
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，横轴为宿主类型，纵轴为产物家族，气泡大小表示实验记录数，深色内圈表示核心/银层占比。</desc>",
    ]
    for xi, host in enumerate(host_keys):
        out.append(f'<text x="{left + xi * cell_w + cell_w / 2}" y="32" text-anchor="middle" class="axis-label">{esc(HOST_LABEL.get(host, host))}</text>')
    for yi, family in enumerate(family_keys):
        y = top + yi * cell_h
        out.append(f'<text x="{left - 12}" y="{y + cell_h / 2 + 5}" text-anchor="end" class="axis-label">{esc(FAMILY_LABEL.get(family, family))}</text>')
        for xi, host in enumerate(host_keys):
            v = counts.get((family, host), 0)
            if not v:
                continue
            r = 5 + 27 * math.sqrt(v / maxv)
            core_ratio = core_counts[(family, host)] / v
            cx = left + xi * cell_w + cell_w / 2
            cy = y + cell_h / 2
            out.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="var(--viz-series-1, #3b82f6)" opacity="0.22"><title>{esc(FAMILY_LABEL.get(family, family))} · {esc(HOST_LABEL.get(host, host))}: {v} 条，核心/银层 {core_counts[(family, host)]} 条</title></circle>')
            out.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{max(2, r * math.sqrt(core_ratio)):.2f}" fill="var(--viz-series-2, #10b981)" opacity="0.55" />')
            if v >= 80:
                out.append(f'<text x="{cx:.2f}" y="{cy + 4:.2f}" text-anchor="middle" class="cell-label">{v:,}</text>')
    out.append("</svg>")
    return "\n".join(out)


def sankey_svg(title: str, width=1180, height=820) -> str:
    family_order = ["flavonoid", "isoflavonoid", "isoprenoid", "terpenoid", "llps_system", "natural_product", "phenylpropanoid", "stilbene", "other", "unknown"]
    host_order = ["yeast", "bacteria", "plant", "mammalian", "cell_free", "cyanobacteria", "other", "unknown"]
    metric_order = [
        "glabridin_yield", "glabridin_titer", "enzyme_activity", "substrate_conversion",
        "llps_state", "specific_activity", "km", "kinetic_efficiency",
        "relative_activity", "critical_phase_concentration", "kcat",
    ]
    clean_order = ["A_complete", "A_llps", "B_product_condition", "C_llps_candidate", "C_partial_context", "D_result_only"]
    tier_order = ["core", "llps_core", "silver", "review"]
    f_to_h = Counter()
    h_to_m = Counter()
    m_to_c = Counter()
    c_to_t = Counter()
    family_total = Counter()
    host_total = Counter()
    metric_total = Counter()
    clean_total = Counter()
    tier_total = Counter()
    for row in rows:
        f = row_value(row, "product_family")
        h = row_value(row, "host_group")
        m = row.get("primary_result_metric") or "unknown"
        c = row.get("clean_level") or "unknown"
        t = row.get("database_tier") or "review"
        f_to_h[(f, h)] += 1
        h_to_m[(h, m)] += 1
        m_to_c[(m, c)] += 1
        c_to_t[(c, t)] += 1
        family_total[f] += 1
        host_total[h] += 1
        metric_total[m] += 1
        clean_total[c] += 1
        tier_total[t] += 1
    columns = [
        ("产物家族", family_order, family_total, FAMILY_LABEL),
        ("宿主类型", host_order, host_total, HOST_LABEL),
        ("主结果指标", metric_order, metric_total, METRIC_LABEL),
        ("清洗等级", clean_order, clean_total, CLEAN_LABEL),
        ("数据库层级", tier_order, tier_total, TIER_LABEL),
    ]
    x_positions = [110, 355, 600, 845, 1080]
    top = 70
    bottom = height - 78
    gap = 9
    max_col_sum = max(sum(total[k] for k in keys) for _, keys, total, _ in columns)
    max_col_nodes = max(len([k for k in keys if total[k]]) for _, keys, total, _ in columns)
    scale = (bottom - top - gap * max(0, max_col_nodes - 1)) / max_col_sum
    nodes = {}
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，展示记录从产物家族流向宿主类型、主结果指标、清洗等级，再流向数据库层级的路径。</desc>",
    ]
    for col_i, (col_title, keys, totals, labels) in enumerate(columns):
        x = x_positions[col_i]
        y = top
        out.append(f'<text x="{x}" y="34" text-anchor="middle" class="section-label">{esc(col_title)}</text>')
        for key in keys:
            value = totals.get(key, 0)
            if not value:
                continue
            h = max(8, value * scale)
            nodes[(col_i, key)] = {"x": x, "y": y, "h": h, "used_out": 0.0, "used_in": 0.0, "value": value, "label": labels.get(key, key)}
            y += h + gap
    def link(source, target, value, color, layer):
        s = nodes[source]
        t = nodes[target]
        sw = max(1.2, value * scale)
        sy = s["y"] + s["used_out"] + sw / 2
        ty = t["y"] + t["used_in"] + sw / 2
        s["used_out"] += sw
        t["used_in"] += sw
        sx = s["x"] + 10
        tx = t["x"] - 10
        c1 = sx + (tx - sx) * 0.45
        c2 = sx + (tx - sx) * 0.55
        opacity = 0.15 if layer == 0 else 0.19 if layer == 1 else 0.22
        out.append(f'<path d="M {sx:.2f},{sy:.2f} C {c1:.2f},{sy:.2f} {c2:.2f},{ty:.2f} {tx:.2f},{ty:.2f}" fill="none" stroke="{color}" stroke-width="{sw:.2f}" opacity="{opacity}"><title>{esc(s["label"])} → {esc(t["label"])}: {value:,}</title></path>')
    for i, ((f, h), value) in enumerate(sorted(f_to_h.items(), key=lambda kv: -kv[1])):
        if (0, f) in nodes and (1, h) in nodes:
            link((0, f), (1, h), value, PALETTE[i % 4], 0)
    for i, ((h, m), value) in enumerate(sorted(h_to_m.items(), key=lambda kv: -kv[1])):
        if (1, h) in nodes and (2, m) in nodes:
            link((1, h), (2, m), value, PALETTE[(i + 1) % 6], 1)
    for i, ((m, c), value) in enumerate(sorted(m_to_c.items(), key=lambda kv: -kv[1])):
        if (2, m) in nodes and (3, c) in nodes:
            link((2, m), (3, c), value, PALETTE[(i + 2) % 6], 2)
    for i, ((c, t), value) in enumerate(sorted(c_to_t.items(), key=lambda kv: -kv[1])):
        if (3, c) in nodes and (4, t) in nodes:
            link((3, c), (4, t), value, PALETTE[(i + 3) % 6], 3)
    for (col_i, key), node in nodes.items():
        x = node["x"]
        y = node["y"]
        h = node["h"]
        out.append(f'<rect x="{x - 10}" y="{y}" width="20" height="{h:.2f}" rx="4" fill="var(--foreground, #111827)" opacity="0.22" />')
        anchor = "end" if col_i == 0 else "start"
        tx = x - 16 if col_i == 0 else x + 16
        label = f'{node["label"]} {node["value"]:,}'
        if len(label) > 24:
            label = label[:22] + "..."
        out.append(f'<text x="{tx}" y="{y + min(h / 2 + 5, h - 2):.2f}" text-anchor="{anchor}" class="axis-label">{esc(label)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def upset_svg(title: str, width=1040, height=610) -> str:
    set_defs = [
        ("Yeast", "酵母宿主", lambda r: (row_value(r, "host_group") == "yeast")),
        ("Natural", "天然产物", lambda r: (row_value(r, "product_family") in {"flavonoid", "isoflavonoid", "isoprenoid", "terpenoid", "natural_product", "stilbene", "phenylpropanoid", "prenylflavonoid"})),
        ("LLPS", "LLPS相关", lambda r: (row_value(r, "product_family") == "llps_system" or r.get("primary_result_metric") in {"llps_state", "critical_phase_concentration"})),
        ("Core", "核心/银层", lambda r: (r.get("database_tier") in {"core", "llps_core", "silver"})),
        ("Condition", "有实验条件", lambda r: any(norm(r.get(f"{m}_value")) for m in ["reaction_time", "reaction_temperature", "reaction_ph", "substrate_concentration", "cell_density_od600"])),
    ]
    inter = Counter()
    set_counts = Counter()
    for row in rows:
        mask = []
        for key, _, fn in set_defs:
            ok = bool(fn(row))
            mask.append(ok)
            if ok:
                set_counts[key] += 1
        if any(mask):
            inter[tuple(mask)] += 1
    top = inter.most_common(14)
    left = 150
    bar_top = 44
    bar_h_max = 190
    matrix_top = 285
    col_w = 58
    maxv = max((v for _, v in top), default=1)
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，展示酵母、天然产物、LLPS、核心/银层、有实验条件五个集合的主要交集。</desc>",
    ]
    for i, (mask, value) in enumerate(top):
        x = left + i * col_w
        h = bar_h_max * value / maxv
        out.append(f'<rect x="{x + 13}" y="{bar_top + bar_h_max - h:.2f}" width="32" height="{h:.2f}" rx="3" fill="var(--viz-series-1, #3b82f6)" opacity="0.75"><title>交集记录数: {value:,}</title></rect>')
        out.append(f'<text x="{x + 29}" y="{bar_top + bar_h_max - h - 6:.2f}" text-anchor="middle" class="value-label">{value:,}</text>')
        active_ys = []
        for j, active in enumerate(mask):
            y = matrix_top + j * 44
            out.append(f'<circle cx="{x + 29}" cy="{y}" r="8" fill="var(--foreground, #111827)" opacity="{0.78 if active else 0.12}" />')
            if active:
                active_ys.append(y)
        if len(active_ys) >= 2:
            out.append(f'<line x1="{x + 29}" y1="{min(active_ys)}" x2="{x + 29}" y2="{max(active_ys)}" stroke="var(--foreground, #111827)" stroke-width="2" opacity="0.45" />')
    for j, (key, label, _) in enumerate(set_defs):
        y = matrix_top + j * 44
        out.append(f'<text x="{left - 18}" y="{y + 5}" text-anchor="end" class="axis-label">{esc(label)} ({set_counts[key]:,})</text>')
        out.append(f'<line x1="{left - 8}" y1="{y}" x2="{left + len(top) * col_w}" y2="{y}" class="axis-line" opacity="0.35" />')
    out.append(f'<text x="{left}" y="22" class="section-label">Top 交集记录数</text>')
    out.append("</svg>")
    return "\n".join(out)


def evidence_chain_svg(title: str, width=1120, row_h=78) -> str:
    doi_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        doi = norm(row.get("doi")).lower()
        if doi:
            doi_groups[doi].append(row)
    top = sorted(doi_groups.items(), key=lambda kv: -len(kv[1]))[:8]
    height = 70 + len(top) * row_h + 35
    x1, x2, x3, x4 = 70, 390, 700, 970
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，按记录数最多的文献展示 DOI 到证据片段、主结果指标和数据库层级的链路。</desc>",
        '<defs><marker id="chain-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="var(--border, #d8deea)" /></marker></defs>',
        f'<text x="{x1}" y="28" class="section-label">文献 DOI / 标题</text>',
        f'<text x="{x2}" y="28" class="section-label">证据片段来源</text>',
        f'<text x="{x3}" y="28" class="section-label">主结果指标</text>',
        f'<text x="{x4}" y="28" class="section-label">实验记录层级</text>',
    ]
    for i, (doi, group) in enumerate(top):
        y = 64 + i * row_h
        title_clean = norm(group[0].get("title_clean") or group[0].get("title"))
        title_short = title_clean[:44] + ("..." if len(title_clean) > 44 else "")
        source_modes = Counter(norm(g.get("source_mode")) or "unknown" for g in group)
        metrics = Counter(g.get("primary_result_metric") or "unknown" for g in group)
        tiers = Counter(g.get("database_tier") or "unknown" for g in group)
        ev_count = sum(int(g.get("source_row_count") or 1) if str(g.get("source_row_count") or "1").isdigit() else 1 for g in group)
        metric_text = "；".join(f"{METRIC_LABEL.get(k, k)} {v}" for k, v in metrics.most_common(3))
        tier_text = "；".join(f"{TIER_LABEL.get(k, k)} {v}" for k, v in tiers.most_common())
        source_text = "；".join(f"{k.replace('_', ' ')} {v}" for k, v in source_modes.most_common(2))
        out.append(f'<rect x="{x1 - 18}" y="{y - 24}" width="260" height="50" rx="6" class="node-fill" />')
        out.append(f'<text x="{x1 - 6}" y="{y - 5}" class="chain-label">{esc(doi)}</text>')
        out.append(f'<text x="{x1 - 6}" y="{y + 14}" class="axis-label">{esc(title_short)}</text>')
        out.append(f'<rect x="{x2 - 18}" y="{y - 24}" width="230" height="50" rx="6" class="node-fill" />')
        out.append(f'<text x="{x2 - 6}" y="{y - 3}" class="chain-label">{esc(source_text)}</text>')
        out.append(f'<text x="{x2 - 6}" y="{y + 16}" class="axis-label">聚合证据约 {ev_count:,} 条</text>')
        out.append(f'<rect x="{x3 - 18}" y="{y - 24}" width="210" height="50" rx="6" class="node-fill" />')
        out.append(f'<text x="{x3 - 6}" y="{y - 3}" class="chain-label">{esc(metric_text[:34])}</text>')
        out.append(f'<text x="{x3 - 6}" y="{y + 16}" class="axis-label">实验记录 {len(group):,} 条</text>')
        out.append(f'<rect x="{x4 - 18}" y="{y - 24}" width="130" height="50" rx="6" class="node-fill" />')
        out.append(f'<text x="{x4 - 6}" y="{y + 3}" class="chain-label">{esc(tier_text[:18])}</text>')
        for a, b in [(x1 + 248, x2 - 24), (x2 + 218, x3 - 24), (x3 + 198, x4 - 24)]:
            out.append(f'<path d="M {a},{y} C {a + 38},{y} {b - 38},{y} {b},{y}" class="chain-line" />')
    out.append("</svg>")
    return "\n".join(out)


def chord_diagram_svg(title: str, width=1040, height=720) -> str:
    families = [k for k, _ in counter("product_family").most_common(8)]
    hosts = [k for k, _ in counter("host_group").most_common(7)]
    links = Counter()
    for row in rows:
        f = row_value(row, "product_family")
        h = row_value(row, "host_group")
        if f in families and h in hosts:
            links[(f, h)] += 1
    top_links = links.most_common(42)
    max_link = max((v for _, v in top_links), default=1)
    cx, cy = width / 2, height / 2 + 12
    rx, ry = 335, 248

    def point_left(i: int, n: int) -> tuple[float, float]:
        angle = math.radians(128 + i * (104 / max(1, n - 1)))
        return cx + math.cos(angle) * rx, cy + math.sin(angle) * ry

    def point_right(i: int, n: int) -> tuple[float, float]:
        angle = math.radians(-52 + i * (104 / max(1, n - 1)))
        return cx + math.cos(angle) * rx, cy + math.sin(angle) * ry

    fam_pos = {f: point_left(i, len(families)) for i, f in enumerate(families)}
    host_pos = {h: point_right(i, len(hosts)) for i, h in enumerate(hosts)}
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，用弦连接产物家族和宿主类型，弦宽表示共现记录数。</desc>",
        f'<text x="{cx}" y="34" text-anchor="middle" class="section-label">产物家族 ↔ 宿主类型共现弦图</text>',
    ]
    for i, ((f, h), v) in enumerate(top_links):
        x1, y1 = fam_pos[f]
        x2, y2 = host_pos[h]
        sw = 1.2 + 17 * math.sqrt(v / max_link)
        color = PALETTE[i % len(PALETTE)]
        out.append(f'<path d="M {x1:.2f},{y1:.2f} C {cx - 130:.2f},{cy:.2f} {cx + 130:.2f},{cy:.2f} {x2:.2f},{y2:.2f}" fill="none" stroke="{color}" stroke-width="{sw:.2f}" opacity="0.22"><title>{esc(FAMILY_LABEL.get(f, f))} - {esc(HOST_LABEL.get(h, h))}: {v:,} 条</title></path>')
    for f, (x, y) in fam_pos.items():
        v = sum(links[(f, h)] for h in hosts)
        out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{7 + 22 * math.sqrt(v / max(1, N)):.2f}" fill="var(--viz-series-1, #3b82f6)" opacity="0.55" />')
        out.append(f'<text x="{x - 16:.2f}" y="{y + 4:.2f}" text-anchor="end" class="axis-label">{esc(FAMILY_LABEL.get(f, f))} {v:,}</text>')
    for h, (x, y) in host_pos.items():
        v = sum(links[(f, h)] for f in families)
        out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{7 + 22 * math.sqrt(v / max(1, N)):.2f}" fill="var(--viz-series-2, #10b981)" opacity="0.55" />')
        out.append(f'<text x="{x + 16:.2f}" y="{y + 4:.2f}" text-anchor="start" class="axis-label">{esc(HOST_LABEL.get(h, h))} {v:,}</text>')
    out.append("</svg>")
    return "\n".join(out)


def network_chart_svg(title: str, width=1120, height=760) -> str:
    fams = [k for k, _ in counter("product_family").most_common(7)]
    hosts = [k for k, _ in counter("host_group").most_common(7)]
    metrics = [k for k, _ in counter("primary_result_metric").most_common(8)]
    nodes: dict[str, dict[str, object]] = {}
    for i, f in enumerate(fams):
        nodes[f"F:{f}"] = {"x": 170, "y": 92 + i * 82, "label": FAMILY_LABEL.get(f, f), "type": "family", "size": counter("product_family")[f]}
    for i, h in enumerate(hosts):
        nodes[f"H:{h}"] = {"x": 520, "y": 92 + i * 82, "label": HOST_LABEL.get(h, h), "type": "host", "size": counter("host_group")[h]}
    for i, m in enumerate(metrics):
        nodes[f"M:{m}"] = {"x": 880, "y": 70 + i * 72, "label": METRIC_LABEL.get(m, m), "type": "metric", "size": counter("primary_result_metric")[m]}
    edges = Counter()
    for row in rows:
        f = row_value(row, "product_family")
        h = row_value(row, "host_group")
        m = row.get("primary_result_metric") or "unknown"
        if f in fams and h in hosts:
            edges[(f"F:{f}", f"H:{h}")] += 1
        if h in hosts and m in metrics:
            edges[(f"H:{h}", f"M:{m}")] += 1
    top_edges = edges.most_common(48)
    max_edge = max((v for _, v in top_edges), default=1)
    max_node = max((int(n["size"]) for n in nodes.values()), default=1)
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，展示产物家族、宿主类型和主结果指标构成的加权网络。</desc>",
        '<text x="170" y="34" text-anchor="middle" class="section-label">产物家族</text>',
        '<text x="520" y="34" text-anchor="middle" class="section-label">宿主类型</text>',
        '<text x="880" y="34" text-anchor="middle" class="section-label">结果指标</text>',
    ]
    for (a, b), v in top_edges:
        n1, n2 = nodes[a], nodes[b]
        sw = 1 + 9 * math.sqrt(v / max_edge)
        out.append(f'<path d="M {n1["x"]},{n1["y"]} C {(n1["x"] + n2["x"]) / 2},{n1["y"]} {(n1["x"] + n2["x"]) / 2},{n2["y"]} {n2["x"]},{n2["y"]}" fill="none" stroke="var(--border, #d8deea)" stroke-width="{sw:.2f}" opacity="0.46"><title>{esc(n1["label"])} → {esc(n2["label"])}: {v:,} 条</title></path>')
    color_by_type = {"family": PALETTE[0], "host": PALETTE[1], "metric": PALETTE[2]}
    for node in nodes.values():
        r = 8 + 22 * math.sqrt(int(node["size"]) / max_node)
        out.append(f'<circle cx="{node["x"]}" cy="{node["y"]}" r="{r:.2f}" fill="{color_by_type[str(node["type"])]}" opacity="0.62"><title>{esc(node["label"])}: {int(node["size"]):,} 条</title></circle>')
        out.append(f'<text x="{float(node["x"]) + r + 8:.2f}" y="{float(node["y"]) + 4:.2f}" class="axis-label">{esc(node["label"])} {int(node["size"]):,}</text>')
    out.append("</svg>")
    return "\n".join(out)


def polar(cx: float, cy: float, r: float, angle: float) -> tuple[float, float]:
    return cx + r * math.cos(angle), cy + r * math.sin(angle)


def annular_sector_path(cx: float, cy: float, r0: float, r1: float, a0: float, a1: float) -> str:
    large = 1 if a1 - a0 > math.pi else 0
    x1, y1 = polar(cx, cy, r1, a0)
    x2, y2 = polar(cx, cy, r1, a1)
    x3, y3 = polar(cx, cy, r0, a1)
    x4, y4 = polar(cx, cy, r0, a0)
    return f"M {x1:.2f},{y1:.2f} A {r1:.2f},{r1:.2f} 0 {large} 1 {x2:.2f},{y2:.2f} L {x3:.2f},{y3:.2f} A {r0:.2f},{r0:.2f} 0 {large} 0 {x4:.2f},{y4:.2f} Z"


def sunburst_chart_svg(title: str, width=980, height=780) -> str:
    tier_counts = Counter()
    clean_counts = Counter()
    metric_counts = Counter()
    for row in rows:
        t = row.get("database_tier") or "review"
        c = row.get("clean_level") or "unknown"
        m = row.get("primary_result_metric") or "unknown"
        tier_counts[t] += 1
        clean_counts[(t, c)] += 1
        metric_counts[(t, c, m)] += 1
    cx, cy = width / 2, height / 2 + 20
    start = -math.pi / 2
    total = sum(tier_counts.values()) or 1
    tier_angles: dict[str, tuple[float, float]] = {}
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，按数据库层级、清洗等级和主结果指标展示层级组成。</desc>",
        f'<circle cx="{cx}" cy="{cy}" r="58" fill="var(--card, #fff)" stroke="var(--border, #d8deea)" />',
        f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" class="section-label">{N:,}</text>',
        f'<text x="{cx}" y="{cy + 18}" text-anchor="middle" class="axis-label">records</text>',
    ]
    for i, (tier, tv) in enumerate(tier_counts.most_common()):
        span = 2 * math.pi * tv / total
        a0, a1 = start, start + span
        tier_angles[tier] = (a0, a1)
        color = PALETTE[i % len(PALETTE)]
        out.append(f'<path d="{annular_sector_path(cx, cy, 70, 145, a0, a1)}" fill="{color}" opacity="0.56"><title>{esc(TIER_LABEL.get(tier, tier))}: {tv:,}</title></path>')
        mid = (a0 + a1) / 2
        lx, ly = polar(cx, cy, 168, mid)
        if span > 0.2:
            out.append(f'<text x="{lx:.2f}" y="{ly:.2f}" text-anchor="middle" class="axis-label">{esc(TIER_LABEL.get(tier, tier))}</text>')
        clean_items_local = [(c, clean_counts[(tier, c)]) for c in CLEAN_LABEL if clean_counts[(tier, c)]]
        clean_start = a0
        for j, (clean, cv) in enumerate(clean_items_local):
            cspan = span * cv / tv
            ca0, ca1 = clean_start, clean_start + cspan
            out.append(f'<path d="{annular_sector_path(cx, cy, 155, 230, ca0, ca1)}" fill="{PALETTE[(i + j + 1) % len(PALETTE)]}" opacity="0.38"><title>{esc(TIER_LABEL.get(tier, tier))} / {esc(CLEAN_LABEL.get(clean, clean))}: {cv:,}</title></path>')
            metric_counter = Counter({m: v for (tt, cc, m), v in metric_counts.items() if tt == tier and cc == clean})
            top_metrics_local = metric_counter.most_common(8)
            metric_total = sum(v for _, v in top_metrics_local) or 1
            metric_start = ca0
            for k, (metric, mv) in enumerate(sorted(top_metrics_local, key=lambda kv: -kv[1])[:5]):
                mspan = cspan * mv / metric_total
                ma0, ma1 = metric_start, metric_start + mspan
                out.append(f'<path d="{annular_sector_path(cx, cy, 240, 305, ma0, ma1)}" fill="{PALETTE[(k + 2) % len(PALETTE)]}" opacity="0.28"><title>{esc(TIER_LABEL.get(tier, tier))} / {esc(CLEAN_LABEL.get(clean, clean))} / {esc(METRIC_LABEL.get(metric, metric))}: {mv:,}</title></path>')
                metric_start += mspan
            clean_start += cspan
        start = a1
    out.append("</svg>")
    return "\n".join(out)


def treemap_svg(title: str, width=1120, height=700) -> str:
    systems = Counter()
    for row in rows:
        f = row_value(row, "product_family")
        h = row_value(row, "host_group")
        m = row.get("primary_result_metric") or "unknown"
        systems[(f, h, m)] += 1
    items = systems.most_common(28)
    total = sum(v for _, v in items) or 1
    x, y, w, h = 30, 66, width - 60, height - 102
    out = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(title)}，按产物家族、宿主类型和结果指标组合展示主要数据块占比。</desc>",
        '<text x="30" y="34" class="section-label">Top 产物家族 / 宿主 / 指标数据块</text>',
    ]
    horizontal = True
    rem_x, rem_y, rem_w, rem_h = x, y, w, h
    remaining = total
    for i, ((fam, host, metric), value) in enumerate(items):
        if i == len(items) - 1:
            rw, rh = rem_w, rem_h
        elif horizontal:
            rw = rem_w * value / remaining
            rh = rem_h
        else:
            rw = rem_w
            rh = rem_h * value / remaining
        color = PALETTE[i % len(PALETTE)]
        out.append(f'<rect x="{rem_x:.2f}" y="{rem_y:.2f}" width="{max(1, rw):.2f}" height="{max(1, rh):.2f}" fill="{color}" opacity="{0.18 + 0.28 * math.sqrt(value / items[0][1]):.3f}" stroke="var(--background, #fff)" stroke-width="2"><title>{esc(FAMILY_LABEL.get(fam, fam))} / {esc(HOST_LABEL.get(host, host))} / {esc(METRIC_LABEL.get(metric, metric))}: {value:,}</title></rect>')
        if rw > 120 and rh > 58:
            label = f"{FAMILY_LABEL.get(fam, fam)} / {HOST_LABEL.get(host, host)}"
            out.append(f'<text x="{rem_x + 8:.2f}" y="{rem_y + 22:.2f}" class="chain-label">{esc(label[:30])}</text>')
            out.append(f'<text x="{rem_x + 8:.2f}" y="{rem_y + 43:.2f}" class="axis-label">{esc(METRIC_LABEL.get(metric, metric))} · {value:,}</text>')
        if horizontal:
            rem_x += rw
            rem_w -= rw
        else:
            rem_y += rh
            rem_h -= rh
        remaining -= value
        horizontal = not horizontal
        if rem_w < 24 or rem_h < 24 or remaining <= 0:
            break
    out.append("</svg>")
    return "\n".join(out)


def two_panel(left_html: str, right_html: str) -> str:
    return f'<div class="two-panel">{left_html}{right_html}</div>'


figures: list[str] = []


def figure(markup: str, caption: str, cls: str = "") -> None:
    caption = re.sub(r"^图\d+", f"图{len(figures) + 1}", caption)
    figures.append(f'<figure class="viz-figure {cls}">\n{markup}\n<figcaption>{caption}</figcaption>\n</figure>')


tier_items = ordered_items(counter("database_tier"), TIER_LABEL, ["core", "llps_core", "silver", "review"])
clean_items = ordered_items(counter("clean_level"), CLEAN_LABEL, ["A_complete", "A_llps", "B_product_condition", "C_llps_candidate", "C_partial_context", "D_result_only"])
metric_items = ordered_items(counter("primary_result_metric"), METRIC_LABEL)
family_items = ordered_items(counter("product_family"), FAMILY_LABEL, ["flavonoid", "isoflavonoid", "isoprenoid", "terpenoid", "llps_system", "natural_product", "stilbene", "other", "unknown"])
host_items = ordered_items(counter("host_group"), HOST_LABEL, ["yeast", "bacteria", "plant", "other", "unknown"])
product_items = ordered_items(counter("canonical_product"), limit=15)
host_top_items = ordered_items(counter("canonical_host"), limit=12)

top_metrics = [k for k, _ in counter("primary_result_metric").most_common(10)]
series = ["core", "llps_core", "silver", "review"]
groups = {m: Counter() for m in top_metrics}
for row in rows:
    metric = row.get("primary_result_metric")
    if metric in groups:
        groups[metric][row.get("database_tier") or "review"] += 1

x_host = ["yeast", "bacteria", "plant", "other", "unknown"]
y_family = ["flavonoid", "isoflavonoid", "isoprenoid", "terpenoid", "llps_system", "natural_product", "stilbene", "other", "unknown"]
mat_hf = defaultdict(int)
for row in rows:
    mat_hf[(row_value(row, "product_family"), row_value(row, "host_group"))] += 1

stages = [
    ("高召回证据", 145892, "文本/表格数值片段"),
    ("清洗后证据", 143208, "去掉短证据/重复"),
    ("附件聚合记录", 15943, "一条实验结果一行"),
    ("三方合并记录", 20587, "正文+原附件+深挖附件"),
    ("最终优化库", 11181, "严格去重分层"),
    ("核心/银层", 3293, "优先分析集"),
]

summary_cards = f"""
<div class="summary-grid" role="list" aria-label="数据库概览">
  <div class="stat" role="listitem"><span>最终实验记录</span><strong>{N:,}</strong><em>严格去重后的主库</em></div>
  <div class="stat" role="listitem"><span>覆盖 DOI</span><strong>{unique_dois:,}</strong><em>可追溯文献来源</em></div>
  <div class="stat" role="listitem"><span>核心/银层</span><strong>{sum(1 for r in rows if r.get("database_tier") in {"core", "llps_core", "silver"}):,}</strong><em>优先用于统计建模</em></div>
  <div class="stat" role="listitem"><span>待复核层</span><strong>{sum(1 for r in rows if r.get("database_tier") == "review"):,}</strong><em>适合二次质控扩展</em></div>
</div>
"""

figure(summary_cards, "图1 数据库整体规模。严格扩量版最终包含 11,181 条实验记录，覆盖 1,397 个 DOI；其中核心/银层 3,293 条更适合直接进入统计分析，review 层保留了大量可追溯但上下文尚不完整的候选。", "summary-figure")
figure(funnel_svg(stages, "实验记录构建漏斗"), "图2 从高召回证据到最终数据库的构建漏斗。145,892 条原始数值证据经过清洗、结构化、聚合和去重后形成 11,181 条实验记录，说明当前扩量主要来自附件表格和补充材料的深挖。")
figure(sankey_svg("产物家族-宿主类型-指标-清洗等级-数据库层级桑基图"), "图3 桑基图现在扩展为五列：产物家族、宿主类型、主结果指标、清洗等级和数据库层级。它能同时展示“研究对象是什么”“在哪个底盘中”“抽到了什么结果”“证据质量如何”以及“最终进入哪个数据库层级”，比原来的三列版本更适合解释完整数据流。")
figure(chord_diagram_svg("产物家族-宿主类型 Chord Diagram"), "图4 Chord diagram 展示产物家族与宿主类型之间的共现关系，弦越粗表示该组合的实验记录越多。它比矩阵图更适合强调“哪些产物类别主要在哪些底盘中被研究”，可用于快速识别酵母-天然产物、细菌-酶体系、植物-天然产物等主线。")
figure(network_chart_svg("产物-宿主-指标 Network Chart"), "图5 Network chart 把产物家族、宿主类型和主结果指标组织成加权网络。节点大小表示记录量，连线粗细表示共现强度，可用于展示数据库不是孤立字段表，而是由产物、底盘和实验结果共同构成的关系网络。")
figure(sunburst_chart_svg("数据库层级 Sunburst Chart"), "图6 Sunburst chart 按数据库层级、清洗等级和主结果指标构建三层环形层级图。它能直观看到 core/silver/review 内部由哪些证据等级和指标组成，适合解释数据质量分层和后续筛选路径。")
figure(treemap_svg("主要数据块 Tree Map"), "图7 Tree map 按产物家族、宿主类型和结果指标组合展示主要数据块占比。矩形面积越大表示该组合记录越多，适合在 PPT 中概括“数据库最大的几类可用信息块”。")
figure(bubble_svg("宿主类型-产物家族气泡图"), "图4 气泡图以宿主类型为横轴、产物家族为纵轴，气泡大小表示记录数，内圈表示核心/银层记录数量。酵母-黄酮、酵母-类异戊二烯等区域是项目最值得优先利用的数据块。")
figure(upset_svg("项目相关集合 UpSet 图"), "图5 UpSet 图展示酵母宿主、天然产物、LLPS 相关、核心/银层、有实验条件五类集合的主要交集。它比普通韦恩图更适合多集合场景，可用于判断哪些记录同时满足“项目相关”和“质量可用”。")
figure(evidence_chain_svg("文献到实验记录证据链图"), "图6 文献到实验记录证据链图展示高产出 DOI 如何经过证据片段、主结果指标，最终落入不同数据库层级。每一行都是可追溯链路，有助于解释数据库不是简单数值堆叠，而是从文献证据逐级结构化而来。")
figure(word_cloud_svg("实验记录关键词词云图"), "图7 词云图汇总标题、证据片段、宿主、产物和主结果指标中的高频关键词。字号越大表示加权出现频次越高，可快速展示数据库主题集中在代谢工程、天然产物、酵母底盘、酶活/滴度/产率以及 LLPS 相关表征上。")
figure(hbar_svg(tier_items, "数据库层级分布"), "图8 数据库层级分布。review 层最多，说明当前数据库为了保证召回保留了较多“有结果但上下文弱”的记录；core、llps_core 与 silver 是更稳妥的分析子集。")
figure(hbar_svg(clean_items, "清洗等级分布"), "图9 清洗等级分布。A/B 级记录包含较完整的产物、宿主或实验条件；C/D 级记录主要用于扩量和后续 LLM 二次补全，不宜在未复核时直接作为强结论。")
figure(hbar_svg(metric_items, "主结果指标构成"), "图10 主结果指标构成。产率/得率和产物滴度占主要部分，其次是酶活、底物转化率和 LLPS 状态；这反映数据库更偏向代谢产物性能与酶催化结果。")
figure(stacked_bar_svg(groups, series, [TIER_LABEL[s] for s in series], "主结果指标与数据库层级"), "图11 不同结果指标在数据库层级中的分布。产率和滴度贡献了最多记录，但其中相当一部分处于 review 层；用于建模时可优先选择 core/silver，再按需求纳入 review。")
figure(two_panel(hbar_svg(host_items, "宿主类型分布", width=820, left=130, right=90), hbar_svg(family_items, "产物家族分布", width=820, left=150, right=90)), "图12 宿主类型与产物家族分布。酵母记录量明显高于细菌和植物，契合 iGEM 项目的酵母底盘需求；但仍有大量 unknown，提示后续可针对宿主和产物名称做 LLM 补全。")
figure(heatmap_svg(x_host, y_family, mat_hf, HOST_LABEL, FAMILY_LABEL, "宿主类型-产物家族矩阵"), "图13 宿主类型与产物家族交叉矩阵。酵母-黄酮/类异戊二烯等组合是项目最相关区域；unknown 单元格较大，主要来自只抽到结果数值、未抽到明确宿主或产物的记录。")
figure(two_panel(hbar_svg(product_items, "Top 产物名称", width=820, left=170, right=80), hbar_svg(host_top_items, "Top 宿主名称", width=820, left=220, right=80)), "图14 高频产物与宿主名称。naringenin、flavonoid、anthocyanin、quercetin 等天然产物条目较多；宿主侧以 yeast、Saccharomyces cerevisiae 与 Escherichia coli 为主，可用于确定后续筛选关键词和实验设计参考对象。")
figure(log_box_svg(["glabridin_titer", "glabridin_yield", "enzyme_activity", "substrate_conversion", "km", "llps_state"], "关键数值指标分布"), "图15 关键数值指标的正值分布。横轴使用 log10 尺度以容纳不同单位和量级；极端值和负值没有进入箱线图，建议在建模前继续按单位、证据和上下文做二次质控。")
figure(quality_heatmap_svg("完整度与项目相关性分布"), "图16 完整度与项目相关性二维分布。右上角代表既完整又高度相关的记录，是优先进入模型和 PPT 展示的部分；左下角和中低完整度区域更适合作为 LLM 补全和人工复核队列。")
figure(method_transfer_table(), "图17 参考文献方法迁移矩阵。该表把 DES 论文中的图形和分析方法逐项映射到本项目数据库：从流程图、Prompt 结构、质量验证、统计组图、累计频率曲线到 Agent 查询链，说明哪些方法已直接复刻、哪些因当前字段限制做了等价替代。")
figure(pipeline_workflow_svg("LLM 驱动实验数据抽取流程图"), "图18 LLM 驱动实验数据抽取流程图。该图复刻参考文献 Fig. 1 的思路，把当前项目从候选文献库、全文与附件、证据抽取、结构化清洗、实验记录库到可查询知识库的全流程串联起来。")
figure(prompt_structure_svg("模块化 Prompt 与 Schema 结构图"), "图19 模块化 Prompt 与 Schema 结构图。该图对应参考文献 Fig. 2 的 Prompt 组织方式，强调当前项目由任务描述、抽取字段、动态 ICL、领域规则和 JSON 输出共同约束 LLM 抽取行为。")
figure(graph_rag_schema_svg("实验数据库 Graph-RAG 结构示意图"), "图20 实验数据库 Graph-RAG 结构示意图。该图对应参考文献 Fig. 3 的 Agent/Graph RAG 框架，展示本数据库可被组织为 Literature、Evidence、ExperimentRecord、Host、Product、Metric 和 QualityTier 等节点。")
figure(fig4_database_source_overview_svg("Fig.4 风格：数据库来源与保留概览"), "图21 Fig.4 风格数据库来源图。该图学习 DES 论文 Fig. 4a 的概览方式，把本项目的数据来源、证据保留链路、来源模式、证据类型和抽取质量标签放在同一张图里，突出数据库从 DOI、附件、证据到最终实验记录的形成过程。")
figure(fig4_research_comparison_svg("Fig.4 风格：数据库规模与研究比较"), "图22 Fig.4 风格 research comparison。该图学习 DES 论文 Fig. 4b 的数据库比较方式，把 DES 参考库、本项目严格库、宽召回库和扩量前版本放在同一尺度下比较，说明本项目虽然文献规模较小，但已经形成了可溯源的万级实验记录库。")
figure(fig6_llps_enzyme_analysis_svg("Fig.6 风格：LLPS 与酶催化体系统计分析"), "图23 Fig.6 风格 LLPS/酶体系分析。该图学习 DES 论文 Fig. 6 的多面板统计方式，围绕 LLPS 与酶催化体系展示记录量、结果指标、质量层级、宿主类型、产物/体系类型、酶名称、条件覆盖和关键数值中位数，适合直接用于说明本数据库对 iGEM 项目设计的支撑。")
figure(availability_panel_svg("数据库字段可用性分析"), "图24 数据库字段可用性分析。该图对应参考文献中数据库概览与数据可用性统计的做法，展示 DOI、标题、证据文本、产物、宿主、实验条件、单位和归一化数值等关键字段的覆盖情况。")
figure(quality_proxy_svg("抽取质量代理分析"), "图25 抽取质量代理分析。参考文献使用自动抽取值与人工/已有数据库的误差分布验证质量；当前库尚无人工金标准，因此用完整度、项目相关性和抽取质量标签作为质量代理，辅助筛选可直接分析和需要复核的记录。")
figure(top_system_cumulative_svg("Top 产物-宿主系统累计贡献曲线"), "图26 Top 产物-宿主系统累计贡献曲线。参考文献 Fig. 7 展示高频 DES 配方随年份的累计研究频次；当前数据库缺少 publication_year 字段，因此这里按 DOI 对记录贡献排序，展示高频产物-宿主系统的累计贡献，并提示后续应补全年份字段以生成真正的时间演化图。")
figure(agent_query_example_svg("实验数据库 Agent 查询链示意图"), "图27 实验数据库 Agent 查询链示意图。该图对应参考文献 Fig. 8 的多轮查询案例，展示用户问题如何被解析为宿主、产物家族和结果指标约束，再通过图结构返回记录、证据和 DOI 来源。")

CSS = """
<style>
#experimental-database-visuals {
  --bg-local: var(--background, #f7f8fb);
  --fg-local: var(--foreground, #18202f);
  --muted-local: var(--muted-foreground, #5f6b7a);
  --card-local: var(--card, #ffffff);
  --border-local: var(--border, #d8deea);
  color: var(--fg-local);
  background: var(--bg-local);
  padding: 24px;
  font-family: "Microsoft YaHei", "Noto Sans SC", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
#experimental-database-visuals * { box-sizing: border-box; }
#experimental-database-visuals .report-header { max-width: 1240px; margin: 0 auto 22px; }
#experimental-database-visuals h1 { margin: 0 0 8px; font-size: clamp(24px, 3vw, 36px); font-weight: 600; letter-spacing: 0; }
#experimental-database-visuals .subtitle { margin: 0; color: var(--muted-local); max-width: 960px; line-height: 1.7; }
#experimental-database-visuals .source-note { margin-top: 10px; color: var(--muted-local); font-size: 13px; }
#experimental-database-visuals .viz-figure { max-width: 1240px; margin: 22px auto 34px; padding: 0; }
#experimental-database-visuals .chart-svg { width: 100%; height: auto; display: block; overflow: visible; }
#experimental-database-visuals figcaption { margin-top: 10px; color: var(--muted-local); line-height: 1.75; font-size: 14px; border-left: 3px solid var(--border-local); padding-left: 12px; }
#experimental-database-visuals .axis-label { fill: var(--muted-local); font-size: 14px; }
#experimental-database-visuals .value-label { fill: var(--fg-local); font-size: 14px; }
#experimental-database-visuals .cell-label { fill: var(--fg-local); font-size: 13px; font-weight: 500; }
#experimental-database-visuals .chain-label { fill: var(--fg-local); font-size: 13px; font-weight: 500; }
#experimental-database-visuals .section-label { fill: var(--fg-local); font-size: 15px; font-weight: 500; }
#experimental-database-visuals .axis-line { stroke: var(--border-local); stroke-width: 1; }
#experimental-database-visuals .chain-line { fill: none; stroke: var(--border-local); stroke-width: 2; marker-end: url(#chain-arrow); }
#experimental-database-visuals .node-fill { fill: var(--card-local); stroke: var(--border-local); }
#experimental-database-visuals .soft-node { fill: var(--muted, #eef2f7); stroke: var(--border-local); opacity: 0.9; }
#experimental-database-visuals .summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
#experimental-database-visuals .stat { background: var(--card-local); border: 1px solid var(--border-local); border-radius: 8px; padding: 16px; min-height: 116px; }
#experimental-database-visuals .stat span { display: block; color: var(--muted-local); font-size: 14px; margin-bottom: 8px; }
#experimental-database-visuals .stat strong { display: block; font-size: clamp(26px, 5vw, 42px); line-height: 1.1; font-weight: 600; letter-spacing: 0; }
#experimental-database-visuals .stat em { display: block; color: var(--muted-local); font-style: normal; font-size: 13px; margin-top: 8px; }
#experimental-database-visuals .two-panel { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 22px; align-items: start; }
#experimental-database-visuals code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
#experimental-database-visuals .table-responsive { overflow-x: auto; }
#experimental-database-visuals .method-table { width: 100%; border-collapse: collapse; background: var(--card-local); border: 1px solid var(--border-local); border-radius: 8px; overflow: hidden; }
#experimental-database-visuals .method-table th, #experimental-database-visuals .method-table td { padding: 12px 14px; border-bottom: 1px solid var(--border-local); vertical-align: top; text-align: left; line-height: 1.65; }
#experimental-database-visuals .method-table th { color: var(--fg-local); font-weight: 500; background: var(--muted, #eef2f7); }
#experimental-database-visuals .method-table td { color: var(--fg-local); }
#experimental-database-visuals .report-footer { max-width: 1240px; margin: 24px auto 0; color: var(--muted-local); line-height: 1.75; font-size: 14px; }
@media (max-width: 820px) {
  #experimental-database-visuals { padding: 16px; }
  #experimental-database-visuals .summary-grid, #experimental-database-visuals .two-panel { grid-template-columns: 1fr; }
  #experimental-database-visuals .axis-label, #experimental-database-visuals .value-label, #experimental-database-visuals .cell-label, #experimental-database-visuals .chain-label { font-size: 12px; }
}
</style>
"""

content = f"""
<div id="experimental-database-visuals">
  <div class="report-header">
    <h1>实验记录数据库可视化表征</h1>
    <p class="subtitle">基于严格扩量版数据库，对实验记录规模、质量层级、指标构成、宿主/产物覆盖、集合交叉关系、文献证据链和关键数值分布进行汇总。字段名沿用当前 schema，其中 <code>glabridin_titer</code> 和 <code>glabridin_yield</code> 在图中按“产物滴度/产率”理解，并不只限定为光甘草定。</p>
    <p class="source-note">数据源：{esc(SRC.name)}；记录数 {N:,}，DOI 覆盖 {unique_dois:,}。</p>
  </div>
  {''.join(figures)}
  <div class="report-footer">建议使用方式：PPT 中可优先采用桑基图、气泡图、UpSet 图和证据链图说明数据库构建逻辑；若用于建模或贝叶斯优化，建议先使用核心/银层数据库，再根据证据文本逐步纳入 review 层记录。</div>
</div>
"""

standalone = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>实验记录数据库可视化表征</title>
{CSS}
</head>
<body>
{content}
</body>
</html>
"""

FRAG.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(standalone, encoding="utf-8")
FRAG.write_text(CSS + "\n" + content, encoding="utf-8")
print(json.dumps({
    "source": str(SRC),
    "standalone_html": str(OUT),
    "inline_fragment": str(FRAG),
    "rows": N,
    "unique_dois": unique_dois,
    "figures": len(figures),
    "standalone_bytes": OUT.stat().st_size,
    "fragment_bytes": FRAG.stat().st_size,
}, ensure_ascii=False, indent=2))
