import streamlit as st
from datetime import datetime

LISA_AVATAR_PATH = "assets/lisa_avatar.png"

STAGE_LABELS_CLEAN = {
    "easy":     "Introductory",
    "medium":   "Intermediate",
    "hard":     "Advanced",
    "adaptive": "Follow-up",
}

STAGE_BADGE_COLORS = {
    "easy":     "#10b981",
    "medium":   "#f59e0b",
    "hard":     "#ef4444",
    "adaptive": "#6366f1",
}


def now_time() -> str:
    return datetime.now().strftime("%I:%M %p")


def stage_badge(level: str) -> str:
    label = STAGE_LABELS_CLEAN.get(level, level.title())
    color = STAGE_BADGE_COLORS.get(level, "#6b7280")
    return (
        f'<span style="display:inline-block;font-size:10px;font-weight:700;'
        f'letter-spacing:1px;text-transform:uppercase;padding:2px 10px;'
        f'border-radius:20px;margin-left:8px;background:{color}22;'
        f'color:{color};border:1px solid {color}55;">{label}</span>'
    )


def strip_emojis(text: str) -> str:
    import re
    pattern = re.compile(
        "[" u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F9FF" u"\U00002600-\U000027BF"
        u"\U0001FA00-\U0001FA9F" "]+", flags=re.UNICODE
    )
    return pattern.sub("", text).strip()


def show_typing_indicator():
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;padding:6px 0;">
        <span style="font-size:11px;color:#10b981;font-weight:700;
                     letter-spacing:0.5px;">LISA is thinking</span>
        <div style="display:flex;gap:5px;align-items:center;">
            <span style="width:7px;height:7px;background:#10b981;border-radius:50%;
                display:inline-block;animation:tb 1.2s infinite 0s;"></span>
            <span style="width:7px;height:7px;background:#10b981;border-radius:50%;
                display:inline-block;animation:tb 1.2s infinite 0.2s;"></span>
            <span style="width:7px;height:7px;background:#10b981;border-radius:50%;
                display:inline-block;animation:tb 1.2s infinite 0.4s;"></span>
        </div>
    </div>
    <style>
    @keyframes tb{
        0%,80%,100%{transform:translateY(0);opacity:0.35;}
        40%{transform:translateY(-6px);opacity:1;}
    }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# INTERVIEW HEADER BAR (rendered inside the chat box)
# ─────────────────────────────────────────────
def render_interview_header(title: str, q_num: int, total_q: int,
                            level: str, timer_str: str, remaining: int):
    """Compact header bar matching reference UI — green icon, title, timer, end button."""
    badge = stage_badge(level)
    
    with st.container(border=True):
        col1, col2, col3 = st.columns([4, 1.5, 1])
        with col1:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="width:36px;height:36px;border-radius:10px;
                            background:linear-gradient(135deg,#10b981,#059669);
                            display:flex;align-items:center;justify-content:center;
                            font-size:18px;">🎯</div>
                <div>
                    <div style="color:#e2e8f0;font-size:15px;font-weight:700;
                                line-height:1.3;">{title}</div>
                    <div style="color:#64748b;font-size:12px;">
                        Question {q_num} of {total_q} {badge}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:6px;
                        background:#1a1f2e;border:1px solid #2d3548;
                        border-radius:8px;padding:6px 12px;width:fit-content;margin-top:4px;">
                <span style="color:#64748b;font-size:13px;">⏱</span>
                <span id="countdown_timer" style="color:#e2e8f0;font-size:14px;font-weight:600;
                             font-family:monospace;">{timer_str}</span>
            </div>
            <script>
                var timeLeft = {remaining};
                var timerSpan = document.getElementById('countdown_timer');
                var interval = setInterval(function() {{
                    if (timeLeft <= 0) {{
                        clearInterval(interval);
                        timerSpan.innerHTML = "00:00";
                    }} else {{
                        timeLeft--;
                        var minutes = Math.floor(timeLeft / 60);
                        var seconds = timeLeft % 60;
                        timerSpan.innerHTML = (minutes < 10 ? "0" : "") + minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
                    }}
                }}, 1000);
            </script>
            """, unsafe_allow_html=True)
        with col3:
            if st.button("🔴 End", type="secondary", key="end_btn_header"):
                st.session_state.interview_complete = True
                st.rerun()


def inject_interview_styles():
    st.markdown("""
    <style>

    /* ══════════════════════════════════════════
       GLOBAL — dark charcoal base (matches reference)
    ══════════════════════════════════════════ */
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stBottomBlockContainer"],
    section.main,
    .main .block-container {
        background-color: #141824 !important;
    }
    .stHeader, header { display: none !important; }
    #MainMenu, footer  { visibility: hidden !important; }

    /* Tighter padding — no excessive scroll */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0 !important;
        max-width: 960px !important;
    }

    /* Default text colour */
    .stApp p, .stApp span, .stApp div,
    .stApp label, .stMarkdown {
        color: #cbd5e1 !important;
    }

    /* ══════════════════════════════════════════
       SCROLLBAR — subtle teal
    ══════════════════════════════════════════ */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #141824; }
    ::-webkit-scrollbar-thumb {
        background: #2d3548;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover { background: #10b981; }

    /* ══════════════════════════════════════════
       PROGRESS BAR — hidden (we use header bar instead)
    ══════════════════════════════════════════ */
    [data-testid="stProgressBar"] { display: none !important; }

    /* ══════════════════════════════════════════
       METRICS — hidden (moved into header bar)
    ══════════════════════════════════════════ */
    [data-testid="stMetric"] { display: none !important; }

    /* ══════════════════════════════════════════
       DIVIDER — subtle
    ══════════════════════════════════════════ */
    hr { border-color: #2d3548 !important; opacity: 0.5 !important; }

    /* ══════════════════════════════════════════
       BUTTONS
    ══════════════════════════════════════════ */
    .stButton > button {
        background: #1a1f2e !important;
        border: 1px solid #2d3548 !important;
        color: #cbd5e1 !important;
        border-radius: 10px !important;
        transition: all 0.2s !important;
        font-size: 13px !important;
    }
    .stButton > button:hover {
        border-color: #10b981 !important;
        color: #10b981 !important;
        box-shadow: 0 0 12px rgba(16,185,129,0.15) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg,#10b981,#059669) !important;
        border: none !important;
        color: #fff !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 20px rgba(16,185,129,0.3) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg,#34d399,#10b981) !important;
        box-shadow: 0 4px 24px rgba(16,185,129,0.45) !important;
    }

    /* End Interview button — red accent */
    .stButton > button[kind="secondary"] {
        background: rgba(239,68,68,0.1) !important;
        border: 1px solid #ef4444 !important;
        color: #ef4444 !important;
        font-weight: 600 !important;
        font-size: 12px !important;
        padding: 4px 14px !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: #ef4444 !important;
        color: #fff !important;
    }

    /* ══════════════════════════════════════════
       SPINNER
    ══════════════════════════════════════════ */
    [data-testid="stSpinner"] div {
        border-top-color: #10b981 !important;
    }

    /* ══════════════════════════════════════════
       ALERTS
    ══════════════════════════════════════════ */
    [data-testid="stAlert"] {
        border-radius: 12px !important;
        border-left-width: 3px !important;
    }

    /* ══════════════════════════════════════════
       LISA BUBBLE — left side, teal-tinted dark card
    ══════════════════════════════════════════ */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
    [data-testid="stChatMessageContent"] {
        background: #1e2a3a !important;
        border: 1px solid #2d3e50 !important;
        border-radius: 4px 14px 14px 14px !important;
        padding: 16px 20px !important;
        max-width: 82% !important;
        margin-right: auto !important;
        margin-left: 0 !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.2) !important;
    }
    /* LISA text */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
    [data-testid="stChatMessageContent"] span,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
    [data-testid="stChatMessageContent"] div {
        color: #e2e8f0 !important;
        font-size: 14px !important;
        line-height: 1.7 !important;
    }
    /* Hide LISA audio player — voice plays via JS */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
    [data-testid="stAudio"],
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
    audio { display: none !important; }

    /* LISA avatar — green ring */
    [data-testid="chatAvatarIcon-assistant"] img {
        border-radius: 50% !important;
        border: 2px solid #10b981 !important;
        box-shadow: 0 0 10px rgba(16,185,129,0.2) !important;
    }

    /* ══════════════════════════════════════════
       USER BUBBLE — right side
    ══════════════════════════════════════════ */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
    [data-testid="stChatMessageContent"] {
        background: #162032 !important;
        border: 1px solid #1e3a5e !important;
        border-radius: 14px 4px 14px 14px !important;
        padding: 16px 20px !important;
        max-width: 82% !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.2) !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
    [data-testid="stChatMessageContent"],
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
    [data-testid="stChatMessageContent"] * {
        color: #dbeafe !important;
        font-size: 14px !important;
        line-height: 1.7 !important;
        background: transparent !important;
    }

    /* ══════════════════════════════════════════
       CAPTIONS / TIMESTAMPS
    ══════════════════════════════════════════ */
    .stChatMessage small,
    .stChatMessage [data-testid="stCaptionContainer"] p {
        color: #475569 !important;
        font-size: 10px !important;
    }

    /* ══════════════════════════════════════════
       MIC / AUDIO INPUT
    ══════════════════════════════════════════ */
    [data-testid="stAudioInput"] {
        background: #1a1f2e !important;
        border: 1px solid #2d3548 !important;
        border-radius: 12px !important;
        padding: 6px 14px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3) !important;
        margin-bottom: 4px !important;
        transition: border-color 0.2s !important;
    }
    [data-testid="stAudioInput"]:focus-within,
    [data-testid="stAudioInput"]:hover {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 2px rgba(16,185,129,0.1) !important;
    }
    [data-testid="stAudioInput"] button {
        color: #10b981 !important;
        background: transparent !important;
    }
    [data-testid="stAudioInput"] button svg {
        filter: drop-shadow(0 0 4px rgba(16,185,129,0.4)) !important;
    }
    [data-testid="stAudioInput"] > div {
        background: transparent !important;
        color: #475569 !important;
    }

    /* ══════════════════════════════════════════
       CHAT INPUT — dark bar at bottom, teal accents
    ══════════════════════════════════════════ */
    /* Kill all white from the bottom container */
    [data-testid="stBottomBlockContainer"],
    [data-testid="stBottomBlockContainer"] > div,
    [data-testid="stBottomBlockContainer"] > div > div,
    [data-testid="stChatInputContainer"],
    [data-testid="stChatInputContainer"] > div {
        background-color: #141824 !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Input pill */
    [data-testid="stChatInput"] {
        background-color: #1a1f2e !important;
        border: 1px solid #2d3548 !important;
        border-radius: 12px !important;
        padding: 8px 14px !important;
        box-shadow: 0 2px 14px rgba(0,0,0,0.3) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    /* Teal glow on focus */
    [data-testid="stChatInput"]:focus-within {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 2px rgba(16,185,129,0.12),
                    0 2px 14px rgba(0,0,0,0.3) !important;
    }

    /* Textarea — dark bg, light text */
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInput"] textarea:focus {
        background-color: #1a1f2e !important;
        color: #f1f5f9 !important;
        -webkit-text-fill-color: #f1f5f9 !important;
        font-size: 14px !important;
        font-weight: 400 !important;
        line-height: 1.5 !important;
        caret-color: #10b981 !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #475569 !important;
        -webkit-text-fill-color: #475569 !important;
        opacity: 1 !important;
    }

    /* Send button — teal gradient matching reference */
    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg,#10b981,#059669) !important;
        border: none !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        padding: 6px 14px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(16,185,129,0.3) !important;
    }
    [data-testid="stChatInput"] button:hover {
        background: linear-gradient(135deg,#34d399,#10b981) !important;
        box-shadow: 0 0 16px rgba(16,185,129,0.4) !important;
        transform: scale(1.05) !important;
    }
    /* Arrow icon — white */
    [data-testid="stChatInput"] button svg {
        color: #ffffff !important;
        filter: drop-shadow(0 0 3px rgba(255,255,255,0.3)) !important;
    }

    /* ══════════════════════════════════════════
       SCROLLABLE CHAT BOX (st.container with height)
       — the contained chat area that scrolls internally
    ══════════════════════════════════════════ */
    /* The outer wrapper Streamlit creates for height-constrained containers */
    [data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) {
        background: #1a1f2e !important;
        border: 1px solid #2d3548 !important;
        border-radius: 14px !important;
        box-shadow: 0 4px 24px rgba(0,0,0,0.3) !important;
        overflow: hidden !important;
    }
    /* The scrollable inner div */
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background: #1a1f2e !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div::-webkit-scrollbar {
        width: 5px;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div::-webkit-scrollbar-track {
        background: #1a1f2e;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div::-webkit-scrollbar-thumb {
        background: #2d3548;
        border-radius: 4px;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div::-webkit-scrollbar-thumb:hover {
        background: #10b981;
    }

    /* ══════════════════════════════════════════
       PAGE OVERFLOW — prevent page-level scroll
    ══════════════════════════════════════════ */
    [data-testid="stAppViewContainer"],
    section.main {
        overflow: hidden !important;
    }
    .main .block-container {
        overflow: visible !important;
    }

    </style>
    """, unsafe_allow_html=True)
