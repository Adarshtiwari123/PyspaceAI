import os
import streamlit as st
from datetime import date

from auth.login import logout_user
from interview.interview_engine import interview_flow
from database.db import get_user_interviews
from utils.resume_parser import extract_resume_text


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_initials(name: str) -> str:
    parts = name.strip().split()
    return "".join([p[0] for p in parts[:2]]).upper()


def get_preparation_level(avg_score: float) -> str:
    if avg_score >= 80:   return "🚀 Interview Ready"
    elif avg_score >= 65: return "⚡ Advanced"
    elif avg_score >= 40: return "📈 Intermediate"
    else:                 return "🌱 Beginner"


def calculate_kpis(interviews: list) -> dict:
    completed = [
        row for row in interviews
        if row[1] == "completed" and row[2] is not None
    ]
    if not completed:
        return {
            "total": len(interviews), "avg": 0.0,
            "best": 0.0, "last": None,
            "delta": None, "level": "🌱 Beginner"
        }
    scores = [round(float(row[2]) * 10, 1) for row in completed]
    avg    = round(sum(scores) / len(scores), 1)
    best   = max(scores)
    delta  = round(scores[0] - scores[1], 1) if len(scores) >= 2 else None
    return {
        "total": len(interviews), "avg": avg, "best": best,
        "last": scores[0], "delta": delta,
        "level": get_preparation_level(avg)
    }


# ─────────────────────────────────────────────
# NAVBAR
# ─────────────────────────────────────────────
def navbar():
    name     = st.session_state.get("user_name", "User")
    initials = get_initials(name)

    col1, col2, col3 = st.columns([2, 4, 1])
    with col1:
        st.markdown("## 🚀 PyspaceAI")
    with col2:
        c1, c2, c3 = st.columns(3)
        if c1.button("Home"):
            st.session_state.page = "home"
            st.session_state.pop("interview_started", None)
            st.rerun()
        if c2.button("History"):
            st.session_state.page = "history"
            st.session_state.pop("interview_started", None)
            st.rerun()
        if c3.button("About"):
            st.session_state.page = "about"
            st.session_state.pop("interview_started", None)
            st.rerun()
    with col3:
        with st.popover(initials):
            st.write("###", name)
            st.write(st.session_state.get("user_email", ""))
            st.divider()
            if st.button("Logout", use_container_width=True):
                logout_user()


# ─────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────
def dashboard_kpi(kpis: dict):
    st.markdown("### 📊 Your Interview Dashboard")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("🎯 Total",        kpis["total"])
    c2.metric("📊 Avg Score",    f"{kpis['avg']}/100"  if kpis["avg"]  else "—")
    c3.metric("🏆 Best Score",   f"{kpis['best']}/100" if kpis["best"] else "—")
    c4.metric("📝 Last",         f"{kpis['last']}/100" if kpis["last"] else "—")
    if kpis["delta"] is not None:
        c5.metric("📈 Improvement",
                  f"+{kpis['delta']}" if kpis["delta"] >= 0 else str(kpis["delta"]),
                  delta=kpis["delta"])
    else:
        c5.metric("📈 Improvement", "—",
                  help="Complete 2+ interviews to see your trend")
    c6.metric("🎓 Level", kpis["level"])


# ─────────────────────────────────────────────
# RESUME UPLOAD
# ─────────────────────────────────────────────
def upload_resume():
    st.subheader("📄 Upload Your Resume to Begin")
    st.caption("LISA will read your resume and tailor every question to your skills.")

    uploaded_file = st.file_uploader("Upload Resume (PDF only)", type=["pdf"])
    if not uploaded_file:
        return

    user_email = st.session_state["user_email"]
    filename   = user_email.replace("@", "_") + "_" + uploaded_file.name
    save_path  = os.path.join("user_resumes", filename)

    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    with st.spinner("LISA is reading your resume..."):
        resume_text = extract_resume_text(save_path)

    if not resume_text or len(resume_text.strip()) < 50:
        st.error("Could not extract text. Please use a text-based PDF, not a scanned image.")
        return

    st.session_state["resume_path"] = save_path
    st.session_state["resume_text"] = resume_text

    word_count = len(resume_text.split())
    st.success(f"✅ Resume uploaded — {word_count} words extracted")

    if st.button("🎤 Start AI Interview", type="primary", use_container_width=True):
        st.session_state["interview_started"] = True
        st.rerun()


# ─────────────────────────────────────────────
# HISTORY PAGE
# ─────────────────────────────────────────────
def history_page(interviews: list):
    st.markdown("### 📋 Interview History")
    if not interviews:
        st.info("No interviews yet. Go to Home and start your first one!")
        return

    for row in interviews:
        iid, status, total_score, start_time, end_time, resume_filename = row
        score_display = (
            f"{round(float(total_score) * 10, 1)}/100"
            if total_score else "—"
        )
        duration = "—"
        if start_time and end_time:
            mins     = int((end_time - start_time).total_seconds() // 60)
            duration = f"{mins} min"
        badge    = {"completed": "✅", "ongoing": "🔄", "abandoned": "❌"}.get(status, "❓")
        date_str = start_time.strftime("%d %b %Y, %H:%M") if start_time else ""

        with st.expander(
            f"{badge}  Interview #{iid}  —  Score: {score_display}  —  {date_str}",
            expanded=False
        ):
            col1, col2, col3 = st.columns(3)
            col1.metric("Score",    score_display)
            col2.metric("Duration", duration)
            col3.metric("Status",   status.title())
            if resume_filename:
                st.caption(f"📄 Resume: {resume_filename}")
            if status == "completed":
                if st.button("📥 Download Report PDF", key=f"pdf_btn_{iid}"):
                    try:
                        from utils.pdf_report import generate_pdf
                        pdf_bytes = generate_pdf(iid)
                        st.download_button(
                            label               = "⬇️ Click to Download",
                            data                = pdf_bytes,
                            file_name           = f"pyspace_report_{iid}.pdf",
                            mime                = "application/pdf",
                            key                 = f"dl_{iid}",
                            use_container_width = True
                        )
                    except Exception as e:
                        st.error(f"Could not generate report: {e}")


# ─────────────────────────────────────────────
# HOME PAGE
# ─────────────────────────────────────────────
def home_page(kpis: dict, user_email: str):

    dashboard_kpi(kpis)
    st.divider()

    # ── Interview already running ────────────
    if st.session_state.get("interview_started"):
        interview_flow()
        return

    # ── Resume already loaded ────────────────
    if st.session_state.get("resume_path") and st.session_state.get("resume_text"):
        fname      = os.path.basename(st.session_state["resume_path"])
        word_count = len(st.session_state["resume_text"].split())
        st.success(f"✅ Resume loaded: `{fname}` — {word_count} words")

        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("🎤 Start AI Interview", type="primary",
                         use_container_width=True):
                st.session_state["interview_started"] = True
                st.rerun()
        with col2:
            if st.button("🔄 Change Resume", use_container_width=True):
                st.session_state.pop("resume_path", None)
                st.session_state.pop("resume_text", None)
                st.rerun()
    else:
        upload_resume()

    # ── How it works ─────────────────────────
    st.divider()
    st.markdown("### 💡 How Pyspace Works")
    c1, c2, c3, c4 = st.columns(4)
    c1.info("**1. Upload Resume**\nLISA reads your skills and projects")
    c2.info("**2. Start Interview**\n3 Easy → 1 Medium → 1 Hard")
    c3.info("**3. Answer by Voice or Text**\nReal-time Whisper transcription")
    c4.info("**4. Get Your Report**\nDetailed PDF with scores and feedback")


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────
def student_dashboard():

    if "page" not in st.session_state:
        st.session_state.page = "home"

    os.makedirs("user_resumes", exist_ok=True)

    user_email = st.session_state.get("user_email", "guest@example.com")
    interviews = []
    kpis       = calculate_kpis(interviews)

    navbar()
    st.divider()

    if st.session_state.page == "home":
        home_page(kpis, user_email)

    elif st.session_state.page == "history":
        history_page(interviews)

    elif st.session_state.page == "about":
        st.title("About PyspaceAI")
        st.markdown("""
        **Pyspace** is an AI-powered mock interview platform built to help
        students and job seekers practice real technical interviews.

        Your interviewer is **LISA** — Learning Intelligent Simulation Assistant —
        who reads your resume, asks adaptive questions, evaluates your answers,
        and generates a detailed PDF report at the end of every session.

        Built with OpenAI GPT-4o-mini, Whisper, Supabase, and Streamlit.

        ---
        **Free Plan:** 1 AI interview per registered account.
        """)
