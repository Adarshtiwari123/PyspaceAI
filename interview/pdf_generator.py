from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem
from reportlab.platypus import PageBreak
from reportlab.platypus import Preformatted
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

import io

def generate_pdf(user_name, total_score, qa_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>Interview Evaluation Report</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(f"Candidate: {user_name}", styles["Normal"]))
    elements.append(Paragraph(f"Overall Score: {total_score}/100", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph("<b>Interview Questions & Answers</b>", styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))

    for i, qa in enumerate(qa_data):
        elements.append(Paragraph(f"<b>Q{i+1}:</b> {qa['question']}", styles["Normal"]))
        elements.append(Paragraph(f"Answer: {qa['answer']}", styles["Normal"]))
        elements.append(Paragraph(f"Score: {qa['score']}/10", styles["Normal"]))
        elements.append(Spacer(1, 0.2 * inch))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf