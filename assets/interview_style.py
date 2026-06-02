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
                   <div class="avatar-circle-main">
                       <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
                   </div>
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
           <span><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg> Voice active</span>
           <span><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg> Resume loaded</span>
           <span><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg> Score tracked</span>
        </div>
        """, unsafe_allow_html=True)

def inject_interview_styles(is_dark: bool = True):
    if is_dark:
        theme_css = """
        :root {
          --page-bg: #1e1e24;
          --header-bg: #1e1e24;
          --chat-bg: #1e1e24;
          --ai-bubble-bg: #162420;
          --ai-bubble-border: #0F6E56;
          --ai-bubble-text: #e2e8f0;
          --user-bubble-bg: #272838;
          --user-bubble-border: #3f3f5a;
          --user-bubble-text: #e2e8f0;
          --input-bg: #1e1e24;
          --input-border: #3f3f5a;
          --btn-skip-border: #3f3f5a;
          --btn-skip-text: #a0aec0;
          --btn-end-bg: transparent;
          --btn-end-text: #e53e3e;
          --btn-end-border: #e53e3e;
          --prog-track: #2d3748;
          --prog-fill: #38b2ac;
          --ai-avatar-bg: #0F6E56;
          --ai-avatar-border: transparent;
          --ai-avatar-icon: #9FE1CB;
          --user-avatar-bg: #272838;
          --user-avatar-border: #3f3f5a;
          --user-avatar-icon: #a0aec0;
          --diff-bg: #4c3a10;
          --diff-text: #f6e05e;
          --timer-bg: transparent;
          --timer-border: #f6e05e;
          --timer-text: #f6e05e;
          --btn-send-bg: #38b2ac;
          --btn-send-text: #ffffff;
          --btn-skip-bg: transparent;
          --header-text-muted: #a0aec0;
          --header-text-main: #ffffff;
          --border-color: #2d3748;
        }
        """
    else:
        theme_css = """
        :root {
          --page-bg: #f8fafc;
          --header-bg: #f8fafc;
          --chat-bg: #f8fafc;
          --ai-bubble-bg: #ffffff;
          --ai-bubble-border: #b2f5ea;
          --ai-bubble-text: #1a202c;
          --user-bubble-bg: #ebf4ff;
          --user-bubble-border: #c3dafe;
          --user-bubble-text: #2b6cb0;
          --input-bg: #f8fafc;
          --input-border: #e2e8f0;
          --btn-skip-border: #e2e8f0;
          --btn-skip-text: #718096;
          --btn-end-bg: #fff5f5;
          --btn-end-text: #e53e3e;
          --btn-end-border: #feb2b2;
          --prog-track: #e2e8f0;
          --prog-fill: #38b2ac;
          --ai-avatar-bg: #38b2ac;
          --ai-avatar-border: transparent;
          --ai-avatar-icon: #ffffff;
          --user-avatar-bg: #ebf4ff;
          --user-avatar-border: #c3dafe;
          --user-avatar-icon: #2b6cb0;
          --diff-bg: #fefcbf;
          --diff-text: #744210;
          --timer-bg: #fffff0;
          --timer-border: #f6e05e;
          --timer-text: #b7791f;
          --btn-send-bg: #38b2ac;
          --btn-send-text: #ffffff;
          --btn-skip-bg: transparent;
          --header-text-muted: #718096;
          --header-text-main: #1a202c;
          --border-color: #e2e8f0;
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

    /* Target the container wrapping the header */
    [data-testid="stVerticalBlock"]:has(.custom-header-target) {
        background-color: var(--header-bg) !important;
        border-radius: 12px;
        border: 1px solid var(--border-color);
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
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 12px;
    }
    
    .header-profile { display: flex; align-items: center; gap: 16px; margin-top: 0; margin-bottom: 0;}
    .avatar-circle-main {
        width: 48px; height: 48px; border-radius: 50%;
        background-color: var(--ai-avatar-bg); color: var(--ai-avatar-icon);
        display: flex; align-items: center; justify-content: center;
        border: 2px solid var(--header-bg); outline: 2px solid var(--ai-avatar-bg);
    }
    .profile-info .job-title { font-size: 20px; font-weight: 600; color: var(--header-text-main); margin-bottom: 4px; }
    .profile-info .sub-info { font-size: 13px; color: var(--header-text-muted); display: flex; gap: 12px; align-items: center; }
    
    .badge-amber { background: var(--diff-bg); color: var(--diff-text); padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
    .badge-green { background: transparent; color: #1D9E75; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; border: 1px solid #1D9E75; }
    
    .header-timer { text-align: left; margin-top: 0; }
    .timer-label { font-size: 11px; font-weight: 600; color: var(--header-text-muted); letter-spacing: 1px; margin-bottom: 4px; text-transform: uppercase; }
    .timer-value { font-size: 28px; font-weight: 600; color: var(--timer-text); font-family: monospace; letter-spacing: 2px; line-height: 1; }
    
    .candidate-info { border-left: 1px solid var(--border-color); padding-left: 20px; text-align: left; }
    .candidate-name { font-size: 16px; font-weight: 600; color: var(--header-text-main); }
    .candidate-role { font-size: 13px; color: var(--header-text-muted); }
    
    .header-progress-row { margin-top: 24px; border-top: none; padding-top: 0; padding-bottom: 0; }
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
        margin-top: 20px; padding-top: 12px; border-top: 1px solid var(--border-color);
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
    [data-testid="stChatMessageAvatarAssistant"] {
        background: var(--ai-avatar-bg) !important;
        border: 1px solid var(--ai-avatar-border) !important;
        border-radius: 50% !important;
        width: 36px !important;
        height: 36px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    [data-testid="stChatMessageAvatarAssistant"] svg {
        fill: var(--ai-avatar-icon) !important;
        color: var(--ai-avatar-icon) !important;
    }
    [data-testid="stChatMessageAvatarUser"] {
        background: var(--user-avatar-bg) !important;
        border: 1px solid var(--user-avatar-border) !important;
        border-radius: 50% !important;
        width: 36px !important;
        height: 36px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    [data-testid="stChatMessageAvatarUser"] svg {
        fill: var(--user-avatar-icon) !important;
        color: var(--user-avatar-icon) !important;
    }

    /* INPUT BOX AND CHAT CONTAINER AREA */
    [data-testid="stVerticalBlock"]:has(.fixed-bottom-input) {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        margin: 0 auto !important;
        width: 100% !important;
        max-width: 46rem !important; /* Match Streamlit's default center column width closely */
        background-color: var(--page-bg) !important;
        z-index: 9999 !important;
        padding: 10px 0px 20px 0px !important;
    }
    
    /* Ensure the main chat window doesn't hide behind the fixed bottom bar */
    .main .block-container {
        padding-bottom: 120px !important;
    }
    
    /* Make st.audio_input smaller and sleeker */
    [data-testid="stAudioInput"] {
        margin-top: 5px;
        transform: scale(0.9);
        transform-origin: left center;
    }

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
