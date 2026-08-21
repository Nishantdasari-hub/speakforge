"""Render the SpeakForge documentation markdown to a styled PDF."""
import pathlib

import markdown
from weasyprint import HTML, CSS

DOCS = pathlib.Path(__file__).parent
SOURCE = DOCS / "SpeakForge_Documentation.md"
OUTPUT = DOCS / "SpeakForge_Documentation.pdf"

CSS_TEXT = """
@page { size: A4; margin: 20mm 16mm; @bottom-center {
    content: counter(page) " / " counter(pages);
    font-size: 9pt; color: #888; } }
body { font-family: "DejaVu Sans", sans-serif; font-size: 10pt;
       line-height: 1.5; color: #1f2937; }
h1 { font-size: 22pt; color: #4338ca; border-bottom: 3px solid #4338ca;
     padding-bottom: 6px; }
h2 { font-size: 15pt; color: #4338ca; margin-top: 22px;
     border-bottom: 1px solid #c7d2fe; padding-bottom: 3px;
     page-break-after: avoid; }
h3 { font-size: 12pt; color: #374151; page-break-after: avoid; }
h4 { font-size: 10.5pt; color: #374151; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 8.5pt;
       background: #f3f4f6; padding: 1px 3px; border-radius: 3px; }
pre { background: #f8fafc; border: 1px solid #e2e8f0; border-left: 3px solid #4338ca;
      padding: 8px; border-radius: 4px; font-size: 7.8pt; line-height: 1.35;
      white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 7.8pt; }
table { border-collapse: collapse; width: 100%; margin: 10px 0;
        font-size: 8.8pt; page-break-inside: avoid; }
th { background: #eef2ff; color: #3730a3; text-align: left; }
th, td { border: 1px solid #d1d5db; padding: 4px 6px; vertical-align: top; }
tr:nth-child(even) td { background: #fafafa; }
hr { border: none; border-top: 1px solid #e5e7eb; margin: 18px 0; }
"""


def main():
    html_body = markdown.markdown(
        SOURCE.read_text(encoding="utf-8"),
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
    )
    html = f"<html><head><meta charset='utf-8'></head><body>{html_body}</body></html>"
    HTML(string=html).write_pdf(OUTPUT, stylesheets=[CSS(string=CSS_TEXT)])
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
