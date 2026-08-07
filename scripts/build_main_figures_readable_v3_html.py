from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ESSAY = ROOT / "essay"
SRC_HTML = ESSAY / "known_clean_methodology_showcase_en.html"
FALLBACK_HTML = ESSAY / "可用汇总7.31.html"
OUT_HTML = ESSAY / "main_known_clean_figures_readable_v3.html"


def between(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        return ""
    end = text.find(end_marker, start)
    if end < 0:
        return text[start:]
    return text[start:end]


def remove_pdf_appendix(content: str) -> str:
    marker = '<section class="pdf-appendix"'
    idx = content.find(marker)
    return content[:idx] if idx >= 0 else content


def main() -> int:
    src = SRC_HTML if SRC_HTML.exists() else FALLBACK_HTML
    html = src.read_text(encoding="utf-8")
    style = between(html, "<style>", "</style>").replace("<style>", "").strip()
    content = between(html, '<div class="grid">', "</main>")
    if not content:
        raise RuntimeError("Could not find figure grid in source HTML")
    content = remove_pdf_appendix(content)
    out = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Known-clean main figures readable v3</title>
  <style>
    {style}
    @page {{ size: A4 landscape; margin: 9mm; }}
    body {{ background: #fbfaf8; }}
    main {{ max-width: none; padding: 0; }}
    h1 {{ font-size: 22px; margin: 0 0 6px; }}
    .subtitle {{ margin-bottom: 12px; max-width: 1000px; }}
    .grid {{
      display: block;
    }}
    .figure {{
      page-break-inside: avoid;
      break-inside: avoid;
      margin: 0 0 18px;
      padding-bottom: 10px;
      border-bottom: 1px solid #DDD8D1;
    }}
    .figure:nth-of-type(2n) {{
      page-break-after: always;
    }}
    .figure h2 {{
      font-size: 19px;
      margin-bottom: 8px;
    }}
    .svg-wrap {{
      max-height: 150mm;
      overflow: visible;
    }}
    svg {{
      max-height: 145mm;
      object-fit: contain;
    }}
    .caption {{
      font-size: 10.5px;
      margin-top: 5px;
    }}
  </style>
</head>
<body>
<main>
  <h1>Known-clean traceable literature database figures, readable v3</h1>
  <p class="subtitle">Main vector figures are printed in a loose one-column/two-figure-per-page layout to avoid label overlap and clipping.</p>
  {content}
</main>
</body>
</html>
"""
    OUT_HTML.write_text(out, encoding="utf-8")
    print(f"Wrote: {OUT_HTML}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
