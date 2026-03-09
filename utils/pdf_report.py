from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, PageBreak, KeepTogether
)
from io import BytesIO
from datetime import datetime

from database.db import get_report, get_interview, get_interview_questions


# ─────────────────────────────────────────────
# COLORS
# ─────────────────────────────────────────────
DARK_BLUE  = colors.HexColor("#1a2744")
MID_BLUE   = colors.HexColor("#2c4a8c")
LIGHT_BLUE = colors.HexColor("#e8eef7")
GREEN      = colors.HexColor("#0f9d58")
ORANGE     = colors.HexColor("#f4b400")
RED_CLR    = colors.HexColor("#db4437")
LIGHT_GREY = colors.HexColor("#f5f5f5")
MID_GREY   = colors.HexColor("#e0e0e0")
TEXT_DARK  = colors.HexColor("#212121")
TEXT_MID   = colors.HexColor("#555555")


def score_color(score_out_of_10: float) -> colors.Color:
    if score_out_of_10 >= 7.5:
        return GREEN
    elif score_out_of_10 >= 5.0:
        return ORANGE
    else:
        return RED_CLR


# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────
def build_styles() -> dict:
    return {
        "title": ParagraphStyle(
            "title", fontName="Helvetica-Bold", fontSize=22,
            textColor=colors.white, alignment=TA_CENTER, spaceAfter=4
        ),
        "section_heading": ParagraphStyle(
            "section_heading", fontName="Helvetica-Bold", fontSize=13,
            textColor=DARK_BLUE, spaceBefore=12, spaceAfter=6
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=10,
            textColor=TEXT_DARK, leading=15, spaceAfter=4, alignment=TA_JUSTIFY
        ),
        "bullet": ParagraphStyle(
            "bullet", fontName="Helvetica", fontSize=10,
            textColor=TEXT_DARK, leading=15, leftIndent=12, spaceAfter=4
        ),
        "q_label": ParagraphStyle(
            "q_label", fontName="Helvetica-Bold", fontSize=10,
            textColor=MID_BLUE, spaceAfter=3
        ),
        "q_text": ParagraphStyle(
            "q_text", fontName="Helvetica-Bold", fontSize=11,
            textColor=TEXT_DARK, leading=15, spaceAfter=5
        ),
        "answer_label": ParagraphStyle(
            "answer_label", fontName="Helvetica-Bold", fontSize=9,
            textColor=TEXT_MID, spaceAfter=2
        ),
        "answer_text": ParagraphStyle(
            "answer_text", fontName="Helvetica", fontSize=10,
            textColor=TEXT_DARK, leading=14, spaceAfter=5, alignment=TA_JUSTIFY
        ),
        "feedback_text": ParagraphStyle(
            "feedback_text", fontName="Helvetica-Oblique", fontSize=10,
            textColor=TEXT_MID, leading=14, spaceAfter=4, alignment=TA_JUSTIFY
        ),
        "score_text": ParagraphStyle(
            "score_text", fontName="Helvetica-Bold", fontSize=11,
            textColor=TEXT_DARK, spaceAfter=2
        ),
        "ideal_label": ParagraphStyle(
            "ideal_label", fontName="Helvetica-Bold", fontSize=9,
            textColor=GREEN, spaceAfter=2
        ),
        "ideal_text": ParagraphStyle(
            "ideal_text", fontName="Helvetica", fontSize=10,
            textColor=colors.HexColor("#1a5c32"), leading=14,
            spaceAfter=4, alignment=TA_JUSTIFY
        ),
        "footer": ParagraphStyle(
            "footer", fontName="Helvetica", fontSize=8,
            textColor=TEXT_MID, alignment=TA_CENTER
        ),
    }


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
def build_header(styles: dict, candidate_name: str, interview_date: str, domain: str = "Technology") -> list:
    elements = []

    header_table = Table(
        [[Paragraph("Interview Evaluation Report", styles["title"])]],
        colWidths=[170 * mm]
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), DARK_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4 * mm))

    info_table = Table(
        [[
            Paragraph(f"<b>Candidate:</b> {candidate_name}", styles["body"]),
            Paragraph(f"<b>Domain:</b> {domain}", styles["body"]),
            Paragraph(f"<b>Date:</b> {interview_date}", styles["body"]),
        ]],
        colWidths=[56 * mm, 57 * mm, 57 * mm]
    )
    info_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.5, MID_GREY),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6 * mm))
    return elements


# ─────────────────────────────────────────────
# PERFORMANCE SUMMARY TABLE
# ─────────────────────────────────────────────
def build_summary_table(styles: dict, scores: dict) -> list:
    elements = []
    elements.append(Paragraph("Performance Summary", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=MID_BLUE, spaceAfter=6))

    # Convert /10 to /25 and /100
    def to_25(v):  return round(float(v or 0) * 2.5, 1)
    def to_100(v): return round(float(v or 0) * 10.0, 1)

    rows = [
        ["Category", "Score"],
        ["Overall Score",          f"{to_100(scores.get('overall_score', 0))}/100"],
        ["Technical Knowledge",    f"{to_25(scores.get('technical_knowledge', 0))}/25"],
        ["Communication Skills",   f"{to_25(scores.get('communication_skills', 0))}/25"],
        ["Problem Solving",        f"{to_25(scores.get('problem_solving', 0))}/25"],
        ["Project Understanding",  f"{to_25(scores.get('project_understanding', 0))}/25"],
    ]

    t = Table(rows, colWidths=[120 * mm, 50 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), DARK_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 11),
        ("ALIGN",         (0, 0), (-1, 0), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND",    (0, 1), (-1, 1), LIGHT_BLUE),
        ("FONTNAME",      (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 1), (-1, 1), 11),
        ("BACKGROUND",    (0, 2), (-1, 2), colors.white),
        ("BACKGROUND",    (0, 3), (-1, 3), LIGHT_GREY),
        ("BACKGROUND",    (0, 4), (-1, 4), colors.white),
        ("BACKGROUND",    (0, 5), (-1, 5), LIGHT_GREY),
        ("FONTNAME",      (0, 2), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 2), (-1, -1), 10),
        ("ALIGN",         (1, 0), (1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("GRID",          (0, 0), (-1, -1), 0.5, MID_GREY),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 6 * mm))
    return elements


# ─────────────────────────────────────────────
# BULLET SECTION (Strengths / Improvements / Suggestions)
# ─────────────────────────────────────────────
def build_bullet_section(styles: dict, heading: str, content: str,
                          bg_color=None) -> list:
    elements = []
    elements.append(Paragraph(heading, styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=MID_BLUE, spaceAfter=4))

    lines   = [l.strip() for l in content.split(".") if len(l.strip()) > 5]
    bullets = [Paragraph(f"• {line}.", styles["bullet"]) for line in lines]

    if bg_color and bullets:
        inner = Table([[bullets]], colWidths=[170 * mm])
        inner.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg_color),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("BOX",           (0, 0), (-1, -1), 0.5, MID_GREY),
        ]))
        elements.append(inner)
    else:
        for b in bullets:
            elements.append(b)

    elements.append(Spacer(1, 5 * mm))
    return elements


# ─────────────────────────────────────────────
# Q&A BLOCK
# Shows: Question → User Answer → Score | Feedback → Ideal Answer
# ─────────────────────────────────────────────
def build_qa_block(styles: dict, index: int, qa: tuple) -> list:
    """
    qa tuple from get_interview_questions():
    (question_number, difficulty_level, topic, question_text,
     user_answer, ai_suggested_answer, score, feedback)
    """
    _, diff_level, topic, q_text, user_ans, ideal_ans, score, feedback = qa

    score_val = float(score or 0)
    s_color   = score_color(score_val)

    # Score + Feedback row
    sf_table = Table(
        [[
            Paragraph(f"{score_val}/10", styles["score_text"]),
            Paragraph(
                f"<b>Feedback:</b> {str(feedback or 'No feedback available.')}",
                styles["feedback_text"]
            ),
        ]],
        colWidths=[22 * mm, 138 * mm]
    )
    sf_table.setStyle(TableStyle([
        ("TEXTCOLOR",     (0, 0), (0, 0), s_color),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    block = [
        Paragraph(f"Q{index}:  [{diff_level.upper()}]", styles["q_label"]),
        Paragraph(str(q_text), styles["q_text"]),
        Spacer(1, 2 * mm),
        Paragraph("Answer:", styles["answer_label"]),
        Paragraph(str(user_ans or "No answer provided."), styles["answer_text"]),
        Spacer(1, 2 * mm),
        sf_table,
    ]

    # Ideal answer — what it should have been
    if ideal_ans:
        block += [
            Spacer(1, 2 * mm),
            Paragraph("✦  What the ideal answer should include:", styles["ideal_label"]),
            Paragraph(str(ideal_ans), styles["ideal_text"]),
        ]

    card = Table([[block]], colWidths=[170 * mm])
    card.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.white),
        ("BOX",           (0, 0), (-1, -1), 0.75, MID_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))

    return [KeepTogether([card]), Spacer(1, 5 * mm)]


# ─────────────────────────────────────────────
# MAIN — generate_pdf()
# ─────────────────────────────────────────────
def _detect_domain(resume_text: str) -> str:
    """Detect job domain from resume keywords."""
    text = (resume_text or "").lower()
    domains = {
        "Software Engineering": ["python","java","javascript","react","node","django","flask","sql","git","api","backend","frontend","fullstack","developer","software engineer"],
        "Data Science / AI":    ["machine learning","deep learning","neural network","tensorflow","pytorch","pandas","numpy","data science","nlp","computer vision","model","dataset"],
        "Cloud / DevOps":       ["aws","azure","gcp","docker","kubernetes","terraform","ci/cd","devops","infrastructure","cloud","pipeline"],
        "Cybersecurity":        ["security","penetration","ethical hacking","vulnerability","firewall","encryption","siem","soc","threat"],
        "Sales & Business":     ["sales","revenue","crm","client","account","business development","b2b","negotiation","pipeline","quota"],
        "HR & Recruitment":     ["recruitment","talent","onboarding","hr","human resources","payroll","employee","hiring","workforce"],
        "Product Management":   ["product manager","roadmap","user stories","agile","scrum","stakeholder","product strategy","okr"],
        "Finance":              ["finance","accounting","budget","investment","financial analysis","excel","forecasting","audit"],
        "Marketing":            ["marketing","seo","content","social media","campaign","branding","digital marketing","analytics"],
        "Design / UX":          ["ux","ui","figma","user research","wireframe","prototype","design thinking","accessibility"],
    }
    scores = {}
    for domain, keywords in domains.items():
        scores[domain] = sum(1 for kw in keywords if kw in text)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Technology"


def generate_pdf(interview_id: int) -> bytes:
    """
    Generate full evaluation PDF.
    Returns bytes for st.download_button().
    """
    interview = get_interview(interview_id)
    report    = get_report(interview_id)
    questions = get_interview_questions(interview_id)

    if not interview or not report:
        raise ValueError(f"No data for interview_id={interview_id}")

    (iid, user_email, resume_text, resume_filename,
     start_time, end_time, status, total_score) = interview

    (overall_score, performance_summary,
     technical_knowledge, communication_skills,
     problem_solving, project_understanding,
     strengths, areas_for_improvement,
     actionable_suggestions, generated_at) = report

    # ── Point 7: Real name from auth_users table ────────────────
    candidate_name = ""
    try:
        from database.db import get_connection, release_connection
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT full_name FROM auth_users WHERE email = %s", (user_email,))
        row = cur.fetchone()
        cur.close()
        release_connection(conn)
        if row and row[0]:
            candidate_name = row[0]
    except Exception:
        pass

    if not candidate_name:
        # fallback: clean email prefix
        candidate_name = user_email.split("@")[0].replace(".", " ").replace("_", " ").title()

    domain         = _detect_domain(resume_text or "")
    interview_date = start_time.strftime("%d %b %Y, %H:%M") if start_time else str(generated_at)

    scores = {
        "overall_score":         overall_score,
        "technical_knowledge":   technical_knowledge,
        "communication_skills":  communication_skills,
        "problem_solving":       problem_solving,
        "project_understanding": project_understanding,
    }

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize     = A4,
        leftMargin   = 20 * mm,
        rightMargin  = 20 * mm,
        topMargin    = 15 * mm,
        bottomMargin = 20 * mm
    )

    styles   = build_styles()
    elements = []

    # Page 1
    elements += build_header(styles, candidate_name, interview_date, domain)
    elements += build_summary_table(styles, scores)

    if performance_summary:
        elements.append(Paragraph("Overall Assessment", styles["section_heading"]))
        elements.append(HRFlowable(width="100%", thickness=1, color=MID_BLUE, spaceAfter=4))
        elements.append(Paragraph(str(performance_summary), styles["body"]))
        elements.append(Spacer(1, 5 * mm))

    if strengths:
        elements += build_bullet_section(
            styles, "Strengths", str(strengths),
            bg_color=colors.HexColor("#e8f5e9")
        )
    if areas_for_improvement:
        elements += build_bullet_section(
            styles, "Areas for Improvement", str(areas_for_improvement),
            bg_color=colors.HexColor("#fff8e1")
        )
    if actionable_suggestions:
        elements += build_bullet_section(
            styles, "Suggestions", str(actionable_suggestions)
        )

    # Page 2+ — Q&A
    elements.append(PageBreak())
    elements.append(Paragraph("Interview Questions & Answers", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=DARK_BLUE, spaceAfter=8))
    elements.append(Spacer(1, 3 * mm))

    for i, qa in enumerate(questions, 1):
        elements += build_qa_block(styles, i, qa)

    # Footer
    elements.append(Spacer(1, 5 * mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=MID_GREY))
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph(
        f"Generated by Pyspace AI  •  {datetime.now().strftime('%Y-%m-%d %H:%M')}  •  Interview #{interview_id}",
        styles["footer"]
    ))

    doc.build(elements)
    return buffer.getvalue()
# from reportlab.lib.pagesizes import A4
# from reportlab.lib import colors
# from reportlab.lib.units import mm
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
# from reportlab.platypus import (
#     SimpleDocTemplate, Paragraph, Spacer, Table,
#     TableStyle, HRFlowable, PageBreak, KeepTogether
# )
# from io import BytesIO
# from datetime import datetime

# from database.db import get_report, get_interview, get_interview_questions


# # ─────────────────────────────────────────────
# # COLORS
# # ─────────────────────────────────────────────
# DARK_BLUE  = colors.HexColor("#1a2744")
# MID_BLUE   = colors.HexColor("#2c4a8c")
# LIGHT_BLUE = colors.HexColor("#e8eef7")
# GREEN      = colors.HexColor("#0f9d58")
# ORANGE     = colors.HexColor("#f4b400")
# RED_CLR    = colors.HexColor("#db4437")
# LIGHT_GREY = colors.HexColor("#f5f5f5")
# MID_GREY   = colors.HexColor("#e0e0e0")
# TEXT_DARK  = colors.HexColor("#212121")
# TEXT_MID   = colors.HexColor("#555555")


# def score_color(score_out_of_10: float) -> colors.Color:
#     if score_out_of_10 >= 7.5:
#         return GREEN
#     elif score_out_of_10 >= 5.0:
#         return ORANGE
#     else:
#         return RED_CLR


# # ─────────────────────────────────────────────
# # STYLES
# # ─────────────────────────────────────────────
# def build_styles() -> dict:
#     return {
#         "title": ParagraphStyle(
#             "title", fontName="Helvetica-Bold", fontSize=22,
#             textColor=colors.white, alignment=TA_CENTER, spaceAfter=4
#         ),
#         "section_heading": ParagraphStyle(
#             "section_heading", fontName="Helvetica-Bold", fontSize=13,
#             textColor=DARK_BLUE, spaceBefore=12, spaceAfter=6
#         ),
#         "body": ParagraphStyle(
#             "body", fontName="Helvetica", fontSize=10,
#             textColor=TEXT_DARK, leading=15, spaceAfter=4, alignment=TA_JUSTIFY
#         ),
#         "bullet": ParagraphStyle(
#             "bullet", fontName="Helvetica", fontSize=10,
#             textColor=TEXT_DARK, leading=15, leftIndent=12, spaceAfter=4
#         ),
#         "q_label": ParagraphStyle(
#             "q_label", fontName="Helvetica-Bold", fontSize=10,
#             textColor=MID_BLUE, spaceAfter=3
#         ),
#         "q_text": ParagraphStyle(
#             "q_text", fontName="Helvetica-Bold", fontSize=11,
#             textColor=TEXT_DARK, leading=15, spaceAfter=5
#         ),
#         "answer_label": ParagraphStyle(
#             "answer_label", fontName="Helvetica-Bold", fontSize=9,
#             textColor=TEXT_MID, spaceAfter=2
#         ),
#         "answer_text": ParagraphStyle(
#             "answer_text", fontName="Helvetica", fontSize=10,
#             textColor=TEXT_DARK, leading=14, spaceAfter=5, alignment=TA_JUSTIFY
#         ),
#         "feedback_text": ParagraphStyle(
#             "feedback_text", fontName="Helvetica-Oblique", fontSize=10,
#             textColor=TEXT_MID, leading=14, spaceAfter=4, alignment=TA_JUSTIFY
#         ),
#         "score_text": ParagraphStyle(
#             "score_text", fontName="Helvetica-Bold", fontSize=11,
#             textColor=TEXT_DARK, spaceAfter=2
#         ),
#         "ideal_label": ParagraphStyle(
#             "ideal_label", fontName="Helvetica-Bold", fontSize=9,
#             textColor=GREEN, spaceAfter=2
#         ),
#         "ideal_text": ParagraphStyle(
#             "ideal_text", fontName="Helvetica", fontSize=10,
#             textColor=colors.HexColor("#1a5c32"), leading=14,
#             spaceAfter=4, alignment=TA_JUSTIFY
#         ),
#         "footer": ParagraphStyle(
#             "footer", fontName="Helvetica", fontSize=8,
#             textColor=TEXT_MID, alignment=TA_CENTER
#         ),
#     }


# # ─────────────────────────────────────────────
# # HEADER
# # ─────────────────────────────────────────────
# def build_header(styles: dict, candidate_name: str, interview_date: str) -> list:
#     elements = []

#     header_table = Table(
#         [[Paragraph("Interview Evaluation Report", styles["title"])]],
#         colWidths=[170 * mm]
#     )
#     header_table.setStyle(TableStyle([
#         ("BACKGROUND",    (0, 0), (-1, -1), DARK_BLUE),
#         ("TOPPADDING",    (0, 0), (-1, -1), 18),
#         ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
#         ("LEFTPADDING",   (0, 0), (-1, -1), 10),
#     ]))
#     elements.append(header_table)
#     elements.append(Spacer(1, 4 * mm))

#     info_table = Table(
#         [[
#             Paragraph(f"<b>Candidate:</b> {candidate_name}", styles["body"]),
#             Paragraph("<b>Interview Type:</b> Technical Practice", styles["body"]),
#             Paragraph(f"<b>Date:</b> {interview_date}", styles["body"]),
#         ]],
#         colWidths=[56 * mm, 57 * mm, 57 * mm]
#     )
#     info_table.setStyle(TableStyle([
#         ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_BLUE),
#         ("TOPPADDING",    (0, 0), (-1, -1), 8),
#         ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
#         ("LEFTPADDING",   (0, 0), (-1, -1), 8),
#         ("GRID",          (0, 0), (-1, -1), 0.5, MID_GREY),
#     ]))
#     elements.append(info_table)
#     elements.append(Spacer(1, 6 * mm))
#     return elements


# # ─────────────────────────────────────────────
# # PERFORMANCE SUMMARY TABLE
# # ─────────────────────────────────────────────
# def build_summary_table(styles: dict, scores: dict) -> list:
#     elements = []
#     elements.append(Paragraph("Performance Summary", styles["section_heading"]))
#     elements.append(HRFlowable(width="100%", thickness=1, color=MID_BLUE, spaceAfter=6))

#     # Convert /10 to /25 and /100
#     def to_25(v):  return round(float(v or 0) * 2.5, 1)
#     def to_100(v): return round(float(v or 0) * 10.0, 1)

#     rows = [
#         ["Category", "Score"],
#         ["Overall Score",          f"{to_100(scores.get('overall_score', 0))}/100"],
#         ["Technical Knowledge",    f"{to_25(scores.get('technical_knowledge', 0))}/25"],
#         ["Communication Skills",   f"{to_25(scores.get('communication_skills', 0))}/25"],
#         ["Problem Solving",        f"{to_25(scores.get('problem_solving', 0))}/25"],
#         ["Project Understanding",  f"{to_25(scores.get('project_understanding', 0))}/25"],
#     ]

#     t = Table(rows, colWidths=[120 * mm, 50 * mm])
#     t.setStyle(TableStyle([
#         ("BACKGROUND",    (0, 0), (-1, 0), DARK_BLUE),
#         ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
#         ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
#         ("FONTSIZE",      (0, 0), (-1, 0), 11),
#         ("ALIGN",         (0, 0), (-1, 0), "CENTER"),
#         ("TOPPADDING",    (0, 0), (-1, 0), 8),
#         ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
#         ("BACKGROUND",    (0, 1), (-1, 1), LIGHT_BLUE),
#         ("FONTNAME",      (0, 1), (-1, 1), "Helvetica-Bold"),
#         ("FONTSIZE",      (0, 1), (-1, 1), 11),
#         ("BACKGROUND",    (0, 2), (-1, 2), colors.white),
#         ("BACKGROUND",    (0, 3), (-1, 3), LIGHT_GREY),
#         ("BACKGROUND",    (0, 4), (-1, 4), colors.white),
#         ("BACKGROUND",    (0, 5), (-1, 5), LIGHT_GREY),
#         ("FONTNAME",      (0, 2), (-1, -1), "Helvetica"),
#         ("FONTSIZE",      (0, 2), (-1, -1), 10),
#         ("ALIGN",         (1, 0), (1, -1), "CENTER"),
#         ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
#         ("TOPPADDING",    (0, 1), (-1, -1), 7),
#         ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
#         ("LEFTPADDING",   (0, 0), (-1, -1), 10),
#         ("GRID",          (0, 0), (-1, -1), 0.5, MID_GREY),
#     ]))
#     elements.append(t)
#     elements.append(Spacer(1, 6 * mm))
#     return elements


# # ─────────────────────────────────────────────
# # BULLET SECTION (Strengths / Improvements / Suggestions)
# # ─────────────────────────────────────────────
# def build_bullet_section(styles: dict, heading: str, content: str,
#                           bg_color=None) -> list:
#     elements = []
#     elements.append(Paragraph(heading, styles["section_heading"]))
#     elements.append(HRFlowable(width="100%", thickness=1, color=MID_BLUE, spaceAfter=4))

#     lines   = [l.strip() for l in content.split(".") if len(l.strip()) > 5]
#     bullets = [Paragraph(f"• {line}.", styles["bullet"]) for line in lines]

#     if bg_color and bullets:
#         inner = Table([[bullets]], colWidths=[170 * mm])
#         inner.setStyle(TableStyle([
#             ("BACKGROUND",    (0, 0), (-1, -1), bg_color),
#             ("TOPPADDING",    (0, 0), (-1, -1), 8),
#             ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
#             ("LEFTPADDING",   (0, 0), (-1, -1), 10),
#             ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
#             ("BOX",           (0, 0), (-1, -1), 0.5, MID_GREY),
#         ]))
#         elements.append(inner)
#     else:
#         for b in bullets:
#             elements.append(b)

#     elements.append(Spacer(1, 5 * mm))
#     return elements


# # ─────────────────────────────────────────────
# # Q&A BLOCK
# # Shows: Question → User Answer → Score | Feedback → Ideal Answer
# # ─────────────────────────────────────────────
# def build_qa_block(styles: dict, index: int, qa: tuple) -> list:
#     """
#     qa tuple from get_interview_questions():
#     (question_number, difficulty_level, topic, question_text,
#      user_answer, ai_suggested_answer, score, feedback)
#     """
#     _, diff_level, topic, q_text, user_ans, ideal_ans, score, feedback = qa

#     score_val = float(score or 0)
#     s_color   = score_color(score_val)

#     # Score + Feedback row
#     sf_table = Table(
#         [[
#             Paragraph(f"{score_val}/10", styles["score_text"]),
#             Paragraph(
#                 f"<b>Feedback:</b> {str(feedback or 'No feedback available.')}",
#                 styles["feedback_text"]
#             ),
#         ]],
#         colWidths=[22 * mm, 138 * mm]
#     )
#     sf_table.setStyle(TableStyle([
#         ("TEXTCOLOR",     (0, 0), (0, 0), s_color),
#         ("VALIGN",        (0, 0), (-1, -1), "TOP"),
#         ("LEFTPADDING",   (0, 0), (-1, -1), 0),
#         ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
#         ("TOPPADDING",    (0, 0), (-1, -1), 0),
#         ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
#     ]))

#     block = [
#         Paragraph(f"Q{index}:  [{diff_level.upper()}]", styles["q_label"]),
#         Paragraph(str(q_text), styles["q_text"]),
#         Spacer(1, 2 * mm),
#         Paragraph("Answer:", styles["answer_label"]),
#         Paragraph(str(user_ans or "No answer provided."), styles["answer_text"]),
#         Spacer(1, 2 * mm),
#         sf_table,
#     ]

#     # Ideal answer — what it should have been
#     if ideal_ans:
#         block += [
#             Spacer(1, 2 * mm),
#             Paragraph("✦  What the ideal answer should include:", styles["ideal_label"]),
#             Paragraph(str(ideal_ans), styles["ideal_text"]),
#         ]

#     card = Table([[block]], colWidths=[170 * mm])
#     card.setStyle(TableStyle([
#         ("BACKGROUND",    (0, 0), (-1, -1), colors.white),
#         ("BOX",           (0, 0), (-1, -1), 0.75, MID_BLUE),
#         ("TOPPADDING",    (0, 0), (-1, -1), 10),
#         ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
#         ("LEFTPADDING",   (0, 0), (-1, -1), 12),
#         ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
#     ]))

#     return [KeepTogether([card]), Spacer(1, 5 * mm)]


# # ─────────────────────────────────────────────
# # MAIN — generate_pdf()
# # ─────────────────────────────────────────────
# def generate_pdf(interview_id: int) -> bytes:
#     """
#     Generate full evaluation PDF.
#     Returns bytes for st.download_button().
#     """
#     interview = get_interview(interview_id)
#     report    = get_report(interview_id)
#     questions = get_interview_questions(interview_id)

#     if not interview or not report:
#         raise ValueError(f"No data for interview_id={interview_id}")

#     (iid, user_email, resume_text, resume_filename,
#      start_time, end_time, status, total_score) = interview

#     (overall_score, performance_summary,
#      technical_knowledge, communication_skills,
#      problem_solving, project_understanding,
#      strengths, areas_for_improvement,
#      actionable_suggestions, generated_at) = report

#     candidate_name = user_email.split("@")[0].replace(".", " ").title()
#     interview_date = start_time.strftime("%Y-%m-%d %H:%M") if start_time else str(generated_at)

#     scores = {
#         "overall_score":         overall_score,
#         "technical_knowledge":   technical_knowledge,
#         "communication_skills":  communication_skills,
#         "problem_solving":       problem_solving,
#         "project_understanding": project_understanding,
#     }

#     buffer = BytesIO()
#     doc = SimpleDocTemplate(
#         buffer,
#         pagesize     = A4,
#         leftMargin   = 20 * mm,
#         rightMargin  = 20 * mm,
#         topMargin    = 15 * mm,
#         bottomMargin = 20 * mm
#     )

#     styles   = build_styles()
#     elements = []

#     # Page 1
#     elements += build_header(styles, candidate_name, interview_date)
#     elements += build_summary_table(styles, scores)

#     if performance_summary:
#         elements.append(Paragraph("Overall Assessment", styles["section_heading"]))
#         elements.append(HRFlowable(width="100%", thickness=1, color=MID_BLUE, spaceAfter=4))
#         elements.append(Paragraph(str(performance_summary), styles["body"]))
#         elements.append(Spacer(1, 5 * mm))

#     if strengths:
#         elements += build_bullet_section(
#             styles, "Strengths", str(strengths),
#             bg_color=colors.HexColor("#e8f5e9")
#         )
#     if areas_for_improvement:
#         elements += build_bullet_section(
#             styles, "Areas for Improvement", str(areas_for_improvement),
#             bg_color=colors.HexColor("#fff8e1")
#         )
#     if actionable_suggestions:
#         elements += build_bullet_section(
#             styles, "Suggestions", str(actionable_suggestions)
#         )

#     # Page 2+ — Q&A
#     elements.append(PageBreak())
#     elements.append(Paragraph("Interview Questions & Answers", styles["section_heading"]))
#     elements.append(HRFlowable(width="100%", thickness=2, color=DARK_BLUE, spaceAfter=8))
#     elements.append(Spacer(1, 3 * mm))

#     for i, qa in enumerate(questions, 1):
#         elements += build_qa_block(styles, i, qa)

#     # Footer
#     elements.append(Spacer(1, 5 * mm))
#     elements.append(HRFlowable(width="100%", thickness=0.5, color=MID_GREY))
#     elements.append(Spacer(1, 3 * mm))
#     elements.append(Paragraph(
#         f"Generated by Pyspace AI  •  {datetime.now().strftime('%Y-%m-%d %H:%M')}  •  Interview #{interview_id}",
#         styles["footer"]
#     ))

#     doc.build(elements)
#     return buffer.getvalue()