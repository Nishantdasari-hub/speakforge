from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak


SOURCE = Path(__file__).with_name("PROJECT_REPORT.md")
OUTPUT = Path(__file__).with_name("SpeakForge-Local-Audit-Report.pdf")


def build_pdf():
    styles = getSampleStyleSheet()
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=9.5, leading=13)
    bullet = ParagraphStyle("Bullet", parent=body, leftIndent=12, firstLineIndent=-8)
    story = []

    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            story.append(Spacer(1, 4))
        elif line.startswith("# "):
            story.append(Paragraph(line[2:], styles["Title"]))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], styles["Heading2"]))
        elif line.startswith("- "):
            story.append(Paragraph("&#8226; " + line[2:], bullet))
        elif line[:2].isdigit() and line[2:4] == ". ":
            story.append(Paragraph(line, body))
        else:
            story.append(Paragraph(line.replace("`", ""), body))

    document = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, rightMargin=16 * mm, leftMargin=16 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
    )
    document.build(story)
    print(OUTPUT)


if __name__ == "__main__":
    build_pdf()