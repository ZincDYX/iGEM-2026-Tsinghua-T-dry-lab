from __future__ import annotations

from pathlib import Path

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


SRC = Path(r"C:\Users\zhaol\Documents\Codex\2026-07-16\d-25-python-code\work\pdf_union_render_all_hi")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "essay" / "all_figures_union_nature_style_panel_clean.pdf"


def main() -> int:
    pages = []
    for path in sorted(SRC.glob("page-*.png")):
        image = Image.open(path).convert("RGB")
        width, height = image.size
        # Remove browser print header and footer while preserving the report title.
        cropped = image.crop((0, 72, width, height - 120))
        pages.append(cropped)
    if not pages:
        raise RuntimeError(f"No rendered pages found in {SRC}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    first_w, first_h = pages[0].size
    pdf = canvas.Canvas(str(OUT), pagesize=(first_w, first_h))
    for page in pages:
        width, height = page.size
        if (width, height) != (first_w, first_h):
            pdf.setPageSize((width, height))
        pdf.drawImage(ImageReader(page), 0, 0, width=width, height=height)
        pdf.showPage()
    pdf.save()
    print(f"Wrote: {OUT}")
    print(f"Pages: {len(pages)}")
    print(f"Bytes: {OUT.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
