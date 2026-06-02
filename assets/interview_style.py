import streamlit as st
from datetime import datetime

LISA_AVATAR_PATH = "assets/lisa_avatar.png"

def now_time() -> str:
    return datetime.now().strftime("%I:%M %p")

def strip_emojis(text: str) -> str:
    import re
    pattern = re.compile(
        "[" u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F9FF" u"\U00002600-\U000027BF"
        u"\U0001FA00-\U0001FA9F" "]+", flags=re.UNICODE
    )
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    return pattern.sub("", text).strip()

def show_typing_indicator():
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;padding:6px 0;">
        <span style="font-size:11px;color:var(--btn-send-bg);font-weight:700;
                     letter-spacing:0.5px;">LISA is thinking</span>
        <div style="display:flex;gap:5px;align-items:center;">
            <span style="width:7px;height:7px;background:var(--btn-send-bg);border-radius:50%;
                display:inline-block;animation:tb 1.2s infinite 0s;"></span>
            <span style="width:7px;height:7px;background:var(--btn-send-bg);border-radius:50%;
                display:inline-block;animation:tb 1.2s infinite 0.2s;"></span>
            <span style="width:7px;height:7px;background:var(--btn-send-bg);border-radius:50%;
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

def render_interview_header(title: str, q_num: int, total_q: int,
                            level: str, timer_str: str, remaining: int, user_name: str):
    
    progress_pct = (q_num / total_q) * 100
    
    # Segmented dots
    dots_html = ""
    for i in range(1, total_q + 1):
        if i <= q_num:
            dots_html += '<div class="seg active"></div>'
        else:
            dots_html += '<div class="seg"></div>'
            
    with st.container():
        st.markdown('<div class="custom-header-target"></div>', unsafe_allow_html=True)
        
        # STATUS ROW
        st.markdown("""
        <div class="header-status-row">
           <span class="active-status"><span class="pulse-dot green"></span> INTERVIEW SESSION ACTIVE</span>
           <span class="recording-status"><span class="pulse-dot red"></span> Session recording</span>
        </div>
        """, unsafe_allow_html=True)
        
        # MAIN ROW
        c1, c2, c3, c4 = st.columns([4, 1.5, 1.5, 1.5])
        with c1:
            st.markdown(f"""
               <div class="header-profile">
                   <div class="avatar-circle-main">💼</div>
                   <div class="profile-info">
                       <div class="job-title">{title}</div>
                       <div class="sub-info">
                           <span>AI Interviewer — LISA</span>
                           <span class="badge-amber">{level.title()}</span>
                           <span class="badge-green"><span class="pulse-dot green" style="width:6px;height:6px;"></span> Live</span>
                       </div>
                   </div>
               </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
               <div class="header-timer">
                   <div class="timer-label">TIME LEFT</div>
                   <div class="timer-value" id="countdown_timer">{timer_str}</div>
               </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
               <div class="candidate-info">
                   <div class="candidate-name">{user_name}</div>
                   <div class="candidate-role">Candidate</div>
               </div>
            """, unsafe_allow_html=True)
        with c4:
            st.button("End interview", key="end_btn_header", use_container_width=True)
            
        # JS for Timer
        st.markdown(f"""
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
                    
                    if (timeLeft < 60) {{
                        timerSpan.style.color = "#E24B4A";
                    }} else if (timeLeft < 120) {{
                        timerSpan.style.color = "#EF9F27";
                    }} else {{
                        timerSpan.style.color = "var(--timer-text)";
                    }}
                }}
            }}, 1000);
        </script>
        """, unsafe_allow_html=True)
            
        # PROGRESS ROW
        st.markdown(f"""
        <div class="header-progress-row">
           <div class="progress-labels-row">
               <span class="progress-title">Question progress</span>
               <div class="progress-dots">
                   {dots_html}
               </div>
           </div>
           <div class="progress-bar-container">
               <span class="q-label">Q {q_num} of {total_q}</span>
               <div class="progress-track-long">
                   <div class="progress-fill-long" style="width:{progress_pct}%"></div>
               </div>
               <span class="pct-label">{int(progress_pct)}%</span>
           </div>
        </div>
        """, unsafe_allow_html=True)
        
        # FOOTER ROW
        st.markdown("""
        <div class="header-footer-row">
           <span>🎤 Voice active</span>
           <span>📄 Resume loaded</span>
           <span>📊 Score tracked</span>
        </div>
        """, unsafe_allow_html=True)

def inject_interview_styles(is_dark: bool = True):
    if is_dark:
        theme_css = """
        :root {
          --page-bg: #0f1117;
          --header-bg: #161922;
          --chat-bg: #0f1117;
          --ai-bubble-bg: #161f1c;
          --ai-bubble-border: #0F6E56;
          --ai-bubble-text: #c8ede4;
          --user-bubble-bg: #1a1d2e;
          --user-bubble-border: #2a2d3a;
          --user-bubble-text: #b8bdd4;
          --input-bg: #1e2130;
          --input-border: #2a2d3a;
          --btn-skip-border: #2a2d3a;
          --btn-skip-text: #8b8fa8;
          --btn-end-bg: #1a1d2e;
          --btn-end-text: #2a2d3a;
          --btn-end-border: #2a2d3a;
          --prog-track: #1e2130;
          --prog-fill: #1D9E75;
          --ai-avatar-bg: #0F6E56;
          --ai-avatar-border: transparent;
          --ai-avatar-icon: #9FE1CB;
          --user-avatar-bg: #1e2130;
          --user-avatar-border: #2a2d3a;
          --user-avatar-icon: #8b8fa8;
          --diff-bg: #2a1f0e;
          --diff-text: #EF9F27;
          --timer-bg: transparent;
          --timer-border: transparent;
          --timer-text: #00ff9d;
          --btn-send-bg: #1D9E75;
          --btn-send-text: #ffffff;
          --btn-skip-bg: transparent;
          --header-text-muted: #8b8fa8;
          --header-text-main: #ffffff;
        }
        """
    else:
        theme_css = """
        :root {
          --page-bg: #f4f6fa;
          --header-bg: #ffffff;
          --chat-bg: #f4f6fa;
          --ai-bubble-bg: #ffffff;
          --ai-bubble-border: #c0e8d8;
          --ai-bubble-text: #2d3550;
          --user-bubble-bg: #EEEDFE;
          --user-bubble-border: #AFA9EC;
          --user-bubble-text: #3C3489;
          --input-bg: #f4f6fa;
          --input-border: #dde1ec;
          --btn-skip-border: #dde1ec;
          --btn-skip-text: #8b8fa8;
          --btn-end-bg: #f4f6fa;
          --btn-end-text: #dde1ec;
          --btn-end-border: #dde1ec;
          --prog-track: #e8ecf5;
          --prog-fill: #1D9E75;
          --ai-avatar-bg: #E1F5EE;
          --ai-avatar-border: #9FE1CB;
          --ai-avatar-icon: #0F6E56;
          --user-avatar-bg: #eef0f8;
          --user-avatar-border: #dde1ec;
          --user-avatar-icon: #534AB7;
          --diff-bg: #fef3e2;
          --diff-text: #854F0B;
          --timer-bg: transparent;
          --timer-border: transparent;
          --timer-text: #1D9E75;
          --btn-send-bg: #1D9E75;
          --btn-send-text: #ffffff;
          --btn-skip-bg: transparent;
          --header-text-muted: #64748b;
          --header-text-main: #0f172a;
        }
        """

    st.markdown("""
    <style>
    /* CSS VARIABLES FOR LIGHT AND DARK MODE */
    """ + theme_css + """

    /* GLOBAL BACKGROUNDS */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], section.main {
        background-color: var(--page-bg) !important;
    }
    .stHeader, header { display: none !important; }

    /* HIDE DEFAULT PROGRESS & METRICS */
    [data-testid="stProgressBar"] { display: none !important; }
    [data-testid="stMetric"] { display: none !important; }

    /* ==================================================
       HEADER STYLING (Image 3 exact replica)
       ================================================== */
    /* Target the container wrapping the header */
    [data-testid="stVerticalBlock"]:has(.custom-header-target) {
        background-color: var(--header-bg) !important;
        border-radius: 12px;
        border: 1px solid var(--input-border);
        padding: 20px 24px !important;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    /* Remove streamlit's default vertical gaps inside the header container */
    [data-testid="stVerticalBlock"]:has(.custom-header-target) > div > div {
        gap: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    [data-testid="stVerticalBlock"]:has(.custom-header-target) p {
        margin-bottom: 0 !important;
    }
    
    .pulse-dot {
        display: inline-block;
        width: 8px; height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }
    .pulse-dot.green { background-color: #1D9E75; box-shadow: 0 0 6px #1D9E75; }
    .pulse-dot.red { background-color: #E24B4A; box-shadow: 0 0 6px #E24B4A; }
    
    .header-status-row {
        display: flex; justify-content: space-between;
        font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;
        color: var(--header-text-muted);
        margin-bottom: 24px;
        border-bottom: 1px solid var(--input-border);
        padding-bottom: 12px;
    }
    
    .header-profile { display: flex; align-items: center; gap: 16px; }
    .avatar-circle-main {
        width: 48px; height: 48px; border-radius: 50%;
        background-color: var(--btn-send-bg); color: white;
        display: flex; align-items: center; justify-content: center; font-size: 24px;
        border: 2px solid var(--header-bg); outline: 2px solid var(--btn-send-bg);
    }
    .profile-info .job-title { font-size: 20px; font-weight: 600; color: var(--header-text-main); margin-bottom: 4px; }
    .profile-info .sub-info { font-size: 13px; color: var(--header-text-muted); display: flex; gap: 12px; align-items: center; }
    
    .badge-amber { background: var(--diff-bg); color: var(--diff-text); padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
    .badge-green { background: transparent; color: #1D9E75; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; border: 1px solid #1D9E75; }
    
    .header-timer { text-align: left; }
    .timer-label { font-size: 11px; font-weight: 600; color: var(--header-text-muted); letter-spacing: 1px; margin-bottom: 4px; }
    .timer-value { font-size: 28px; font-weight: 600; color: var(--timer-text); font-family: monospace; letter-spacing: 2px; line-height: 1; }
    
    .candidate-info { border-left: 1px solid var(--input-border); padding-left: 20px; text-align: left; }
    .candidate-name { font-size: 16px; font-weight: 600; color: var(--header-text-main); }
    .candidate-role { font-size: 13px; color: var(--header-text-muted); }
    
    .header-progress-row { margin-top: 24px; }
    .progress-labels-row { display: flex; justify-content: space-between; margin-bottom: 8px; align-items: center; }
    .progress-title { font-size: 13px; color: var(--header-text-muted); }
    .progress-dots { display: flex; gap: 6px; }
    .progress-dots .seg { width: 32px; height: 4px; background: var(--prog-track); border-radius: 4px; }
    .progress-dots .seg.active { background: var(--prog-fill); }
    
    .progress-bar-container { display: flex; align-items: center; gap: 16px; }
    .q-label { font-size: 13px; color: var(--header-text-muted); white-space: nowrap; }
    .progress-track-long { flex-grow: 1; height: 4px; background: var(--prog-track); border-radius: 4px; overflow: hidden; }
    .progress-fill-long { height: 100%; background: var(--prog-fill); transition: width 0.3s ease; }
    .pct-label { font-size: 13px; font-weight: 600; color: var(--prog-fill); white-space: nowrap; }
    
    .header-footer-row {
        display: flex; gap: 24px; font-size: 12px; color: var(--header-text-muted);
        margin-top: 20px; padding-top: 12px; border-top: 1px solid var(--input-border);
    }

    /* BUTTONS */
    .stButton > button {
        background: var(--btn-skip-bg) !important;
        border: 1px solid var(--btn-skip-border) !important;
        color: var(--btn-skip-text) !important;
        border-radius: 10px !important;
        transition: all 0.2s !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--btn-send-bg) !important;
        border: none !important;
        color: var(--btn-send-text) !important;
        border-radius: 10px !important;
    }
    
    /* End Interview Button styling matching the image (dark/faded) */
    button:contains("End") {
        background: var(--btn-end-bg) !important;
        border: 1px solid var(--btn-end-border) !important;
        color: var(--btn-end-text) !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-weight: 500 !important;
        height: auto !important;
    }

    /* ==================================================
       CHAT MESSAGE RENDERING FIXES
       ================================================== */
       
    /* Remove any default Streamlit chat backgrounds */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
    }
       
    /* 1. AI MESSAGE BUBBLE (Left Aligned) */
    [data-testid="stChatMessage"]:has(.chat-role-assistant) [data-testid="stChatMessageContent"] {
        background: var(--ai-bubble-bg) !important;
        border: 0.5px solid var(--ai-bubble-border) !important;
        border-radius: 0 12px 12px 12px !important;
        padding: 16px 20px !important;
        max-width: 85% !important;
        margin-right: auto !important;
        margin-left: 0 !important;
        color: var(--ai-bubble-text) !important;
        box-shadow: none !important;
    }
    [data-testid="stChatMessage"]:has(.chat-role-assistant) p {
        color: var(--ai-bubble-text) !important;
    }
    
    /* HIGHLIGHT PROJECT NAMES (strong tags in assistant chat) */
    [data-testid="stChatMessage"]:has(.chat-role-assistant) p strong {
        color: var(--btn-send-bg) !important;
        font-weight: 600 !important;
    }

    /* 2. USER MESSAGE BUBBLE (Right Aligned) */
    [data-testid="stChatMessage"]:has(.chat-role-user) {
        flex-direction: row-reverse !important;
    }
    [data-testid="stChatMessage"]:has(.chat-role-user) [data-testid="stChatMessageContent"] {
        background: var(--user-bubble-bg) !important;
        border: 0.5px solid var(--user-bubble-border) !important;
        border-radius: 12px 0 12px 12px !important;
        padding: 16px 20px !important;
        max-width: 85% !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        color: var(--user-bubble-text) !important;
        text-align: left;
        box-shadow: none !important;
    }
    [data-testid="stChatMessage"]:has(.chat-role-user) p {
        color: var(--user-bubble-text) !important;
    }

    /* AVATARS */
    [data-testid="stChatMessageAvatarCustom"] {
        background: transparent !important;
    }
    [data-testid="stChatMessage"]:has(.chat-role-assistant) [data-testid="stChatMessageAvatarCustom"] {
        background: var(--ai-avatar-bg) !important;
        border: 1px solid var(--ai-avatar-border) !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
    }
    [data-testid="stChatMessage"]:has(.chat-role-user) [data-testid="stChatMessageAvatarCustom"] {
        background: var(--user-avatar-bg) !important;
        border: 1px solid var(--user-avatar-border) !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
    }

    /* INPUT BOX AND CHAT CONTAINER AREA */
    [data-testid="stChatInputContainer"], [data-testid="stBottomBlockContainer"] {
        background-color: var(--page-bg) !important;
        border: none !important;
        box-shadow: none !important;
    }
    [data-testid="stChatInput"] {
        background-color: var(--input-bg) !important;
        border: 0.5px solid var(--input-border) !important;
        border-radius: 12px !important;
    }
    [data-testid="stChatInput"] textarea {
        background-color: var(--input-bg) !important;
        color: var(--ai-bubble-text) !important;
    }
    
    /* SCROLLBARS */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #2d3548; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)
