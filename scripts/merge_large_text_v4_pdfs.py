from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter


ROOT = Path(__file__).resolve().parents[1]
ESSAY = ROOT / "essay"
SOURCES = [
    ESSAY / "main_known_clean_figures_large_text_v4_no_header.pdf",
    ESSAY / "nature_style_complete_vector_figure_pack_en_v4_large_text.pdf",
]
OUT = ESSAY / "all_figures_union_vector_large_text_v4.pdf"


def main() -> int:
    writer = PdfWriter()
    counts = {}
    for path in SOURCES:
        reader = PdfReader(str(path))
        counts[path.name] = len(reader.pages)
        for page in reader.pages:
            writer.add_page(page)
    with OUT.open("wb") as handle:
        writer.write(handle)
    print(f"Wrote: {OUT}")
    print(counts)
    print(f"total_pages={sum(counts.values())}")
    print(f"bytes={OUT.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
