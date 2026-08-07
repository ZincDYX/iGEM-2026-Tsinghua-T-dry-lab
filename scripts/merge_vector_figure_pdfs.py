from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter


ROOT = Path(__file__).resolve().parents[1]
ESSAY = ROOT / "essay"
SOURCES = [
    ESSAY / "main_known_clean_figures_vector.pdf",
    ESSAY / "nature_style_complete_vector_figure_pack_en.pdf",
    ESSAY / "nature_style_complete_vector_figure_pack_en_v2.pdf",
]
OUT = ESSAY / "all_figures_union_vector_original_pdf_pages.pdf"


def append_pdf(writer: PdfWriter, path: Path) -> int:
    reader = PdfReader(str(path))
    count = 0
    for page in reader.pages:
        writer.add_page(page)
        count += 1
    return count


def main() -> int:
    writer = PdfWriter()
    page_counts = {}
    for path in SOURCES:
        if not path.exists():
            raise FileNotFoundError(path)
        page_counts[path.name] = append_pdf(writer, path)
    with OUT.open("wb") as handle:
        writer.write(handle)
    print(f"Wrote: {OUT}")
    print(page_counts)
    print(f"total_pages={sum(page_counts.values())}")
    print(f"bytes={OUT.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
