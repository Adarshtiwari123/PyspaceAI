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
    """Convert average score /100 to preparation tier."""
    if avg_score >= 80:
        return "🚀 Interview Ready"
    elif avg_score >= 65:
        return "⚡ Advanced"
    elif avg_score >= 40:
        return "📈 Intermediate"
    else:
        return "🌱 Beginner"


def calculate_kpis(interviews: list) -> dict:
    """
    Calculate all dashboard KPIs from interview history.
    interviews: list of (id, status, total_score, start_time, end_time, resume_filename)
    Only counts 'completed' interviews with a valid score.
    """
    completed = [
        row for row in interviews
        if row[1] == "completed" and row[2] is not None
    ]

    if not completed:
        return {
            "total": len(interviews),
            "avg":   0.0,
            "best":  0.0,
            "last":  None,
            "delta": None,
            "level": "🌱 Beginner"
        }

    # Scores stored /10 in DB → convert to /100 for display
    scores = [round(float(row[2]) * 10, 1) for row in completed]

    total = len(interviews)
    avg   = round(sum(scores) / len(scores), 1)
    best  = max(scores)
    last  = scores[0]   # most recent first (ORDER BY created_at DESC)

    # Improvement: last vs previous interview
    delta = None
    if len(scores) >= 2:
        delta = round(scores[0] - scores[1], 1)

    return {
        "total": total,
        "avg":   avg,
        "best":  best,
        "last":  last,
        "delta": delta,
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
            pic = st.session_state.get("user_picture", "")
            if pic:
                st.image(pic, width=90)
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

    c1.metric(
        "🎯 Total Interviews",
        kpis["total"]
    )
    c2.metric(
        "📊 Avg Score",
        f"{kpis['avg']}/100" if kpis["avg"] else "—"
    )
    c3.metric(
        "🏆 Best Score",
        f"{kpis['best']}/100" if kpis["best"] else "—"
    )
    c4.metric(
        "📝 Last Interview",
        f"{kpis['last']}/100" if kpis["last"] else "—"
    )

    # Improvement delta with color arrow
    if kpis["delta"] is not None:
        delta_val = kpis["delta"]
        c5.metric(
            "📈 Improvement",
            f"+{delta_val}" if delta_val >= 0 else str(delta_val),
            delta=delta_val
        )
    else:
        c5.metric(
            "📈 Improvement",
            "—",
            help="Complete 2+ interviews to see your trend"
        )

    c6.metric(
        "🎓 Level",
        kpis["level"]
    )


# ─────────────────────────────────────────────
# RESUME UPLOAD + TEXT EXTRACTION
# ─────────────────────────────────────────────
def upload_resume():
    st.subheader("📄 Upload Your Resume to Begin")
    st.caption("LISA will read your resume and tailor every question to your skills and projects.")

    uploaded_file = st.file_uploader(
        "Upload Resume (PDF only)",
        type=["pdf"]
    )

    if not uploaded_file:
        return

    user_email = st.session_state["user_email"]
    filename   = user_email.replace("@", "_") + "_" + uploaded_file.name
    save_path  = os.path.join("user_resumes", filename)

    # Save file to disk
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # ── CRITICAL: Extract text immediately ──
    # Without this, LISA receives None as resume and asks generic questions
    with st.spinner("LISA is reading your resume..."):
        resume_text = extract_resume_text(save_path)

    if not resume_text or len(resume_text.strip()) < 50:
        st.error(
            "Could not extract text from this PDF. "
            "Please make sure it's a text-based PDF, not a scanned image."
        )
        return

    # Store both in session state
    st.session_state["resume_path"] = save_path
    st.session_state["resume_text"] = resume_text

    word_count = len(resume_text.split())
    st.success(f"✅ Resume uploaded — {word_count} words extracted successfully")
    st.caption("LISA has read your resume and is ready to interview you.")

    if st.button("🎤 Start AI Interview", type="primary", use_container_width=True):
        st.session_state["interview_started"] = True
        st.rerun()


# ─────────────────────────────────────────────
# INTERVIEW HISTORY PAGE
# ─────────────────────────────────────────────
def history_page(interviews: list):
    st.markdown("### 📋 Interview History")

    if not interviews:
        st.info("You haven't completed any interviews yet. Go to Home and start your first one!")
        return

    for row in interviews:
        iid, status, total_score, start_time, end_time, resume_filename = row

        # Score /100
        score_display = (
            f"{round(float(total_score) * 10, 1)}/100"
            if total_score else "—"
        )

        # Duration
        duration = "—"
        if start_time and end_time:
            mins     = int((end_time - start_time).total_seconds() // 60)
            duration = f"{mins} min"

        # Status badge
        badge = {
            "completed": "✅",
            "ongoing":   "🔄",
            "abandoned": "❌"
        }.get(status, "❓")

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

            # PDF download only for completed interviews
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
def home_page(kpis: dict):

    # KPI strip
    dashboard_kpi(kpis)
    st.divider()

    # ── Interview already running ────────────
    if st.session_state.get("interview_started"):
        interview_flow()
        return

    # ── Resume already loaded this session ──
    if st.session_state.get("resume_path") and st.session_state.get("resume_text"):
        fname      = os.path.basename(st.session_state["resume_path"])
        word_count = len(st.session_state["resume_text"].split())

        st.success(f"✅ Resume loaded: `{fname}` — {word_count} words")

        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button(
                "🎤 Start AI Interview",
                type                = "primary",
                use_container_width = True
            ):
                st.session_state["interview_started"] = True
                st.rerun()
        with col2:
            if st.button("🔄 Change Resume", use_container_width=True):
                st.session_state.pop("resume_path", None)
                st.session_state.pop("resume_text", None)
                st.rerun()

    else:
        # ── No resume yet ────────────────────
        upload_resume()

    # ── How it works ─────────────────────────
    st.divider()
    st.markdown("### 💡 How Pyspace Works")
    c1, c2, c3, c4 = st.columns(4)
    c1.info("**1. Upload Resume**\nLISA reads your skills and projects to tailor questions")
    c2.info("**2. Start Interview**\n4 Easy → 3 Medium → 3 Hard + Adaptive follow-ups")
    c3.info("**3. Answer by Voice or Text**\nReal-time transcription powered by Whisper")
    c4.info("**4. Get Your Report**\nDetailed PDF with scores, feedback and ideal answers")


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# Called from app.py
# ─────────────────────────────────────────────
def student_dashboard():

    if not st.session_state.get("logged_in"):
        st.error("Please login first.")
        return

    # Init page
    if "page" not in st.session_state:
        st.session_state.page = "home"

    # Ensure resume folder exists
    os.makedirs("user_resumes", exist_ok=True)

    # Fetch history + calculate KPIs
    user_email = st.session_state["user_email"]
    interviews = get_user_interviews(user_email)
    kpis       = calculate_kpis(interviews)

    # Render
    navbar()
    st.divider()

    if st.session_state.page == "home":
        home_page(kpis)

    elif st.session_state.page == "history":
        history_page(interviews)

    elif st.session_state.page == "about":
        st.title("About PyspaceAI")
        st.markdown("""
        **Pyspace** is an AI-powered mock interview platform built to help students
        and job seekers practice real technical interviews.

        Your interviewer is **LISA** — Learning Intelligent Simulation Assistant —
        who reads your resume, asks adaptive questions, evaluates your answers,
        and generates a detailed PDF report at the end of every session.

        Built with OpenAI GPT-4o-mini, Whisper, Supabase, and Streamlit.
        """)

# import streamlit as st
# from datetime import date
# from auth.google_login import logout_user
# from interview.interview_engine import interview_flow
# import os

# def get_initials(name):

#     parts = name.split()
#     initials = "".join([p[0] for p in parts[:2]])

#     return initials.upper()


# def navbar():

#     name = st.session_state["user_name"]
#     initials = get_initials(name)

#     col1, col2, col3 = st.columns([2,4,1])

#     with col1:
#         st.markdown("## 🚀 PyspaceAI")

#     with col2:

#         c1,c2,c3 = st.columns(3)

#         if c1.button("Home"):
#             st.session_state.page = "home"

#         if c2.button("About"):
#             st.session_state.page = "about"

#         if c3.button("Contact"):
#             st.session_state.page = "contact"

#     with col3:

#         with st.popover(initials):

#             st.image(st.session_state["user_picture"], width=90)

#             st.write("###", st.session_state["user_name"])
#             st.write(st.session_state["user_email"])

#             if st.button("Logout"):
#                 logout_user()


# def dashboard_kpi():

#     today = date.today().strftime("%d %B %Y")

#     st.markdown("### 📊 Interview Dashboard")

#     c1, c2, c3, c4 = st.columns(4)

#     c1.metric("Interviews", "0")
#     c2.metric("Preparation Level", "Beginner")
#     c3.metric("Average Score", "0%")
#     c4.metric("Today", today)


# # def interview_button():

# #     st.divider()

# #     if "interview_started" not in st.session_state:
# #         st.session_state.interview_started = False

# #     if st.button("🎤 Start Interview", use_container_width=True):

# #         st.session_state.interview_started = True
# #         st.rerun()
# def interview_button():

#     st.divider()

#     if "resume_path" not in st.session_state:

#         upload_resume()

#     else:

#         if st.button("🎤 Continue Interview", use_container_width=True):

#             st.session_state.interview_started = True
#             st.rerun()

# def upload_resume():

#     st.subheader("📄 Upload Your Resume")

#     uploaded_file = st.file_uploader(
#         "Upload Resume (PDF or DOCX)",
#         type=["pdf", "docx"]
#     )

#     if uploaded_file:

#         user_email = st.session_state["user_email"]

#         filename = user_email.replace("@","_") + "_" + uploaded_file.name

#         save_path = os.path.join("user_resumes", filename)

#         with open(save_path, "wb") as f:
#             f.write(uploaded_file.getbuffer())

#         st.session_state.resume_path = save_path

#         st.success("Resume uploaded successfully ✅")

#         if st.button("Start AI Interview"):

#             st.session_state.interview_started = True
#             st.rerun()

# def student_dashboard():

#     if "logged_in" not in st.session_state:
#         st.error("Login required")
#         return

#     if "page" not in st.session_state:
#         st.session_state.page = "home"

#     navbar()

#     if st.session_state.page == "home":

#         dashboard_kpi()

#         interview_button()

#         if st.session_state.get("interview_started"):

#             interview_flow()

#     elif st.session_state.page == "about":

#         st.title("About PyspaceAI")
#         st.write("AI Interview practice platform powered by Gemini.")

#     elif st.session_state.page == "contact":

#         st.title("Contact Us")
#         st.write("Email: support@pyspace.ai")



# # import streamlit as st
# # from datetime import date
# # import pyttsx3
# # from auth.google_login import logout_user

# # # ---------------------------------------------------
# # # CREATE INITIALS FOR PROFILE AVATAR
# # # ---------------------------------------------------
# # def get_initials(name):

# #     parts = name.split()

# #     initials = "".join([p[0] for p in parts[:2]])

# #     return initials.upper()


# # # ---------------------------------------------------
# # # NAVBAR
# # # ---------------------------------------------------
# # # ---------------------------------------------------
# # # NAVBAR
# # # ---------------------------------------------------
# # def navbar():

# #     name = st.session_state["user_name"]
# #     initials = get_initials(name)

# #     col1, col2, col3 = st.columns([2,4,1])

# #     with col1:
# #         st.markdown("## 🚀 PyspaceAI")

# #     with col2:

# #         c1,c2,c3 = st.columns(3)

# #         with c1:
# #             if st.button("Home"):
# #                 st.session_state.page = "home"

# #         with c2:
# #             if st.button("About"):
# #                 st.session_state.page = "about"

# #         with c3:
# #             if st.button("Contact"):
# #                 st.session_state.page = "contact"

# #     with col3:

# #         with st.popover(initials):

# #             st.image(st.session_state["user_picture"], width=90)

# #             st.write("###", st.session_state["user_name"])
# #             st.write(st.session_state["user_email"])

# #             if st.button("Logout"):
# #                 logout_user()

# # # ---------------------------------------------------
# # # PROFILE CARD
# # # ---------------------------------------------------
# # def profile_card():

# #     with st.popover("Profile"):

# #         st.image(st.session_state["user_picture"], width=80)

# #         st.write("###", st.session_state["user_name"])
# #         st.write(st.session_state["user_email"])

# #         if st.button("Logout"):
# #             logout_user()


# # # ---------------------------------------------------
# # # KPI DASHBOARD
# # # ---------------------------------------------------
# # def dashboard_kpi():

# #     today = date.today().strftime("%d %B %Y")

# #     st.markdown("### 📊 Interview Dashboard")

# #     c1, c2, c3, c4 = st.columns(4)

# #     c1.metric("Interviews", "0")
# #     c2.metric("Preparation Level", "Beginner")
# #     c3.metric("Average Score", "0%")
# #     c4.metric("Today", today)
# # # ---------------------------------------------------
# # # LISA CHAT
# # # ---------------------------------------------------

# # # ---------------------------------------------------
# # # LISA VOICE
# # # ---------------------------------------------------
# # def lisa_voice(text):

# #     engine = pyttsx3.init()

# #     engine.setProperty('rate', 170)

# #     engine.say(text)

# #     engine.runAndWait()

# # def lisa_chat():

# #     if not st.session_state.get("interview_started"):
# #         return

# #     username = st.session_state["user_name"]

# #     st.markdown("### 🤖 LISA Interview")

# #     if "messages" not in st.session_state:

# #         first_message = f"Hi {username}, can we start your interview?"

# #         st.session_state.messages = [
# #             {"role":"assistant","content":first_message}
# #         ]

        

# #     for msg in st.session_state.messages:

# #         with st.chat_message(msg["role"]):
# #             st.write(msg["content"])

# #     prompt = st.chat_input("Type your answer...")

# #     if prompt:

# #         st.session_state.messages.append(
# #             {"role":"user","content":prompt}
# #         )

# #         with st.chat_message("user"):
# #             st.write(prompt)

# #         response = "Great answer. Let's move to the next question."

# #         with st.chat_message("assistant"):
# #             st.write(response)

# #         st.session_state.messages.append(
# #             {"role":"assistant","content":response}
# #         )
# #         lisa_voice(first_message)
# # def interview_button():

# #     st.divider()

# #     if "interview_started" not in st.session_state:
# #         st.session_state.interview_started = False

# #     if st.button("🎤 Start Interview", use_container_width=True):

# #         st.session_state.interview_started = True
# # # ---------------------------------------------------
# # # LISA RESPONSE (TEMP)
# # # ---------------------------------------------------
# # def lisa_response(prompt):

# #     if "interview" in prompt.lower():
# #         return "Hello 👋 I'm LISA. Click **Start Interview** to begin."

# #     return "Hi! I'm LISA, your AI interview assistant."


# # # ---------------------------------------------------
# # # MAIN DASHBOARD
# # # ---------------------------------------------------
# # def student_dashboard():

# #     if "logged_in" not in st.session_state:
# #         st.error("Login required")
# #         return

# #     if "page" not in st.session_state:
# #         st.session_state.page = "home"

# #     navbar()

# #     if st.session_state.page == "home":

# #         dashboard_kpi()

# #         interview_button()

# #         lisa_chat()

# #     elif st.session_state.page == "about":

# #         st.title("About PyspaceAI")
# #         st.write("AI Interview practice platform.")

# #     elif st.session_state.page == "contact":

# #         st.title("Contact Us")
# #         st.write("Email: support@pyspace.ai")