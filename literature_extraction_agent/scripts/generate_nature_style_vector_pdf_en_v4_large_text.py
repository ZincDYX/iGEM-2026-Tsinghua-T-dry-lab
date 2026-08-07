from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_SCRIPTS = Path(__file__).resolve().parent
if str(PROJECT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PROJECT_SCRIPTS))

import generate_nature_style_vector_pdf_en_v3 as v3


ROOT = v3.ROOT
v3.OUT = ROOT / "essay" / "nature_style_complete_vector_figure_pack_en_v4_large_text.pdf"
v3.SUMMARY = ROOT / "essay" / "nature_style_complete_vector_figure_pack_en_v4_large_text_summary.json"

INK = v3.INK
MUTED = v3.MUTED
PALETTE = v3.PALETTE


_original_figure = plt.figure


def large_figure(*args, **kwargs):
    if "figsize" in kwargs:
        kwargs["figsize"] = (14.4, 9.2)
    return _original_figure(*args, **kwargs)


def setup_style() -> None:
    v3.v2.setup_style()
    plt.rcParams.update(
        {
            "font.size": 10.2,
            "axes.titlesize": 12.5,
            "axes.labelsize": 10.4,
            "xtick.labelsize": 9.2,
            "ytick.labelsize": 9.2,
            "legend.fontsize": 9.1,
            "figure.autolayout": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def add_title(fig, title: str, subtitle: str = "") -> None:
    subtitle = subtitle.replace("Readable v3", "Large-text v4")
    fig.text(0.035, 0.974, title, ha="left", va="top", fontsize=17.0, fontweight="bold", color=INK)
    if subtitle:
        fig.text(0.035, 0.944, subtitle, ha="left", va="top", fontsize=11.0, color=MUTED)


def caption(fig, text: str) -> None:
    fig.text(
        0.035,
        0.026,
        v3.base.wrapped(text, 155),
        ha="left",
        va="bottom",
        fontsize=9.5,
        color=INK,
        linespacing=1.24,
    )


def save(pdf, fig, text: str) -> None:
    caption(fig, text)
    pdf.savefig(fig)
    plt.close(fig)


def panel(ax, letter: str, title: str) -> None:
    ax.text(
        -0.052,
        1.055,
        letter,
        transform=ax.transAxes,
        fontsize=14.0,
        fontweight="bold",
        va="top",
        ha="left",
        color=INK,
    )
    ax.set_title(title, loc="left", pad=10, fontweight="bold", color=INK)


def clean_axes(ax, grid_axis: str = "x") -> None:
    v3.v2.clean_axes(ax, grid_axis)
    ax.tick_params(axis="both", labelsize=9.2, pad=4)


def barh_readable(ax, counter: Counter[str], letter: str, title: str, n: int, color: str, label_limit: int = 30) -> None:
    items = [(k, value) for k, value in counter.most_common(n) if k][::-1]
    labels = [k if len(k) <= label_limit else k[: label_limit - 1] + "." for k, _ in items]
    values = [value for _, value in items]
    ax.barh(labels, values, color=color, alpha=0.86, height=0.52)
    if values:
        ax.set_xlim(0, max(values) * 1.26)
        offset = max(values) * 0.020
        for y, value in enumerate(values):
            ax.text(value + offset, y, f"{value:,}", va="center", fontsize=9.0, color=INK)
    ax.set_xlabel("Records")
    panel(ax, letter, title)
    clean_axes(ax)


def figure_note(ax, lines: list[str], letter: str, title: str) -> None:
    ax.axis("off")
    panel(ax, letter, title)
    y = 0.88
    for line in lines:
        size = 10.4 if line.startswith("Key") or line.startswith("Use") else 9.8
        weight = "bold" if line.startswith("Key") or line.startswith("Use") else "normal"
        ax.text(
            0.02,
            y,
            v3.base.wrapped(line, 82),
            transform=ax.transAxes,
            fontsize=size,
            fontweight=weight,
            color=INK,
            va="top",
            linespacing=1.32,
        )
        y -= 0.16 if line.startswith("Key") or line.startswith("Use") else 0.13


def hist_readable(ax, values: list[float], bins, letter: str, title: str, xlabel: str, color: str, markers=None, kde: bool = False) -> None:
    v3.v2.hist(ax, values, bins, letter, title, xlabel, color, markers=markers, kde=kde)
    ax.margins(x=0.025)
    clean_axes(ax, "both")
    if getattr(ax, "legend_", None):
        ax.legend_.set_title(None)
        for text in ax.legend_.get_texts():
            text.set_fontsize(9.0)


def titer_box_readable(ax, rows: list[dict[str, str]]) -> None:
    v3.v2.titer_box(ax, rows)
    ax.tick_params(axis="x", labelsize=9.0, pad=6)
    ax.tick_params(axis="y", labelsize=9.2)
    for label in ax.get_xticklabels():
        label.set_rotation(18)
        label.set_ha("right")


_original_product_host_bubble = v3.base.product_host_bubble


def product_host_bubble(ax, rows: list[dict[str, str]]) -> None:
    ax.set_position([0.12, 0.16, 0.82, 0.68])
    _original_product_host_bubble(ax, rows)
    ax.set_position([0.12, 0.16, 0.82, 0.68])
    ax.tick_params(axis="both", labelsize=9.2, pad=5)


def main() -> None:
    v3.plt.figure = large_figure
    v3.setup_style = setup_style
    v3.add_title = add_title
    v3.caption = caption
    v3.save = save
    v3.panel = panel
    v3.clean_axes = clean_axes
    v3.barh_readable = barh_readable
    v3.figure_note = figure_note
    v3.hist_readable = hist_readable
    v3.titer_box_readable = titer_box_readable
    v3.base.product_host_bubble = product_host_bubble

    summary = v3.generate()
    summary["pages"] = 14
    summary["layout"] = "large-text v4, 14.4 x 9.2 inch pages"
    v3.SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Wrote: {v3.OUT}")
    print(f"Wrote: {v3.SUMMARY}")


if __name__ == "__main__":
    main()
