import os
import time
import streamlit as st

from interview.lisa_ai import generate_question, evaluate_answer, generate_session_feedback
from interview.scoring import (
    should_trigger_adaptive,
    calculate_total_score,
    calculate_skill_scores,
    generate_performance_summary
)
from database.db import (
    create_interview,
    save_question,
    complete_interview,
    save_report,
    get_interview_questions
)
from config import QUESTIONS_PER_LEVEL, INTRO_QUESTION
from assets.interview_style import (
    inject_interview_styles,
    show_typing_indicator,
    stage_badge,
    strip_emojis,
    now_time,
    LISA_AVATAR_PATH,
    STAGE_LABELS_CLEAN
)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
STAGES       = ["easy", "medium", "hard"]
TIME_LIMIT   = 30 * 60   # 30 minutes
BASE_Q_COUNT = sum(QUESTIONS_PER_LEVEL.values())   # 10

# Words per second for typewriter — matches gTTS speed
WORDS_PER_SECOND = 2.2


# ─────────────────────────────────────────────
# TYPEWRITER GENERATOR
# ─────────────────────────────────────────────
def typewriter_stream(text: str, wps: float = WORDS_PER_SECOND):
    words = text.split()
    delay = 1.0 / wps
    for word in words:
        yield word + " "
        time.sleep(delay)


# ─────────────────────────────────────────────
# PLAY LISA VOICE — browser Web Speech API
# No MP3 files. No disk writes. No gTTS.
# ─────────────────────────────────────────────
def play_lisa_voice(text: str) -> bool:
    try:
        from utils.text_to_speech import speak
        speak(text)
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
def init_interview():
    if st.session_state.get("interview_initialized"):
        return

    st.session_state.interview_initialized = True
    st.session_state.interview_id          = None
    st.session_state.interview_stage       = "easy"
    st.session_state.stage_q_index         = 0
    st.session_state.total_q_index         = 0
    st.session_state.current_question      = None
    st.session_state.current_level         = "easy"
    st.session_state.qa_history            = []
    st.session_state.asked_questions       = set()   # ← prevent duplicates
    st.session_state.adaptive_mode         = False
    st.session_state.adaptive_direction    = ""
    st.session_state.interview_complete    = False
    st.session_state.interview_finalized   = False
    st.session_state.start_time            = time.time()
    st.session_state.question_displayed    = False
    st.session_state.question_time         = now_time()


# ─────────────────────────────────────────────
# RESUME
# ─────────────────────────────────────────────
def get_resume_text() -> str:
    if st.session_state.get("resume_text"):
        return st.session_state.resume_text
    resume_path = st.session_state.get("resume_path")
    if resume_path and os.path.exists(resume_path):
        from utils.resume_parser import extract_resume_text
        text = extract_resume_text(resume_path)
        st.session_state.resume_text = text
        return text
    return "No resume provided."


# ─────────────────────────────────────────────
# QUESTION GENERATION — with duplicate prevention
# ─────────────────────────────────────────────
def get_next_question(resume_text: str) -> tuple[str, str]:
    total_index = st.session_state.total_q_index
    last_qa     = st.session_state.qa_history[-1] if st.session_state.qa_history else {}
    asked       = st.session_state.asked_questions   # this session

    if total_index == 0:
        return INTRO_QUESTION, "easy"

    # ── Cross-session dedup: load ALL past questions for this user ──
    # Prevents repeat questions if user runs interview again
    all_asked = list(asked)
    try:
        from database.db import get_all_user_questions
        past = get_all_user_questions(st.session_state.get("user_email", ""))
        # past is list of question_text strings
        all_asked = list(set(all_asked + past))
    except Exception:
        pass   # silently fallback to session-only dedup

    asked_context = all_asked[-16:] if all_asked else []

    if st.session_state.adaptive_mode:
        question = generate_question(
            level           = "adaptive",
            resume          = resume_text,
            previous_answer = last_qa.get("answer", ""),
            previous_score  = last_qa.get("score", 5.0),
            asked_questions = asked_context
        )
        return question, "adaptive"

    stage    = st.session_state.interview_stage
    question = generate_question(
        level           = stage,
        resume          = resume_text,
        previous_answer = last_qa.get("answer"),
        previous_score  = last_qa.get("score"),
        asked_questions = asked_context
    )
    return question, stage


# ─────────────────────────────────────────────
# STAGE PROGRESSION
# ─────────────────────────────────────────────
def advance_stage():
    current = st.session_state.interview_stage
    idx     = STAGES.index(current)
    if idx + 1 < len(STAGES):
        st.session_state.interview_stage = STAGES[idx + 1]
        st.session_state.stage_q_index  = 0
    else:
        st.session_state.interview_complete = True


def time_expired() -> bool:
    return (time.time() - st.session_state.start_time) >= TIME_LIMIT


# ─────────────────────────────────────────────
# HANDLE ANSWER
# ─────────────────────────────────────────────
def handle_answer(answer: str, resume_text: str):
    question = st.session_state.current_question
    level    = st.session_state.current_level

    # Evaluate silently — score hidden from chat
    with st.spinner("LISA is reviewing your answer..."):
        evaluation = evaluate_answer(question, answer)

    score        = evaluation["score"]
    ideal_answer = evaluation["ideal_answer"]
    feedback     = evaluation["feedback"]

    # Save to DB
    save_question(
        interview_id        = st.session_state.interview_id,
        question_number     = st.session_state.total_q_index + 1,
        difficulty_level    = level,
        topic               = None,
        question_text       = question,
        user_answer         = answer,
        ai_suggested_answer = ideal_answer,
        score               = score,
        feedback            = feedback
    )

    # Store in history
    st.session_state.qa_history.append({
        "question":     question,
        "answer":       answer,
        "score":        score,
        "feedback":     feedback,
        "ideal_answer": ideal_answer,
        "level":        level,
        "timestamp":    now_time()
    })

    st.session_state.total_q_index     += 1
    st.session_state.question_displayed = False

    # Adaptive trigger
    if not st.session_state.adaptive_mode and level in ["medium", "hard"]:
        trigger, direction = should_trigger_adaptive(level, score)
        if trigger:
            st.session_state.adaptive_mode      = True
            st.session_state.adaptive_direction = direction
            st.session_state.current_question   = None
            st.rerun()
            return

    st.session_state.adaptive_mode      = False
    st.session_state.adaptive_direction = ""

    # Advance stage
    st.session_state.stage_q_index += 1
    stage = st.session_state.interview_stage
    if st.session_state.stage_q_index >= QUESTIONS_PER_LEVEL.get(stage, 3):
        advance_stage()

    st.session_state.current_question = None
    st.rerun()


# ─────────────────────────────────────────────
# FINALIZE
# ─────────────────────────────────────────────
def finalize_interview():
    qa_history = st.session_state.qa_history
    if not qa_history:
        return

    questions_scored = [
        {
            "difficulty_level": q["level"],
            "score":            q["score"],
            "topic":            "",
            "question_text":    q["question"]
        }
        for q in qa_history
    ]

    total_score         = calculate_total_score(questions_scored)
    skill_scores        = calculate_skill_scores(questions_scored)
    performance_summary = generate_performance_summary(total_score, skill_scores)

    qa_pairs = [
        {"question": q["question"], "user_answer": q["answer"], "score": q["score"]}
        for q in qa_history
    ]

    with st.spinner("LISA is generating your full evaluation report..."):
        ai_feedback = generate_session_feedback(qa_pairs)

    complete_interview(st.session_state.interview_id, total_score)

    save_report(
        interview_id           = st.session_state.interview_id,
        overall_score          = total_score,
        performance_summary    = performance_summary,
        technical_knowledge    = skill_scores["technical_knowledge"],
        communication_skills   = skill_scores["communication_skills"],
        problem_solving        = skill_scores["problem_solving"],
        project_understanding  = skill_scores["project_understanding"],
        strengths              = ai_feedback["strengths"],
        areas_for_improvement  = ai_feedback["improvements"],
        actionable_suggestions = ai_feedback["study_plan"],
        report_pdf             = b""
    )

    st.session_state.final_score         = total_score
    st.session_state.skill_scores        = skill_scores
    st.session_state.ai_feedback         = ai_feedback
    st.session_state.performance_summary = performance_summary
    st.session_state.interview_finalized = True


# ─────────────────────────────────────────────
# RESULTS SCREEN
# ─────────────────────────────────────────────
def show_results():
    score        = st.session_state.get("final_score", 0)
    skill_scores = st.session_state.get("skill_scores", {})
    feedback     = st.session_state.get("ai_feedback", {})
    name         = (st.session_state.get("user_name", "") or "Friend").split()[0]

    def to_25(v):  return round(float(v or 0) * 2.5, 1)
    def to_100(v): return round(float(v or 0) * 10.0, 1)

    score_100 = to_100(score)

    # Grade
    if score_100 >= 85:
        grade, gc = "Excellent",  "#10b981"
        grade_msg  = "You're genuinely interview-ready."
        motive     = (f"Incredible performance, {name}! You demonstrated real "
                      f"depth and clarity across every area today. Your "
                      f"preparation clearly shows — walk into your next "
                      f"interview with full confidence. You've earned it. "
                      f"Wishing you every success in your career ahead!")
    elif score_100 >= 70:
        grade, gc = "Strong",     "#3b82f6"
        grade_msg  = "A few more rounds and you'll be there."
        motive     = (f"Great work, {name}! You showed solid understanding and "
                      f"real potential today. A little more focused practice on "
                      f"the areas highlighted below and you'll be unstoppable. "
                      f"Keep going — your next interview is going to be even "
                      f"better. Believe in yourself!")
    elif score_100 >= 55:
        grade, gc = "Developing", "#f59e0b"
        grade_msg  = "Solid base — the gaps are fixable with focused prep."
        motive     = (f"Well done for showing up and giving it your best, "
                      f"{name}! You have a strong foundation to build on. "
                      f"Every gap you see in this report is just an opportunity "
                      f"waiting for you. Stay consistent, use your study plan, "
                      f"and you'll get there. Rooting for you all the way!")
    else:
        grade, gc = "Needs Work", "#ef4444"
        grade_msg  = "Every expert started here — use this report as your roadmap."
        motive     = (f"Thank you for completing this interview, {name}! "
                      f"This took courage, and that matters. Every professional "
                      f"you admire once sat exactly where you are right now. "
                      f"This report is your personal roadmap — follow it step "
                      f"by step and your progress will surprise you. "
                      f"We believe in you. Keep pushing!")

    # ── Hero ──────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0f172a,#1e1b4b);
                border:1px solid #312e81;border-radius:20px;
                padding:36px;text-align:center;margin-bottom:24px;">
        <div style="font-size:12px;color:#64748b;letter-spacing:2px;
                    text-transform:uppercase;margin-bottom:10px;">
            Interview Complete — Session #{st.session_state.interview_id}
        </div>
        <div style="font-size:60px;font-weight:900;color:#f0f4ff;
                    letter-spacing:-2px;line-height:1;">
            {score_100}<span style="font-size:22px;color:#475569;
            font-weight:400;">/100</span>
        </div>
        <div style="font-size:20px;font-weight:700;color:{gc};
                    margin:12px 0 6px;">{grade}</div>
        <div style="font-size:14px;color:#64748b;">{grade_msg}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── LISA Motivation — always shown ────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0f2a1e,#064e3b);
                border:1px solid #065f46;border-radius:14px;
                padding:22px 26px;margin-bottom:24px;">
        <div style="font-size:11px;color:#34d399;font-weight:700;
                    letter-spacing:1.5px;text-transform:uppercase;
                    margin-bottom:10px;">A Personal Note from LISA</div>
        <div style="color:#d1fae5;font-size:15px;line-height:1.8;
                    font-style:italic;">"{motive}"</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Skill Breakdown — ALL in one st.markdown call ────────────
    tech = to_25(skill_scores.get("technical_knowledge",   0))
    comm = to_25(skill_scores.get("communication_skills",  0))
    prob = to_25(skill_scores.get("problem_solving",       0))
    proj = to_25(skill_scores.get("project_understanding", 0))

    def skill_bar_html(label, val, max_val=25):
        pct   = int((val / max_val) * 100) if max_val else 0
        color = "#10b981" if pct >= 70 else "#f59e0b" if pct >= 50 else "#ef4444"
        level = "Strong" if pct >= 70 else "Building" if pct >= 50 else "Focus Here"
        return (
            f'<div style="margin-bottom:18px;">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:6px;">'
            f'<span style="color:#e2e8f0;font-size:14px;font-weight:600;">{label}</span>'
            f'<span style="color:{color};font-size:13px;font-weight:700;">'
            f'{val}/25 &nbsp;·&nbsp; {level}</span>'
            f'</div>'
            f'<div style="background:#1e293b;border-radius:6px;height:9px;">'
            f'<div style="background:{color};width:{pct}%;height:9px;border-radius:6px;"></div>'
            f'</div>'
            f'</div>'
        )

    # ONE single st.markdown call — open div, all bars, close div together
    st.markdown(f"""
    <div style="background:#111827;border:1px solid #1e2d47;
                border-radius:16px;padding:24px;margin-bottom:20px;">
        <div style="font-size:12px;font-weight:700;color:#00d4ff;
                    letter-spacing:1.5px;text-transform:uppercase;
                    margin-bottom:20px;">Skill Breakdown</div>
        {skill_bar_html("Technical Knowledge",   tech)}
        {skill_bar_html("Communication Skills",  comm)}
        {skill_bar_html("Problem Solving",       prob)}
        {skill_bar_html("Project Understanding", proj)}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Strengths + Improvements ──────────────
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        <div style="font-size:12px;font-weight:700;color:#10b981;
                    letter-spacing:1px;text-transform:uppercase;
                    margin-bottom:6px;">What You Did Well</div>
        """, unsafe_allow_html=True)
        if feedback.get("strengths"):
            st.success(feedback["strengths"])
        else:
            st.success("You completed the interview — that takes real commitment.")

    with col_b:
        st.markdown("""
        <div style="font-size:12px;font-weight:700;color:#f59e0b;
                    letter-spacing:1px;text-transform:uppercase;
                    margin-bottom:6px;">Where to Focus Next</div>
        """, unsafe_allow_html=True)
        if feedback.get("improvements"):
            st.warning(feedback["improvements"])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Study Plan ────────────────────────────
    if feedback.get("study_plan"):
        study = feedback["study_plan"]
        topics = [t.strip() for t in study.split(",") if t.strip()] or [study]
        rows   = "".join([
            f'<div style="display:flex;align-items:flex-start;gap:12px;'
            f'padding:10px 0;border-bottom:1px solid #1e293b;">'
            f'<span style="color:#00d4ff;font-weight:700;">→</span>'
            f'<span style="color:#e2e8f0;font-size:14px;">{t}</span></div>'
            for t in topics
        ])
        st.markdown(
            f'<div style="background:#111827;border:1px solid #1e2d47;'
            f'border-radius:16px;padding:20px;margin-bottom:20px;">'
            f'<div style="font-size:12px;font-weight:700;color:#00d4ff;'
            f'letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;">'
            f'Your Personalised Study Plan</div>'
            f'<div style="font-size:12px;color:#374151;margin-bottom:12px;">'
            f'Master these before your next interview</div>'
            f'{rows}</div>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Buttons ───────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Download Full PDF Report", type="primary",
                     use_container_width=True):
            try:
                from utils.pdf_report import generate_pdf
                pdf_bytes = generate_pdf(st.session_state.interview_id)
                st.download_button(
                    label               = "Click to Download PDF",
                    data                = pdf_bytes,
                    file_name           = f"pyspace_report_{st.session_state.interview_id}.pdf",
                    mime                = "application/pdf",
                    use_container_width = True
                )
            except Exception as e:
                st.error(f"PDF generation failed: {e}")
    with c2:
        if st.button("Start New Interview", use_container_width=True):
            keys = [
                "interview_initialized", "interview_id", "interview_stage",
                "stage_q_index", "total_q_index", "current_question", "current_level",
                "qa_history", "asked_questions", "adaptive_mode", "adaptive_direction",
                "interview_complete", "interview_finalized", "start_time", "final_score",
                "skill_scores", "ai_feedback", "performance_summary", "interview_started",
                "resume_path", "resume_text", "question_displayed", "question_time"
            ]
            for k in keys:
                st.session_state.pop(k, None)
            st.rerun()


# ─────────────────────────────────────────────
# MAIN INTERVIEW FLOW
# ─────────────────────────────────────────────
def interview_flow():

    # 1. Dark theme + styles
    inject_interview_styles()

    # 2. Init
    init_interview()
    resume_text = get_resume_text()

    # 3. Create DB record once
    if st.session_state.interview_id is None:
        filename = os.path.basename(st.session_state.get("resume_path", "unknown"))
        st.session_state.interview_id = create_interview(
            user_email      = st.session_state["user_email"],
            resume_text     = resume_text,
            resume_filename = filename
        )

    # 4. Results / finalize check
    if st.session_state.get("interview_finalized"):
        show_results()
        return

    if st.session_state.interview_complete or time_expired():
        finalize_interview()
        st.rerun()
        return

    # ── HEADER ──────────────────────────────────────────────────
    elapsed    = int(time.time() - st.session_state.start_time)
    mins, secs = divmod(elapsed, 60)
    remaining  = max(0, TIME_LIMIT - elapsed)
    rem_m, rem_s = divmod(remaining, 60)

    total_done  = st.session_state.total_q_index
    # Total expected = base 10 + any adaptive questions fired so far
    total_exp   = max(BASE_Q_COUNT, total_done + 1)
    progress    = min(total_done / BASE_Q_COUNT, 1.0)
    stage       = st.session_state.interview_stage
    stage_label = STAGE_LABELS_CLEAN.get(stage, stage.title())

    h1, h2, h3, h4 = st.columns([4, 1, 1, 1])
    with h1:
        st.progress(
            progress,
            text=f"{stage_label} Stage  ·  Question {total_done + 1}"
        )
    with h2:
        st.metric("Elapsed", f"{mins:02d}:{secs:02d}")
    with h3:
        st.metric("Remaining", f"{rem_m:02d}:{rem_s:02d}")
    with h4:
        if st.button("End Interview", type="secondary"):
            st.session_state.interview_complete = True
            st.rerun()

    st.divider()

    # ── CONVERSATION HISTORY ─────────────────────────────────────
    for i, qa in enumerate(st.session_state.qa_history, 1):

        # LISA bubble
        with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
            st.markdown(
                f'<span style="font-size:11px;font-weight:700;color:#00d4ff;">'
                f'LISA &nbsp;•&nbsp; AI Interviewer</span>'
                f'{stage_badge(qa["level"])}',
                unsafe_allow_html=True
            )
            st.markdown(strip_emojis(qa["question"]))
            st.caption(qa.get("timestamp", ""))

        # User bubble — dark card matching LISA style
        st.markdown(f"""
        <div style="
            background: #0f1f3d;
            border: 1px solid #1e3a6e;
            border-radius: 16px 0 16px 16px;
            padding: 16px 20px;
            max-width: 76%;
            margin-left: auto;
            margin-right: 0;
            margin-bottom: 12px;
            box-shadow: 0 0 20px rgba(37,99,235,0.08);
        ">
            <span style="font-size:11px;font-weight:700;color:#60a5fa;">
                {st.session_state.get("user_name", "You")}
            </span>
            <span style="font-size:11px;color:#1e3a6e;margin-left:8px;">
                {qa.get("timestamp", "")}
            </span>
            <div style="color:#dbeafe;font-size:15px;
                        line-height:1.7;margin-top:8px;">
                {qa["answer"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── GENERATE CURRENT QUESTION ─────────────────────────────────
    if st.session_state.current_question is None:
        with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
            show_typing_indicator()

        question, level = get_next_question(resume_text)

        # Track to prevent duplicates
        st.session_state.asked_questions.add(question.strip().lower()[:80])

        st.session_state.current_question   = question
        st.session_state.current_level      = level
        st.session_state.question_displayed = False
        st.session_state.question_time      = now_time()
        st.rerun()

    question = st.session_state.current_question
    level    = st.session_state.current_level

    # ── ADAPTIVE BANNER ───────────────────────────────────────────
    if st.session_state.adaptive_mode:
        d   = st.session_state.adaptive_direction
        msg = (
            "Let me rephrase that — I want to make sure we cover this concept."
            if d == "easier"
            else "Strong response. Let me take this a level deeper."
        )
        st.markdown(
            f'<div style="background:#0f172a;border-left:3px solid #6366f1;'
            f'border-radius:0 8px 8px 0;padding:10px 16px;margin:8px 0;'
            f'font-size:13px;color:#a5b4fc;">LISA — {msg}</div>',
            unsafe_allow_html=True
        )

    # ── LISA QUESTION BUBBLE ──────────────────────────────────────
    with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
        st.markdown(
            f'<span style="font-size:11px;font-weight:700;color:#00d4ff;">'
            f'LISA &nbsp;•&nbsp; AI Interviewer</span>'
            f'{stage_badge(level)}'
            f'<span style="font-size:11px;color:#374151;margin-left:8px;">'
            f'Question {total_done + 1}</span>',
            unsafe_allow_html=True
        )

        clean_q = strip_emojis(question)

        if not st.session_state.question_displayed:
            # ── VOICE plays first (hidden) ──
            play_lisa_voice(clean_q)
            # ── TYPEWRITER runs simultaneously ──
            st.write_stream(typewriter_stream(clean_q, WORDS_PER_SECOND))
            st.session_state.question_displayed = True
        else:
            st.markdown(clean_q)

        st.caption(st.session_state.get("question_time", now_time()))

    # ── USER INPUT ────────────────────────────────────────────────
    user_name = st.session_state.get("user_name", "You")

    # ── helper: render answer as dark card matching LISA bubble ──
    def show_user_bubble(text: str):
        st.markdown(f"""
        <div style="
            background: #0f1f3d;
            border: 1px solid #1e3a6e;
            border-radius: 16px 0 16px 16px;
            padding: 16px 20px;
            max-width: 76%;
            margin-left: auto;
            margin-right: 0;
            margin-bottom: 8px;
            box-shadow: 0 0 20px rgba(37,99,235,0.08);
        ">
            <span style="font-size:11px;font-weight:700;color:#60a5fa;">
                {user_name}
            </span>
            <span style="font-size:11px;color:#1e3a6e;margin-left:8px;">
                {now_time()}
            </span>
            <div style="color:#dbeafe;font-size:15px;
                        line-height:1.7;margin-top:8px;">
                {text}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Step 1 — voice transcribed in previous run → show bubble + submit
    prefill = st.session_state.pop(f"prefill_{total_done}", None)
    if prefill:
        show_user_bubble(prefill)
        handle_answer(prefill, resume_text)
        return

    # Step 2 — mic widget
    audio_input = st.audio_input(
        "Hold to record your answer",
        key              = f"voice_{total_done}",
        label_visibility = "collapsed"
    )

    if audio_input:
        with st.spinner("Transcribing..."):
            from utils.speech_to_text import transcribe_audio_debug
            transcribed, debug_msg = transcribe_audio_debug(audio_input)

        if transcribed and transcribed.strip():
            st.session_state[f"prefill_{total_done}"] = transcribed.strip()
            st.rerun()
        else:
            st.markdown(f"""
            <div style="
                background:#1a0a0a;border:1px solid #7f1d1d;
                border-radius:10px;padding:12px 16px;margin:8px 0;
                color:#fca5a5;font-size:13px;">
                ⚠️ Could not transcribe: <b>{debug_msg}</b><br>
                <span style="color:#6b7280;font-size:12px;">
                    Please type your answer in the box below.
                </span>
            </div>
            """, unsafe_allow_html=True)

    # Step 3 — chat_input pinned at bottom
    typed = st.chat_input(
        "Type your answer and press Enter  (or use mic above)",
        key = f"chat_{total_done}"
    )
    if typed:
        answer = typed.strip()
        if not answer:
            return
        if answer.lower() == "/skip":
            answer = "I am not sure about this question."
        show_user_bubble(answer)
        handle_answer(answer, resume_text)


# import os
# import time
# import streamlit as st

# from interview.lisa_ai import generate_question, evaluate_answer, generate_session_feedback
# from interview.scoring import (
#     should_trigger_adaptive,
#     calculate_total_score,
#     calculate_skill_scores,
#     generate_performance_summary
# )
# from database.db import (
#     create_interview,
#     save_question,
#     complete_interview,
#     save_report,
#     get_interview_questions
# )
# from config import QUESTIONS_PER_LEVEL, INTRO_QUESTION
# from assets.interview_style import (
#     inject_interview_styles,
#     show_typing_indicator,
#     stage_badge,
#     strip_emojis,
#     now_time,
#     LISA_AVATAR_PATH,
#     STAGE_LABELS_CLEAN
# )

# # ─────────────────────────────────────────────
# # CONSTANTS
# # ─────────────────────────────────────────────
# STAGES       = ["easy", "medium", "hard"]
# TIME_LIMIT   = 30 * 60   # 30 minutes
# BASE_Q_COUNT = sum(QUESTIONS_PER_LEVEL.values())   # 10

# # Words per second for typewriter — matches gTTS speed
# WORDS_PER_SECOND = 2.2


# # ─────────────────────────────────────────────
# # TYPEWRITER GENERATOR
# # ─────────────────────────────────────────────
# def typewriter_stream(text: str, wps: float = WORDS_PER_SECOND):
#     words = text.split()
#     delay = 1.0 / wps
#     for word in words:
#         yield word + " "
#         time.sleep(delay)


# # ─────────────────────────────────────────────
# # PLAY LISA VOICE — browser Web Speech API
# # No MP3 files. No disk writes. No gTTS.
# # ─────────────────────────────────────────────
# def play_lisa_voice(text: str) -> bool:
#     try:
#         from utils.text_to_speech import speak
#         speak(text)
#         return True
#     except Exception:
#         return False


# # ─────────────────────────────────────────────
# # SESSION STATE INIT
# # ─────────────────────────────────────────────
# def init_interview():
#     if st.session_state.get("interview_initialized"):
#         return

#     st.session_state.interview_initialized = True
#     st.session_state.interview_id          = None
#     st.session_state.interview_stage       = "easy"
#     st.session_state.stage_q_index         = 0
#     st.session_state.total_q_index         = 0
#     st.session_state.current_question      = None
#     st.session_state.current_level         = "easy"
#     st.session_state.qa_history            = []
#     st.session_state.asked_questions       = set()   # ← prevent duplicates
#     st.session_state.adaptive_mode         = False
#     st.session_state.adaptive_direction    = ""
#     st.session_state.interview_complete    = False
#     st.session_state.interview_finalized   = False
#     st.session_state.start_time            = time.time()
#     st.session_state.question_displayed    = False
#     st.session_state.question_time         = now_time()


# # ─────────────────────────────────────────────
# # RESUME
# # ─────────────────────────────────────────────
# def get_resume_text() -> str:
#     if st.session_state.get("resume_text"):
#         return st.session_state.resume_text
#     resume_path = st.session_state.get("resume_path")
#     if resume_path and os.path.exists(resume_path):
#         from utils.resume_parser import extract_resume_text
#         text = extract_resume_text(resume_path)
#         st.session_state.resume_text = text
#         return text
#     return "No resume provided."


# # ─────────────────────────────────────────────
# # QUESTION GENERATION — with duplicate prevention
# # ─────────────────────────────────────────────
# def get_next_question(resume_text: str) -> tuple[str, str]:
#     total_index = st.session_state.total_q_index
#     last_qa     = st.session_state.qa_history[-1] if st.session_state.qa_history else {}
#     asked       = st.session_state.asked_questions   # this session

#     if total_index == 0:
#         return INTRO_QUESTION, "easy"

#     # ── Cross-session dedup: load ALL past questions for this user ──
#     # Prevents repeat questions if user runs interview again
#     all_asked = list(asked)
#     try:
#         from database.db import get_all_user_questions
#         past = get_all_user_questions(st.session_state.get("user_email", ""))
#         # past is list of question_text strings
#         all_asked = list(set(all_asked + past))
#     except Exception:
#         pass   # silently fallback to session-only dedup

#     asked_context = all_asked[-16:] if all_asked else []

#     if st.session_state.adaptive_mode:
#         question = generate_question(
#             level           = "adaptive",
#             resume          = resume_text,
#             previous_answer = last_qa.get("answer", ""),
#             previous_score  = last_qa.get("score", 5.0),
#             asked_questions = asked_context
#         )
#         return question, "adaptive"

#     stage    = st.session_state.interview_stage
#     question = generate_question(
#         level           = stage,
#         resume          = resume_text,
#         previous_answer = last_qa.get("answer"),
#         previous_score  = last_qa.get("score"),
#         asked_questions = asked_context
#     )
#     return question, stage


# # ─────────────────────────────────────────────
# # STAGE PROGRESSION
# # ─────────────────────────────────────────────
# def advance_stage():
#     current = st.session_state.interview_stage
#     idx     = STAGES.index(current)
#     if idx + 1 < len(STAGES):
#         st.session_state.interview_stage = STAGES[idx + 1]
#         st.session_state.stage_q_index  = 0
#     else:
#         st.session_state.interview_complete = True


# def time_expired() -> bool:
#     return (time.time() - st.session_state.start_time) >= TIME_LIMIT


# # ─────────────────────────────────────────────
# # HANDLE ANSWER
# # ─────────────────────────────────────────────
# def handle_answer(answer: str, resume_text: str):
#     question = st.session_state.current_question
#     level    = st.session_state.current_level

#     # Evaluate silently — score hidden from chat
#     with st.spinner("LISA is reviewing your answer..."):
#         evaluation = evaluate_answer(question, answer)

#     score        = evaluation["score"]
#     ideal_answer = evaluation["ideal_answer"]
#     feedback     = evaluation["feedback"]

#     # Save to DB
#     save_question(
#         interview_id        = st.session_state.interview_id,
#         question_number     = st.session_state.total_q_index + 1,
#         difficulty_level    = level,
#         topic               = None,
#         question_text       = question,
#         user_answer         = answer,
#         ai_suggested_answer = ideal_answer,
#         score               = score,
#         feedback            = feedback
#     )

#     # Store in history
#     st.session_state.qa_history.append({
#         "question":     question,
#         "answer":       answer,
#         "score":        score,
#         "feedback":     feedback,
#         "ideal_answer": ideal_answer,
#         "level":        level,
#         "timestamp":    now_time()
#     })

#     st.session_state.total_q_index     += 1
#     st.session_state.question_displayed = False

#     # Adaptive trigger
#     if not st.session_state.adaptive_mode and level in ["medium", "hard"]:
#         trigger, direction = should_trigger_adaptive(level, score)
#         if trigger:
#             st.session_state.adaptive_mode      = True
#             st.session_state.adaptive_direction = direction
#             st.session_state.current_question   = None
#             st.rerun()
#             return

#     st.session_state.adaptive_mode      = False
#     st.session_state.adaptive_direction = ""

#     # Advance stage
#     st.session_state.stage_q_index += 1
#     stage = st.session_state.interview_stage
#     if st.session_state.stage_q_index >= QUESTIONS_PER_LEVEL.get(stage, 3):
#         advance_stage()

#     st.session_state.current_question = None
#     st.rerun()


# # ─────────────────────────────────────────────
# # FINALIZE
# # ─────────────────────────────────────────────
# def finalize_interview():
#     qa_history = st.session_state.qa_history
#     if not qa_history:
#         return

#     questions_scored = [
#         {
#             "difficulty_level": q["level"],
#             "score":            q["score"],
#             "topic":            "",
#             "question_text":    q["question"]
#         }
#         for q in qa_history
#     ]

#     total_score         = calculate_total_score(questions_scored)
#     skill_scores        = calculate_skill_scores(questions_scored)
#     performance_summary = generate_performance_summary(total_score, skill_scores)

#     qa_pairs = [
#         {"question": q["question"], "user_answer": q["answer"], "score": q["score"]}
#         for q in qa_history
#     ]

#     with st.spinner("LISA is generating your full evaluation report..."):
#         ai_feedback = generate_session_feedback(qa_pairs)

#     complete_interview(st.session_state.interview_id, total_score)

#     save_report(
#         interview_id           = st.session_state.interview_id,
#         overall_score          = total_score,
#         performance_summary    = performance_summary,
#         technical_knowledge    = skill_scores["technical_knowledge"],
#         communication_skills   = skill_scores["communication_skills"],
#         problem_solving        = skill_scores["problem_solving"],
#         project_understanding  = skill_scores["project_understanding"],
#         strengths              = ai_feedback["strengths"],
#         areas_for_improvement  = ai_feedback["improvements"],
#         actionable_suggestions = ai_feedback["study_plan"],
#         report_pdf             = b""
#     )

#     st.session_state.final_score         = total_score
#     st.session_state.skill_scores        = skill_scores
#     st.session_state.ai_feedback         = ai_feedback
#     st.session_state.performance_summary = performance_summary
#     st.session_state.interview_finalized = True


# # ─────────────────────────────────────────────
# # RESULTS SCREEN — motivational, detailed KPIs
# # ─────────────────────────────────────────────
# def show_results():
#     score        = st.session_state.get("final_score", 0)
#     skill_scores = st.session_state.get("skill_scores", {})
#     feedback     = st.session_state.get("ai_feedback", {})
#     summary      = st.session_state.get("performance_summary", "")
#     name         = st.session_state.get("user_name", "").split()[0]

#     def to_25(v):  return round(float(v or 0) * 2.5, 1)
#     def to_100(v): return round(float(v or 0) * 10.0, 1)

#     score_100 = to_100(score)

#     # ── Grade label ──────────────────────────
#     if score_100 >= 85:
#         grade, grade_color, grade_msg = "Excellent", "#10b981", "You're genuinely interview-ready."
#     elif score_100 >= 70:
#         grade, grade_color, grade_msg = "Strong", "#3b82f6", "A few more practice rounds and you're there."
#     elif score_100 >= 55:
#         grade, grade_color, grade_msg = "Developing", "#f59e0b", "Solid base — the gaps are fixable with focused prep."
#     else:
#         grade, grade_color, grade_msg = "Needs Work", "#ef4444", "Every expert started here — use this report as your roadmap."

#     # ── Hero section ─────────────────────────
#     st.markdown(f"""
#     <div style="background:linear-gradient(135deg,#0f172a,#1e1b4b);
#                 border:1px solid #312e81;border-radius:20px;
#                 padding:32px;text-align:center;margin-bottom:24px;">
#         <div style="font-size:13px;color:#64748b;letter-spacing:2px;
#                     text-transform:uppercase;margin-bottom:8px;">
#             Interview Complete — Session #{st.session_state.interview_id}
#         </div>
#         <div style="font-size:52px;font-weight:900;color:#f0f4ff;
#                     letter-spacing:-2px;line-height:1;">
#             {score_100}<span style="font-size:24px;color:#475569;">/100</span>
#         </div>
#         <div style="font-size:18px;font-weight:700;color:{grade_color};
#                     margin:8px 0 4px 0;">{grade}</div>
#         <div style="font-size:14px;color:#64748b;">{grade_msg}</div>
#     </div>
#     """, unsafe_allow_html=True)

#     # ── Skill scores ─────────────────────────
#     tech  = to_25(skill_scores.get("technical_knowledge",   0))
#     comm  = to_25(skill_scores.get("communication_skills",  0))
#     prob  = to_25(skill_scores.get("problem_solving",       0))
#     proj  = to_25(skill_scores.get("project_understanding", 0))

#     def skill_bar(label, val, max_val=25):
#         pct   = int((val / max_val) * 100)
#         color = "#10b981" if pct >= 70 else "#f59e0b" if pct >= 50 else "#ef4444"
#         level = "Strong" if pct >= 70 else "Building" if pct >= 50 else "Focus Here"
#         return f"""
#         <div style="margin-bottom:14px;">
#             <div style="display:flex;justify-content:space-between;
#                         margin-bottom:4px;">
#                 <span style="color:#e2e8f0;font-size:13px;font-weight:600;">
#                     {label}
#                 </span>
#                 <span style="color:{color};font-size:13px;font-weight:700;">
#                     {val}/25 &nbsp;·&nbsp; {level}
#                 </span>
#             </div>
#             <div style="background:#1e293b;border-radius:6px;height:8px;">
#                 <div style="background:{color};width:{pct}%;
#                             height:8px;border-radius:6px;
#                             transition:width 0.5s ease;"></div>
#             </div>
#         </div>"""

#     st.markdown(f"""
#     <div style="background:#111827;border:1px solid #1e2d47;
#                 border-radius:16px;padding:24px;margin-bottom:20px;">
#         <div style="font-size:14px;font-weight:700;color:#00d4ff;
#                     letter-spacing:1px;text-transform:uppercase;
#                     margin-bottom:16px;">Skill Breakdown</div>
#         {skill_bar("Technical Knowledge",   tech)}
#         {skill_bar("Communication Skills",  comm)}
#         {skill_bar("Problem Solving",       prob)}
#         {skill_bar("Project Understanding", proj)}
#     </div>
#     """, unsafe_allow_html=True)

#     # ── Motivational note from LISA ──────────
#     motivational = feedback.get("motivation", "")
#     if motivational:
#         st.markdown(f"""
#         <div style="background:linear-gradient(135deg,#0f2a1e,#064e3b);
#                     border:1px solid #065f46;border-radius:14px;
#                     padding:20px 24px;margin-bottom:20px;">
#             <div style="font-size:12px;color:#34d399;font-weight:700;
#                         letter-spacing:1px;text-transform:uppercase;
#                         margin-bottom:8px;">A note from LISA</div>
#             <div style="color:#d1fae5;font-size:15px;line-height:1.7;
#                         font-style:italic;">"{motivational}"</div>
#         </div>
#         """, unsafe_allow_html=True)

#     # ── Summary + Strengths + Improvements ───
#     col_a, col_b = st.columns(2)
#     with col_a:
#         if feedback.get("strengths"):
#             st.markdown("""
#             <div style="font-size:13px;font-weight:700;color:#10b981;
#                         letter-spacing:1px;text-transform:uppercase;
#                         margin-bottom:8px;">What You Did Well</div>
#             """, unsafe_allow_html=True)
#             st.success(feedback["strengths"])

#     with col_b:
#         if feedback.get("improvements"):
#             st.markdown("""
#             <div style="font-size:13px;font-weight:700;color:#f59e0b;
#                         letter-spacing:1px;text-transform:uppercase;
#                         margin-bottom:8px;">Where to Focus Next</div>
#             """, unsafe_allow_html=True)
#             st.warning(feedback["improvements"])

#     # ── Communication phrases ─────────────────
#     phrases_raw = feedback.get("communication_tips", "")
#     if phrases_raw:
#         phrases = [p.strip() for p in phrases_raw.split(",") if p.strip()]
#         if not phrases:
#             phrases = [phrases_raw]
#         cards = "".join([
#             f'<div style="background:#0f172a;border:1px solid #1e3a6e;'
#             f'border-radius:10px;padding:10px 16px;font-size:13px;'
#             f'color:#93c5fd;font-style:italic;">"{p}"</div>'
#             for p in phrases
#         ])
#         st.markdown(f"""
#         <div style="background:#111827;border:1px solid #1e2d47;
#                     border-radius:16px;padding:20px;margin:16px 0;">
#             <div style="font-size:13px;font-weight:700;color:#00d4ff;
#                         letter-spacing:1px;text-transform:uppercase;
#                         margin-bottom:12px;">
#                 Power Phrases to Use in Your Next Interview
#             </div>
#             <div style="display:flex;flex-direction:column;gap:8px;">
#                 {cards}
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#     # ── Study plan ───────────────────────────
#     if feedback.get("study_plan"):
#         topics = [t.strip() for t in feedback["study_plan"].split(",") if t.strip()]
#         if not topics:
#             topics = [feedback["study_plan"]]
#         topic_rows = "".join([
#             f'<div style="display:flex;align-items:flex-start;gap:10px;'
#             f'padding:10px 0;border-bottom:1px solid #1e293b;">'
#             f'<span style="color:#00d4ff;font-weight:700;min-width:20px;">→</span>'
#             f'<span style="color:#e2e8f0;font-size:14px;">{t}</span></div>'
#             for t in topics
#         ])
#         st.markdown(f"""
#         <div style="background:#111827;border:1px solid #1e2d47;
#                     border-radius:16px;padding:20px;margin:16px 0;">
#             <div style="font-size:13px;font-weight:700;color:#00d4ff;
#                         letter-spacing:1px;text-transform:uppercase;
#                         margin-bottom:4px;">Your Personalised Study Plan</div>
#             <div style="font-size:12px;color:#374151;margin-bottom:12px;">
#                 Master these before your next interview
#             </div>
#             {topic_rows}
#         </div>
#         """, unsafe_allow_html=True)

#     st.markdown("<br>", unsafe_allow_html=True)

#     # ── Download + New interview ──────────────
#     c1, c2 = st.columns(2)
#     with c1:
#         if st.button("Download Full PDF Report", type="primary",
#                      use_container_width=True):
#             try:
#                 from utils.pdf_report import generate_pdf
#                 pdf_bytes = generate_pdf(st.session_state.interview_id)
#                 st.download_button(
#                     label               = "Click to Download",
#                     data                = pdf_bytes,
#                     file_name           = f"pyspace_report_{st.session_state.interview_id}.pdf",
#                     mime                = "application/pdf",
#                     use_container_width = True
#                 )
#             except Exception as e:
#                 st.error(f"PDF generation failed: {e}")
#     with c2:
#         if st.button("Start New Interview", use_container_width=True):
#             keys = [
#                 "interview_initialized", "interview_id", "interview_stage",
#                 "stage_q_index", "total_q_index", "current_question", "current_level",
#                 "qa_history", "asked_questions", "adaptive_mode", "adaptive_direction",
#                 "interview_complete", "interview_finalized", "start_time", "final_score",
#                 "skill_scores", "ai_feedback", "performance_summary", "interview_started",
#                 "resume_path", "resume_text", "question_displayed", "question_time"
#             ]
#             for k in keys:
#                 st.session_state.pop(k, None)
#             st.rerun()


# # ─────────────────────────────────────────────
# # MAIN INTERVIEW FLOW
# # ─────────────────────────────────────────────
# def interview_flow():

#     # 1. Dark theme + styles
#     inject_interview_styles()

#     # 2. Init
#     init_interview()
#     resume_text = get_resume_text()

#     # 3. Create DB record once
#     if st.session_state.interview_id is None:
#         filename = os.path.basename(st.session_state.get("resume_path", "unknown"))
#         st.session_state.interview_id = create_interview(
#             user_email      = st.session_state["user_email"],
#             resume_text     = resume_text,
#             resume_filename = filename
#         )

#     # 4. Results / finalize check
#     if st.session_state.get("interview_finalized"):
#         show_results()
#         return

#     if st.session_state.interview_complete or time_expired():
#         finalize_interview()
#         st.rerun()
#         return

#     # ── HEADER ──────────────────────────────────────────────────
#     elapsed    = int(time.time() - st.session_state.start_time)
#     mins, secs = divmod(elapsed, 60)
#     remaining  = max(0, TIME_LIMIT - elapsed)
#     rem_m, rem_s = divmod(remaining, 60)

#     total_done  = st.session_state.total_q_index
#     # Total expected = base 10 + any adaptive questions fired so far
#     total_exp   = max(BASE_Q_COUNT, total_done + 1)
#     progress    = min(total_done / BASE_Q_COUNT, 1.0)
#     stage       = st.session_state.interview_stage
#     stage_label = STAGE_LABELS_CLEAN.get(stage, stage.title())

#     h1, h2, h3, h4 = st.columns([4, 1, 1, 1])
#     with h1:
#         st.progress(
#             progress,
#             text=f"{stage_label} Stage  ·  Question {total_done + 1}"
#         )
#     with h2:
#         st.metric("Elapsed", f"{mins:02d}:{secs:02d}")
#     with h3:
#         st.metric("Remaining", f"{rem_m:02d}:{rem_s:02d}")
#     with h4:
#         if st.button("End Interview", type="secondary"):
#             st.session_state.interview_complete = True
#             st.rerun()

#     st.divider()

#     # ── CONVERSATION HISTORY ─────────────────────────────────────
#     for i, qa in enumerate(st.session_state.qa_history, 1):

#         # LISA bubble
#         with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
#             st.markdown(
#                 f'<span style="font-size:11px;font-weight:700;color:#00d4ff;">'
#                 f'LISA &nbsp;•&nbsp; AI Interviewer</span>'
#                 f'{stage_badge(qa["level"])}',
#                 unsafe_allow_html=True
#             )
#             st.markdown(strip_emojis(qa["question"]))
#             st.caption(qa.get("timestamp", ""))

#         # User bubble — dark card matching LISA style
#         st.markdown(f"""
#         <div style="
#             background: #0f1f3d;
#             border: 1px solid #1e3a6e;
#             border-radius: 16px 0 16px 16px;
#             padding: 16px 20px;
#             max-width: 76%;
#             margin-left: auto;
#             margin-right: 0;
#             margin-bottom: 12px;
#             box-shadow: 0 0 20px rgba(37,99,235,0.08);
#         ">
#             <span style="font-size:11px;font-weight:700;color:#60a5fa;">
#                 {st.session_state.get("user_name", "You")}
#             </span>
#             <span style="font-size:11px;color:#1e3a6e;margin-left:8px;">
#                 {qa.get("timestamp", "")}
#             </span>
#             <div style="color:#dbeafe;font-size:15px;
#                         line-height:1.7;margin-top:8px;">
#                 {qa["answer"]}
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#     # ── GENERATE CURRENT QUESTION ─────────────────────────────────
#     if st.session_state.current_question is None:
#         with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
#             show_typing_indicator()

#         question, level = get_next_question(resume_text)

#         # Track to prevent duplicates
#         st.session_state.asked_questions.add(question.strip().lower()[:80])

#         st.session_state.current_question   = question
#         st.session_state.current_level      = level
#         st.session_state.question_displayed = False
#         st.session_state.question_time      = now_time()
#         st.rerun()

#     question = st.session_state.current_question
#     level    = st.session_state.current_level

#     # ── ADAPTIVE BANNER ───────────────────────────────────────────
#     if st.session_state.adaptive_mode:
#         d   = st.session_state.adaptive_direction
#         msg = (
#             "Let me rephrase that — I want to make sure we cover this concept."
#             if d == "easier"
#             else "Strong response. Let me take this a level deeper."
#         )
#         st.markdown(
#             f'<div style="background:#0f172a;border-left:3px solid #6366f1;'
#             f'border-radius:0 8px 8px 0;padding:10px 16px;margin:8px 0;'
#             f'font-size:13px;color:#a5b4fc;">LISA — {msg}</div>',
#             unsafe_allow_html=True
#         )

#     # ── LISA QUESTION BUBBLE ──────────────────────────────────────
#     with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
#         st.markdown(
#             f'<span style="font-size:11px;font-weight:700;color:#00d4ff;">'
#             f'LISA &nbsp;•&nbsp; AI Interviewer</span>'
#             f'{stage_badge(level)}'
#             f'<span style="font-size:11px;color:#374151;margin-left:8px;">'
#             f'Question {total_done + 1}</span>',
#             unsafe_allow_html=True
#         )

#         clean_q = strip_emojis(question)

#         if not st.session_state.question_displayed:
#             # ── VOICE plays first (hidden) ──
#             play_lisa_voice(clean_q)
#             # ── TYPEWRITER runs simultaneously ──
#             st.write_stream(typewriter_stream(clean_q, WORDS_PER_SECOND))
#             st.session_state.question_displayed = True
#         else:
#             st.markdown(clean_q)

#         st.caption(st.session_state.get("question_time", now_time()))

#     # ── USER INPUT ────────────────────────────────────────────────
#     user_name = st.session_state.get("user_name", "You")

#     # ── helper: render answer as dark card matching LISA bubble ──
#     def show_user_bubble(text: str):
#         st.markdown(f"""
#         <div style="
#             background: #0f1f3d;
#             border: 1px solid #1e3a6e;
#             border-radius: 16px 0 16px 16px;
#             padding: 16px 20px;
#             max-width: 76%;
#             margin-left: auto;
#             margin-right: 0;
#             margin-bottom: 8px;
#             box-shadow: 0 0 20px rgba(37,99,235,0.08);
#         ">
#             <span style="font-size:11px;font-weight:700;color:#60a5fa;">
#                 {user_name}
#             </span>
#             <span style="font-size:11px;color:#1e3a6e;margin-left:8px;">
#                 {now_time()}
#             </span>
#             <div style="color:#000000;font-size:15px;
#                         line-height:1.7;margin-top:8px;">
#                 {text}
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#     # Step 1 — voice transcribed in previous run → show bubble + submit
#     prefill = st.session_state.pop(f"prefill_{total_done}", None)
#     if prefill:
#         show_user_bubble(prefill)
#         handle_answer(prefill, resume_text)
#         return

#     # Step 2 — mic widget
#     audio_input = st.audio_input(
#         "Hold to record your answer",
#         key              = f"voice_{total_done}",
#         label_visibility = "collapsed"
#     )

#     if audio_input:
#         with st.spinner("Transcribing..."):
#             from utils.speech_to_text import transcribe_audio_debug
#             transcribed, debug_msg = transcribe_audio_debug(audio_input)

#         if transcribed and transcribed.strip():
#             st.session_state[f"prefill_{total_done}"] = transcribed.strip()
#             st.rerun()
#         else:
#             st.markdown(f"""
#             <div style="
#                 background:#1a0a0a;border:1px solid #7f1d1d;
#                 border-radius:10px;padding:12px 16px;margin:8px 0;
#                 color:#fca5a5;font-size:13px;">
#                 ⚠️ Could not transcribe: <b>{debug_msg}</b><br>
#                 <span style="color:#6b7280;font-size:12px;">
#                     Please type your answer in the box below.
#                 </span>
#             </div>
#             """, unsafe_allow_html=True)

#     # Step 3 — chat_input pinned at bottom
#     typed = st.chat_input(
#         "Type your answer and press Enter  (or use mic above)",
#         key = f"chat_{total_done}"
#     )
#     if typed:
#         answer = typed.strip()
#         if not answer:
#             return
#         if answer.lower() == "/skip":
#             answer = "I am not sure about this question."
#         show_user_bubble(answer)
#         handle_answer(answer, resume_text)
# # import os
# # import time
# # import streamlit as st

# # from interview.lisa_ai import generate_question, evaluate_answer, generate_session_feedback
# # from interview.scoring import (
# #     should_trigger_adaptive,
# #     calculate_total_score,
# #     calculate_skill_scores,
# #     generate_performance_summary
# # )
# # from database.db import (
# #     create_interview,
# #     save_question,
# #     complete_interview,
# #     save_report
# # )
# # from config import QUESTIONS_PER_LEVEL, INTRO_QUESTION
# # from assets.interview_style import (
# #     inject_interview_styles,
# #     show_typing_indicator,
# #     stage_badge,
# #     strip_emojis,
# #     now_time,
# #     LISA_AVATAR_PATH,
# #     STAGE_LABELS_CLEAN
# # )

# # # ─────────────────────────────────────────────
# # # CONSTANTS
# # # ─────────────────────────────────────────────
# # STAGES       = ["easy", "medium", "hard"]
# # TIME_LIMIT   = 30 * 60   # 30 minutes
# # BASE_Q_COUNT = sum(QUESTIONS_PER_LEVEL.values())   # 10

# # # Words per second for typewriter — matches gTTS speed
# # WORDS_PER_SECOND = 2.2


# # # ─────────────────────────────────────────────
# # # TYPEWRITER GENERATOR
# # # ─────────────────────────────────────────────
# # def typewriter_stream(text: str, wps: float = WORDS_PER_SECOND):
# #     words = text.split()
# #     delay = 1.0 / wps
# #     for word in words:
# #         yield word + " "
# #         time.sleep(delay)


# # # ─────────────────────────────────────────────
# # # PLAY LISA VOICE — browser Web Speech API
# # # No MP3 files. No disk writes. No gTTS.
# # # ─────────────────────────────────────────────
# # def play_lisa_voice(text: str) -> bool:
# #     try:
# #         from utils.text_to_speech import speak
# #         speak(text)
# #         return True
# #     except Exception:
# #         return False


# # # ─────────────────────────────────────────────
# # # SESSION STATE INIT
# # # ─────────────────────────────────────────────
# # def init_interview():
# #     if st.session_state.get("interview_initialized"):
# #         return

# #     st.session_state.interview_initialized = True
# #     st.session_state.interview_id          = None
# #     st.session_state.interview_stage       = "easy"
# #     st.session_state.stage_q_index         = 0
# #     st.session_state.total_q_index         = 0
# #     st.session_state.current_question      = None
# #     st.session_state.current_level         = "easy"
# #     st.session_state.qa_history            = []
# #     st.session_state.asked_questions       = set()   # ← prevent duplicates
# #     st.session_state.adaptive_mode         = False
# #     st.session_state.adaptive_direction    = ""
# #     st.session_state.interview_complete    = False
# #     st.session_state.interview_finalized   = False
# #     st.session_state.start_time            = time.time()
# #     st.session_state.question_displayed    = False
# #     st.session_state.question_time         = now_time()


# # # ─────────────────────────────────────────────
# # # RESUME
# # # ─────────────────────────────────────────────
# # def get_resume_text() -> str:
# #     if st.session_state.get("resume_text"):
# #         return st.session_state.resume_text
# #     resume_path = st.session_state.get("resume_path")
# #     if resume_path and os.path.exists(resume_path):
# #         from utils.resume_parser import extract_resume_text
# #         text = extract_resume_text(resume_path)
# #         st.session_state.resume_text = text
# #         return text
# #     return "No resume provided."


# # # ─────────────────────────────────────────────
# # # QUESTION GENERATION — with duplicate prevention
# # # ─────────────────────────────────────────────
# # def get_next_question(resume_text: str) -> tuple[str, str]:
# #     total_index = st.session_state.total_q_index
# #     last_qa     = st.session_state.qa_history[-1] if st.session_state.qa_history else {}
# #     asked       = st.session_state.asked_questions

# #     # Q1 is always the intro — hardcoded, no API
# #     if total_index == 0:
# #         return INTRO_QUESTION, "easy"

# #     # Build "already asked" context for the prompt
# #     asked_context = list(asked)[-8:] if asked else []   # last 8 to keep prompt short

# #     if st.session_state.adaptive_mode:
# #         question = generate_question(
# #             level           = "adaptive",
# #             resume          = resume_text,
# #             previous_answer = last_qa.get("answer", ""),
# #             previous_score  = last_qa.get("score", 5.0),
# #             asked_questions = asked_context
# #         )
# #         return question, "adaptive"

# #     stage    = st.session_state.interview_stage
# #     question = generate_question(
# #         level           = stage,
# #         resume          = resume_text,
# #         previous_answer = last_qa.get("answer"),
# #         previous_score  = last_qa.get("score"),
# #         asked_questions = asked_context
# #     )
# #     return question, stage


# # # ─────────────────────────────────────────────
# # # STAGE PROGRESSION
# # # ─────────────────────────────────────────────
# # def advance_stage():
# #     current = st.session_state.interview_stage
# #     idx     = STAGES.index(current)
# #     if idx + 1 < len(STAGES):
# #         st.session_state.interview_stage = STAGES[idx + 1]
# #         st.session_state.stage_q_index  = 0
# #     else:
# #         st.session_state.interview_complete = True


# # def time_expired() -> bool:
# #     return (time.time() - st.session_state.start_time) >= TIME_LIMIT


# # # ─────────────────────────────────────────────
# # # HANDLE ANSWER
# # # ─────────────────────────────────────────────
# # def handle_answer(answer: str, resume_text: str):
# #     question = st.session_state.current_question
# #     level    = st.session_state.current_level

# #     # Evaluate silently — score hidden from chat
# #     with st.spinner("LISA is reviewing your answer..."):
# #         evaluation = evaluate_answer(question, answer)

# #     score        = evaluation["score"]
# #     ideal_answer = evaluation["ideal_answer"]
# #     feedback     = evaluation["feedback"]

# #     # Save to DB
# #     save_question(
# #         interview_id        = st.session_state.interview_id,
# #         question_number     = st.session_state.total_q_index + 1,
# #         difficulty_level    = level,
# #         topic               = None,
# #         question_text       = question,
# #         user_answer         = answer,
# #         ai_suggested_answer = ideal_answer,
# #         score               = score,
# #         feedback            = feedback
# #     )

# #     # Store in history
# #     st.session_state.qa_history.append({
# #         "question":     question,
# #         "answer":       answer,
# #         "score":        score,
# #         "feedback":     feedback,
# #         "ideal_answer": ideal_answer,
# #         "level":        level,
# #         "timestamp":    now_time()
# #     })

# #     st.session_state.total_q_index     += 1
# #     st.session_state.question_displayed = False

# #     # Adaptive trigger
# #     if not st.session_state.adaptive_mode and level in ["medium", "hard"]:
# #         trigger, direction = should_trigger_adaptive(level, score)
# #         if trigger:
# #             st.session_state.adaptive_mode      = True
# #             st.session_state.adaptive_direction = direction
# #             st.session_state.current_question   = None
# #             st.rerun()
# #             return

# #     st.session_state.adaptive_mode      = False
# #     st.session_state.adaptive_direction = ""

# #     # Advance stage
# #     st.session_state.stage_q_index += 1
# #     stage = st.session_state.interview_stage
# #     if st.session_state.stage_q_index >= QUESTIONS_PER_LEVEL.get(stage, 3):
# #         advance_stage()

# #     st.session_state.current_question = None
# #     st.rerun()


# # # ─────────────────────────────────────────────
# # # FINALIZE
# # # ─────────────────────────────────────────────
# # def finalize_interview():
# #     qa_history = st.session_state.qa_history
# #     if not qa_history:
# #         return

# #     questions_scored = [
# #         {
# #             "difficulty_level": q["level"],
# #             "score":            q["score"],
# #             "topic":            "",
# #             "question_text":    q["question"]
# #         }
# #         for q in qa_history
# #     ]

# #     total_score         = calculate_total_score(questions_scored)
# #     skill_scores        = calculate_skill_scores(questions_scored)
# #     performance_summary = generate_performance_summary(total_score, skill_scores)

# #     qa_pairs = [
# #         {"question": q["question"], "user_answer": q["answer"], "score": q["score"]}
# #         for q in qa_history
# #     ]

# #     with st.spinner("LISA is generating your full evaluation report..."):
# #         ai_feedback = generate_session_feedback(qa_pairs)

# #     complete_interview(st.session_state.interview_id, total_score)

# #     save_report(
# #         interview_id           = st.session_state.interview_id,
# #         overall_score          = total_score,
# #         performance_summary    = performance_summary,
# #         technical_knowledge    = skill_scores["technical_knowledge"],
# #         communication_skills   = skill_scores["communication_skills"],
# #         problem_solving        = skill_scores["problem_solving"],
# #         project_understanding  = skill_scores["project_understanding"],
# #         strengths              = ai_feedback["strengths"],
# #         areas_for_improvement  = ai_feedback["improvements"],
# #         actionable_suggestions = ai_feedback["study_plan"],
# #         report_pdf             = b""
# #     )

# #     st.session_state.final_score         = total_score
# #     st.session_state.skill_scores        = skill_scores
# #     st.session_state.ai_feedback         = ai_feedback
# #     st.session_state.performance_summary = performance_summary
# #     st.session_state.interview_finalized = True


# # # ─────────────────────────────────────────────
# # # RESULTS SCREEN
# # # ─────────────────────────────────────────────
# # def show_results():
# #     score        = st.session_state.get("final_score", 0)
# #     skill_scores = st.session_state.get("skill_scores", {})
# #     feedback     = st.session_state.get("ai_feedback", {})
# #     summary      = st.session_state.get("performance_summary", "")

# #     def to_25(v):  return round(float(v or 0) * 2.5, 1)
# #     def to_100(v): return round(float(v or 0) * 10.0, 1)

# #     st.markdown("## Interview Complete")
# #     st.caption(f"Session #{st.session_state.interview_id}")
# #     st.divider()

# #     c1, c2, c3, c4, c5 = st.columns(5)
# #     c1.metric("Overall",         f"{to_100(score)}/100")
# #     c2.metric("Technical",       f"{to_25(skill_scores.get('technical_knowledge', 0))}/25")
# #     c3.metric("Communication",   f"{to_25(skill_scores.get('communication_skills', 0))}/25")
# #     c4.metric("Problem Solving", f"{to_25(skill_scores.get('problem_solving', 0))}/25")
# #     c5.metric("Projects",        f"{to_25(skill_scores.get('project_understanding', 0))}/25")

# #     st.divider()
# #     st.markdown("### Performance Summary")
# #     st.info(summary)

# #     col_a, col_b = st.columns(2)
# #     with col_a:
# #         st.markdown("### Strengths")
# #         st.success(feedback.get("strengths", ""))
# #     with col_b:
# #         st.markdown("### Areas for Improvement")
# #         st.warning(feedback.get("improvements", ""))

# #     st.markdown("### Study Plan")
# #     st.write(feedback.get("study_plan", ""))
# #     st.divider()

# #     if st.button("Download Evaluation Report (PDF)", type="primary",
# #                  use_container_width=True):
# #         try:
# #             from utils.pdf_report import generate_pdf
# #             pdf_bytes = generate_pdf(st.session_state.interview_id)
# #             st.download_button(
# #                 label               = "Click to Download PDF",
# #                 data                = pdf_bytes,
# #                 file_name           = f"pyspace_report_{st.session_state.interview_id}.pdf",
# #                 mime                = "application/pdf",
# #                 use_container_width = True
# #             )
# #         except Exception as e:
# #             st.error(f"PDF generation failed: {e}")

# #     st.divider()
# #     if st.button("Start New Interview", use_container_width=True):
# #         keys = [
# #             "interview_initialized", "interview_id", "interview_stage",
# #             "stage_q_index", "total_q_index", "current_question", "current_level",
# #             "qa_history", "asked_questions", "adaptive_mode", "adaptive_direction",
# #             "interview_complete", "interview_finalized", "start_time", "final_score",
# #             "skill_scores", "ai_feedback", "performance_summary", "interview_started",
# #             "resume_path", "resume_text", "question_displayed", "question_time"
# #         ]
# #         for k in keys:
# #             st.session_state.pop(k, None)
# #         st.rerun()


# # # ─────────────────────────────────────────────
# # # MAIN INTERVIEW FLOW
# # # ─────────────────────────────────────────────
# # def interview_flow():

# #     # 1. Dark theme + styles
# #     inject_interview_styles()

# #     # 2. Init
# #     init_interview()
# #     resume_text = get_resume_text()

# #     # 3. Create DB record once
# #     if st.session_state.interview_id is None:
# #         filename = os.path.basename(st.session_state.get("resume_path", "unknown"))
# #         st.session_state.interview_id = create_interview(
# #             user_email      = st.session_state["user_email"],
# #             resume_text     = resume_text,
# #             resume_filename = filename
# #         )

# #     # 4. Results / finalize check
# #     if st.session_state.get("interview_finalized"):
# #         show_results()
# #         return

# #     if st.session_state.interview_complete or time_expired():
# #         finalize_interview()
# #         st.rerun()
# #         return

# #     # ── HEADER ──────────────────────────────────────────────────
# #     elapsed    = int(time.time() - st.session_state.start_time)
# #     mins, secs = divmod(elapsed, 60)
# #     remaining  = max(0, TIME_LIMIT - elapsed)
# #     rem_m, rem_s = divmod(remaining, 60)

# #     total_done  = st.session_state.total_q_index
# #     # Total expected = base 10 + any adaptive questions fired so far
# #     total_exp   = max(BASE_Q_COUNT, total_done + 1)
# #     progress    = min(total_done / BASE_Q_COUNT, 1.0)
# #     stage       = st.session_state.interview_stage
# #     stage_label = STAGE_LABELS_CLEAN.get(stage, stage.title())

# #     h1, h2, h3, h4 = st.columns([4, 1, 1, 1])
# #     with h1:
# #         st.progress(
# #             progress,
# #             text=f"{stage_label} Stage  ·  Question {total_done + 1}"
# #         )
# #     with h2:
# #         st.metric("Elapsed", f"{mins:02d}:{secs:02d}")
# #     with h3:
# #         st.metric("Remaining", f"{rem_m:02d}:{rem_s:02d}")
# #     with h4:
# #         if st.button("End Interview", type="secondary"):
# #             st.session_state.interview_complete = True
# #             st.rerun()

# #     st.divider()

# #     # ── CONVERSATION HISTORY ─────────────────────────────────────
# #     for i, qa in enumerate(st.session_state.qa_history, 1):

# #         # LISA bubble
# #         with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
# #             st.markdown(
# #                 f'<span style="font-size:11px;font-weight:700;color:#00d4ff;">'
# #                 f'LISA &nbsp;•&nbsp; AI Interviewer</span>'
# #                 f'{stage_badge(qa["level"])}',
# #                 unsafe_allow_html=True
# #             )
# #             st.markdown(strip_emojis(qa["question"]))
# #             st.caption(qa.get("timestamp", ""))

# #         # User bubble — dark card matching LISA style
# #         st.markdown(f"""
# #         <div style="
# #             background: #0f1f3d;
# #             border: 1px solid #1e3a6e;
# #             border-radius: 16px 0 16px 16px;
# #             padding: 16px 20px;
# #             max-width: 76%;
# #             margin-left: auto;
# #             margin-right: 0;
# #             margin-bottom: 12px;
# #             box-shadow: 0 0 20px rgba(37,99,235,0.08);
# #         ">
# #             <span style="font-size:11px;font-weight:700;color:#60a5fa;">
# #                 {st.session_state.get("user_name", "You")}
# #             </span>
# #             <span style="font-size:11px;color:#1e3a6e;margin-left:8px;">
# #                 {qa.get("timestamp", "")}
# #             </span>
# #             <div style="color:#dbeafe;font-size:15px;
# #                         line-height:1.7;margin-top:8px;">
# #                 {qa["answer"]}
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #     # ── GENERATE CURRENT QUESTION ─────────────────────────────────
# #     if st.session_state.current_question is None:
# #         with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
# #             show_typing_indicator()

# #         question, level = get_next_question(resume_text)

# #         # Track to prevent duplicates
# #         st.session_state.asked_questions.add(question.strip().lower()[:80])

# #         st.session_state.current_question   = question
# #         st.session_state.current_level      = level
# #         st.session_state.question_displayed = False
# #         st.session_state.question_time      = now_time()
# #         st.rerun()

# #     question = st.session_state.current_question
# #     level    = st.session_state.current_level

# #     # ── ADAPTIVE BANNER ───────────────────────────────────────────
# #     if st.session_state.adaptive_mode:
# #         d   = st.session_state.adaptive_direction
# #         msg = (
# #             "Let me rephrase that — I want to make sure we cover this concept."
# #             if d == "easier"
# #             else "Strong response. Let me take this a level deeper."
# #         )
# #         st.markdown(
# #             f'<div style="background:#0f172a;border-left:3px solid #6366f1;'
# #             f'border-radius:0 8px 8px 0;padding:10px 16px;margin:8px 0;'
# #             f'font-size:13px;color:#a5b4fc;">LISA — {msg}</div>',
# #             unsafe_allow_html=True
# #         )

# #     # ── LISA QUESTION BUBBLE ──────────────────────────────────────
# #     with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
# #         st.markdown(
# #             f'<span style="font-size:11px;font-weight:700;color:#00d4ff;">'
# #             f'LISA &nbsp;•&nbsp; AI Interviewer</span>'
# #             f'{stage_badge(level)}'
# #             f'<span style="font-size:11px;color:#374151;margin-left:8px;">'
# #             f'Question {total_done + 1}</span>',
# #             unsafe_allow_html=True
# #         )

# #         clean_q = strip_emojis(question)

# #         if not st.session_state.question_displayed:
# #             # ── VOICE plays first (hidden) ──
# #             play_lisa_voice(clean_q)
# #             # ── TYPEWRITER runs simultaneously ──
# #             st.write_stream(typewriter_stream(clean_q, WORDS_PER_SECOND))
# #             st.session_state.question_displayed = True
# #         else:
# #             st.markdown(clean_q)

# #         st.caption(st.session_state.get("question_time", now_time()))

# #     # ── USER INPUT ────────────────────────────────────────────────
# #     user_name = st.session_state.get("user_name", "You")

# #     # ── helper: render answer as dark card matching LISA bubble ──
# #     def show_user_bubble(text: str):
# #         st.markdown(f"""
# #         <div style="
# #             background: #0f1f3d;
# #             border: 1px solid #1e3a6e;
# #             border-radius: 16px 0 16px 16px;
# #             padding: 16px 20px;
# #             max-width: 76%;
# #             margin-left: auto;
# #             margin-right: 0;
# #             margin-bottom: 8px;
# #             box-shadow: 0 0 20px rgba(37,99,235,0.08);
# #         ">
# #             <span style="font-size:11px;font-weight:700;color:#60a5fa;">
# #                 {user_name}
# #             </span>
# #             <span style="font-size:11px;color:#1e3a6e;margin-left:8px;">
# #                 {now_time()}
# #             </span>
# #             <div style="color:#dbeafe;font-size:15px;
# #                         line-height:1.7;margin-top:8px;">
# #                 {text}
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #     # Step 1 — voice transcribed in previous run → show bubble + submit
# #     prefill = st.session_state.pop(f"prefill_{total_done}", None)
# #     if prefill:
# #         show_user_bubble(prefill)
# #         handle_answer(prefill, resume_text)
# #         return

# #     # Step 2 — mic widget
# #     audio_input = st.audio_input(
# #         "Hold to record your answer",
# #         key              = f"voice_{total_done}",
# #         label_visibility = "collapsed"
# #     )

# #     if audio_input:
# #         with st.spinner("Transcribing..."):
# #             from utils.speech_to_text import transcribe_audio_debug
# #             transcribed, debug_msg = transcribe_audio_debug(audio_input)

# #         if transcribed and transcribed.strip():
# #             st.session_state[f"prefill_{total_done}"] = transcribed.strip()
# #             st.rerun()
# #         else:
# #             st.markdown(f"""
# #             <div style="
# #                 background:#1a0a0a;border:1px solid #7f1d1d;
# #                 border-radius:10px;padding:12px 16px;margin:8px 0;
# #                 color:#fca5a5;font-size:13px;">
# #                 ⚠️ Could not transcribe: <b>{debug_msg}</b><br>
# #                 <span style="color:#6b7280;font-size:12px;">
# #                     Please type your answer in the box below.
# #                 </span>
# #             </div>
# #             """, unsafe_allow_html=True)

# #     # Step 3 — chat_input pinned at bottom
# #     typed = st.chat_input(
# #         "Type your answer and press Enter  (or use mic above)",
# #         key = f"chat_{total_done}"
# #     )
# #     if typed:
# #         answer = typed.strip()
# #         if not answer:
# #             return
# #         if answer.lower() == "/skip":
# #             answer = "I am not sure about this question."
# #         show_user_bubble(answer)
# #         handle_answer(answer, resume_text)
# # # import os
# # # import time
# # # import streamlit as st

# # # from interview.lisa_ai import generate_question, evaluate_answer, generate_session_feedback
# # # from interview.scoring import (
# # #     should_trigger_adaptive,
# # #     calculate_total_score,
# # #     calculate_skill_scores,
# # #     generate_performance_summary
# # # )
# # # from database.db import (
# # #     create_interview,
# # #     save_question,
# # #     complete_interview,
# # #     save_report
# # # )
# # # from config import QUESTIONS_PER_LEVEL, INTRO_QUESTION
# # # from assets.interview_style import (
# # #     inject_interview_styles,
# # #     show_typing_indicator,
# # #     stage_badge,
# # #     strip_emojis,
# # #     now_time,
# # #     LISA_AVATAR_PATH,
# # #     STAGE_LABELS_CLEAN
# # # )

# # # # ─────────────────────────────────────────────
# # # # CONSTANTS
# # # # ─────────────────────────────────────────────
# # # STAGES       = ["easy", "medium", "hard"]
# # # TIME_LIMIT   = 30 * 60   # 30 minutes
# # # BASE_Q_COUNT = sum(QUESTIONS_PER_LEVEL.values())   # 10

# # # # Words per second for typewriter — matches gTTS speed
# # # WORDS_PER_SECOND = 2.2


# # # # ─────────────────────────────────────────────
# # # # TYPEWRITER GENERATOR
# # # # ─────────────────────────────────────────────
# # # def typewriter_stream(text: str, wps: float = WORDS_PER_SECOND):
# # #     words = text.split()
# # #     delay = 1.0 / wps
# # #     for word in words:
# # #         yield word + " "
# # #         time.sleep(delay)


# # # # ─────────────────────────────────────────────
# # # # PLAY LISA VOICE — browser Web Speech API
# # # # No MP3 files. No disk writes. No gTTS.
# # # # ─────────────────────────────────────────────
# # # def play_lisa_voice(text: str) -> bool:
# # #     try:
# # #         from utils.text_to_speech import speak
# # #         speak(text)
# # #         return True
# # #     except Exception:
# # #         return False


# # # # ─────────────────────────────────────────────
# # # # SESSION STATE INIT
# # # # ─────────────────────────────────────────────
# # # def init_interview():
# # #     if st.session_state.get("interview_initialized"):
# # #         return

# # #     st.session_state.interview_initialized = True
# # #     st.session_state.interview_id          = None
# # #     st.session_state.interview_stage       = "easy"
# # #     st.session_state.stage_q_index         = 0
# # #     st.session_state.total_q_index         = 0
# # #     st.session_state.current_question      = None
# # #     st.session_state.current_level         = "easy"
# # #     st.session_state.qa_history            = []
# # #     st.session_state.asked_questions       = set()   # ← prevent duplicates
# # #     st.session_state.adaptive_mode         = False
# # #     st.session_state.adaptive_direction    = ""
# # #     st.session_state.interview_complete    = False
# # #     st.session_state.interview_finalized   = False
# # #     st.session_state.start_time            = time.time()
# # #     st.session_state.question_displayed    = False
# # #     st.session_state.question_time         = now_time()


# # # # ─────────────────────────────────────────────
# # # # RESUME
# # # # ─────────────────────────────────────────────
# # # def get_resume_text() -> str:
# # #     if st.session_state.get("resume_text"):
# # #         return st.session_state.resume_text
# # #     resume_path = st.session_state.get("resume_path")
# # #     if resume_path and os.path.exists(resume_path):
# # #         from utils.resume_parser import extract_resume_text
# # #         text = extract_resume_text(resume_path)
# # #         st.session_state.resume_text = text
# # #         return text
# # #     return "No resume provided."


# # # # ─────────────────────────────────────────────
# # # # QUESTION GENERATION — with duplicate prevention
# # # # ─────────────────────────────────────────────
# # # def get_next_question(resume_text: str) -> tuple[str, str]:
# # #     total_index = st.session_state.total_q_index
# # #     last_qa     = st.session_state.qa_history[-1] if st.session_state.qa_history else {}
# # #     asked       = st.session_state.asked_questions

# # #     # Q1 is always the intro — hardcoded, no API
# # #     if total_index == 0:
# # #         return INTRO_QUESTION, "easy"

# # #     # Build "already asked" context for the prompt
# # #     asked_context = list(asked)[-8:] if asked else []   # last 8 to keep prompt short

# # #     if st.session_state.adaptive_mode:
# # #         question = generate_question(
# # #             level           = "adaptive",
# # #             resume          = resume_text,
# # #             previous_answer = last_qa.get("answer", ""),
# # #             previous_score  = last_qa.get("score", 5.0),
# # #             asked_questions = asked_context
# # #         )
# # #         return question, "adaptive"

# # #     stage    = st.session_state.interview_stage
# # #     question = generate_question(
# # #         level           = stage,
# # #         resume          = resume_text,
# # #         previous_answer = last_qa.get("answer"),
# # #         previous_score  = last_qa.get("score"),
# # #         asked_questions = asked_context
# # #     )
# # #     return question, stage


# # # # ─────────────────────────────────────────────
# # # # STAGE PROGRESSION
# # # # ─────────────────────────────────────────────
# # # def advance_stage():
# # #     current = st.session_state.interview_stage
# # #     idx     = STAGES.index(current)
# # #     if idx + 1 < len(STAGES):
# # #         st.session_state.interview_stage = STAGES[idx + 1]
# # #         st.session_state.stage_q_index  = 0
# # #     else:
# # #         st.session_state.interview_complete = True


# # # def time_expired() -> bool:
# # #     return (time.time() - st.session_state.start_time) >= TIME_LIMIT


# # # # ─────────────────────────────────────────────
# # # # HANDLE ANSWER
# # # # ─────────────────────────────────────────────
# # # def handle_answer(answer: str, resume_text: str):
# # #     question = st.session_state.current_question
# # #     level    = st.session_state.current_level

# # #     # Evaluate silently — score hidden from chat
# # #     with st.spinner("LISA is reviewing your answer..."):
# # #         evaluation = evaluate_answer(question, answer)

# # #     score        = evaluation["score"]
# # #     ideal_answer = evaluation["ideal_answer"]
# # #     feedback     = evaluation["feedback"]

# # #     # Save to DB
# # #     save_question(
# # #         interview_id        = st.session_state.interview_id,
# # #         question_number     = st.session_state.total_q_index + 1,
# # #         difficulty_level    = level,
# # #         topic               = None,
# # #         question_text       = question,
# # #         user_answer         = answer,
# # #         ai_suggested_answer = ideal_answer,
# # #         score               = score,
# # #         feedback            = feedback
# # #     )

# # #     # Store in history
# # #     st.session_state.qa_history.append({
# # #         "question":     question,
# # #         "answer":       answer,
# # #         "score":        score,
# # #         "feedback":     feedback,
# # #         "ideal_answer": ideal_answer,
# # #         "level":        level,
# # #         "timestamp":    now_time()
# # #     })

# # #     st.session_state.total_q_index     += 1
# # #     st.session_state.question_displayed = False

# # #     # Adaptive trigger
# # #     if not st.session_state.adaptive_mode and level in ["medium", "hard"]:
# # #         trigger, direction = should_trigger_adaptive(level, score)
# # #         if trigger:
# # #             st.session_state.adaptive_mode      = True
# # #             st.session_state.adaptive_direction = direction
# # #             st.session_state.current_question   = None
# # #             st.rerun()
# # #             return

# # #     st.session_state.adaptive_mode      = False
# # #     st.session_state.adaptive_direction = ""

# # #     # Advance stage
# # #     st.session_state.stage_q_index += 1
# # #     stage = st.session_state.interview_stage
# # #     if st.session_state.stage_q_index >= QUESTIONS_PER_LEVEL.get(stage, 3):
# # #         advance_stage()

# # #     st.session_state.current_question = None
# # #     st.rerun()


# # # # ─────────────────────────────────────────────
# # # # FINALIZE
# # # # ─────────────────────────────────────────────
# # # def finalize_interview():
# # #     qa_history = st.session_state.qa_history
# # #     if not qa_history:
# # #         return

# # #     questions_scored = [
# # #         {
# # #             "difficulty_level": q["level"],
# # #             "score":            q["score"],
# # #             "topic":            "",
# # #             "question_text":    q["question"]
# # #         }
# # #         for q in qa_history
# # #     ]

# # #     total_score         = calculate_total_score(questions_scored)
# # #     skill_scores        = calculate_skill_scores(questions_scored)
# # #     performance_summary = generate_performance_summary(total_score, skill_scores)

# # #     qa_pairs = [
# # #         {"question": q["question"], "user_answer": q["answer"], "score": q["score"]}
# # #         for q in qa_history
# # #     ]

# # #     with st.spinner("LISA is generating your full evaluation report..."):
# # #         ai_feedback = generate_session_feedback(qa_pairs)

# # #     complete_interview(st.session_state.interview_id, total_score)

# # #     save_report(
# # #         interview_id           = st.session_state.interview_id,
# # #         overall_score          = total_score,
# # #         performance_summary    = performance_summary,
# # #         technical_knowledge    = skill_scores["technical_knowledge"],
# # #         communication_skills   = skill_scores["communication_skills"],
# # #         problem_solving        = skill_scores["problem_solving"],
# # #         project_understanding  = skill_scores["project_understanding"],
# # #         strengths              = ai_feedback["strengths"],
# # #         areas_for_improvement  = ai_feedback["improvements"],
# # #         actionable_suggestions = ai_feedback["study_plan"],
# # #         report_pdf             = b""
# # #     )

# # #     st.session_state.final_score         = total_score
# # #     st.session_state.skill_scores        = skill_scores
# # #     st.session_state.ai_feedback         = ai_feedback
# # #     st.session_state.performance_summary = performance_summary
# # #     st.session_state.interview_finalized = True


# # # # ─────────────────────────────────────────────
# # # # RESULTS SCREEN
# # # # ─────────────────────────────────────────────
# # # def show_results():
# # #     score        = st.session_state.get("final_score", 0)
# # #     skill_scores = st.session_state.get("skill_scores", {})
# # #     feedback     = st.session_state.get("ai_feedback", {})
# # #     summary      = st.session_state.get("performance_summary", "")

# # #     def to_25(v):  return round(float(v or 0) * 2.5, 1)
# # #     def to_100(v): return round(float(v or 0) * 10.0, 1)

# # #     st.markdown("## Interview Complete")
# # #     st.caption(f"Session #{st.session_state.interview_id}")
# # #     st.divider()

# # #     c1, c2, c3, c4, c5 = st.columns(5)
# # #     c1.metric("Overall",         f"{to_100(score)}/100")
# # #     c2.metric("Technical",       f"{to_25(skill_scores.get('technical_knowledge', 0))}/25")
# # #     c3.metric("Communication",   f"{to_25(skill_scores.get('communication_skills', 0))}/25")
# # #     c4.metric("Problem Solving", f"{to_25(skill_scores.get('problem_solving', 0))}/25")
# # #     c5.metric("Projects",        f"{to_25(skill_scores.get('project_understanding', 0))}/25")

# # #     st.divider()
# # #     st.markdown("### Performance Summary")
# # #     st.info(summary)

# # #     col_a, col_b = st.columns(2)
# # #     with col_a:
# # #         st.markdown("### Strengths")
# # #         st.success(feedback.get("strengths", ""))
# # #     with col_b:
# # #         st.markdown("### Areas for Improvement")
# # #         st.warning(feedback.get("improvements", ""))

# # #     st.markdown("### Study Plan")
# # #     st.write(feedback.get("study_plan", ""))
# # #     st.divider()

# # #     if st.button("Download Evaluation Report (PDF)", type="primary",
# # #                  use_container_width=True):
# # #         try:
# # #             from utils.pdf_report import generate_pdf
# # #             pdf_bytes = generate_pdf(st.session_state.interview_id)
# # #             st.download_button(
# # #                 label               = "Click to Download PDF",
# # #                 data                = pdf_bytes,
# # #                 file_name           = f"pyspace_report_{st.session_state.interview_id}.pdf",
# # #                 mime                = "application/pdf",
# # #                 use_container_width = True
# # #             )
# # #         except Exception as e:
# # #             st.error(f"PDF generation failed: {e}")

# # #     st.divider()
# # #     if st.button("Start New Interview", use_container_width=True):
# # #         keys = [
# # #             "interview_initialized", "interview_id", "interview_stage",
# # #             "stage_q_index", "total_q_index", "current_question", "current_level",
# # #             "qa_history", "asked_questions", "adaptive_mode", "adaptive_direction",
# # #             "interview_complete", "interview_finalized", "start_time", "final_score",
# # #             "skill_scores", "ai_feedback", "performance_summary", "interview_started",
# # #             "resume_path", "resume_text", "question_displayed", "question_time"
# # #         ]
# # #         for k in keys:
# # #             st.session_state.pop(k, None)
# # #         st.rerun()


# # # # ─────────────────────────────────────────────
# # # # MAIN INTERVIEW FLOW
# # # # ─────────────────────────────────────────────
# # # def interview_flow():

# # #     # 1. Dark theme + styles
# # #     inject_interview_styles()

# # #     # 2. Init
# # #     init_interview()
# # #     resume_text = get_resume_text()

# # #     # 3. Create DB record once
# # #     if st.session_state.interview_id is None:
# # #         filename = os.path.basename(st.session_state.get("resume_path", "unknown"))
# # #         st.session_state.interview_id = create_interview(
# # #             user_email      = st.session_state["user_email"],
# # #             resume_text     = resume_text,
# # #             resume_filename = filename
# # #         )

# # #     # 4. Results / finalize check
# # #     if st.session_state.get("interview_finalized"):
# # #         show_results()
# # #         return

# # #     if st.session_state.interview_complete or time_expired():
# # #         finalize_interview()
# # #         st.rerun()
# # #         return

# # #     # ── HEADER ──────────────────────────────────────────────────
# # #     elapsed    = int(time.time() - st.session_state.start_time)
# # #     mins, secs = divmod(elapsed, 60)
# # #     remaining  = max(0, TIME_LIMIT - elapsed)
# # #     rem_m, rem_s = divmod(remaining, 60)

# # #     total_done  = st.session_state.total_q_index
# # #     # Total expected = base 10 + any adaptive questions fired so far
# # #     total_exp   = max(BASE_Q_COUNT, total_done + 1)
# # #     progress    = min(total_done / BASE_Q_COUNT, 1.0)
# # #     stage       = st.session_state.interview_stage
# # #     stage_label = STAGE_LABELS_CLEAN.get(stage, stage.title())

# # #     h1, h2, h3, h4 = st.columns([4, 1, 1, 1])
# # #     with h1:
# # #         st.progress(
# # #             progress,
# # #             text=f"{stage_label} Stage  ·  Question {total_done + 1}"
# # #         )
# # #     with h2:
# # #         st.metric("Elapsed", f"{mins:02d}:{secs:02d}")
# # #     with h3:
# # #         st.metric("Remaining", f"{rem_m:02d}:{rem_s:02d}")
# # #     with h4:
# # #         if st.button("End Interview", type="secondary"):
# # #             st.session_state.interview_complete = True
# # #             st.rerun()

# # #     st.divider()

# # #     # ── CONVERSATION HISTORY ─────────────────────────────────────
# # #     for i, qa in enumerate(st.session_state.qa_history, 1):

# # #         # LISA bubble
# # #         with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
# # #             st.markdown(
# # #                 f'<span style="font-size:11px;font-weight:700;color:#00d4ff;">'
# # #                 f'LISA &nbsp;•&nbsp; AI Interviewer</span>'
# # #                 f'{stage_badge(qa["level"])}',
# # #                 unsafe_allow_html=True
# # #             )
# # #             st.markdown(strip_emojis(qa["question"]))
# # #             st.caption(qa.get("timestamp", ""))

# # #         # User bubble
# # #         with st.chat_message("user", avatar="👤"):
# # #             st.markdown(
# # #                 f'<span style="font-size:11px;font-weight:700;color:#60a5fa;">'
# # #                 f'{st.session_state.get("user_name", "You")}</span>',
# # #                 unsafe_allow_html=True
# # #             )
# # #             st.markdown(qa["answer"])
# # #             st.caption(qa.get("timestamp", ""))

# # #     # ── GENERATE CURRENT QUESTION ─────────────────────────────────
# # #     if st.session_state.current_question is None:
# # #         with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
# # #             show_typing_indicator()

# # #         question, level = get_next_question(resume_text)

# # #         # Track to prevent duplicates
# # #         st.session_state.asked_questions.add(question.strip().lower()[:80])

# # #         st.session_state.current_question   = question
# # #         st.session_state.current_level      = level
# # #         st.session_state.question_displayed = False
# # #         st.session_state.question_time      = now_time()
# # #         st.rerun()

# # #     question = st.session_state.current_question
# # #     level    = st.session_state.current_level

# # #     # ── ADAPTIVE BANNER ───────────────────────────────────────────
# # #     if st.session_state.adaptive_mode:
# # #         d   = st.session_state.adaptive_direction
# # #         msg = (
# # #             "Let me rephrase that — I want to make sure we cover this concept."
# # #             if d == "easier"
# # #             else "Strong response. Let me take this a level deeper."
# # #         )
# # #         st.markdown(
# # #             f'<div style="background:#0f172a;border-left:3px solid #6366f1;'
# # #             f'border-radius:0 8px 8px 0;padding:10px 16px;margin:8px 0;'
# # #             f'font-size:13px;color:#a5b4fc;">LISA — {msg}</div>',
# # #             unsafe_allow_html=True
# # #         )

# # #     # ── LISA QUESTION BUBBLE ──────────────────────────────────────
# # #     with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
# # #         st.markdown(
# # #             f'<span style="font-size:11px;font-weight:700;color:#00d4ff;">'
# # #             f'LISA &nbsp;•&nbsp; AI Interviewer</span>'
# # #             f'{stage_badge(level)}'
# # #             f'<span style="font-size:11px;color:#374151;margin-left:8px;">'
# # #             f'Question {total_done + 1}</span>',
# # #             unsafe_allow_html=True
# # #         )

# # #         clean_q = strip_emojis(question)

# # #         if not st.session_state.question_displayed:
# # #             # ── VOICE plays first (hidden) ──
# # #             play_lisa_voice(clean_q)
# # #             # ── TYPEWRITER runs simultaneously ──
# # #             st.write_stream(typewriter_stream(clean_q, WORDS_PER_SECOND))
# # #             st.session_state.question_displayed = True
# # #         else:
# # #             st.markdown(clean_q)

# # #         st.caption(st.session_state.get("question_time", now_time()))

# # #     # ── USER INPUT ────────────────────────────────────────────────
# # #     # Step 1 — if voice was transcribed in previous run, show + submit
# # #     prefill = st.session_state.pop(f"prefill_{total_done}", None)
# # #     if prefill:
# # #         with st.chat_message("user", avatar="👤"):
# # #             st.markdown(
# # #                 f'<span style="font-size:11px;font-weight:700;color:#60a5fa;">'
# # #                 f'{st.session_state.get("user_name", "You")}</span>',
# # #                 unsafe_allow_html=True
# # #             )
# # #             st.markdown(prefill)
# # #             st.caption(now_time())
# # #         handle_answer(prefill, resume_text)
# # #         return

# # #     # Step 2 — mic widget (styled dark, above chat bar)
# # #     audio_input = st.audio_input(
# # #         "🎙️",
# # #         key              = f"voice_{total_done}",
# # #         label_visibility = "collapsed"
# # #     )

# # #     if audio_input:
# # #         with st.spinner("Transcribing your answer..."):
# # #             try:
# # #                 from utils.speech_to_text import transcribe_audio
# # #                 transcribed = transcribe_audio(audio_input)
# # #             except Exception as e:
# # #                 transcribed = ""
# # #                 st.warning(f"Transcription error: {e}")

# # #         if transcribed and transcribed.strip():
# # #             st.session_state[f"prefill_{total_done}"] = transcribed.strip()
# # #             st.rerun()
# # #         else:
# # #             st.warning(
# # #                 "Could not transcribe audio. "
# # #                 "Check that your mic recorded correctly, "
# # #                 "or type your answer below."
# # #             )

# # #     # Step 3 — chat_input pinned at bottom, Enter to submit
# # #     typed = st.chat_input(
# # #         "Type your answer and press Enter...",
# # #         key = f"chat_{total_done}"
# # #     )
# # #     if typed:
# # #         answer = typed.strip()
# # #         if not answer:
# # #             return
# # #         if answer.lower() == "/skip":
# # #             answer = "I am not sure about this question."
# # #         with st.chat_message("user", avatar="👤"):
# # #             st.markdown(
# # #                 f'<span style="font-size:11px;font-weight:700;color:#60a5fa;">'
# # #                 f'{st.session_state.get("user_name", "You")}</span>',
# # #                 unsafe_allow_html=True
# # #             )
# # #             st.markdown(answer)
# # #             st.caption(now_time())
# # #         handle_answer(answer, resume_text)
# # # # import os
# # # # import time
# # # # import base64
# # # # import streamlit as st

# # # # from interview.lisa_ai import generate_question, evaluate_answer, generate_session_feedback
# # # # from interview.scoring import (
# # # #     should_trigger_adaptive,
# # # #     calculate_total_score,
# # # #     calculate_skill_scores,
# # # #     generate_performance_summary
# # # # )
# # # # from database.db import (
# # # #     create_interview,
# # # #     save_question,
# # # #     complete_interview,
# # # #     save_report
# # # # )
# # # # from config import QUESTIONS_PER_LEVEL, INTRO_QUESTION
# # # # from assets.interview_style import (
# # # #     inject_interview_styles,
# # # #     show_typing_indicator,
# # # #     stage_badge,
# # # #     strip_emojis,
# # # #     now_time,
# # # #     LISA_AVATAR_PATH,
# # # #     STAGE_LABELS_CLEAN
# # # # )

# # # # # ─────────────────────────────────────────────
# # # # # CONSTANTS
# # # # # ─────────────────────────────────────────────
# # # # STAGES       = ["easy", "medium", "hard"]
# # # # TIME_LIMIT   = 30 * 60   # 30 minutes
# # # # BASE_Q_COUNT = sum(QUESTIONS_PER_LEVEL.values())   # 10

# # # # # Words per second for typewriter — matches gTTS speed
# # # # WORDS_PER_SECOND = 2.2


# # # # # ─────────────────────────────────────────────
# # # # # TYPEWRITER GENERATOR
# # # # # ─────────────────────────────────────────────
# # # # def typewriter_stream(text: str, wps: float = WORDS_PER_SECOND):
# # # #     words = text.split()
# # # #     delay = 1.0 / wps
# # # #     for word in words:
# # # #         yield word + " "
# # # #         time.sleep(delay)


# # # # # ─────────────────────────────────────────────
# # # # # PLAY LISA VOICE — hidden HTML audio player
# # # # # Returns True if played, False on failure
# # # # # ─────────────────────────────────────────────
# # # # def play_lisa_voice(text: str) -> bool:
# # # #     try:
# # # #         from utils.text_to_speech import speak
# # # #         audio_path = speak(text)
# # # #         if not audio_path or not os.path.exists(audio_path):
# # # #             return False
# # # #         with open(audio_path, "rb") as f:
# # # #             audio_bytes = f.read()
# # # #         b64 = base64.b64encode(audio_bytes).decode()
# # # #         # Inject hidden autoplay — no widget visible
# # # #         st.markdown(
# # # #             f'<audio autoplay style="display:none;">'
# # # #             f'<source src="data:audio/mp3;base64,{b64}" type="audio/mp3">'
# # # #             f'</audio>',
# # # #             unsafe_allow_html=True
# # # #         )
# # # #         return True
# # # #     except Exception:
# # # #         return False   # Voice is optional — never crash the interview


# # # # # ─────────────────────────────────────────────
# # # # # SESSION STATE INIT
# # # # # ─────────────────────────────────────────────
# # # # def init_interview():
# # # #     if st.session_state.get("interview_initialized"):
# # # #         return

# # # #     st.session_state.interview_initialized = True
# # # #     st.session_state.interview_id          = None
# # # #     st.session_state.interview_stage       = "easy"
# # # #     st.session_state.stage_q_index         = 0
# # # #     st.session_state.total_q_index         = 0
# # # #     st.session_state.current_question      = None
# # # #     st.session_state.current_level         = "easy"
# # # #     st.session_state.qa_history            = []
# # # #     st.session_state.asked_questions       = set()   # ← prevent duplicates
# # # #     st.session_state.adaptive_mode         = False
# # # #     st.session_state.adaptive_direction    = ""
# # # #     st.session_state.interview_complete    = False
# # # #     st.session_state.interview_finalized   = False
# # # #     st.session_state.start_time            = time.time()
# # # #     st.session_state.question_displayed    = False
# # # #     st.session_state.question_time         = now_time()


# # # # # ─────────────────────────────────────────────
# # # # # RESUME
# # # # # ─────────────────────────────────────────────
# # # # def get_resume_text() -> str:
# # # #     if st.session_state.get("resume_text"):
# # # #         return st.session_state.resume_text
# # # #     resume_path = st.session_state.get("resume_path")
# # # #     if resume_path and os.path.exists(resume_path):
# # # #         from utils.resume_parser import extract_resume_text
# # # #         text = extract_resume_text(resume_path)
# # # #         st.session_state.resume_text = text
# # # #         return text
# # # #     return "No resume provided."


# # # # # ─────────────────────────────────────────────
# # # # # QUESTION GENERATION — with duplicate prevention
# # # # # ─────────────────────────────────────────────
# # # # def get_next_question(resume_text: str) -> tuple[str, str]:
# # # #     total_index = st.session_state.total_q_index
# # # #     last_qa     = st.session_state.qa_history[-1] if st.session_state.qa_history else {}
# # # #     asked       = st.session_state.asked_questions

# # # #     # Q1 is always the intro — hardcoded, no API
# # # #     if total_index == 0:
# # # #         return INTRO_QUESTION, "easy"

# # # #     # Build "already asked" context for the prompt
# # # #     asked_context = list(asked)[-8:] if asked else []   # last 8 to keep prompt short

# # # #     if st.session_state.adaptive_mode:
# # # #         question = generate_question(
# # # #             level           = "adaptive",
# # # #             resume          = resume_text,
# # # #             previous_answer = last_qa.get("answer", ""),
# # # #             previous_score  = last_qa.get("score", 5.0),
# # # #             asked_questions = asked_context
# # # #         )
# # # #         return question, "adaptive"

# # # #     stage    = st.session_state.interview_stage
# # # #     question = generate_question(
# # # #         level           = stage,
# # # #         resume          = resume_text,
# # # #         previous_answer = last_qa.get("answer"),
# # # #         previous_score  = last_qa.get("score"),
# # # #         asked_questions = asked_context
# # # #     )
# # # #     return question, stage


# # # # # ─────────────────────────────────────────────
# # # # # STAGE PROGRESSION
# # # # # ─────────────────────────────────────────────
# # # # def advance_stage():
# # # #     current = st.session_state.interview_stage
# # # #     idx     = STAGES.index(current)
# # # #     if idx + 1 < len(STAGES):
# # # #         st.session_state.interview_stage = STAGES[idx + 1]
# # # #         st.session_state.stage_q_index  = 0
# # # #     else:
# # # #         st.session_state.interview_complete = True


# # # # def time_expired() -> bool:
# # # #     return (time.time() - st.session_state.start_time) >= TIME_LIMIT


# # # # # ─────────────────────────────────────────────
# # # # # HANDLE ANSWER
# # # # # ─────────────────────────────────────────────
# # # # def handle_answer(answer: str, resume_text: str):
# # # #     question = st.session_state.current_question
# # # #     level    = st.session_state.current_level

# # # #     # Evaluate silently — score hidden from chat
# # # #     with st.spinner("LISA is reviewing your answer..."):
# # # #         evaluation = evaluate_answer(question, answer)

# # # #     score        = evaluation["score"]
# # # #     ideal_answer = evaluation["ideal_answer"]
# # # #     feedback     = evaluation["feedback"]

# # # #     # Save to DB
# # # #     save_question(
# # # #         interview_id        = st.session_state.interview_id,
# # # #         question_number     = st.session_state.total_q_index + 1,
# # # #         difficulty_level    = level,
# # # #         topic               = None,
# # # #         question_text       = question,
# # # #         user_answer         = answer,
# # # #         ai_suggested_answer = ideal_answer,
# # # #         score               = score,
# # # #         feedback            = feedback
# # # #     )

# # # #     # Store in history
# # # #     st.session_state.qa_history.append({
# # # #         "question":     question,
# # # #         "answer":       answer,
# # # #         "score":        score,
# # # #         "feedback":     feedback,
# # # #         "ideal_answer": ideal_answer,
# # # #         "level":        level,
# # # #         "timestamp":    now_time()
# # # #     })

# # # #     st.session_state.total_q_index     += 1
# # # #     st.session_state.question_displayed = False

# # # #     # Adaptive trigger
# # # #     if not st.session_state.adaptive_mode and level in ["medium", "hard"]:
# # # #         trigger, direction = should_trigger_adaptive(level, score)
# # # #         if trigger:
# # # #             st.session_state.adaptive_mode      = True
# # # #             st.session_state.adaptive_direction = direction
# # # #             st.session_state.current_question   = None
# # # #             st.rerun()
# # # #             return

# # # #     st.session_state.adaptive_mode      = False
# # # #     st.session_state.adaptive_direction = ""

# # # #     # Advance stage
# # # #     st.session_state.stage_q_index += 1
# # # #     stage = st.session_state.interview_stage
# # # #     if st.session_state.stage_q_index >= QUESTIONS_PER_LEVEL.get(stage, 3):
# # # #         advance_stage()

# # # #     st.session_state.current_question = None
# # # #     st.rerun()


# # # # # ─────────────────────────────────────────────
# # # # # FINALIZE
# # # # # ─────────────────────────────────────────────
# # # # def finalize_interview():
# # # #     qa_history = st.session_state.qa_history
# # # #     if not qa_history:
# # # #         return

# # # #     questions_scored = [
# # # #         {
# # # #             "difficulty_level": q["level"],
# # # #             "score":            q["score"],
# # # #             "topic":            "",
# # # #             "question_text":    q["question"]
# # # #         }
# # # #         for q in qa_history
# # # #     ]

# # # #     total_score         = calculate_total_score(questions_scored)
# # # #     skill_scores        = calculate_skill_scores(questions_scored)
# # # #     performance_summary = generate_performance_summary(total_score, skill_scores)

# # # #     qa_pairs = [
# # # #         {"question": q["question"], "user_answer": q["answer"], "score": q["score"]}
# # # #         for q in qa_history
# # # #     ]

# # # #     with st.spinner("LISA is generating your full evaluation report..."):
# # # #         ai_feedback = generate_session_feedback(qa_pairs)

# # # #     complete_interview(st.session_state.interview_id, total_score)

# # # #     save_report(
# # # #         interview_id           = st.session_state.interview_id,
# # # #         overall_score          = total_score,
# # # #         performance_summary    = performance_summary,
# # # #         technical_knowledge    = skill_scores["technical_knowledge"],
# # # #         communication_skills   = skill_scores["communication_skills"],
# # # #         problem_solving        = skill_scores["problem_solving"],
# # # #         project_understanding  = skill_scores["project_understanding"],
# # # #         strengths              = ai_feedback["strengths"],
# # # #         areas_for_improvement  = ai_feedback["improvements"],
# # # #         actionable_suggestions = ai_feedback["study_plan"],
# # # #         report_pdf             = b""
# # # #     )

# # # #     st.session_state.final_score         = total_score
# # # #     st.session_state.skill_scores        = skill_scores
# # # #     st.session_state.ai_feedback         = ai_feedback
# # # #     st.session_state.performance_summary = performance_summary
# # # #     st.session_state.interview_finalized = True


# # # # # ─────────────────────────────────────────────
# # # # # RESULTS SCREEN
# # # # # ─────────────────────────────────────────────
# # # # def show_results():
# # # #     score        = st.session_state.get("final_score", 0)
# # # #     skill_scores = st.session_state.get("skill_scores", {})
# # # #     feedback     = st.session_state.get("ai_feedback", {})
# # # #     summary      = st.session_state.get("performance_summary", "")

# # # #     def to_25(v):  return round(float(v or 0) * 2.5, 1)
# # # #     def to_100(v): return round(float(v or 0) * 10.0, 1)

# # # #     st.markdown("## Interview Complete")
# # # #     st.caption(f"Session #{st.session_state.interview_id}")
# # # #     st.divider()

# # # #     c1, c2, c3, c4, c5 = st.columns(5)
# # # #     c1.metric("Overall",         f"{to_100(score)}/100")
# # # #     c2.metric("Technical",       f"{to_25(skill_scores.get('technical_knowledge', 0))}/25")
# # # #     c3.metric("Communication",   f"{to_25(skill_scores.get('communication_skills', 0))}/25")
# # # #     c4.metric("Problem Solving", f"{to_25(skill_scores.get('problem_solving', 0))}/25")
# # # #     c5.metric("Projects",        f"{to_25(skill_scores.get('project_understanding', 0))}/25")

# # # #     st.divider()
# # # #     st.markdown("### Performance Summary")
# # # #     st.info(summary)

# # # #     col_a, col_b = st.columns(2)
# # # #     with col_a:
# # # #         st.markdown("### Strengths")
# # # #         st.success(feedback.get("strengths", ""))
# # # #     with col_b:
# # # #         st.markdown("### Areas for Improvement")
# # # #         st.warning(feedback.get("improvements", ""))

# # # #     st.markdown("### Study Plan")
# # # #     st.write(feedback.get("study_plan", ""))
# # # #     st.divider()

# # # #     if st.button("Download Evaluation Report (PDF)", type="primary",
# # # #                  use_container_width=True):
# # # #         try:
# # # #             from utils.pdf_report import generate_pdf
# # # #             pdf_bytes = generate_pdf(st.session_state.interview_id)
# # # #             st.download_button(
# # # #                 label               = "Click to Download PDF",
# # # #                 data                = pdf_bytes,
# # # #                 file_name           = f"pyspace_report_{st.session_state.interview_id}.pdf",
# # # #                 mime                = "application/pdf",
# # # #                 use_container_width = True
# # # #             )
# # # #         except Exception as e:
# # # #             st.error(f"PDF generation failed: {e}")

# # # #     st.divider()
# # # #     if st.button("Start New Interview", use_container_width=True):
# # # #         keys = [
# # # #             "interview_initialized", "interview_id", "interview_stage",
# # # #             "stage_q_index", "total_q_index", "current_question", "current_level",
# # # #             "qa_history", "asked_questions", "adaptive_mode", "adaptive_direction",
# # # #             "interview_complete", "interview_finalized", "start_time", "final_score",
# # # #             "skill_scores", "ai_feedback", "performance_summary", "interview_started",
# # # #             "resume_path", "resume_text", "question_displayed", "question_time"
# # # #         ]
# # # #         for k in keys:
# # # #             st.session_state.pop(k, None)
# # # #         st.rerun()


# # # # # ─────────────────────────────────────────────
# # # # # MAIN INTERVIEW FLOW
# # # # # ─────────────────────────────────────────────
# # # # def interview_flow():

# # # #     # 1. Dark theme + styles
# # # #     inject_interview_styles()

# # # #     # 2. Init
# # # #     init_interview()
# # # #     resume_text = get_resume_text()

# # # #     # 3. Create DB record once
# # # #     if st.session_state.interview_id is None:
# # # #         filename = os.path.basename(st.session_state.get("resume_path", "unknown"))
# # # #         st.session_state.interview_id = create_interview(
# # # #             user_email      = st.session_state["user_email"],
# # # #             resume_text     = resume_text,
# # # #             resume_filename = filename
# # # #         )

# # # #     # 4. Results / finalize check
# # # #     if st.session_state.get("interview_finalized"):
# # # #         show_results()
# # # #         return

# # # #     if st.session_state.interview_complete or time_expired():
# # # #         finalize_interview()
# # # #         st.rerun()
# # # #         return

# # # #     # ── HEADER ──────────────────────────────────────────────────
# # # #     elapsed    = int(time.time() - st.session_state.start_time)
# # # #     mins, secs = divmod(elapsed, 60)
# # # #     remaining  = max(0, TIME_LIMIT - elapsed)
# # # #     rem_m, rem_s = divmod(remaining, 60)

# # # #     total_done  = st.session_state.total_q_index
# # # #     # Total expected = base 10 + any adaptive questions fired so far
# # # #     total_exp   = max(BASE_Q_COUNT, total_done + 1)
# # # #     progress    = min(total_done / BASE_Q_COUNT, 1.0)
# # # #     stage       = st.session_state.interview_stage
# # # #     stage_label = STAGE_LABELS_CLEAN.get(stage, stage.title())

# # # #     h1, h2, h3, h4 = st.columns([4, 1, 1, 1])
# # # #     with h1:
# # # #         st.progress(
# # # #             progress,
# # # #             text=f"{stage_label} Stage  ·  Question {total_done + 1}"
# # # #         )
# # # #     with h2:
# # # #         st.metric("Elapsed", f"{mins:02d}:{secs:02d}")
# # # #     with h3:
# # # #         st.metric("Remaining", f"{rem_m:02d}:{rem_s:02d}")
# # # #     with h4:
# # # #         if st.button("End Interview", type="secondary"):
# # # #             st.session_state.interview_complete = True
# # # #             st.rerun()

# # # #     st.divider()

# # # #     # ── CONVERSATION HISTORY ─────────────────────────────────────
# # # #     for i, qa in enumerate(st.session_state.qa_history, 1):

# # # #         # LISA bubble
# # # #         with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
# # # #             st.markdown(
# # # #                 f'<span style="font-size:11px;font-weight:700;color:#00d4ff;">'
# # # #                 f'LISA &nbsp;•&nbsp; AI Interviewer</span>'
# # # #                 f'{stage_badge(qa["level"])}',
# # # #                 unsafe_allow_html=True
# # # #             )
# # # #             st.markdown(strip_emojis(qa["question"]))
# # # #             st.caption(qa.get("timestamp", ""))

# # # #         # User bubble
# # # #         with st.chat_message("user", avatar="👤"):
# # # #             st.markdown(
# # # #                 f'<span style="font-size:11px;font-weight:700;color:#60a5fa;">'
# # # #                 f'{st.session_state.get("user_name", "You")}</span>',
# # # #                 unsafe_allow_html=True
# # # #             )
# # # #             st.markdown(qa["answer"])
# # # #             st.caption(qa.get("timestamp", ""))

# # # #     # ── GENERATE CURRENT QUESTION ─────────────────────────────────
# # # #     if st.session_state.current_question is None:
# # # #         with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
# # # #             show_typing_indicator()

# # # #         question, level = get_next_question(resume_text)

# # # #         # Track to prevent duplicates
# # # #         st.session_state.asked_questions.add(question.strip().lower()[:80])

# # # #         st.session_state.current_question   = question
# # # #         st.session_state.current_level      = level
# # # #         st.session_state.question_displayed = False
# # # #         st.session_state.question_time      = now_time()
# # # #         st.rerun()

# # # #     question = st.session_state.current_question
# # # #     level    = st.session_state.current_level

# # # #     # ── ADAPTIVE BANNER ───────────────────────────────────────────
# # # #     if st.session_state.adaptive_mode:
# # # #         d   = st.session_state.adaptive_direction
# # # #         msg = (
# # # #             "Let me rephrase that — I want to make sure we cover this concept."
# # # #             if d == "easier"
# # # #             else "Strong response. Let me take this a level deeper."
# # # #         )
# # # #         st.markdown(
# # # #             f'<div style="background:#0f172a;border-left:3px solid #6366f1;'
# # # #             f'border-radius:0 8px 8px 0;padding:10px 16px;margin:8px 0;'
# # # #             f'font-size:13px;color:#a5b4fc;">LISA — {msg}</div>',
# # # #             unsafe_allow_html=True
# # # #         )

# # # #     # ── LISA QUESTION BUBBLE ──────────────────────────────────────
# # # #     with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
# # # #         st.markdown(
# # # #             f'<span style="font-size:11px;font-weight:700;color:#00d4ff;">'
# # # #             f'LISA &nbsp;•&nbsp; AI Interviewer</span>'
# # # #             f'{stage_badge(level)}'
# # # #             f'<span style="font-size:11px;color:#374151;margin-left:8px;">'
# # # #             f'Question {total_done + 1}</span>',
# # # #             unsafe_allow_html=True
# # # #         )

# # # #         clean_q = strip_emojis(question)

# # # #         if not st.session_state.question_displayed:
# # # #             # ── VOICE plays first (hidden) ──
# # # #             play_lisa_voice(clean_q)
# # # #             # ── TYPEWRITER runs simultaneously ──
# # # #             st.write_stream(typewriter_stream(clean_q, WORDS_PER_SECOND))
# # # #             st.session_state.question_displayed = True
# # # #         else:
# # # #             st.markdown(clean_q)

# # # #         st.caption(st.session_state.get("question_time", now_time()))

# # # #     # ── USER INPUT ────────────────────────────────────────────────
# # # #     # Step 1 — if voice was transcribed in previous run, show + submit
# # # #     prefill = st.session_state.pop(f"prefill_{total_done}", None)
# # # #     if prefill:
# # # #         with st.chat_message("user", avatar="👤"):
# # # #             st.markdown(
# # # #                 f'<span style="font-size:11px;font-weight:700;color:#60a5fa;">'
# # # #                 f'{st.session_state.get("user_name", "You")}</span>',
# # # #                 unsafe_allow_html=True
# # # #             )
# # # #             st.markdown(prefill)
# # # #             st.caption(now_time())
# # # #         handle_answer(prefill, resume_text)
# # # #         return

# # # #     # Step 2 — mic widget (styled dark, above chat bar)
# # # #     audio_input = st.audio_input(
# # # #         "🎙️",
# # # #         key              = f"voice_{total_done}",
# # # #         label_visibility = "collapsed"
# # # #     )

# # # #     if audio_input:
# # # #         with st.spinner("Transcribing your answer..."):
# # # #             try:
# # # #                 from utils.speech_to_text import transcribe_audio
# # # #                 transcribed = transcribe_audio(audio_input)
# # # #             except Exception as e:
# # # #                 transcribed = ""
# # # #                 st.warning(f"Transcription failed: {e}")

# # # #         if transcribed and transcribed.strip():
# # # #             st.session_state[f"prefill_{total_done}"] = transcribed.strip()
# # # #             st.rerun()
# # # #         else:
# # # #             st.warning("Could not transcribe. Please type your answer below.")

# # # #     # Step 3 — chat_input pinned at bottom, Enter to submit
# # # #     typed = st.chat_input(
# # # #         "Type your answer and press Enter...",
# # # #         key = f"chat_{total_done}"
# # # #     )
# # # #     if typed:
# # # #         answer = typed.strip()
# # # #         if not answer:
# # # #             return
# # # #         if answer.lower() == "/skip":
# # # #             answer = "I am not sure about this question."
# # # #         with st.chat_message("user", avatar="👤"):
# # # #             st.markdown(
# # # #                 f'<span style="font-size:11px;font-weight:700;color:#60a5fa;">'
# # # #                 f'{st.session_state.get("user_name", "You")}</span>',
# # # #                 unsafe_allow_html=True
# # # #             )
# # # #             st.markdown(answer)
# # # #             st.caption(now_time())
# # # #         handle_answer(answer, resume_text)
# # # # # import os
# # # # # import time
# # # # # import base64
# # # # # import streamlit as st

# # # # # from interview.lisa_ai import generate_question, evaluate_answer, generate_session_feedback
# # # # # from interview.scoring import (
# # # # #     should_trigger_adaptive,
# # # # #     calculate_total_score,
# # # # #     calculate_skill_scores,
# # # # #     generate_performance_summary
# # # # # )
# # # # # from database.db import (
# # # # #     create_interview,
# # # # #     save_question,
# # # # #     complete_interview,
# # # # #     save_report
# # # # # )
# # # # # from config import QUESTIONS_PER_LEVEL, INTRO_QUESTION
# # # # # from assets.interview_style import (
# # # # #     inject_interview_styles,
# # # # #     show_typing_indicator,
# # # # #     stage_badge,
# # # # #     strip_emojis,
# # # # #     now_time,
# # # # #     LISA_AVATAR_PATH,
# # # # #     STAGE_LABELS_CLEAN
# # # # # )

# # # # # # ─────────────────────────────────────────────
# # # # # # CONSTANTS
# # # # # # ─────────────────────────────────────────────
# # # # # STAGES       = ["easy", "medium", "hard"]
# # # # # TIME_LIMIT   = 30 * 60   # 30 minutes
# # # # # BASE_Q_COUNT = sum(QUESTIONS_PER_LEVEL.values())   # 10

# # # # # # Words per second for typewriter — matches gTTS speed
# # # # # WORDS_PER_SECOND = 2.2


# # # # # # ─────────────────────────────────────────────
# # # # # # TYPEWRITER GENERATOR
# # # # # # ─────────────────────────────────────────────
# # # # # def typewriter_stream(text: str, wps: float = WORDS_PER_SECOND):
# # # # #     words = text.split()
# # # # #     delay = 1.0 / wps
# # # # #     for word in words:
# # # # #         yield word + " "
# # # # #         time.sleep(delay)


# # # # # # ─────────────────────────────────────────────
# # # # # # PLAY LISA VOICE — hidden HTML audio player
# # # # # # Returns True if played, False on failure
# # # # # # ─────────────────────────────────────────────
# # # # # def play_lisa_voice(text: str) -> bool:
# # # # #     try:
# # # # #         from utils.text_to_speech import speak
# # # # #         audio_path = speak(text)
# # # # #         if not audio_path or not os.path.exists(audio_path):
# # # # #             return False
# # # # #         with open(audio_path, "rb") as f:
# # # # #             audio_bytes = f.read()
# # # # #         b64 = base64.b64encode(audio_bytes).decode()
# # # # #         # Inject hidden autoplay — no widget visible
# # # # #         st.markdown(
# # # # #             f'<audio autoplay style="display:none;">'
# # # # #             f'<source src="data:audio/mp3;base64,{b64}" type="audio/mp3">'
# # # # #             f'</audio>',
# # # # #             unsafe_allow_html=True
# # # # #         )
# # # # #         return True
# # # # #     except Exception:
# # # # #         return False   # Voice is optional — never crash the interview


# # # # # # ─────────────────────────────────────────────
# # # # # # SESSION STATE INIT
# # # # # # ─────────────────────────────────────────────
# # # # # def init_interview():
# # # # #     if st.session_state.get("interview_initialized"):
# # # # #         return

# # # # #     st.session_state.interview_initialized = True
# # # # #     st.session_state.interview_id          = None
# # # # #     st.session_state.interview_stage       = "easy"
# # # # #     st.session_state.stage_q_index         = 0
# # # # #     st.session_state.total_q_index         = 0
# # # # #     st.session_state.current_question      = None
# # # # #     st.session_state.current_level         = "easy"
# # # # #     st.session_state.qa_history            = []
# # # # #     st.session_state.asked_questions       = set()   # ← prevent duplicates
# # # # #     st.session_state.adaptive_mode         = False
# # # # #     st.session_state.adaptive_direction    = ""
# # # # #     st.session_state.interview_complete    = False
# # # # #     st.session_state.interview_finalized   = False
# # # # #     st.session_state.start_time            = time.time()
# # # # #     st.session_state.question_displayed    = False
# # # # #     st.session_state.question_time         = now_time()


# # # # # # ─────────────────────────────────────────────
# # # # # # RESUME
# # # # # # ─────────────────────────────────────────────
# # # # # def get_resume_text() -> str:
# # # # #     if st.session_state.get("resume_text"):
# # # # #         return st.session_state.resume_text
# # # # #     resume_path = st.session_state.get("resume_path")
# # # # #     if resume_path and os.path.exists(resume_path):
# # # # #         from utils.resume_parser import extract_resume_text
# # # # #         text = extract_resume_text(resume_path)
# # # # #         st.session_state.resume_text = text
# # # # #         return text
# # # # #     return "No resume provided."


# # # # # # ─────────────────────────────────────────────
# # # # # # QUESTION GENERATION — with duplicate prevention
# # # # # # ─────────────────────────────────────────────
# # # # # def get_next_question(resume_text: str) -> tuple[str, str]:
# # # # #     total_index = st.session_state.total_q_index
# # # # #     last_qa     = st.session_state.qa_history[-1] if st.session_state.qa_history else {}
# # # # #     asked       = st.session_state.asked_questions

# # # # #     # Q1 is always the intro — hardcoded, no API
# # # # #     if total_index == 0:
# # # # #         return INTRO_QUESTION, "easy"

# # # # #     # Build "already asked" context for the prompt
# # # # #     asked_context = list(asked)[-8:] if asked else []   # last 8 to keep prompt short

# # # # #     if st.session_state.adaptive_mode:
# # # # #         question = generate_question(
# # # # #             level           = "adaptive",
# # # # #             resume          = resume_text,
# # # # #             previous_answer = last_qa.get("answer", ""),
# # # # #             previous_score  = last_qa.get("score", 5.0),
# # # # #             asked_questions = asked_context
# # # # #         )
# # # # #         return question, "adaptive"

# # # # #     stage    = st.session_state.interview_stage
# # # # #     question = generate_question(
# # # # #         level           = stage,
# # # # #         resume          = resume_text,
# # # # #         previous_answer = last_qa.get("answer"),
# # # # #         previous_score  = last_qa.get("score"),
# # # # #         asked_questions = asked_context
# # # # #     )
# # # # #     return question, stage


# # # # # # ─────────────────────────────────────────────
# # # # # # STAGE PROGRESSION
# # # # # # ─────────────────────────────────────────────
# # # # # def advance_stage():
# # # # #     current = st.session_state.interview_stage
# # # # #     idx     = STAGES.index(current)
# # # # #     if idx + 1 < len(STAGES):
# # # # #         st.session_state.interview_stage = STAGES[idx + 1]
# # # # #         st.session_state.stage_q_index  = 0
# # # # #     else:
# # # # #         st.session_state.interview_complete = True


# # # # # def time_expired() -> bool:
# # # # #     return (time.time() - st.session_state.start_time) >= TIME_LIMIT


# # # # # # ─────────────────────────────────────────────
# # # # # # HANDLE ANSWER
# # # # # # ─────────────────────────────────────────────
# # # # # def handle_answer(answer: str, resume_text: str):
# # # # #     question = st.session_state.current_question
# # # # #     level    = st.session_state.current_level

# # # # #     # Evaluate silently — score hidden from chat
# # # # #     with st.spinner("LISA is reviewing your answer..."):
# # # # #         evaluation = evaluate_answer(question, answer)

# # # # #     score        = evaluation["score"]
# # # # #     ideal_answer = evaluation["ideal_answer"]
# # # # #     feedback     = evaluation["feedback"]

# # # # #     # Save to DB
# # # # #     save_question(
# # # # #         interview_id        = st.session_state.interview_id,
# # # # #         question_number     = st.session_state.total_q_index + 1,
# # # # #         difficulty_level    = level,
# # # # #         topic               = None,
# # # # #         question_text       = question,
# # # # #         user_answer         = answer,
# # # # #         ai_suggested_answer = ideal_answer,
# # # # #         score               = score,
# # # # #         feedback            = feedback
# # # # #     )

# # # # #     # Store in history
# # # # #     st.session_state.qa_history.append({
# # # # #         "question":     question,
# # # # #         "answer":       answer,
# # # # #         "score":        score,
# # # # #         "feedback":     feedback,
# # # # #         "ideal_answer": ideal_answer,
# # # # #         "level":        level,
# # # # #         "timestamp":    now_time()
# # # # #     })

# # # # #     st.session_state.total_q_index     += 1
# # # # #     st.session_state.question_displayed = False

# # # # #     # Adaptive trigger
# # # # #     if not st.session_state.adaptive_mode and level in ["medium", "hard"]:
# # # # #         trigger, direction = should_trigger_adaptive(level, score)
# # # # #         if trigger:
# # # # #             st.session_state.adaptive_mode      = True
# # # # #             st.session_state.adaptive_direction = direction
# # # # #             st.session_state.current_question   = None
# # # # #             st.rerun()
# # # # #             return

# # # # #     st.session_state.adaptive_mode      = False
# # # # #     st.session_state.adaptive_direction = ""

# # # # #     # Advance stage
# # # # #     st.session_state.stage_q_index += 1
# # # # #     stage = st.session_state.interview_stage
# # # # #     if st.session_state.stage_q_index >= QUESTIONS_PER_LEVEL.get(stage, 3):
# # # # #         advance_stage()

# # # # #     st.session_state.current_question = None
# # # # #     st.rerun()


# # # # # # ─────────────────────────────────────────────
# # # # # # FINALIZE
# # # # # # ─────────────────────────────────────────────
# # # # # def finalize_interview():
# # # # #     qa_history = st.session_state.qa_history
# # # # #     if not qa_history:
# # # # #         return

# # # # #     questions_scored = [
# # # # #         {
# # # # #             "difficulty_level": q["level"],
# # # # #             "score":            q["score"],
# # # # #             "topic":            "",
# # # # #             "question_text":    q["question"]
# # # # #         }
# # # # #         for q in qa_history
# # # # #     ]

# # # # #     total_score         = calculate_total_score(questions_scored)
# # # # #     skill_scores        = calculate_skill_scores(questions_scored)
# # # # #     performance_summary = generate_performance_summary(total_score, skill_scores)

# # # # #     qa_pairs = [
# # # # #         {"question": q["question"], "user_answer": q["answer"], "score": q["score"]}
# # # # #         for q in qa_history
# # # # #     ]

# # # # #     with st.spinner("LISA is generating your full evaluation report..."):
# # # # #         ai_feedback = generate_session_feedback(qa_pairs)

# # # # #     complete_interview(st.session_state.interview_id, total_score)

# # # # #     save_report(
# # # # #         interview_id           = st.session_state.interview_id,
# # # # #         overall_score          = total_score,
# # # # #         performance_summary    = performance_summary,
# # # # #         technical_knowledge    = skill_scores["technical_knowledge"],
# # # # #         communication_skills   = skill_scores["communication_skills"],
# # # # #         problem_solving        = skill_scores["problem_solving"],
# # # # #         project_understanding  = skill_scores["project_understanding"],
# # # # #         strengths              = ai_feedback["strengths"],
# # # # #         areas_for_improvement  = ai_feedback["improvements"],
# # # # #         actionable_suggestions = ai_feedback["study_plan"],
# # # # #         report_pdf             = b""
# # # # #     )

# # # # #     st.session_state.final_score         = total_score
# # # # #     st.session_state.skill_scores        = skill_scores
# # # # #     st.session_state.ai_feedback         = ai_feedback
# # # # #     st.session_state.performance_summary = performance_summary
# # # # #     st.session_state.interview_finalized = True


# # # # # # ─────────────────────────────────────────────
# # # # # # RESULTS SCREEN
# # # # # # ─────────────────────────────────────────────
# # # # # def show_results():
# # # # #     score        = st.session_state.get("final_score", 0)
# # # # #     skill_scores = st.session_state.get("skill_scores", {})
# # # # #     feedback     = st.session_state.get("ai_feedback", {})
# # # # #     summary      = st.session_state.get("performance_summary", "")

# # # # #     def to_25(v):  return round(float(v or 0) * 2.5, 1)
# # # # #     def to_100(v): return round(float(v or 0) * 10.0, 1)

# # # # #     st.markdown("## Interview Complete")
# # # # #     st.caption(f"Session #{st.session_state.interview_id}")
# # # # #     st.divider()

# # # # #     c1, c2, c3, c4, c5 = st.columns(5)
# # # # #     c1.metric("Overall",         f"{to_100(score)}/100")
# # # # #     c2.metric("Technical",       f"{to_25(skill_scores.get('technical_knowledge', 0))}/25")
# # # # #     c3.metric("Communication",   f"{to_25(skill_scores.get('communication_skills', 0))}/25")
# # # # #     c4.metric("Problem Solving", f"{to_25(skill_scores.get('problem_solving', 0))}/25")
# # # # #     c5.metric("Projects",        f"{to_25(skill_scores.get('project_understanding', 0))}/25")

# # # # #     st.divider()
# # # # #     st.markdown("### Performance Summary")
# # # # #     st.info(summary)

# # # # #     col_a, col_b = st.columns(2)
# # # # #     with col_a:
# # # # #         st.markdown("### Strengths")
# # # # #         st.success(feedback.get("strengths", ""))
# # # # #     with col_b:
# # # # #         st.markdown("### Areas for Improvement")
# # # # #         st.warning(feedback.get("improvements", ""))

# # # # #     st.markdown("### Study Plan")
# # # # #     st.write(feedback.get("study_plan", ""))
# # # # #     st.divider()

# # # # #     if st.button("Download Evaluation Report (PDF)", type="primary",
# # # # #                  use_container_width=True):
# # # # #         try:
# # # # #             from utils.pdf_report import generate_pdf
# # # # #             pdf_bytes = generate_pdf(st.session_state.interview_id)
# # # # #             st.download_button(
# # # # #                 label               = "Click to Download PDF",
# # # # #                 data                = pdf_bytes,
# # # # #                 file_name           = f"pyspace_report_{st.session_state.interview_id}.pdf",
# # # # #                 mime                = "application/pdf",
# # # # #                 use_container_width = True
# # # # #             )
# # # # #         except Exception as e:
# # # # #             st.error(f"PDF generation failed: {e}")

# # # # #     st.divider()
# # # # #     if st.button("Start New Interview", use_container_width=True):
# # # # #         keys = [
# # # # #             "interview_initialized", "interview_id", "interview_stage",
# # # # #             "stage_q_index", "total_q_index", "current_question", "current_level",
# # # # #             "qa_history", "asked_questions", "adaptive_mode", "adaptive_direction",
# # # # #             "interview_complete", "interview_finalized", "start_time", "final_score",
# # # # #             "skill_scores", "ai_feedback", "performance_summary", "interview_started",
# # # # #             "resume_path", "resume_text", "question_displayed", "question_time"
# # # # #         ]
# # # # #         for k in keys:
# # # # #             st.session_state.pop(k, None)
# # # # #         st.rerun()


# # # # # # ─────────────────────────────────────────────
# # # # # # MAIN INTERVIEW FLOW
# # # # # # ─────────────────────────────────────────────
# # # # # def interview_flow():

# # # # #     # 1. Dark theme + styles
# # # # #     inject_interview_styles()

# # # # #     # 2. Init
# # # # #     init_interview()
# # # # #     resume_text = get_resume_text()

# # # # #     # 3. Create DB record once
# # # # #     if st.session_state.interview_id is None:
# # # # #         filename = os.path.basename(st.session_state.get("resume_path", "unknown"))
# # # # #         st.session_state.interview_id = create_interview(
# # # # #             user_email      = st.session_state["user_email"],
# # # # #             resume_text     = resume_text,
# # # # #             resume_filename = filename
# # # # #         )

# # # # #     # 4. Results / finalize check
# # # # #     if st.session_state.get("interview_finalized"):
# # # # #         show_results()
# # # # #         return

# # # # #     if st.session_state.interview_complete or time_expired():
# # # # #         finalize_interview()
# # # # #         st.rerun()
# # # # #         return

# # # # #     # ── HEADER ──────────────────────────────────────────────────
# # # # #     elapsed    = int(time.time() - st.session_state.start_time)
# # # # #     mins, secs = divmod(elapsed, 60)
# # # # #     remaining  = max(0, TIME_LIMIT - elapsed)
# # # # #     rem_m, rem_s = divmod(remaining, 60)

# # # # #     total_done  = st.session_state.total_q_index
# # # # #     # Total expected = base 10 + any adaptive questions fired so far
# # # # #     total_exp   = max(BASE_Q_COUNT, total_done + 1)
# # # # #     progress    = min(total_done / BASE_Q_COUNT, 1.0)
# # # # #     stage       = st.session_state.interview_stage
# # # # #     stage_label = STAGE_LABELS_CLEAN.get(stage, stage.title())

# # # # #     h1, h2, h3, h4 = st.columns([4, 1, 1, 1])
# # # # #     with h1:
# # # # #         st.progress(
# # # # #             progress,
# # # # #             text=f"{stage_label} Stage  ·  Question {total_done + 1}"
# # # # #         )
# # # # #     with h2:
# # # # #         st.metric("Elapsed", f"{mins:02d}:{secs:02d}")
# # # # #     with h3:
# # # # #         st.metric("Remaining", f"{rem_m:02d}:{rem_s:02d}")
# # # # #     with h4:
# # # # #         if st.button("End Interview", type="secondary"):
# # # # #             st.session_state.interview_complete = True
# # # # #             st.rerun()

# # # # #     st.divider()

# # # # #     # ── CONVERSATION HISTORY ─────────────────────────────────────
# # # # #     for i, qa in enumerate(st.session_state.qa_history, 1):

# # # # #         # LISA bubble
# # # # #         with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
# # # # #             st.markdown(
# # # # #                 f'<span style="font-size:11px;font-weight:700;color:#00d4ff;">'
# # # # #                 f'LISA &nbsp;•&nbsp; AI Interviewer</span>'
# # # # #                 f'{stage_badge(qa["level"])}',
# # # # #                 unsafe_allow_html=True
# # # # #             )
# # # # #             st.markdown(strip_emojis(qa["question"]))
# # # # #             st.caption(qa.get("timestamp", ""))

# # # # #         # User bubble
# # # # #         with st.chat_message("user", avatar="👤"):
# # # # #             st.markdown(
# # # # #                 f'<span style="font-size:11px;font-weight:700;color:#60a5fa;">'
# # # # #                 f'{st.session_state.get("user_name", "You")}</span>',
# # # # #                 unsafe_allow_html=True
# # # # #             )
# # # # #             st.markdown(qa["answer"])
# # # # #             st.caption(qa.get("timestamp", ""))

# # # # #     # ── GENERATE CURRENT QUESTION ─────────────────────────────────
# # # # #     if st.session_state.current_question is None:
# # # # #         with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
# # # # #             show_typing_indicator()

# # # # #         question, level = get_next_question(resume_text)

# # # # #         # Track to prevent duplicates
# # # # #         st.session_state.asked_questions.add(question.strip().lower()[:80])

# # # # #         st.session_state.current_question   = question
# # # # #         st.session_state.current_level      = level
# # # # #         st.session_state.question_displayed = False
# # # # #         st.session_state.question_time      = now_time()
# # # # #         st.rerun()

# # # # #     question = st.session_state.current_question
# # # # #     level    = st.session_state.current_level

# # # # #     # ── ADAPTIVE BANNER ───────────────────────────────────────────
# # # # #     if st.session_state.adaptive_mode:
# # # # #         d   = st.session_state.adaptive_direction
# # # # #         msg = (
# # # # #             "Let me rephrase that — I want to make sure we cover this concept."
# # # # #             if d == "easier"
# # # # #             else "Strong response. Let me take this a level deeper."
# # # # #         )
# # # # #         st.markdown(
# # # # #             f'<div style="background:#0f172a;border-left:3px solid #6366f1;'
# # # # #             f'border-radius:0 8px 8px 0;padding:10px 16px;margin:8px 0;'
# # # # #             f'font-size:13px;color:#a5b4fc;">LISA — {msg}</div>',
# # # # #             unsafe_allow_html=True
# # # # #         )

# # # # #     # ── LISA QUESTION BUBBLE ──────────────────────────────────────
# # # # #     with st.chat_message("assistant", avatar=LISA_AVATAR_PATH):
# # # # #         st.markdown(
# # # # #             f'<span style="font-size:11px;font-weight:700;color:#00d4ff;">'
# # # # #             f'LISA &nbsp;•&nbsp; AI Interviewer</span>'
# # # # #             f'{stage_badge(level)}'
# # # # #             f'<span style="font-size:11px;color:#374151;margin-left:8px;">'
# # # # #             f'Question {total_done + 1}</span>',
# # # # #             unsafe_allow_html=True
# # # # #         )

# # # # #         clean_q = strip_emojis(question)

# # # # #         if not st.session_state.question_displayed:
# # # # #             # ── VOICE plays first (hidden) ──
# # # # #             play_lisa_voice(clean_q)
# # # # #             # ── TYPEWRITER runs simultaneously ──
# # # # #             st.write_stream(typewriter_stream(clean_q, WORDS_PER_SECOND))
# # # # #             st.session_state.question_displayed = True
# # # # #         else:
# # # # #             st.markdown(clean_q)

# # # # #         st.caption(st.session_state.get("question_time", now_time()))

# # # # #     # ── USER INPUT ────────────────────────────────────────────────
# # # # #     # Check if voice was transcribed in previous run
# # # # #     prefill = st.session_state.pop(f"prefill_{total_done}", None)

# # # # #     if prefill:
# # # # #         # Show as user bubble then submit
# # # # #         with st.chat_message("user", avatar="👤"):
# # # # #             st.markdown(
# # # # #                 f'<span style="font-size:11px;font-weight:700;color:#60a5fa;">'
# # # # #                 f'{st.session_state.get("user_name", "You")}</span>',
# # # # #                 unsafe_allow_html=True
# # # # #             )
# # # # #             st.markdown(prefill)
# # # # #             st.caption(now_time())
# # # # #         handle_answer(prefill, resume_text)

# # # # #     else:
# # # # #         # ── USER BUBBLE with mic inside ───────────────────────────
# # # # #         with st.chat_message("user", avatar="👤"):
# # # # #             st.markdown(
# # # # #                 f'<span style="font-size:11px;font-weight:700;color:#60a5fa;">'
# # # # #                 f'{st.session_state.get("user_name", "You")}</span>'
# # # # #                 f'<span style="font-size:11px;color:#374151;margin-left:8px;">'
# # # # #                 f'Record or type your answer</span>',
# # # # #                 unsafe_allow_html=True
# # # # #             )

# # # # #             # Mic widget — dark styled via CSS
# # # # #             audio_input = st.audio_input(
# # # # #                 "Record",
# # # # #                 key              = f"voice_{total_done}",
# # # # #                 label_visibility = "collapsed"
# # # # #             )

# # # # #             if audio_input:
# # # # #                 with st.spinner("Transcribing..."):
# # # # #                     try:
# # # # #                         from utils.speech_to_text import transcribe_audio
# # # # #                         transcribed = transcribe_audio(audio_input)
# # # # #                     except Exception:
# # # # #                         transcribed = ""

# # # # #                 if transcribed and transcribed.strip():
# # # # #                     st.session_state[f"prefill_{total_done}"] = transcribed.strip()
# # # # #                     st.rerun()
# # # # #                 else:
# # # # #                     st.caption("Could not transcribe — please type your answer below.")

# # # # #         # ── CHAT INPUT — ChatGPT style, pinned at bottom ──────────
# # # # #         typed = st.chat_input(
# # # # #             "Type your answer and press Enter...",
# # # # #             key = f"chat_{total_done}"
# # # # #         )
# # # # #         if typed:
# # # # #             if typed.strip().lower() == "/skip":
# # # # #                 handle_answer("I am not sure about this question.", resume_text)
# # # # #             else:
# # # # #                 handle_answer(typed.strip(), resume_text)

# # # # # # import os
# # # # # # import time
# # # # # # import streamlit as st

# # # # # # from interview.lisa_ai import generate_question, evaluate_answer, generate_session_feedback
# # # # # # from utils.text_to_speech import speak
# # # # # # from interview.scoring import (
# # # # # #     should_trigger_adaptive,
# # # # # #     calculate_total_score,
# # # # # #     calculate_skill_scores,
# # # # # #     generate_performance_summary
# # # # # # )
# # # # # # from database.db import (
# # # # # #     create_interview,
# # # # # #     save_question,
# # # # # #     complete_interview,
# # # # # #     save_report
# # # # # # )
# # # # # # from config import QUESTIONS_PER_LEVEL, INTRO_QUESTION

# # # # # # # ─────────────────────────────────────────────
# # # # # # # CONSTANTS
# # # # # # # ─────────────────────────────────────────────
# # # # # # STAGES     = ["easy", "medium", "hard"]
# # # # # # TIME_LIMIT = 30 * 60  # 30 minutes in seconds

# # # # # # STAGE_LABELS = {
# # # # # #     "easy":     "🟢 Easy",
# # # # # #     "medium":   "🟡 Medium",
# # # # # #     "hard":     "🔴 Hard",
# # # # # #     "adaptive": "🔵 Adaptive"
# # # # # # }

# # # # # # # Average words per second for gTTS speech (~2.5 words/sec)
# # # # # # WORDS_PER_SECOND = 2.5


# # # # # # # ─────────────────────────────────────────────
# # # # # # # TYPEWRITER STREAM GENERATOR
# # # # # # # Yields one word at a time synced to audio speed
# # # # # # # ─────────────────────────────────────────────
# # # # # # def typewriter_stream(text: str, words_per_second: float = WORDS_PER_SECOND):
# # # # # #     """
# # # # # #     Generator for st.write_stream().
# # # # # #     Yields words with delay so text appears in sync with LISA's audio.
# # # # # #     """
# # # # # #     words = text.split()
# # # # # #     delay = 1.0 / words_per_second
# # # # # #     for word in words:
# # # # # #         yield word + " "
# # # # # #         time.sleep(delay)


# # # # # # # ─────────────────────────────────────────────
# # # # # # # STATE INITIALIZATION
# # # # # # # ─────────────────────────────────────────────
# # # # # # def init_interview():
# # # # # #     """Set up all session state. Runs once per interview."""
# # # # # #     if st.session_state.get("interview_initialized"):
# # # # # #         return

# # # # # #     st.session_state.interview_initialized = True
# # # # # #     st.session_state.interview_id          = None
# # # # # #     st.session_state.interview_stage       = "easy"
# # # # # #     st.session_state.stage_q_index         = 0
# # # # # #     st.session_state.total_q_index         = 0
# # # # # #     st.session_state.current_question      = None
# # # # # #     st.session_state.current_level         = "easy"
# # # # # #     st.session_state.qa_history            = []     # completed Q&A dicts (scores hidden from UI)
# # # # # #     st.session_state.adaptive_mode         = False
# # # # # #     st.session_state.adaptive_direction    = ""
# # # # # #     st.session_state.interview_complete    = False
# # # # # #     st.session_state.interview_finalized   = False
# # # # # #     st.session_state.start_time            = time.time()
# # # # # #     st.session_state.audio_file            = None
# # # # # #     st.session_state.question_displayed    = False  # typewriter already played?


# # # # # # # ─────────────────────────────────────────────
# # # # # # # RESUME
# # # # # # # ─────────────────────────────────────────────
# # # # # # def get_resume_text() -> str:
# # # # # #     if st.session_state.get("resume_text"):
# # # # # #         return st.session_state.resume_text
# # # # # #     resume_path = st.session_state.get("resume_path")
# # # # # #     if resume_path and os.path.exists(resume_path):
# # # # # #         from utils.resume_parser import extract_resume_text
# # # # # #         text = extract_resume_text(resume_path)
# # # # # #         st.session_state.resume_text = text
# # # # # #         return text
# # # # # #     return "No resume provided."


# # # # # # # ─────────────────────────────────────────────
# # # # # # # QUESTION GENERATION
# # # # # # # ─────────────────────────────────────────────
# # # # # # def get_next_question(resume_text: str) -> tuple[str, str]:
# # # # # #     total_index = st.session_state.total_q_index
# # # # # #     last_qa     = st.session_state.qa_history[-1] if st.session_state.qa_history else {}

# # # # # #     if total_index == 0:
# # # # # #         return INTRO_QUESTION, "easy"

# # # # # #     if st.session_state.adaptive_mode:
# # # # # #         question = generate_question(
# # # # # #             level           = "adaptive",
# # # # # #             resume          = resume_text,
# # # # # #             previous_answer = last_qa.get("answer", ""),
# # # # # #             previous_score  = last_qa.get("score", 5.0)
# # # # # #         )
# # # # # #         return question, "adaptive"

# # # # # #     stage    = st.session_state.interview_stage
# # # # # #     question = generate_question(
# # # # # #         level           = stage,
# # # # # #         resume          = resume_text,
# # # # # #         previous_answer = last_qa.get("answer"),
# # # # # #         previous_score  = last_qa.get("score")
# # # # # #     )
# # # # # #     return question, stage


# # # # # # # ─────────────────────────────────────────────
# # # # # # # STAGE PROGRESSION
# # # # # # # ─────────────────────────────────────────────
# # # # # # def advance_stage():
# # # # # #     current = st.session_state.interview_stage
# # # # # #     idx     = STAGES.index(current)
# # # # # #     if idx + 1 < len(STAGES):
# # # # # #         st.session_state.interview_stage = STAGES[idx + 1]
# # # # # #         st.session_state.stage_q_index  = 0
# # # # # #     else:
# # # # # #         st.session_state.interview_complete = True


# # # # # # def time_expired() -> bool:
# # # # # #     return (time.time() - st.session_state.start_time) >= TIME_LIMIT


# # # # # # # ─────────────────────────────────────────────
# # # # # # # ANSWER SUBMISSION HANDLER
# # # # # # # ─────────────────────────────────────────────
# # # # # # def handle_answer(answer: str, resume_text: str):
# # # # # #     """
# # # # # #     Process submitted answer:
# # # # # #     1. Evaluate silently (score NOT shown in chat)
# # # # # #     2. Save to DB
# # # # # #     3. Store in history
# # # # # #     4. Check adaptive trigger
# # # # # #     5. Advance state
# # # # # #     """
# # # # # #     question = st.session_state.current_question
# # # # # #     level    = st.session_state.current_level

# # # # # #     # ── Evaluate (silent — user doesn't see score yet) ──
# # # # # #     with st.spinner("LISA is processing your answer..."):
# # # # # #         evaluation = evaluate_answer(question, answer)

# # # # # #     score        = evaluation["score"]
# # # # # #     ideal_answer = evaluation["ideal_answer"]
# # # # # #     feedback     = evaluation["feedback"]

# # # # # #     # ── Save to DB ──
# # # # # #     save_question(
# # # # # #         interview_id        = st.session_state.interview_id,
# # # # # #         question_number     = st.session_state.total_q_index + 1,
# # # # # #         difficulty_level    = level,
# # # # # #         topic               = None,
# # # # # #         question_text       = question,
# # # # # #         user_answer         = answer,
# # # # # #         ai_suggested_answer = ideal_answer,
# # # # # #         score               = score,
# # # # # #         feedback            = feedback
# # # # # #     )

# # # # # #     # ── Store in history (score hidden from chat UI) ──
# # # # # #     st.session_state.qa_history.append({
# # # # # #         "question":     question,
# # # # # #         "answer":       answer,
# # # # # #         "score":        score,
# # # # # #         "feedback":     feedback,
# # # # # #         "ideal_answer": ideal_answer,
# # # # # #         "level":        level
# # # # # #     })

# # # # # #     st.session_state.total_q_index     += 1
# # # # # #     st.session_state.question_displayed = False

# # # # # #     # ── Adaptive trigger check ──
# # # # # #     if not st.session_state.adaptive_mode and level in ["medium", "hard"]:
# # # # # #         trigger, direction = should_trigger_adaptive(level, score)
# # # # # #         if trigger:
# # # # # #             st.session_state.adaptive_mode      = True
# # # # # #             st.session_state.adaptive_direction = direction
# # # # # #             st.session_state.current_question   = None
# # # # # #             st.session_state.audio_file         = None
# # # # # #             st.rerun()
# # # # # #             return

# # # # # #     st.session_state.adaptive_mode      = False
# # # # # #     st.session_state.adaptive_direction = ""

# # # # # #     # ── Advance stage question counter ──
# # # # # #     st.session_state.stage_q_index += 1

# # # # # #     stage = st.session_state.interview_stage
# # # # # #     if st.session_state.stage_q_index >= QUESTIONS_PER_LEVEL.get(stage, 3):
# # # # # #         advance_stage()

# # # # # #     st.session_state.current_question = None
# # # # # #     st.session_state.audio_file       = None
# # # # # #     st.rerun()


# # # # # # # ─────────────────────────────────────────────
# # # # # # # FINALIZE
# # # # # # # ─────────────────────────────────────────────
# # # # # # def finalize_interview():
# # # # # #     qa_history = st.session_state.qa_history
# # # # # #     if not qa_history:
# # # # # #         return

# # # # # #     questions_scored = [
# # # # # #         {
# # # # # #             "difficulty_level": q["level"],
# # # # # #             "score":            q["score"],
# # # # # #             "topic":            "",
# # # # # #             "question_text":    q["question"]
# # # # # #         }
# # # # # #         for q in qa_history
# # # # # #     ]

# # # # # #     total_score         = calculate_total_score(questions_scored)
# # # # # #     skill_scores        = calculate_skill_scores(questions_scored)
# # # # # #     performance_summary = generate_performance_summary(total_score, skill_scores)

# # # # # #     qa_pairs = [
# # # # # #         {"question": q["question"], "user_answer": q["answer"], "score": q["score"]}
# # # # # #         for q in qa_history
# # # # # #     ]

# # # # # #     with st.spinner("LISA is preparing your full evaluation report..."):
# # # # # #         ai_feedback = generate_session_feedback(qa_pairs)

# # # # # #     complete_interview(st.session_state.interview_id, total_score)

# # # # # #     save_report(
# # # # # #         interview_id           = st.session_state.interview_id,
# # # # # #         overall_score          = total_score,
# # # # # #         performance_summary    = performance_summary,
# # # # # #         technical_knowledge    = skill_scores["technical_knowledge"],
# # # # # #         communication_skills   = skill_scores["communication_skills"],
# # # # # #         problem_solving        = skill_scores["problem_solving"],
# # # # # #         project_understanding  = skill_scores["project_understanding"],
# # # # # #         strengths              = ai_feedback["strengths"],
# # # # # #         areas_for_improvement  = ai_feedback["improvements"],
# # # # # #         actionable_suggestions = ai_feedback["study_plan"],
# # # # # #         report_pdf             = b""
# # # # # #     )

# # # # # #     st.session_state.final_score         = total_score
# # # # # #     st.session_state.skill_scores        = skill_scores
# # # # # #     st.session_state.ai_feedback         = ai_feedback
# # # # # #     st.session_state.performance_summary = performance_summary
# # # # # #     st.session_state.interview_finalized = True


# # # # # # # ─────────────────────────────────────────────
# # # # # # # RESULTS SCREEN (no scores during interview)
# # # # # # # ─────────────────────────────────────────────
# # # # # # def show_results():
# # # # # #     score        = st.session_state.get("final_score", 0)
# # # # # #     skill_scores = st.session_state.get("skill_scores", {})
# # # # # #     feedback     = st.session_state.get("ai_feedback", {})
# # # # # #     summary      = st.session_state.get("performance_summary", "")

# # # # # #     # Convert /10 → /25 to match PDF format
# # # # # #     def to_25(val): return round(float(val or 0) * 2.5, 1)
# # # # # #     def to_100(val): return round(float(val or 0) * 10, 1)

# # # # # #     st.markdown("---")
# # # # # #     st.markdown("## 🎉 Interview Complete — Your Results")
# # # # # #     st.caption(f"Interview #{st.session_state.interview_id}")

# # # # # #     # ── Score cards (matching PDF format /25 each, /100 overall) ──
# # # # # #     c1, c2, c3, c4, c5 = st.columns(5)
# # # # # #     c1.metric("🏆 Overall",           f"{to_100(score)}/100")
# # # # # #     c2.metric("🔧 Technical",         f"{to_25(skill_scores.get('technical_knowledge', 0))}/25")
# # # # # #     c3.metric("🗣 Communication",     f"{to_25(skill_scores.get('communication_skills', 0))}/25")
# # # # # #     c4.metric("🧩 Problem Solving",   f"{to_25(skill_scores.get('problem_solving', 0))}/25")
# # # # # #     c5.metric("📁 Project",           f"{to_25(skill_scores.get('project_understanding', 0))}/25")

# # # # # #     st.markdown("---")
# # # # # #     st.markdown("### 📝 Performance Summary")
# # # # # #     st.info(summary)

# # # # # #     col_a, col_b = st.columns(2)
# # # # # #     with col_a:
# # # # # #         st.markdown("### ✅ Strengths")
# # # # # #         st.success(feedback.get("strengths", ""))
# # # # # #     with col_b:
# # # # # #         st.markdown("### 📈 Areas for Improvement")
# # # # # #         st.warning(feedback.get("improvements", ""))

# # # # # #     st.markdown("### 📚 Actionable Study Plan")
# # # # # #     st.write(feedback.get("study_plan", ""))

# # # # # #     st.markdown("---")

# # # # # #     # ── PDF Download ──
# # # # # #     if st.button("📥 Download Full Evaluation Report (PDF)",
# # # # # #                  type="primary", use_container_width=True):
# # # # # #         try:
# # # # # #             from utils.pdf_report import generate_pdf
# # # # # #             pdf_bytes = generate_pdf(st.session_state.interview_id)
# # # # # #             st.download_button(
# # # # # #                 label               = "⬇️ Click to Download PDF",
# # # # # #                 data                = pdf_bytes,
# # # # # #                 file_name           = f"pyspace_report_{st.session_state.interview_id}.pdf",
# # # # # #                 mime                = "application/pdf",
# # # # # #                 use_container_width = True
# # # # # #             )
# # # # # #         except Exception as e:
# # # # # #             st.error(f"PDF generation failed: {e}")

# # # # # #     st.markdown("---")

# # # # # #     if st.button("🔄 Start New Interview", use_container_width=True):
# # # # # #         keys = [
# # # # # #             "interview_initialized","interview_id","interview_stage",
# # # # # #             "stage_q_index","total_q_index","current_question","current_level",
# # # # # #             "qa_history","adaptive_mode","adaptive_direction","interview_complete",
# # # # # #             "interview_finalized","start_time","audio_file","final_score",
# # # # # #             "skill_scores","ai_feedback","performance_summary","interview_started",
# # # # # #             "resume_path","resume_text","question_displayed"
# # # # # #         ]
# # # # # #         for k in keys:
# # # # # #             st.session_state.pop(k, None)
# # # # # #         st.rerun()


# # # # # # # ─────────────────────────────────────────────
# # # # # # # MAIN FLOW
# # # # # # # ─────────────────────────────────────────────
# # # # # # def interview_flow():

# # # # # #     init_interview()
# # # # # #     resume_text = get_resume_text()

# # # # # #     # Create DB record once
# # # # # #     if st.session_state.interview_id is None:
# # # # # #         filename = os.path.basename(st.session_state.get("resume_path", "unknown"))
# # # # # #         st.session_state.interview_id = create_interview(
# # # # # #             user_email      = st.session_state["user_email"],
# # # # # #             resume_text     = resume_text,
# # # # # #             resume_filename = filename
# # # # # #         )

# # # # # #     if st.session_state.get("interview_finalized"):
# # # # # #         show_results()
# # # # # #         return

# # # # # #     if st.session_state.interview_complete or time_expired():
# # # # # #         finalize_interview()
# # # # # #         st.rerun()
# # # # # #         return

# # # # # #     # ── HEADER ──────────────────────────────────────────────────
# # # # # #     elapsed    = int(time.time() - st.session_state.start_time)
# # # # # #     mins, secs = divmod(elapsed, 60)
# # # # # #     remaining  = max(0, int((TIME_LIMIT - elapsed) / 60))
# # # # # #     total_done = st.session_state.total_q_index
# # # # # #     total_exp  = sum(QUESTIONS_PER_LEVEL.values())
# # # # # #     progress   = min(total_done / total_exp, 1.0)
# # # # # #     stage      = st.session_state.interview_stage

# # # # # #     h1, h2, h3, h4 = st.columns([4, 1, 1, 1])
# # # # # #     with h1:
# # # # # #         st.progress(progress,
# # # # # #                     text=f"Stage: {STAGE_LABELS.get(stage, stage)}  |  Question {total_done + 1}")
# # # # # #     with h2:
# # # # # #         st.metric("⏱ Elapsed", f"{mins:02d}:{secs:02d}")
# # # # # #     with h3:
# # # # # #         st.metric("⏳ Left", f"~{remaining}m")
# # # # # #     with h4:
# # # # # #         if st.button("🚪 End Interview"):
# # # # # #             st.session_state.interview_complete = True
# # # # # #             st.rerun()

# # # # # #     st.markdown("---")

# # # # # #     # ── CONVERSATION HISTORY ─────────────────────────────────────
# # # # # #     # Scores NOT shown here — only the conversation
# # # # # #     for i, qa in enumerate(st.session_state.qa_history, 1):
# # # # # #         with st.chat_message("assistant", avatar="🤖"):
# # # # # #             st.markdown(
# # # # # #                 f"**{STAGE_LABELS.get(qa['level'], qa['level'])}**  \n{qa['question']}"
# # # # # #             )
# # # # # #         with st.chat_message("user", avatar="👤"):
# # # # # #             st.write(qa["answer"])
# # # # # #             # Only show a neutral acknowledgment — NO score
# # # # # #             st.caption("✔️ Answer recorded")

# # # # # #     # ── GENERATE CURRENT QUESTION ────────────────────────────────
# # # # # #     if st.session_state.current_question is None:
# # # # # #         with st.spinner("LISA is preparing your next question..."):
# # # # # #             question, level   = get_next_question(resume_text)
# # # # # #             audio_path        = speak(question)
# # # # # #         st.session_state.current_question  = question
# # # # # #         st.session_state.current_level     = level
# # # # # #         st.session_state.audio_file        = audio_path
# # # # # #         st.session_state.question_displayed = False

# # # # # #     question = st.session_state.current_question
# # # # # #     level    = st.session_state.current_level

# # # # # #     # ── ADAPTIVE BANNER ──────────────────────────────────────────
# # # # # #     if st.session_state.adaptive_mode:
# # # # # #         d = st.session_state.adaptive_direction
# # # # # #         if d == "easier":
# # # # # #             st.info("🔽 Let me rephrase that question for you.")
# # # # # #         else:
# # # # # #             st.info("🔼 Excellent! Let's go a level deeper.")

# # # # # #     # ── LISA SPEAKS + TYPEWRITER ─────────────────────────────────
# # # # # #     with st.chat_message("assistant", avatar="🤖"):
# # # # # #         st.markdown(f"**{STAGE_LABELS.get(level, level)}**")

# # # # # #         # Audio plays first (autoplay) — user hears LISA start speaking
# # # # # #         if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
# # # # # #             st.audio(st.session_state.audio_file, autoplay=True)

# # # # # #         # Typewriter runs simultaneously with audio
# # # # # #         # Only runs once — after that shows static text to avoid re-streaming on rerun
# # # # # #         if not st.session_state.question_displayed:
# # # # # #             st.write_stream(typewriter_stream(question, WORDS_PER_SECOND))
# # # # # #             st.session_state.question_displayed = True
# # # # # #         else:
# # # # # #             # Already typed — just show static text
# # # # # #             st.markdown(question)

# # # # # #     # ── USER ANSWER ──────────────────────────────────────────────
# # # # # #     with st.chat_message("user", avatar="👤"):

# # # # # #         answer_mode = st.radio(
# # # # # #             "How would you like to answer?",
# # # # # #             ["⌨️ Type my answer", "🎤 Speak my answer"],
# # # # # #             horizontal = True,
# # # # # #             key        = f"mode_{total_done}"
# # # # # #         )

# # # # # #         answer = ""

# # # # # #         if answer_mode == "⌨️ Type my answer":
# # # # # #             answer = st.text_area(
# # # # # #                 "Your answer:",
# # # # # #                 height      = 150,
# # # # # #                 placeholder = "Take your time. Answer clearly and completely.",
# # # # # #                 key         = f"text_{total_done}"
# # # # # #             )

# # # # # #         else:
# # # # # #             st.caption("🎙️ Press the mic button below, speak your answer, then stop.")
# # # # # #             audio_input = st.audio_input(
# # # # # #                 "Record your answer",
# # # # # #                 key = f"voice_{total_done}"
# # # # # #             )

# # # # # #             if audio_input:
# # # # # #                 with st.spinner("Transcribing..."):
# # # # # #                     from utils.speech_to_text import transcribe_audio
# # # # # #                     answer = transcribe_audio(audio_input)

# # # # # #                 if answer:
# # # # # #                     # Show transcription typewriter style — feels like real-time
# # # # # #                     st.write_stream(typewriter_stream(answer, words_per_second=8.0))
# # # # # #                     st.caption("✏️ Your spoken answer — edit below if needed.")
# # # # # #                     answer = st.text_area(
# # # # # #                         "Edit if needed:",
# # # # # #                         value  = answer,
# # # # # #                         height = 100,
# # # # # #                         key    = f"edit_{total_done}"
# # # # # #                     )
# # # # # #                 else:
# # # # # #                     st.warning("Could not transcribe. Re-record or switch to text.")

# # # # # #         st.markdown("&nbsp;")

# # # # # #         b1, b2 = st.columns([3, 1])
# # # # # #         with b1:
# # # # # #             if st.button("✅ Submit Answer", type="primary",
# # # # # #                          use_container_width=True, key=f"submit_{total_done}"):
# # # # # #                 if answer.strip():
# # # # # #                     handle_answer(answer.strip(), resume_text)
# # # # # #                 else:
# # # # # #                     st.warning("Please provide an answer before submitting.")
# # # # # #         with b2:
# # # # # #             if st.button("⏭ Skip", use_container_width=True, key=f"skip_{total_done}",
# # # # # #                          help="Skip this question"):
# # # # # #                 handle_answer("I am not sure about this question.", resume_text)
# # # # # # # import os
# # # # # # # import time
# # # # # # # import streamlit as st

# # # # # # # from interview.lisa_ai import generate_question, evaluate_answer, generate_session_feedback
# # # # # # # from utils.text_to_speech import speak
# # # # # # # from interview.scoring import (
# # # # # # #     should_trigger_adaptive,
# # # # # # #     calculate_total_score,
# # # # # # #     calculate_skill_scores,
# # # # # # #     generate_performance_summary
# # # # # # # )
# # # # # # # from database.db import (
# # # # # # #     create_interview,
# # # # # # #     save_question,
# # # # # # #     complete_interview,
# # # # # # #     save_report
# # # # # # # )
# # # # # # # from config import QUESTIONS_PER_LEVEL, INTRO_QUESTION

# # # # # # # # ─────────────────────────────────────────────
# # # # # # # # CONSTANTS
# # # # # # # # ─────────────────────────────────────────────
# # # # # # # STAGES     = ["easy", "medium", "hard"]
# # # # # # # TIME_LIMIT = 30 * 60  # 30 minutes in seconds

# # # # # # # STAGE_LABELS = {
# # # # # # #     "easy":     "🟢 Easy",
# # # # # # #     "medium":   "🟡 Medium",
# # # # # # #     "hard":     "🔴 Hard",
# # # # # # #     "adaptive": "🔵 Adaptive"
# # # # # # # }

# # # # # # # # Average words per second for gTTS speech (~2.5 words/sec)
# # # # # # # WORDS_PER_SECOND = 2.5


# # # # # # # # ─────────────────────────────────────────────
# # # # # # # # TYPEWRITER STREAM GENERATOR
# # # # # # # # Yields one word at a time synced to audio speed
# # # # # # # # ─────────────────────────────────────────────
# # # # # # # def typewriter_stream(text: str, words_per_second: float = WORDS_PER_SECOND):
# # # # # # #     """
# # # # # # #     Generator for st.write_stream().
# # # # # # #     Yields words with delay so text appears in sync with LISA's audio.
# # # # # # #     """
# # # # # # #     words = text.split()
# # # # # # #     delay = 1.0 / words_per_second
# # # # # # #     for word in words:
# # # # # # #         yield word + " "
# # # # # # #         time.sleep(delay)


# # # # # # # # ─────────────────────────────────────────────
# # # # # # # # STATE INITIALIZATION
# # # # # # # # ─────────────────────────────────────────────
# # # # # # # def init_interview():
# # # # # # #     """Set up all session state. Runs once per interview."""
# # # # # # #     if st.session_state.get("interview_initialized"):
# # # # # # #         return

# # # # # # #     st.session_state.interview_initialized = True
# # # # # # #     st.session_state.interview_id          = None
# # # # # # #     st.session_state.interview_stage       = "easy"
# # # # # # #     st.session_state.stage_q_index         = 0
# # # # # # #     st.session_state.total_q_index         = 0
# # # # # # #     st.session_state.current_question      = None
# # # # # # #     st.session_state.current_level         = "easy"
# # # # # # #     st.session_state.qa_history            = []     # completed Q&A dicts (scores hidden from UI)
# # # # # # #     st.session_state.adaptive_mode         = False
# # # # # # #     st.session_state.adaptive_direction    = ""
# # # # # # #     st.session_state.interview_complete    = False
# # # # # # #     st.session_state.interview_finalized   = False
# # # # # # #     st.session_state.start_time            = time.time()
# # # # # # #     st.session_state.audio_file            = None
# # # # # # #     st.session_state.question_displayed    = False  # typewriter already played?


# # # # # # # # ─────────────────────────────────────────────
# # # # # # # # RESUME
# # # # # # # # ─────────────────────────────────────────────
# # # # # # # def get_resume_text() -> str:
# # # # # # #     if st.session_state.get("resume_text"):
# # # # # # #         return st.session_state.resume_text
# # # # # # #     resume_path = st.session_state.get("resume_path")
# # # # # # #     if resume_path and os.path.exists(resume_path):
# # # # # # #         from utils.resume_parser import extract_resume_text
# # # # # # #         text = extract_resume_text(resume_path)
# # # # # # #         st.session_state.resume_text = text
# # # # # # #         return text
# # # # # # #     return "No resume provided."


# # # # # # # # ─────────────────────────────────────────────
# # # # # # # # QUESTION GENERATION
# # # # # # # # ─────────────────────────────────────────────
# # # # # # # def get_next_question(resume_text: str) -> tuple[str, str]:
# # # # # # #     total_index = st.session_state.total_q_index
# # # # # # #     last_qa     = st.session_state.qa_history[-1] if st.session_state.qa_history else {}

# # # # # # #     if total_index == 0:
# # # # # # #         return INTRO_QUESTION, "easy"

# # # # # # #     if st.session_state.adaptive_mode:
# # # # # # #         question = generate_question(
# # # # # # #             level           = "adaptive",
# # # # # # #             resume          = resume_text,
# # # # # # #             previous_answer = last_qa.get("answer", ""),
# # # # # # #             previous_score  = last_qa.get("score", 5.0)
# # # # # # #         )
# # # # # # #         return question, "adaptive"

# # # # # # #     stage    = st.session_state.interview_stage
# # # # # # #     question = generate_question(
# # # # # # #         level           = stage,
# # # # # # #         resume          = resume_text,
# # # # # # #         previous_answer = last_qa.get("answer"),
# # # # # # #         previous_score  = last_qa.get("score")
# # # # # # #     )
# # # # # # #     return question, stage


# # # # # # # # ─────────────────────────────────────────────
# # # # # # # # STAGE PROGRESSION
# # # # # # # # ─────────────────────────────────────────────
# # # # # # # def advance_stage():
# # # # # # #     current = st.session_state.interview_stage
# # # # # # #     idx     = STAGES.index(current)
# # # # # # #     if idx + 1 < len(STAGES):
# # # # # # #         st.session_state.interview_stage = STAGES[idx + 1]
# # # # # # #         st.session_state.stage_q_index  = 0
# # # # # # #     else:
# # # # # # #         st.session_state.interview_complete = True


# # # # # # # def time_expired() -> bool:
# # # # # # #     return (time.time() - st.session_state.start_time) >= TIME_LIMIT


# # # # # # # # ─────────────────────────────────────────────
# # # # # # # # ANSWER SUBMISSION HANDLER
# # # # # # # # ─────────────────────────────────────────────
# # # # # # # def handle_answer(answer: str, resume_text: str):
# # # # # # #     """
# # # # # # #     Process submitted answer:
# # # # # # #     1. Evaluate silently (score NOT shown in chat)
# # # # # # #     2. Save to DB
# # # # # # #     3. Store in history
# # # # # # #     4. Check adaptive trigger
# # # # # # #     5. Advance state
# # # # # # #     """
# # # # # # #     question = st.session_state.current_question
# # # # # # #     level    = st.session_state.current_level

# # # # # # #     # ── Evaluate (silent — user doesn't see score yet) ──
# # # # # # #     with st.spinner("LISA is processing your answer..."):
# # # # # # #         evaluation = evaluate_answer(question, answer)

# # # # # # #     score        = evaluation["score"]
# # # # # # #     ideal_answer = evaluation["ideal_answer"]
# # # # # # #     feedback     = evaluation["feedback"]

# # # # # # #     # ── Save to DB ──
# # # # # # #     save_question(
# # # # # # #         interview_id        = st.session_state.interview_id,
# # # # # # #         question_number     = st.session_state.total_q_index + 1,
# # # # # # #         difficulty_level    = level,
# # # # # # #         topic               = None,
# # # # # # #         question_text       = question,
# # # # # # #         user_answer         = answer,
# # # # # # #         ai_suggested_answer = ideal_answer,
# # # # # # #         score               = score,
# # # # # # #         feedback            = feedback
# # # # # # #     )

# # # # # # #     # ── Store in history (score hidden from chat UI) ──
# # # # # # #     st.session_state.qa_history.append({
# # # # # # #         "question":     question,
# # # # # # #         "answer":       answer,
# # # # # # #         "score":        score,
# # # # # # #         "feedback":     feedback,
# # # # # # #         "ideal_answer": ideal_answer,
# # # # # # #         "level":        level
# # # # # # #     })

# # # # # # #     st.session_state.total_q_index     += 1
# # # # # # #     st.session_state.question_displayed = False

# # # # # # #     # ── Adaptive trigger check ──
# # # # # # #     if not st.session_state.adaptive_mode and level in ["medium", "hard"]:
# # # # # # #         trigger, direction = should_trigger_adaptive(level, score)
# # # # # # #         if trigger:
# # # # # # #             st.session_state.adaptive_mode      = True
# # # # # # #             st.session_state.adaptive_direction = direction
# # # # # # #             st.session_state.current_question   = None
# # # # # # #             st.session_state.audio_file         = None
# # # # # # #             st.rerun()
# # # # # # #             return

# # # # # # #     st.session_state.adaptive_mode      = False
# # # # # # #     st.session_state.adaptive_direction = ""

# # # # # # #     # ── Advance stage question counter ──
# # # # # # #     st.session_state.stage_q_index += 1

# # # # # # #     stage = st.session_state.interview_stage
# # # # # # #     if st.session_state.stage_q_index >= QUESTIONS_PER_LEVEL.get(stage, 3):
# # # # # # #         advance_stage()

# # # # # # #     st.session_state.current_question = None
# # # # # # #     st.session_state.audio_file       = None
# # # # # # #     st.rerun()


# # # # # # # # ─────────────────────────────────────────────
# # # # # # # # FINALIZE
# # # # # # # # ─────────────────────────────────────────────
# # # # # # # def finalize_interview():
# # # # # # #     qa_history = st.session_state.qa_history
# # # # # # #     if not qa_history:
# # # # # # #         return

# # # # # # #     questions_scored = [
# # # # # # #         {
# # # # # # #             "difficulty_level": q["level"],
# # # # # # #             "score":            q["score"],
# # # # # # #             "topic":            "",
# # # # # # #             "question_text":    q["question"]
# # # # # # #         }
# # # # # # #         for q in qa_history
# # # # # # #     ]

# # # # # # #     total_score         = calculate_total_score(questions_scored)
# # # # # # #     skill_scores        = calculate_skill_scores(questions_scored)
# # # # # # #     performance_summary = generate_performance_summary(total_score, skill_scores)

# # # # # # #     qa_pairs = [
# # # # # # #         {"question": q["question"], "user_answer": q["answer"], "score": q["score"]}
# # # # # # #         for q in qa_history
# # # # # # #     ]

# # # # # # #     with st.spinner("LISA is preparing your full evaluation report..."):
# # # # # # #         ai_feedback = generate_session_feedback(qa_pairs)

# # # # # # #     complete_interview(st.session_state.interview_id, total_score)

# # # # # # #     save_report(
# # # # # # #         interview_id           = st.session_state.interview_id,
# # # # # # #         overall_score          = total_score,
# # # # # # #         performance_summary    = performance_summary,
# # # # # # #         technical_knowledge    = skill_scores["technical_knowledge"],
# # # # # # #         communication_skills   = skill_scores["communication_skills"],
# # # # # # #         problem_solving        = skill_scores["problem_solving"],
# # # # # # #         project_understanding  = skill_scores["project_understanding"],
# # # # # # #         strengths              = ai_feedback["strengths"],
# # # # # # #         areas_for_improvement  = ai_feedback["improvements"],
# # # # # # #         actionable_suggestions = ai_feedback["study_plan"],
# # # # # # #         report_pdf             = b""
# # # # # # #     )

# # # # # # #     st.session_state.final_score         = total_score
# # # # # # #     st.session_state.skill_scores        = skill_scores
# # # # # # #     st.session_state.ai_feedback         = ai_feedback
# # # # # # #     st.session_state.performance_summary = performance_summary
# # # # # # #     st.session_state.interview_finalized = True


# # # # # # # # ─────────────────────────────────────────────
# # # # # # # # RESULTS SCREEN (no scores during interview)
# # # # # # # # ─────────────────────────────────────────────
# # # # # # # def show_results():
# # # # # # #     score        = st.session_state.get("final_score", 0)
# # # # # # #     skill_scores = st.session_state.get("skill_scores", {})
# # # # # # #     feedback     = st.session_state.get("ai_feedback", {})
# # # # # # #     summary      = st.session_state.get("performance_summary", "")

# # # # # # #     # Convert /10 → /25 to match PDF format
# # # # # # #     def to_25(val): return round(float(val or 0) * 2.5, 1)
# # # # # # #     def to_100(val): return round(float(val or 0) * 10, 1)

# # # # # # #     st.markdown("---")
# # # # # # #     st.markdown("## 🎉 Interview Complete — Your Results")
# # # # # # #     st.caption(f"Interview #{st.session_state.interview_id}")

# # # # # # #     # ── Score cards (matching PDF format /25 each, /100 overall) ──
# # # # # # #     c1, c2, c3, c4, c5 = st.columns(5)
# # # # # # #     c1.metric("🏆 Overall",           f"{to_100(score)}/100")
# # # # # # #     c2.metric("🔧 Technical",         f"{to_25(skill_scores.get('technical_knowledge', 0))}/25")
# # # # # # #     c3.metric("🗣 Communication",     f"{to_25(skill_scores.get('communication_skills', 0))}/25")
# # # # # # #     c4.metric("🧩 Problem Solving",   f"{to_25(skill_scores.get('problem_solving', 0))}/25")
# # # # # # #     c5.metric("📁 Project",           f"{to_25(skill_scores.get('project_understanding', 0))}/25")

# # # # # # #     st.markdown("---")
# # # # # # #     st.markdown("### 📝 Performance Summary")
# # # # # # #     st.info(summary)

# # # # # # #     col_a, col_b = st.columns(2)
# # # # # # #     with col_a:
# # # # # # #         st.markdown("### ✅ Strengths")
# # # # # # #         st.success(feedback.get("strengths", ""))
# # # # # # #     with col_b:
# # # # # # #         st.markdown("### 📈 Areas for Improvement")
# # # # # # #         st.warning(feedback.get("improvements", ""))

# # # # # # #     st.markdown("### 📚 Actionable Study Plan")
# # # # # # #     st.write(feedback.get("study_plan", ""))

# # # # # # #     st.markdown("---")

# # # # # # #     # ── PDF Download ──
# # # # # # #     if st.button("📥 Download Full Evaluation Report (PDF)",
# # # # # # #                  type="primary", use_container_width=True):
# # # # # # #         try:
# # # # # # #             from utils.pdf_report import generate_pdf
# # # # # # #             pdf_bytes = generate_pdf(st.session_state.interview_id)
# # # # # # #             st.download_button(
# # # # # # #                 label               = "⬇️ Click to Download PDF",
# # # # # # #                 data                = pdf_bytes,
# # # # # # #                 file_name           = f"pyspace_report_{st.session_state.interview_id}.pdf",
# # # # # # #                 mime                = "application/pdf",
# # # # # # #                 use_container_width = True
# # # # # # #             )
# # # # # # #         except Exception as e:
# # # # # # #             st.error(f"PDF generation failed: {e}")

# # # # # # #     st.markdown("---")

# # # # # # #     if st.button("🔄 Start New Interview", use_container_width=True):
# # # # # # #         keys = [
# # # # # # #             "interview_initialized","interview_id","interview_stage",
# # # # # # #             "stage_q_index","total_q_index","current_question","current_level",
# # # # # # #             "qa_history","adaptive_mode","adaptive_direction","interview_complete",
# # # # # # #             "interview_finalized","start_time","audio_file","final_score",
# # # # # # #             "skill_scores","ai_feedback","performance_summary","interview_started",
# # # # # # #             "resume_path","resume_text","question_displayed"
# # # # # # #         ]
# # # # # # #         for k in keys:
# # # # # # #             st.session_state.pop(k, None)
# # # # # # #         st.rerun()


# # # # # # # # ─────────────────────────────────────────────
# # # # # # # # MAIN FLOW
# # # # # # # # ─────────────────────────────────────────────
# # # # # # # def interview_flow():

# # # # # # #     init_interview()
# # # # # # #     resume_text = get_resume_text()

# # # # # # #     # Create DB record once
# # # # # # #     if st.session_state.interview_id is None:
# # # # # # #         filename = os.path.basename(st.session_state.get("resume_path", "unknown"))
# # # # # # #         st.session_state.interview_id = create_interview(
# # # # # # #             user_email      = st.session_state["user_email"],
# # # # # # #             resume_text     = resume_text,
# # # # # # #             resume_filename = filename
# # # # # # #         )

# # # # # # #     if st.session_state.get("interview_finalized"):
# # # # # # #         show_results()
# # # # # # #         return

# # # # # # #     if st.session_state.interview_complete or time_expired():
# # # # # # #         finalize_interview()
# # # # # # #         st.rerun()
# # # # # # #         return

# # # # # # #     # ── HEADER ──────────────────────────────────────────────────
# # # # # # #     elapsed    = int(time.time() - st.session_state.start_time)
# # # # # # #     mins, secs = divmod(elapsed, 60)
# # # # # # #     remaining  = max(0, int((TIME_LIMIT - elapsed) / 60))
# # # # # # #     total_done = st.session_state.total_q_index
# # # # # # #     total_exp  = sum(QUESTIONS_PER_LEVEL.values())
# # # # # # #     progress   = min(total_done / total_exp, 1.0)
# # # # # # #     stage      = st.session_state.interview_stage

# # # # # # #     h1, h2, h3, h4 = st.columns([4, 1, 1, 1])
# # # # # # #     with h1:
# # # # # # #         st.progress(progress,
# # # # # # #                     text=f"Stage: {STAGE_LABELS.get(stage, stage)}  |  Question {total_done + 1}")
# # # # # # #     with h2:
# # # # # # #         st.metric("⏱ Elapsed", f"{mins:02d}:{secs:02d}")
# # # # # # #     with h3:
# # # # # # #         st.metric("⏳ Left", f"~{remaining}m")
# # # # # # #     with h4:
# # # # # # #         if st.button("🚪 End Interview"):
# # # # # # #             st.session_state.interview_complete = True
# # # # # # #             st.rerun()

# # # # # # #     st.markdown("---")

# # # # # # #     # ── CONVERSATION HISTORY ─────────────────────────────────────
# # # # # # #     # Scores NOT shown here — only the conversation
# # # # # # #     for i, qa in enumerate(st.session_state.qa_history, 1):
# # # # # # #         with st.chat_message("assistant", avatar="🤖"):
# # # # # # #             st.markdown(
# # # # # # #                 f"**{STAGE_LABELS.get(qa['level'], qa['level'])}**  \n{qa['question']}"
# # # # # # #             )
# # # # # # #         with st.chat_message("user", avatar="👤"):
# # # # # # #             st.write(qa["answer"])
# # # # # # #             # Only show a neutral acknowledgment — NO score
# # # # # # #             st.caption("✔️ Answer recorded")

# # # # # # #     # ── GENERATE CURRENT QUESTION ────────────────────────────────
# # # # # # #     if st.session_state.current_question is None:
# # # # # # #         with st.spinner("LISA is preparing your next question..."):
# # # # # # #             question, level   = get_next_question(resume_text)
# # # # # # #             audio_path        = speak(question)
# # # # # # #         st.session_state.current_question  = question
# # # # # # #         st.session_state.current_level     = level
# # # # # # #         st.session_state.audio_file        = audio_path
# # # # # # #         st.session_state.question_displayed = False

# # # # # # #     question = st.session_state.current_question
# # # # # # #     level    = st.session_state.current_level

# # # # # # #     # ── ADAPTIVE BANNER ──────────────────────────────────────────
# # # # # # #     if st.session_state.adaptive_mode:
# # # # # # #         d = st.session_state.adaptive_direction
# # # # # # #         if d == "easier":
# # # # # # #             st.info("🔽 Let me rephrase that question for you.")
# # # # # # #         else:
# # # # # # #             st.info("🔼 Excellent! Let's go a level deeper.")

# # # # # # #     # ── LISA SPEAKS + TYPEWRITER ─────────────────────────────────
# # # # # # #     with st.chat_message("assistant", avatar="🤖"):
# # # # # # #         st.markdown(f"**{STAGE_LABELS.get(level, level)}**")

# # # # # # #         # Audio plays first (autoplay) — user hears LISA start speaking
# # # # # # #         if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
# # # # # # #             st.audio(st.session_state.audio_file, autoplay=True)

# # # # # # #         # Typewriter runs simultaneously with audio
# # # # # # #         # Only runs once — after that shows static text to avoid re-streaming on rerun
# # # # # # #         if not st.session_state.question_displayed:
# # # # # # #             st.write_stream(typewriter_stream(question, WORDS_PER_SECOND))
# # # # # # #             st.session_state.question_displayed = True
# # # # # # #         else:
# # # # # # #             # Already typed — just show static text
# # # # # # #             st.markdown(question)

# # # # # # #     # ── USER ANSWER ──────────────────────────────────────────────
# # # # # # #     with st.chat_message("user", avatar="👤"):

# # # # # # #         answer_mode = st.radio(
# # # # # # #             "How would you like to answer?",
# # # # # # #             ["⌨️ Type my answer", "🎤 Speak my answer"],
# # # # # # #             horizontal = True,
# # # # # # #             key        = f"mode_{total_done}"
# # # # # # #         )

# # # # # # #         answer = ""

# # # # # # #         if answer_mode == "⌨️ Type my answer":
# # # # # # #             answer = st.text_area(
# # # # # # #                 "Your answer:",
# # # # # # #                 height      = 150,
# # # # # # #                 placeholder = "Take your time. Answer clearly and completely.",
# # # # # # #                 key         = f"text_{total_done}"
# # # # # # #             )

# # # # # # #         else:
# # # # # # #             st.caption("🎙️ Press the mic button below, speak your answer, then stop.")
# # # # # # #             audio_input = st.audio_input(
# # # # # # #                 "Record your answer",
# # # # # # #                 key = f"voice_{total_done}"
# # # # # # #             )

# # # # # # #             if audio_input:
# # # # # # #                 with st.spinner("Transcribing..."):
# # # # # # #                     from utils.speech_to_text import transcribe_audio
# # # # # # #                     answer = transcribe_audio(audio_input)

# # # # # # #                 if answer:
# # # # # # #                     # Show transcription typewriter style — feels like real-time
# # # # # # #                     st.write_stream(typewriter_stream(answer, words_per_second=8.0))
# # # # # # #                     st.caption("✏️ Your spoken answer — edit below if needed.")
# # # # # # #                     answer = st.text_area(
# # # # # # #                         "Edit if needed:",
# # # # # # #                         value  = answer,
# # # # # # #                         height = 100,
# # # # # # #                         key    = f"edit_{total_done}"
# # # # # # #                     )
# # # # # # #                 else:
# # # # # # #                     st.warning("Could not transcribe. Re-record or switch to text.")

# # # # # # #         st.markdown("&nbsp;")

# # # # # # #         b1, b2 = st.columns([3, 1])
# # # # # # #         with b1:
# # # # # # #             if st.button("✅ Submit Answer", type="primary",
# # # # # # #                          use_container_width=True, key=f"submit_{total_done}"):
# # # # # # #                 if answer.strip():
# # # # # # #                     handle_answer(answer.strip(), resume_text)
# # # # # # #                 else:
# # # # # # #                     st.warning("Please provide an answer before submitting.")
# # # # # # #         with b2:
# # # # # # #             if st.button("⏭ Skip", use_container_width=True, key=f"skip_{total_done}",
# # # # # # #                          help="Skip this question"):
# # # # # # #                 handle_answer("I am not sure about this question.", resume_text)

# # # # # # # # import streamlit as st
# # # # # # # # from interview.lisa_ai import generate_question
# # # # # # # # from interview.scoring import evaluate_answer
# # # # # # # # from interview.voice_ai import speak_question
# # # # # # # # from interview.transcribe import transcribe_audio


# # # # # # # # def interview_flow():

# # # # # # # #     resume = st.session_state.get("resume_text")

# # # # # # # #     if "question" not in st.session_state:
# # # # # # # #         st.session_state.question = generate_question("medium", resume)

# # # # # # # #     question = st.session_state.question

# # # # # # # #     st.write("### 🤖 LISA asks:")

# # # # # # # #     st.write(question)

# # # # # # # #     audio_file = speak_question(question)

# # # # # # # #     st.audio(audio_file)

# # # # # # # #     option = st.radio(
# # # # # # # #         "Choose Answer Mode",
# # # # # # # #         ["Chat Answer", "Speak Answer"]
# # # # # # # #     )

# # # # # # # #     if option == "Chat Answer":

# # # # # # # #         answer = st.text_area("Your Answer")

# # # # # # # #     else:

# # # # # # # #         audio = st.file_uploader(
# # # # # # # #             "Upload voice answer",
# # # # # # # #             type=["wav", "mp3", "m4a"]
# # # # # # # #         )

# # # # # # # #         answer = ""

# # # # # # # #         if audio:
# # # # # # # #             answer = transcribe_audio(audio)
# # # # # # # #             st.write("Transcription:", answer)

# # # # # # # #     if st.button("Submit Answer"):

# # # # # # # #         score, feedback = evaluate_answer(question, answer)

# # # # # # # #         st.write("### Score:", score)
# # # # # # # #         st.write("### Feedback:", feedback)

# # # # # # # #         st.session_state.question = generate_question(
# # # # # # # #             "medium",
# # # # # # # #             resume,
# # # # # # # #             answer
# # # # # # # #         )

# # # # # # # # # import streamlit as st
# # # # # # # # # from interview.lisa_ai import generate_question
# # # # # # # # # from interview.scoring import evaluate_answer
# # # # # # # # # from utils.resume_parser import extract_resume_text

# # # # # # # # # levels = ["easy"] * 4 + ["medium"] * 4 + ["hard"] * 4


# # # # # # # # # def interview_flow():

# # # # # # # # #     resume_path = st.session_state.get("resume_path")

# # # # # # # # #     resume_text = extract_resume_text(resume_path)

# # # # # # # # #     st.title("🎤 AI Interview with LISA")

# # # # # # # # #     if "q_index" not in st.session_state:

# # # # # # # # #         st.session_state.q_index = 0
# # # # # # # # #         st.session_state.answers = []
# # # # # # # # #         st.session_state.current_question = None

# # # # # # # # #     if st.session_state.q_index >= len(levels):

# # # # # # # # #         st.success("Interview Completed 🎉")
# # # # # # # # #         return

# # # # # # # # #     level = levels[st.session_state.q_index]

# # # # # # # # #     if st.session_state.current_question is None:

# # # # # # # # #         st.session_state.current_question = generate_question(
# # # # # # # # #             level,
# # # # # # # # #             resume_text
# # # # # # # # #         )

# # # # # # # # #     question = st.session_state.current_question

# # # # # # # # #     st.write(f"**LISA ({level.upper()}):** {question}")

# # # # # # # # #     answer = st.text_area("Your Answer")

# # # # # # # # #     if st.button("Submit Answer"):

# # # # # # # # #         score, feedback = evaluate_answer(question, answer)

# # # # # # # # #         st.session_state.answers.append({
# # # # # # # # #             "question": question,
# # # # # # # # #             "answer": answer,
# # # # # # # # #             "score": score
# # # # # # # # #         })

# # # # # # # # #         st.session_state.q_index += 1
# # # # # # # # #         st.session_state.current_question = None

# # # # # # # # #         st.rerun()

# # # # # # # # # # import streamlit as st
# # # # # # # # # # from interview.lisa_ai import generate_question
# # # # # # # # # # from interview.scoring import evaluate_answer

# # # # # # # # # # levels = ["easy"] * 4 + ["medium"] * 4 + ["hard"] * 4


# # # # # # # # # # def interview_flow():

# # # # # # # # # #     st.title("🎤 AI Interview with LISA")

# # # # # # # # # #     if "q_index" not in st.session_state:
# # # # # # # # # #         st.session_state.q_index = 0
# # # # # # # # # #         st.session_state.answers = []
# # # # # # # # # #         st.session_state.current_question = None

# # # # # # # # # #     # interview finished
# # # # # # # # # #     if st.session_state.q_index >= len(levels):
# # # # # # # # # #         st.success("Interview Completed 🎉")
# # # # # # # # # #         return

# # # # # # # # # #     level = levels[st.session_state.q_index]

# # # # # # # # # #     # generate question only once
# # # # # # # # # #     if st.session_state.current_question is None:

# # # # # # # # # #         st.session_state.current_question = generate_question(level)

# # # # # # # # # #     question = st.session_state.current_question

# # # # # # # # # #     st.write(f"**LISA ({level.upper()}):** {question}")

# # # # # # # # # #     answer = st.text_area("Your Answer", key=f"answer_{st.session_state.q_index}")

# # # # # # # # # #     if st.button("Submit Answer"):

# # # # # # # # # #         score, feedback = evaluate_answer(question, answer)

# # # # # # # # # #         st.session_state.answers.append({
# # # # # # # # # #             "question": question,
# # # # # # # # # #             "answer": answer,
# # # # # # # # # #             "score": score,
# # # # # # # # # #             "feedback": feedback
# # # # # # # # # #         })

# # # # # # # # # #         st.session_state.q_index += 1
# # # # # # # # # #         st.session_state.current_question = None

# # # # # # # # # #         st.rerun()


# # # # # # # # # # import streamlit as st
# # # # # # # # # # from interview.lisa_ai import generate_question

# # # # # # # # # # levels = ["easy"]*4 + ["medium"]*4 + ["hard"]*4

# # # # # # # # # # def interview_flow():
# # # # # # # # # #     st.title("🎤 AI Interview with LISA")

# # # # # # # # # #     if "q_index" not in st.session_state:
# # # # # # # # # #         st.session_state.q_index = 0
# # # # # # # # # #         st.session_state.answers = []

# # # # # # # # # #     if st.session_state.q_index < len(levels):

# # # # # # # # # #         level = levels[st.session_state.q_index]
# # # # # # # # # #         question = generate_question(level)

# # # # # # # # # #         st.write(f"**LISA ({level.upper()}):** {question}")

# # # # # # # # # #         answer = st.text_area("Your Answer")

# # # # # # # # # #         if st.button("Submit Answer"):
# # # # # # # # # #             st.session_state.answers.append((question, answer))
# # # # # # # # # #             st.session_state.q_index += 1
# # # # # # # # # #             st.rerun()

# # # # # # # # # #     else:
# # # # # # # # # #         st.success("Interview Completed 🎉")