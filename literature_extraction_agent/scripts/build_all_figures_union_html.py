from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ESSAY = ROOT / "essay"
SRC_HTML = ESSAY / "known_clean_methodology_showcase_en.html"
FALLBACK_HTML = ESSAY / "可用汇总7.31.html"
OUT_HTML = ESSAY / "all_figures_union_for_pdf.html"


def between(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        return ""
    end = text.find(end_marker, start)
    if end < 0:
        return text[start:]
    return text[start:end]


def main() -> int:
    src = SRC_HTML if SRC_HTML.exists() else FALLBACK_HTML
    html = src.read_text(encoding="utf-8")
    style = between(html, "<style>", "</style>")
    style = style.replace("<style>", "").strip()
    content = between(html, '<div class="grid">', "</main>")
    if not content:
        raise RuntimeError("Could not find figure grid in source HTML")
    pdf_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>All figures union - literature database</title>
  <style>
    {style}
    @page {{ size: A4 landscape; margin: 11mm; }}
    body {{ background: #fbfaf8; }}
    main {{ max-width: none; padding: 0; }}
    h1 {{ font-size: 22px; margin: 0 0 6px; }}
    .subtitle {{ margin-bottom: 14px; max-width: 980px; }}
    .grid {{ grid-template-columns: 1fr 1fr; gap: 14px; }}
    .figure {{ page-break-inside: avoid; margin-bottom: 14px; }}
    .pdf-appendix {{ page-break-before: always; }}
    .pdf-page-grid {{ grid-template-columns: 1fr 1fr; gap: 12px; }}
    .pdf-page {{ page-break-inside: avoid; }}
    .pdf-page img {{ max-height: 176mm; object-fit: contain; }}
    .caption, .pdf-page figcaption {{ font-size: 10.5px; }}
  </style>
</head>
<body>
<main>
  <h1>All figures union for the traceable LLPS-enzyme literature database</h1>
  <p class="subtitle">Union of the known-clean showcase figures and the two previously generated Nature-style PDF panel versions.</p>
  {content}
</main>
</body>
</html>
"""
    OUT_HTML.write_text(pdf_html, encoding="utf-8")
    print(f"Wrote: {OUT_HTML}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
