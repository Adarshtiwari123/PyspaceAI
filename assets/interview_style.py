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
        <span style="font-size:11px;color:#00d4ff;font-weight:700;
                     letter-spacing:0.5px;">LISA is thinking</span>
        <div style="display:flex;gap:5px;align-items:center;">
            <span style="width:7px;height:7px;background:#00d4ff;border-radius:50%;
                display:inline-block;animation:tb 1.2s infinite 0s;"></span>
            <span style="width:7px;height:7px;background:#00d4ff;border-radius:50%;
                display:inline-block;animation:tb 1.2s infinite 0.2s;"></span>
            <span style="width:7px;height:7px;background:#00d4ff;border-radius:50%;
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


def inject_interview_styles():
    st.markdown("""
    <style>

    /* ══════════════════════════════════════════
       GLOBAL — same base as login page
    ══════════════════════════════════════════ */
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stBottomBlockContainer"],
    section.main,
    .main .block-container {
        background-color: #0a0c12 !important;
    }
    .stHeader, header { display: none !important; }
    #MainMenu, footer  { visibility: hidden !important; }

    /* Default text colour */
    .stApp p, .stApp span, .stApp div,
    .stApp label, .stMarkdown {
        color: #cbd5e1 !important;
    }

    /* ══════════════════════════════════════════
       SCROLLBAR — subtle dark blue
    ══════════════════════════════════════════ */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #0a0c12; }
    ::-webkit-scrollbar-thumb {
        background: #1e3a6e;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover { background: #00d4ff; }

    /* ══════════════════════════════════════════
       PROGRESS BAR
    ══════════════════════════════════════════ */
    [data-testid="stProgressBar"] > div {
        background: #111827 !important;
        border-radius: 6px !important;
        border: 1px solid #1e2d47 !important;
    }
    [data-testid="stProgressBar"] > div > div {
        background: linear-gradient(90deg, #1d4ed8, #00d4ff) !important;
        border-radius: 6px !important;
        box-shadow: 0 0 10px rgba(0,212,255,0.3) !important;
    }

    /* ══════════════════════════════════════════
       METRICS
    ══════════════════════════════════════════ */
    [data-testid="stMetricValue"] {
        color: #00d4ff !important;
        font-weight: 800 !important;
        text-shadow: 0 0 12px rgba(0,212,255,0.25) !important;
    }
    [data-testid="stMetricLabel"] { color: #475569 !important; }

    /* ══════════════════════════════════════════
       BUTTONS
    ══════════════════════════════════════════ */
    .stButton > button {
        background: #0f172a !important;
        border: 1px solid #1e3a6e !important;
        color: #cbd5e1 !important;
        border-radius: 10px !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover {
        border-color: #00d4ff !important;
        color: #00d4ff !important;
        box-shadow: 0 0 12px rgba(0,212,255,0.2) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg,#1d4ed8,#2563eb) !important;
        border: none !important;
        color: #fff !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 20px rgba(29,78,216,0.35) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg,#2563eb,#00d4ff) !important;
        box-shadow: 0 4px 24px rgba(0,212,255,0.35) !important;
    }

    /* ══════════════════════════════════════════
       DIVIDER
    ══════════════════════════════════════════ */
    hr { border-color: #1e293b !important; }

    /* ══════════════════════════════════════════
       SPINNER
    ══════════════════════════════════════════ */
    [data-testid="stSpinner"] div {
        border-top-color: #00d4ff !important;
    }

    /* ══════════════════════════════════════════
       ALERTS
    ══════════════════════════════════════════ */
    [data-testid="stAlert"] {
        border-radius: 12px !important;
        border-left-width: 3px !important;
    }

    /* ══════════════════════════════════════════
       LISA BUBBLE — left side
       Same card language as login page cards
    ══════════════════════════════════════════ */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
    [data-testid="stChatMessageContent"] {
        background: #111827 !important;
        border: 1px solid #1e2d47 !important;
        border-radius: 0 16px 16px 16px !important;
        padding: 18px 22px !important;
        max-width: 76% !important;
        margin-right: auto !important;
        margin-left: 0 !important;
        box-shadow:
            0 0 0 1px rgba(0,212,255,0.04),
            0 4px 24px rgba(0,0,0,0.4) !important;
    }
    /* LISA text */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
    [data-testid="stChatMessageContent"] span,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
    [data-testid="stChatMessageContent"] div {
        color: #f0f4ff !important;
        font-size: 15px !important;
        line-height: 1.75 !important;
    }
    /* Hide LISA audio player — voice plays via JS */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
    [data-testid="stAudio"],
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
    audio { display: none !important; }

    /* LISA avatar ring — matches login glow ring */
    [data-testid="chatAvatarIcon-assistant"] img {
        border-radius: 50% !important;
        border: 2px solid transparent !important;
        background: linear-gradient(#111827,#111827) padding-box,
                    linear-gradient(135deg,#00d4ff,#2563eb) border-box !important;
        box-shadow: 0 0 14px rgba(0,212,255,0.2) !important;
    }

    /* ══════════════════════════════════════════
       USER BUBBLE — right side
    ══════════════════════════════════════════ */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
    [data-testid="stChatMessageContent"] {
        background: #0f1f3d !important;
        border: 1px solid #1e3a6e !important;
        border-radius: 16px 0 16px 16px !important;
        padding: 18px 22px !important;
        max-width: 76% !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        box-shadow: 0 4px 20px rgba(37,99,235,0.1) !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
    [data-testid="stChatMessageContent"],
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
    [data-testid="stChatMessageContent"] * {
        color: #dbeafe !important;
        font-size: 15px !important;
        line-height: 1.75 !important;
        background: transparent !important;
    }

    /* ══════════════════════════════════════════
       CAPTIONS / TIMESTAMPS
    ══════════════════════════════════════════ */
    .stChatMessage small,
    .stChatMessage [data-testid="stCaptionContainer"] p {
        color: #1e3a6e !important;
        font-size: 10px !important;
    }

    /* ══════════════════════════════════════════
       MIC / AUDIO INPUT
       Same card as chat input — consistent feel
    ══════════════════════════════════════════ */
    [data-testid="stAudioInput"] {
        background: #0d1117 !important;
        border: 1.5px solid #1e3a6e !important;
        border-radius: 16px !important;
        padding: 8px 16px !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.4) !important;
        margin-bottom: 6px !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    [data-testid="stAudioInput"]:focus-within,
    [data-testid="stAudioInput"]:hover {
        border-color: #00d4ff !important;
        box-shadow: 0 0 0 3px rgba(0,212,255,0.1),
                    0 4px 16px rgba(0,0,0,0.4) !important;
    }
    [data-testid="stAudioInput"] button {
        color: #00d4ff !important;
        background: transparent !important;
    }
    [data-testid="stAudioInput"] button svg {
        filter: drop-shadow(0 0 4px rgba(0,212,255,0.5)) !important;
    }
    [data-testid="stAudioInput"] > div {
        background: transparent !important;
        color: #334155 !important;
    }

    /* ══════════════════════════════════════════
       CHAT INPUT — deep black, LISA cyan accents
       Same exact language as login input fields
    ══════════════════════════════════════════ */
    /* Kill all white from the bottom container */
    [data-testid="stBottomBlockContainer"],
    [data-testid="stBottomBlockContainer"] > div,
    [data-testid="stBottomBlockContainer"] > div > div,
    [data-testid="stChatInputContainer"],
    [data-testid="stChatInputContainer"] > div {
        background-color: #0a0c12 !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Input pill — matches login .stTextInput card */
    [data-testid="stChatInput"] {
        background-color: #0f172a !important;
        border: 1.5px solid #1e3a6e !important;
        border-radius: 14px !important;
        padding: 10px 16px !important;
        box-shadow: 0 4px 24px rgba(0,0,0,0.5),
                    inset 0 1px 0 rgba(255,255,255,0.02) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    /* Cyan glow on focus — same as login inputs */
    [data-testid="stChatInput"]:focus-within {
        border-color: #00d4ff !important;
        box-shadow: 0 0 0 3px rgba(0,212,255,0.1),
                    0 4px 24px rgba(0,0,0,0.5) !important;
    }

    /* Textarea — dark bg, light text, NEVER transparent */
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInput"] textarea:focus {
        background-color: #0f172a !important;
        color: #f1f5f9 !important;
        -webkit-text-fill-color: #f1f5f9 !important;
        font-size: 15px !important;
        font-weight: 400 !important;
        line-height: 1.6 !important;
        caret-color: #00d4ff !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #1e3a6e !important;
        -webkit-text-fill-color: #1e3a6e !important;
        opacity: 1 !important;
    }

    /* Send button — matches LISA primary button language */
    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg,#1d4ed8,#2563eb) !important;
        border: none !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        padding: 6px 12px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 12px rgba(29,78,216,0.4) !important;
    }
    [data-testid="stChatInput"] button:hover {
        background: linear-gradient(135deg,#2563eb,#00d4ff) !important;
        box-shadow: 0 0 20px rgba(0,212,255,0.45),
                    0 2px 12px rgba(29,78,216,0.4) !important;
        transform: scale(1.05) !important;
    }
    /* Arrow icon — white with subtle cyan glow */
    [data-testid="stChatInput"] button svg {
        color: #ffffff !important;
        filter: drop-shadow(0 0 4px rgba(0,212,255,0.6)) !important;
    }

    </style>
    """, unsafe_allow_html=True)
# import streamlit as st
# from datetime import datetime

# LISA_AVATAR_PATH = "assets/lisa_avatar.png"

# STAGE_LABELS_CLEAN = {
#     "easy":     "Introductory",
#     "medium":   "Intermediate",
#     "hard":     "Advanced",
#     "adaptive": "Follow-up",
# }

# STAGE_BADGE_COLORS = {
#     "easy":     "#10b981",
#     "medium":   "#f59e0b",
#     "hard":     "#ef4444",
#     "adaptive": "#6366f1",
# }


# def now_time() -> str:
#     return datetime.now().strftime("%I:%M %p")


# def stage_badge(level: str) -> str:
#     label = STAGE_LABELS_CLEAN.get(level, level.title())
#     color = STAGE_BADGE_COLORS.get(level, "#6b7280")
#     return (
#         f'<span style="display:inline-block;font-size:10px;font-weight:700;'
#         f'letter-spacing:1px;text-transform:uppercase;padding:2px 10px;'
#         f'border-radius:20px;margin-left:8px;background:{color}22;'
#         f'color:{color};border:1px solid {color}55;">{label}</span>'
#     )


# def strip_emojis(text: str) -> str:
#     import re
#     pattern = re.compile(
#         "[" u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF"
#         u"\U0001F680-\U0001F9FF" u"\U00002600-\U000027BF"
#         u"\U0001FA00-\U0001FA9F" "]+", flags=re.UNICODE
#     )
#     return pattern.sub("", text).strip()


# def show_typing_indicator():
#     st.markdown("""
#     <div style="display:flex;align-items:center;gap:6px;padding:4px 0;">
#         <span style="font-size:11px;color:#00d4ff;font-weight:600;">LISA is typing</span>
#         <div style="display:flex;gap:4px;align-items:center;">
#             <span style="width:7px;height:7px;background:#00d4ff;border-radius:50%;
#                 display:inline-block;animation:tb 1.2s infinite 0s;opacity:0.4;"></span>
#             <span style="width:7px;height:7px;background:#00d4ff;border-radius:50%;
#                 display:inline-block;animation:tb 1.2s infinite 0.2s;opacity:0.4;"></span>
#             <span style="width:7px;height:7px;background:#00d4ff;border-radius:50%;
#                 display:inline-block;animation:tb 1.2s infinite 0.4s;opacity:0.4;"></span>
#         </div>
#     </div>
#     <style>
#     @keyframes tb{0%,80%,100%{transform:translateY(0);opacity:0.4;}40%{transform:translateY(-5px);opacity:1;}}
#     </style>
#     """, unsafe_allow_html=True)


# def inject_interview_styles():
#     st.markdown("""
#     <style>

#     /* ════ DARK BACKGROUND — every layer ════ */
#     .stApp,
#     .stApp > div,
#     [data-testid="stAppViewContainer"],
#     [data-testid="stMain"],
#     [data-testid="stBottomBlockContainer"],
#     section.main,
#     .main .block-container {
#         background-color: #0a0c12 !important;
#     }
#     .stHeader, header { display: none !important; }
#     #MainMenu, footer { visibility: hidden !important; }

#     /* ════ DEFAULT TEXT ════ */
#     .stApp p, .stApp span, .stApp div,
#     .stApp label, .stMarkdown {
#         color: #e2e8f0 !important;
#     }

#     /* ════ LISA BUBBLE — left ════ */
#     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
#     [data-testid="stChatMessageContent"] {
#         background: #111827 !important;
#         border: 1px solid #1e2d47 !important;
#         border-radius: 0 16px 16px 16px !important;
#         padding: 16px 20px !important;
#         max-width: 76% !important;
#         margin-right: auto !important;
#         margin-left: 0 !important;
#         box-shadow: 0 0 30px rgba(0,212,255,0.04) !important;
#     }
#     /* LISA text — bright white */
#     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
#     [data-testid="stChatMessageContent"] p,
#     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
#     [data-testid="stChatMessageContent"] span,
#     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
#     [data-testid="stChatMessageContent"] div {
#         color: #f0f4ff !important;
#         font-size: 15px !important;
#         line-height: 1.7 !important;
#     }

#     /* ════ USER BUBBLE — right, dark navy ════ */
#     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
#     [data-testid="stChatMessageContent"] {
#         background: #0f1f3d !important;
#         border: 1px solid #1e3a6e !important;
#         border-radius: 16px 0 16px 16px !important;
#         padding: 16px 20px !important;
#         max-width: 76% !important;
#         margin-left: auto !important;
#         margin-right: 0 !important;
#         box-shadow: 0 0 20px rgba(37,99,235,0.08) !important;
#     }
#     /* USER text — white, every element forced */
#     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
#     [data-testid="stChatMessageContent"],
#     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
#     [data-testid="stChatMessageContent"] *,
#     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
#     [data-testid="stChatMessageContent"] p,
#     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
#     [data-testid="stChatMessageContent"] span,
#     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
#     [data-testid="stChatMessageContent"] div {
#         color: #dbeafe !important;
#         font-size: 15px !important;
#         line-height: 1.7 !important;
#         background: transparent !important;
#     }

#     /* ════ CHAT INPUT — dark background, white text ════ */
#     [data-testid="stBottomBlockContainer"],
#     [data-testid="stBottomBlockContainer"] > div,
#     [data-testid="stBottomBlockContainer"] > div > div {
#         background-color: #0a0c12 !important;
#     }
#     [data-testid="stChatInput"] {
#         background: linear-gradient(145deg,#111827,#1f2937) !important;
#         border: 1px solid #374151 !important;
#         border-radius: 16px !important;
#         padding: 10px 14px !important;
#         box-shadow: 0 6px 25px rgba(0,0,0,0.45) !important;
#         transition: all 0.25s ease !important;
#     }
#     [data-testid="stChatInput"]:focus-within {
#         border: 1px solid #00d4ff !important;
#         box-shadow: 0 0 10px rgba(0,212,255,0.4) !important;
#     }
#     /* Force dark bg + dark text on textarea so text is always readable */
#     [data-testid="stChatInput"] textarea {
#         background-color: #111827 !important;
#         color: #f1f5f9 !important;
#         font-size: 15px !important;
#         font-weight: 400 !important;
#         caret-color: #00d4ff !important;
#         border: none !important;
#         outline: none !important;
#         -webkit-text-fill-color: #f1f5f9 !important;
#     }
#     [data-testid="stChatInput"] textarea::placeholder {
#         color: #4b5563 !important;
#         -webkit-text-fill-color: #4b5563 !important;
#         opacity: 1 !important;
#     }
#     [data-testid="stChatInput"] button {
#         color: #00d4ff !important;
#         background: transparent !important;
#     }
#     [data-testid="stChatInput"] button:hover {
#         color: #ffffff !important;
#         background: #1e3a6e !important;
#         border-radius: 8px !important;
#     }

#     /* ════ MIC / AUDIO INPUT — dark, matches chat bar ════ */
#     [data-testid="stAudioInput"] {
#         background: linear-gradient(145deg,#111827,#1f2937) !important;
#         border: 1px solid #374151 !important;
#         border-radius: 16px !important;
#         padding: 6px 14px !important;
#         box-shadow: 0 4px 16px rgba(0,0,0,0.4) !important;
#         margin-bottom: 6px !important;
#     }
#     [data-testid="stAudioInput"]:focus-within {
#         border-color: #00d4ff !important;
#         box-shadow: 0 0 10px rgba(0,212,255,0.3) !important;
#     }
#     [data-testid="stAudioInput"] button {
#         color: #00d4ff !important;
#         background: transparent !important;
#     }
#     [data-testid="stAudioInput"] > div {
#         background: transparent !important;
#         color: #9ca3af !important;
#     }
#     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
#     [data-testid="stAudio"],
#     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
#     audio { display: none !important; }

#     /* ════ PROGRESS BAR ════ */
#     [data-testid="stProgressBar"] > div > div {
#         background: linear-gradient(90deg,#00d4ff,#2563eb) !important;
#         border-radius: 4px !important;
#     }

#     /* ════ METRICS ════ */
#     [data-testid="stMetricValue"] { color: #00d4ff !important; font-weight:700 !important; }
#     [data-testid="stMetricLabel"] { color: #6b7280 !important; }

#     /* ════ BUTTONS ════ */
#     .stButton > button {
#         background: #111827 !important;
#         border: 1px solid #1e2d47 !important;
#         color: #e2e8f0 !important;
#         border-radius: 8px !important;
#     }
#     .stButton > button:hover {
#         border-color: #00d4ff !important;
#         color: #00d4ff !important;
#     }

#     /* ════ SPINNER ════ */
#     [data-testid="stSpinner"] div { border-top-color: #00d4ff !important; }

#     /* ════ DIVIDER ════ */
#     hr { border-color: #1e2d47 !important; }

#     /* ════ CAPTIONS ════ */
#     .stChatMessage small,
#     .stChatMessage [data-testid="stCaptionContainer"] p {
#         color: #374151 !important;
#         font-size: 11px !important;
#     }

#     /* ════ AVATAR ════ */
#     [data-testid="chatAvatarIcon-assistant"] img {
#         border-radius: 50% !important;
#         border: 1px solid #00d4ff33 !important;
#     }

#     /* ════ SCROLLBAR ════ */
#     ::-webkit-scrollbar { width: 5px; }
#     ::-webkit-scrollbar-track { background: #0a0c12; }
#     ::-webkit-scrollbar-thumb { background: #1e2d47; border-radius: 4px; }
#     ::-webkit-scrollbar-thumb:hover { background: #2563eb; }

#     </style>
#     """, unsafe_allow_html=True)
# # import streamlit as st
# # from datetime import datetime

# # LISA_AVATAR_PATH = "assets/lisa_avatar.png"

# # STAGE_LABELS_CLEAN = {
# #     "easy":     "Introductory",
# #     "medium":   "Intermediate",
# #     "hard":     "Advanced",
# #     "adaptive": "Follow-up",
# # }

# # STAGE_BADGE_COLORS = {
# #     "easy":     "#10b981",
# #     "medium":   "#f59e0b",
# #     "hard":     "#ef4444",
# #     "adaptive": "#6366f1",
# # }


# # def now_time() -> str:
# #     return datetime.now().strftime("%I:%M %p")


# # def stage_badge(level: str) -> str:
# #     label = STAGE_LABELS_CLEAN.get(level, level.title())
# #     color = STAGE_BADGE_COLORS.get(level, "#6b7280")
# #     return (
# #         f'<span style="display:inline-block;font-size:10px;font-weight:700;'
# #         f'letter-spacing:1px;text-transform:uppercase;padding:2px 10px;'
# #         f'border-radius:20px;margin-left:8px;background:{color}22;'
# #         f'color:{color};border:1px solid {color}55;">{label}</span>'
# #     )


# # def strip_emojis(text: str) -> str:
# #     import re
# #     pattern = re.compile(
# #         "[" u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF"
# #         u"\U0001F680-\U0001F9FF" u"\U00002600-\U000027BF"
# #         u"\U0001FA00-\U0001FA9F" "]+", flags=re.UNICODE
# #     )
# #     return pattern.sub("", text).strip()


# # def show_typing_indicator():
# #     st.markdown("""
# #     <div style="display:flex;align-items:center;gap:6px;padding:4px 0;">
# #         <span style="font-size:11px;color:#00d4ff;font-weight:600;">LISA is typing</span>
# #         <div style="display:flex;gap:4px;align-items:center;">
# #             <span style="width:7px;height:7px;background:#00d4ff;border-radius:50%;
# #                 display:inline-block;animation:tb 1.2s infinite 0s;opacity:0.4;"></span>
# #             <span style="width:7px;height:7px;background:#00d4ff;border-radius:50%;
# #                 display:inline-block;animation:tb 1.2s infinite 0.2s;opacity:0.4;"></span>
# #             <span style="width:7px;height:7px;background:#00d4ff;border-radius:50%;
# #                 display:inline-block;animation:tb 1.2s infinite 0.4s;opacity:0.4;"></span>
# #         </div>
# #     </div>
# #     <style>
# #     @keyframes tb{0%,80%,100%{transform:translateY(0);opacity:0.4;}40%{transform:translateY(-5px);opacity:1;}}
# #     </style>
# #     """, unsafe_allow_html=True)


# # def inject_interview_styles():
# #     st.markdown("""
# #     <style>

# #     /* ════ DARK BACKGROUND — every layer ════ */
# #     .stApp,
# #     .stApp > div,
# #     [data-testid="stAppViewContainer"],
# #     [data-testid="stMain"],
# #     [data-testid="stBottomBlockContainer"],
# #     section.main,
# #     .main .block-container {
# #         background-color: #0a0c12 !important;
# #     }
# #     .stHeader, header { display: none !important; }
# #     #MainMenu, footer { visibility: hidden !important; }

# #     /* ════ DEFAULT TEXT ════ */
# #     .stApp p, .stApp span, .stApp div,
# #     .stApp label, .stMarkdown {
# #         color: #e2e8f0 !important;
# #     }

# #     /* ════ LISA BUBBLE — left ════ */
# #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
# #     [data-testid="stChatMessageContent"] {
# #         background: #111827 !important;
# #         border: 1px solid #1e2d47 !important;
# #         border-radius: 0 16px 16px 16px !important;
# #         padding: 16px 20px !important;
# #         max-width: 76% !important;
# #         margin-right: auto !important;
# #         margin-left: 0 !important;
# #         box-shadow: 0 0 30px rgba(0,212,255,0.04) !important;
# #     }
# #     /* LISA text — bright white */
# #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
# #     [data-testid="stChatMessageContent"] p,
# #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
# #     [data-testid="stChatMessageContent"] span,
# #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
# #     [data-testid="stChatMessageContent"] div {
# #         color: #f0f4ff !important;
# #         font-size: 15px !important;
# #         line-height: 1.7 !important;
# #     }

# #     /* ════ USER BUBBLE — right, dark navy ════ */
# #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
# #     [data-testid="stChatMessageContent"] {
# #         background: #0f1f3d !important;
# #         border: 1px solid #1e3a6e !important;
# #         border-radius: 16px 0 16px 16px !important;
# #         padding: 16px 20px !important;
# #         max-width: 76% !important;
# #         margin-left: auto !important;
# #         margin-right: 0 !important;
# #         box-shadow: 0 0 20px rgba(37,99,235,0.08) !important;
# #     }
# #     /* USER text — white, every element forced */
# #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
# #     [data-testid="stChatMessageContent"],
# #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
# #     [data-testid="stChatMessageContent"] *,
# #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
# #     [data-testid="stChatMessageContent"] p,
# #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
# #     [data-testid="stChatMessageContent"] span,
# #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
# #     [data-testid="stChatMessageContent"] div {
# #         color: #dbeafe !important;
# #         font-size: 15px !important;
# #         line-height: 1.7 !important;
# #         background: transparent !important;
# #     }

# #     /* ════ CHAT INPUT — your exact CSS ════ */
# #     [data-testid="stChatInput"] {
# #         background: linear-gradient(145deg,#111827,#1f2937) !important;
# #         border: 1px solid #374151 !important;
# #         border-radius: 16px !important;
# #         padding: 10px 14px !important;
# #         box-shadow: 0 6px 25px rgba(0,0,0,0.45) !important;
# #         transition: all 0.25s ease !important;
# #     }
# #     [data-testid="stChatInput"]:focus-within {
# #         border: 1px solid #00d4ff !important;
# #         box-shadow: 0 0 10px rgba(0,212,255,0.4) !important;
# #     }
# #     [data-testid="stChatInput"] textarea {
# #         background: transparent !important;
# #         color: #ffffff !important;
# #         font-size: 16px !important;
# #         font-weight: 500 !important;
# #         caret-color: #00d4ff !important;
# #         border: none !important;
# #         outline: none !important;
# #     }
# #     [data-testid="stChatInput"] textarea::placeholder {
# #         color: #9ca3af !important;
# #         opacity: 1 !important;
# #     }
# #     [data-testid="stChatInput"] button {
# #         color: #00d4ff !important;
# #         background: transparent !important;
# #     }
# #     [data-testid="stChatInput"] button:hover {
# #         color: #ffffff !important;
# #         background: #1e3a6e !important;
# #         border-radius: 8px !important;
# #     }

# #     /* ════ MIC / AUDIO INPUT — dark, matches chat bar ════ */
# #     [data-testid="stAudioInput"] {
# #         background: linear-gradient(145deg,#111827,#1f2937) !important;
# #         border: 1px solid #374151 !important;
# #         border-radius: 16px !important;
# #         padding: 6px 14px !important;
# #         box-shadow: 0 4px 16px rgba(0,0,0,0.4) !important;
# #         margin-bottom: 6px !important;
# #     }
# #     [data-testid="stAudioInput"]:focus-within {
# #         border-color: #00d4ff !important;
# #         box-shadow: 0 0 10px rgba(0,212,255,0.3) !important;
# #     }
# #     [data-testid="stAudioInput"] button {
# #         color: #00d4ff !important;
# #         background: transparent !important;
# #     }
# #     [data-testid="stAudioInput"] > div {
# #         background: transparent !important;
# #         color: #9ca3af !important;
# #     }
# #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
# #     [data-testid="stAudio"],
# #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
# #     audio { display: none !important; }

# #     /* ════ PROGRESS BAR ════ */
# #     [data-testid="stProgressBar"] > div > div {
# #         background: linear-gradient(90deg,#00d4ff,#2563eb) !important;
# #         border-radius: 4px !important;
# #     }

# #     /* ════ METRICS ════ */
# #     [data-testid="stMetricValue"] { color: #00d4ff !important; font-weight:700 !important; }
# #     [data-testid="stMetricLabel"] { color: #6b7280 !important; }

# #     /* ════ BUTTONS ════ */
# #     .stButton > button {
# #         background: #111827 !important;
# #         border: 1px solid #1e2d47 !important;
# #         color: #e2e8f0 !important;
# #         border-radius: 8px !important;
# #     }
# #     .stButton > button:hover {
# #         border-color: #00d4ff !important;
# #         color: #00d4ff !important;
# #     }

# #     /* ════ SPINNER ════ */
# #     [data-testid="stSpinner"] div { border-top-color: #00d4ff !important; }

# #     /* ════ DIVIDER ════ */
# #     hr { border-color: #1e2d47 !important; }

# #     /* ════ CAPTIONS ════ */
# #     .stChatMessage small,
# #     .stChatMessage [data-testid="stCaptionContainer"] p {
# #         color: #374151 !important;
# #         font-size: 11px !important;
# #     }

# #     /* ════ AVATAR ════ */
# #     [data-testid="chatAvatarIcon-assistant"] img {
# #         border-radius: 50% !important;
# #         border: 1px solid #00d4ff33 !important;
# #     }

# #     /* ════ SCROLLBAR ════ */
# #     ::-webkit-scrollbar { width: 5px; }
# #     ::-webkit-scrollbar-track { background: #0a0c12; }
# #     ::-webkit-scrollbar-thumb { background: #1e2d47; border-radius: 4px; }
# #     ::-webkit-scrollbar-thumb:hover { background: #2563eb; }

# #     </style>
# #     """, unsafe_allow_html=True)
# # # import streamlit as st
# # # from datetime import datetime

# # # # ─────────────────────────────────────────────
# # # # LISA AVATAR — uploaded robot image
# # # # Place lisa_avatar.png inside assets/ folder
# # # # ─────────────────────────────────────────────
# # # LISA_AVATAR_PATH = "assets/lisa_avatar.png"

# # # # ─────────────────────────────────────────────
# # # # STAGE LABELS — professional, no emoji
# # # # ─────────────────────────────────────────────
# # # STAGE_LABELS_CLEAN = {
# # #     "easy":     "Introductory",
# # #     "medium":   "Intermediate",
# # #     "hard":     "Advanced",
# # #     "adaptive": "Follow-up",
# # # }

# # # STAGE_BADGE_COLORS = {
# # #     "easy":     "#10b981",
# # #     "medium":   "#f59e0b",
# # #     "hard":     "#ef4444",
# # #     "adaptive": "#6366f1",
# # # }


# # # def now_time() -> str:
# # #     return datetime.now().strftime("%I:%M %p")


# # # # ─────────────────────────────────────────────
# # # # STAGE BADGE HTML
# # # # ─────────────────────────────────────────────
# # # def stage_badge(level: str) -> str:
# # #     label = STAGE_LABELS_CLEAN.get(level, level.title())
# # #     color = STAGE_BADGE_COLORS.get(level, "#6b7280")
# # #     return (
# # #         f'<span style="'
# # #         f'display:inline-block;font-size:10px;font-weight:700;'
# # #         f'letter-spacing:1px;text-transform:uppercase;'
# # #         f'padding:2px 10px;border-radius:20px;margin-left:8px;'
# # #         f'background:{color}22;color:{color};border:1px solid {color}55;">'
# # #         f'{label}</span>'
# # #     )


# # # # ─────────────────────────────────────────────
# # # # STRIP EMOJIS — professional LISA questions
# # # # ─────────────────────────────────────────────
# # # def strip_emojis(text: str) -> str:
# # #     import re
# # #     pattern = re.compile(
# # #         "["
# # #         u"\U0001F600-\U0001F64F"
# # #         u"\U0001F300-\U0001F5FF"
# # #         u"\U0001F680-\U0001F9FF"
# # #         u"\U00002600-\U000027BF"
# # #         u"\U0001FA00-\U0001FA9F"
# # #         "]+",
# # #         flags=re.UNICODE
# # #     )
# # #     return pattern.sub("", text).strip()


# # # # ─────────────────────────────────────────────
# # # # TYPING INDICATOR
# # # # ─────────────────────────────────────────────
# # # def show_typing_indicator():
# # #     st.markdown("""
# # #     <div style="display:flex;align-items:center;gap:6px;padding:4px 0;">
# # #         <span style="font-size:11px;color:#00d4ff;font-weight:600;">
# # #             LISA is typing
# # #         </span>
# # #         <div style="display:flex;gap:4px;align-items:center;">
# # #             <span style="width:7px;height:7px;background:#00d4ff;border-radius:50%;
# # #                 display:inline-block;animation:tb 1.2s infinite 0s;opacity:0.4;"></span>
# # #             <span style="width:7px;height:7px;background:#00d4ff;border-radius:50%;
# # #                 display:inline-block;animation:tb 1.2s infinite 0.2s;opacity:0.4;"></span>
# # #             <span style="width:7px;height:7px;background:#00d4ff;border-radius:50%;
# # #                 display:inline-block;animation:tb 1.2s infinite 0.4s;opacity:0.4;"></span>
# # #         </div>
# # #     </div>
# # #     <style>
# # #     @keyframes tb {
# # #         0%,80%,100%{transform:translateY(0);opacity:0.4;}
# # #         40%{transform:translateY(-5px);opacity:1;}
# # #     }
# # #     </style>
# # #     """, unsafe_allow_html=True)


# # # # ─────────────────────────────────────────────
# # # # MAIN STYLE INJECTION
# # # # ─────────────────────────────────────────────
# # # def inject_interview_styles():
# # #     st.markdown("""
# # #     <style>

# # #     /* ════ GLOBAL DARK BACKGROUND ════ */
# # #     .stApp, .stApp > div {
# # #         background-color: #0d0f14 !important;
# # #     }
# # #     .stMain, [data-testid="stAppViewContainer"] {
# # #         background-color: #0d0f14 !important;
# # #     }
# # #     .stHeader { display: none !important; }
# # #     #MainMenu, footer { visibility: hidden !important; }

# # #     /* ════ ALL TEXT DEFAULT ════ */
# # #     .stApp p, .stApp span, .stApp div,
# # #     .stApp label, .stMarkdown {
# # #         color: #e2e8f0 !important;
# # #     }

# # #     /* ════ LISA BUBBLE — left, dark card ════ */
# # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
# # #     [data-testid="stChatMessageContent"] {
# # #         background: #161b27 !important;
# # #         border: 1px solid #1e2d47 !important;
# # #         border-radius: 0 16px 16px 16px !important;
# # #         padding: 16px 20px !important;
# # #         max-width: 78% !important;
# # #         margin-right: auto !important;
# # #         box-shadow: 0 0 20px rgba(0, 212, 255, 0.05) !important;
# # #     }

# # #     /* LISA bubble text — bright white, easy to read */
# # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
# # #     [data-testid="stChatMessageContent"] p,
# # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
# # #     [data-testid="stChatMessageContent"] span,
# # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
# # #     [data-testid="stChatMessageContent"] div {
# # #         color: #f0f4ff !important;
# # #         font-size: 15px !important;
# # #         line-height: 1.65 !important;
# # #     }

# # #     /* ════ USER BUBBLE — right, dark navy ════ */
# # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
# # #     [data-testid="stChatMessageContent"] {
# # #         background: #0f1f3d !important;
# # #         border: 1px solid #1e3a6e !important;
# # #         border-radius: 16px 0 16px 16px !important;
# # #         padding: 16px 20px !important;
# # #         max-width: 78% !important;
# # #         margin-left: auto !important;
# # #         box-shadow: 0 0 20px rgba(37, 99, 235, 0.08) !important;
# # #     }

# # #     /* USER bubble text — white */
# # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
# # #     [data-testid="stChatMessageContent"] p,
# # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
# # #     [data-testid="stChatMessageContent"] span,
# # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
# # #     [data-testid="stChatMessageContent"] div {
# # #         color: #dbeafe !important;
# # #         font-size: 15px !important;
# # #     }

# # #     /* ════ AUDIO INPUT inside USER bubble — dark ════ */
# # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
# # #     [data-testid="stAudioInput"] {
# # #         background: #091529 !important;
# # #         border: 1px solid #1e3a6e !important;
# # #         border-radius: 12px !important;
# # #         padding: 6px !important;
# # #     }
# # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
# # #     [data-testid="stAudioInput"] > div {
# # #         background: transparent !important;
# # #     }

# # #     /* ════ CHAT INPUT BAR — ChatGPT style dark ════ */
# # #    [data-testid="stChatInput"] {
# # #     background: linear-gradient(145deg,#111827,#1f2937) !important;
# # #     border: 1px solid #374151 !important;
# # #     border-radius: 16px !important;
# # #     padding: 10px 14px !important;
# # #     box-shadow: 0 6px 25px rgba(0,0,0,0.45) !important;
# # #     transition: all 0.25s ease !important;
# # # }

# # # /* Glow effect when typing */
# # # [data-testid="stChatInput"]:focus-within {
# # #     border: 1px solid #00d4ff !important;
# # #     box-shadow: 0 0 10px rgba(0,212,255,0.4) !important;
# # # }

# # # /* Text area where you type */
# # # [data-testid="stChatInput"] textarea {
# # #     background: transparent !important;
# # #     color: #ffffff !important;
# # #     font-size: 16px !important;
# # #     font-weight: 500 !important;
# # #     caret-color: #00d4ff !important;
# # #     border: none !important;
# # #     outline: none !important;
# # # }

# # #     /* Submit arrow button */
# # #     [data-testid="stChatInput"] button {
# # #         background: #1e3a6e !important;
# # #         border-radius: 8px !important;
# # #         color: #00d4ff !important;
# # #     }
# # #     [data-testid="stChatInput"] button:hover {
# # #         background: #2563eb !important;
# # #     }

# # #     /* ════ HIDE LISA AUDIO PLAYER WIDGET ════ */
# # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
# # #     [data-testid="stAudio"],
# # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
# # #     audio {
# # #         display: none !important;
# # #     }

# # #     /* ════ PROGRESS BAR ════ */
# # #     [data-testid="stProgressBar"] > div > div {
# # #         background: linear-gradient(90deg, #00d4ff, #2563eb) !important;
# # #         border-radius: 4px !important;
# # #     }

# # #     /* ════ METRICS ════ */
# # #     [data-testid="stMetricValue"] { color: #00d4ff !important; font-weight: 700 !important; }
# # #     [data-testid="stMetricLabel"] { color: #6b7280 !important; }

# # #     /* ════ BUTTONS ════ */
# # #     .stButton > button {
# # #         background: #161b27 !important;
# # #         border: 1px solid #1e2d47 !important;
# # #         color: #e2e8f0 !important;
# # #         border-radius: 8px !important;
# # #     }
# # #     .stButton > button:hover {
# # #         border-color: #00d4ff !important;
# # #         color: #00d4ff !important;
# # #     }

# # #     /* ════ SPINNER ════ */
# # #     [data-testid="stSpinner"] div {
# # #         border-top-color: #00d4ff !important;
# # #     }

# # #     /* ════ DIVIDER ════ */
# # #     hr { border-color: #1e2d47 !important; }

# # #     /* ════ CAPTIONS / TIMESTAMPS ════ */
# # #     .stChatMessage .stCaption,
# # #     small, .caption {
# # #         color: #374151 !important;
# # #         font-size: 11px !important;
# # #     }

# # #     /* ════ AVATAR IMAGES ════ */
# # #     [data-testid="chatAvatarIcon-assistant"] img {
# # #         border-radius: 50% !important;
# # #         border: 1px solid #00d4ff33 !important;
# # #     }

# # #     /* ════ SCROLLBAR ════ */
# # #     ::-webkit-scrollbar { width: 5px; }
# # #     ::-webkit-scrollbar-track { background: #0d0f14; }
# # #     ::-webkit-scrollbar-thumb { background: #1e2d47; border-radius: 4px; }
# # #     ::-webkit-scrollbar-thumb:hover { background: #2563eb; }

# # #     </style>
# # #     """, unsafe_allow_html=True)

# # # # import streamlit as st
# # # # from datetime import datetime


# # # # # ─────────────────────────────────────────────
# # # # # LISA SVG AVATAR
# # # # # Professional AI interviewer icon
# # # # # ─────────────────────────────────────────────
# # # # LISA_AVATAR_SVG = """
# # # # data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
# # # #   <circle cx='50' cy='50' r='50' fill='%231a2744'/>
# # # #   <circle cx='50' cy='38' r='18' fill='%234285F4'/>
# # # #   <ellipse cx='50' cy='85' rx='28' ry='20' fill='%234285F4'/>
# # # #   <circle cx='43' cy='35' r='3' fill='white'/>
# # # #   <circle cx='57' cy='35' r='3' fill='white'/>
# # # #   <path d='M 43 45 Q 50 51 57 45' stroke='white' stroke-width='2' fill='none' stroke-linecap='round'/>
# # # # </svg>
# # # # """.strip().replace("\n", "")


# # # # # ─────────────────────────────────────────────
# # # # # STAGE COLORS (no emoji — professional)
# # # # # ─────────────────────────────────────────────
# # # # STAGE_LABELS_CLEAN = {
# # # #     "easy":     "Introductory",
# # # #     "medium":   "Intermediate",
# # # #     "hard":     "Advanced",
# # # #     "adaptive": "Follow-up"
# # # # }

# # # # STAGE_BADGE_COLORS = {
# # # #     "easy":     "#10b981",   # green
# # # #     "medium":   "#f59e0b",   # amber
# # # #     "hard":     "#ef4444",   # red
# # # #     "adaptive": "#6366f1",   # indigo
# # # # }


# # # # # ─────────────────────────────────────────────
# # # # # TIMESTAMP HELPER
# # # # # ─────────────────────────────────────────────
# # # # def now_time() -> str:
# # # #     return datetime.now().strftime("%I:%M %p")


# # # # # ─────────────────────────────────────────────
# # # # # INJECT DARK THEME + CHAT STYLES
# # # # # Call once at top of interview_flow()
# # # # # ─────────────────────────────────────────────
# # # # def inject_interview_styles():
# # # #     st.markdown("""
# # # #     <style>

# # # #     /* ── GLOBAL DARK BACKGROUND ── */
# # # #     .stApp {
# # # #         background-color: #0f1117 !important;
# # # #     }
# # # #     section[data-testid="stSidebar"] {
# # # #         background-color: #1a1d27 !important;
# # # #     }

# # # #     /* ── HIDE DEFAULT STREAMLIT HEADER/FOOTER ── */
# # # #     #MainMenu, footer, header { visibility: hidden; }

# # # #     /* ── CHAT CONTAINER ── */
# # # #     .stChatMessage {
# # # #         background: transparent !important;
# # # #         border: none !important;
# # # #         padding: 4px 0 !important;
# # # #     }

# # # #     /* ── LISA BUBBLE — left aligned, dark grey ── */
# # # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) 
# # # #     .stChatMessageContent {
# # # #         background: #1e2130 !important;
# # # #         border: 1px solid #2d3348 !important;
# # # #         border-radius: 0px 16px 16px 16px !important;
# # # #         color: #e2e8f0 !important;
# # # #         padding: 14px 18px !important;
# # # #         max-width: 75% !important;
# # # #         margin-left: 0 !important;
# # # #         margin-right: auto !important;
# # # #         box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
# # # #     }

# # # #     /* ── USER BUBBLE — right aligned, dark blue ── */
# # # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) 
# # # #     .stChatMessageContent {
# # # #         background: #1a3a6b !important;
# # # #         border: 1px solid #2563eb !important;
# # # #         border-radius: 16px 0px 16px 16px !important;
# # # #         color: #ffffff !important;
# # # #         padding: 14px 18px !important;
# # # #         max-width: 78% !important;
# # # #         margin-left: auto !important;
# # # #         margin-right: 0 !important;
# # # #         box-shadow: 0 2px 8px rgba(29,78,216,0.2) !important;
# # # #     }

# # # #     /* ── USER BUBBLE TEXT — white ── */
# # # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p,
# # # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) span {
# # # #         color: #ffffff !important;
# # # #     }

# # # #     /* ── USER BUBBLE — audio_input dark styled ── */
# # # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
# # # #     [data-testid="stAudioInput"] {
# # # #         background: #0f2a54 !important;
# # # #         border: 1px solid #2563eb !important;
# # # #         border-radius: 10px !important;
# # # #         margin-bottom: 4px !important;
# # # #     }
# # # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
# # # #     [data-testid="stAudioInput"] button {
# # # #         background: #2563eb !important;
# # # #         border-radius: 50% !important;
# # # #     }

# # # #     /* ── HIDE LISA AUDIO PLAYER — voice plays via autoplay ── */
# # # #     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
# # # #     [data-testid="stAudio"] {
# # # #         display: none !important;
# # # #     }

# # # #     /* ── CHAT INPUT BAR — dark ── */
# # # #     .stChatInput {
# # # #         background: #1e2130 !important;
# # # #         border: 1px solid #2d3348 !important;
# # # #         border-radius: 12px !important;
# # # #     }
# # # #     .stChatInput textarea {
# # # #         background: #1e2130 !important;
# # # #         color: #e2e8f0 !important;
# # # #         caret-color: #4285F4 !important;
# # # #     }
# # # #     .stChatInput textarea::placeholder {
# # # #         color: #6b7280 !important;
# # # #     }

# # # #     /* ── PROGRESS BAR ── */
# # # #     .stProgress > div > div {
# # # #         background: #4285F4 !important;
# # # #     }

# # # #     /* ── METRICS ── */
# # # #     [data-testid="stMetricValue"] {
# # # #         color: #e2e8f0 !important;
# # # #     }
# # # #     [data-testid="stMetricLabel"] {
# # # #         color: #9ca3af !important;
# # # #     }

# # # #     /* ── CAPTIONS ── */
# # # #     .stChatMessage .stCaption {
# # # #         color: #6b7280 !important;
# # # #         font-size: 11px !important;
# # # #     }

# # # #     /* ── TYPING INDICATOR ANIMATION ── */
# # # #     .typing-indicator {
# # # #         display: flex;
# # # #         align-items: center;
# # # #         gap: 5px;
# # # #         padding: 10px 14px;
# # # #         background: #1e2130;
# # # #         border: 1px solid #2d3348;
# # # #         border-radius: 0px 16px 16px 16px;
# # # #         width: fit-content;
# # # #         margin: 4px 0;
# # # #     }
# # # #     .typing-dot {
# # # #         width: 8px;
# # # #         height: 8px;
# # # #         background: #4285F4;
# # # #         border-radius: 50%;
# # # #         animation: typing-bounce 1.2s infinite;
# # # #     }
# # # #     .typing-dot:nth-child(2) { animation-delay: 0.2s; }
# # # #     .typing-dot:nth-child(3) { animation-delay: 0.4s; }
# # # #     @keyframes typing-bounce {
# # # #         0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
# # # #         40%            { transform: translateY(-6px); opacity: 1; }
# # # #     }

# # # #     /* ── STAGE BADGE ── */
# # # #     .stage-badge {
# # # #         display: inline-block;
# # # #         font-size: 10px;
# # # #         font-weight: 600;
# # # #         letter-spacing: 1px;
# # # #         text-transform: uppercase;
# # # #         padding: 2px 8px;
# # # #         border-radius: 20px;
# # # #         margin-bottom: 6px;
# # # #     }

# # # #     /* ── TIMESTAMP ── */
# # # #     .msg-timestamp {
# # # #         font-size: 10px;
# # # #         color: #4b5563;
# # # #         margin-top: 4px;
# # # #         display: block;
# # # #     }

# # # #     /* ── LISA NAME LABEL ── */
# # # #     .lisa-label {
# # # #         font-size: 11px;
# # # #         font-weight: 600;
# # # #         color: #4285F4;
# # # #         letter-spacing: 0.5px;
# # # #         margin-bottom: 4px;
# # # #         display: block;
# # # #     }

# # # #     /* ── USER LABEL ── */
# # # #     .user-label {
# # # #         font-size: 11px;
# # # #         font-weight: 600;
# # # #         color: #93c5fd;
# # # #         letter-spacing: 0.5px;
# # # #         margin-bottom: 4px;
# # # #         display: block;
# # # #         text-align: right;
# # # #     }

# # # #     /* ── ADAPTIVE BANNER ── */
# # # #     .adaptive-banner {
# # # #         background: #1e1b4b;
# # # #         border-left: 3px solid #6366f1;
# # # #         border-radius: 0 8px 8px 0;
# # # #         padding: 8px 14px;
# # # #         font-size: 13px;
# # # #         color: #a5b4fc;
# # # #         margin: 8px 0;
# # # #     }

# # # #     /* ── AUDIO INPUT — dark styled, full width ── */
# # # #     [data-testid="stAudioInput"] {
# # # #         background: #1e2130 !important;
# # # #         border: 1px solid #2d3348 !important;
# # # #         border-radius: 12px !important;
# # # #         padding: 8px !important;
# # # #         margin-bottom: 6px !important;
# # # #     }
# # # #     [data-testid="stAudioInput"] button {
# # # #         background: #4285F4 !important;
# # # #         border-radius: 50% !important;
# # # #     }

# # # #     /* ── SPINNER ── */
# # # #     .stSpinner > div {
# # # #         border-top-color: #4285F4 !important;
# # # #     }

# # # #     /* ── SCROLLBAR ── */
# # # #     ::-webkit-scrollbar { width: 6px; }
# # # #     ::-webkit-scrollbar-track { background: #0f1117; }
# # # #     ::-webkit-scrollbar-thumb { background: #2d3348; border-radius: 3px; }

# # # #     </style>
# # # #     """, unsafe_allow_html=True)


# # # # # ─────────────────────────────────────────────
# # # # # TYPING INDICATOR HTML
# # # # # ─────────────────────────────────────────────
# # # # def show_typing_indicator():
# # # #     st.markdown("""
# # # #     <div style="display:flex; align-items:center; gap:8px; margin: 6px 0;">
# # # #         <span class="lisa-label">LISA is typing</span>
# # # #         <div class="typing-indicator">
# # # #             <div class="typing-dot"></div>
# # # #             <div class="typing-dot"></div>
# # # #             <div class="typing-dot"></div>
# # # #         </div>
# # # #     </div>
# # # #     """, unsafe_allow_html=True)


# # # # # ─────────────────────────────────────────────
# # # # # STAGE BADGE HTML
# # # # # ─────────────────────────────────────────────
# # # # def stage_badge(level: str) -> str:
# # # #     label = STAGE_LABELS_CLEAN.get(level, level.title())
# # # #     color = STAGE_BADGE_COLORS.get(level, "#6b7280")
# # # #     return (
# # # #         f'<span class="stage-badge" '
# # # #         f'style="background:{color}22; color:{color}; border:1px solid {color}55;">'
# # # #         f'{label}</span>'
# # # #     )


# # # # # ─────────────────────────────────────────────
# # # # # STRIP EMOJIS FROM LISA QUESTIONS
# # # # # Keeps text professional
# # # # # ─────────────────────────────────────────────
# # # # def strip_emojis(text: str) -> str:
# # # #     import re
# # # #     emoji_pattern = re.compile(
# # # #         "["
# # # #         u"\U0001F600-\U0001F64F"
# # # #         u"\U0001F300-\U0001F5FF"
# # # #         u"\U0001F680-\U0001F9FF"
# # # #         u"\U00002600-\U000027BF"
# # # #         u"\U0001FA00-\U0001FA9F"
# # # #         "]+",
# # # #         flags=re.UNICODE
# # # #     )
# # # #     return emoji_pattern.sub("", text).strip()