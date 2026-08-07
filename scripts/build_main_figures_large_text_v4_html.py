from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ESSAY = ROOT / "essay"
SRC_HTML = ESSAY / "known_clean_methodology_showcase_en.html"
FALLBACK_HTML = ESSAY / "可用汇总7.31.html"
OUT_HTML = ESSAY / "main_known_clean_figures_large_text_v4.html"


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
  <title>Known-clean main figures large text v4</title>
  <style>
    {style}
    @page {{ size: A3 landscape; margin: 12mm; }}
    * {{ box-sizing: border-box; }}
    html, body {{ background: #fbfaf8; }}
    body {{ font-size: 16px; }}
    main {{ max-width: none; padding: 0; }}
    h1, .subtitle {{ display: none; }}
    .grid {{ display: block; }}
    .figure {{
      min-height: 270mm;
      page-break-after: always;
      break-after: page;
      page-break-inside: avoid;
      break-inside: avoid;
      display: flex;
      flex-direction: column;
      gap: 9px;
      margin: 0;
      padding: 0 0 10mm;
      border: 0;
    }}
    .figure:last-child {{
      page-break-after: auto;
      break-after: auto;
    }}
    .figure h2 {{
      font-size: 26px;
      line-height: 1.12;
      margin: 0 0 6px;
      letter-spacing: 0;
    }}
    .svg-wrap {{
      flex: 1 1 auto;
      min-height: 0;
      max-height: 223mm;
      overflow: visible;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    svg {{
      width: 100%;
      max-width: 100%;
      height: auto;
      max-height: 220mm;
      object-fit: contain;
      overflow: visible;
    }}
    .caption {{
      flex: 0 0 auto;
      font-size: 15px;
      line-height: 1.34;
      margin-top: 4px;
      max-width: 1320px;
    }}
  </style>
</head>
<body>
<main>
  <h1>Known-clean traceable literature database figures</h1>
  <p class="subtitle">Large-text v4 layout. Each figure is printed on a wider page with expanded captions and dedicated chart space to improve projection readability without overlap.</p>
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
