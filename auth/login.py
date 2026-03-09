import base64
import os
import streamlit as st
from auth.auth import register_user, login_user


def logout_user():
    st.session_state.clear()
    st.rerun()


def _set_session(user: dict):
    st.session_state["logged_in"]  = True
    st.session_state["user_name"]  = user["name"]
    st.session_state["user_email"] = user["email"]


def _get_lisa_b64() -> str:
    for p in ["assets/lisa_avatar.png", "lisa_avatar.png"]:
        if os.path.exists(p):
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return ""


def login_page():

    st.markdown("""
    <style>
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stBottomBlockContainer"],
    section.main { background-color: #0a0c12 !important; }
    header, #MainMenu, footer { visibility: hidden !important; }
    .block-container { padding-top: 0 !important; }

    .stApp p, .stApp span, .stApp div,
    .stApp label, .stMarkdown { color: #cbd5e1 !important; }

    /* tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 2px solid #1e293b !important;
        padding: 0 !important; gap: 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #475569 !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        padding: 12px 36px !important;
        border-bottom: 3px solid transparent !important;
        border-radius: 0 !important;
        margin-bottom: -2px !important;
    }
    .stTabs [aria-selected="true"] {
        color: #00d4ff !important;
        border-bottom: 3px solid #00d4ff !important;
        background: transparent !important;
    }

    /* inputs — unified border, no overlap */
    .stTextInput > div {
        border: none !important;
        box-shadow: none !important;
    }
    .stTextInput > div > div {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }
    .stTextInput > div > div > input {
        background: #0f172a !important;
        border: 1.5px solid #1e293b !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
        font-size: 14px !important;
        padding: 12px 16px !important;
        height: 46px !important;
        transition: border-color 0.2s !important;
        outline: none !important;
        box-shadow: none !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #00d4ff !important;
        box-shadow: 0 0 0 3px rgba(0,212,255,0.1) !important;
        outline: none !important;
    }
    .stTextInput > div > div > input::placeholder { color: #334155 !important; }
    .stTextInput label {
        color: #64748b !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
    }

    /* password eye button — remove all borders, match input */
    .stTextInput > div > div > div[data-testid="InputInstructions"],
    .stTextInput > div > div > button,
    .stTextInput button {
        background: #0f172a !important;
        border: none !important;
        border-left: none !important;
        border-radius: 0 10px 10px 0 !important;
        color: #475569 !important;
        box-shadow: none !important;
        outline: none !important;
    }
    .stTextInput button:hover {
        color: #00d4ff !important;
        background: #0f172a !important;
        border: none !important;
        box-shadow: none !important;
    }
    /* remove the inner wrapper border that causes overlap */
    .stTextInput [data-baseweb="input"] {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }

    /* primary button */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg,#1d4ed8,#2563eb) !important;
        border: none !important;
        color: #fff !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        height: 50px !important;
        width: 100% !important;
        letter-spacing: 0.3px !important;
        transition: all 0.25s !important;
        box-shadow: 0 4px 20px rgba(29,78,216,0.3) !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg,#2563eb,#00d4ff) !important;
        box-shadow: 0 6px 28px rgba(37,99,235,0.5) !important;
        transform: translateY(-1px) !important;
    }

    [data-testid="stAlert"] { border-radius: 10px !important; }

    /* LISA ring — medium size */
    .lisa-ring {
        width: 120px; height: 120px;
        border-radius: 50%;
        padding: 3px;
        background: linear-gradient(135deg, #00d4ff, #2563eb);
        margin: 0 auto 10px auto;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 0 40px rgba(0,212,255,0.25);
    }
    .lisa-ring img {
        width: 114px; height: 114px;
        border-radius: 50%;
        object-fit: cover;
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    left, gap, right = st.columns([1.1, 0.15, 1.1])

    # ── LEFT — LISA hero ─────────────────────────────────────────
    with left:
        st.markdown("<br><br>", unsafe_allow_html=True)

        lisa_b64 = _get_lisa_b64()
        if lisa_b64:
            st.markdown(f"""
            <div class="lisa-ring">
                <img src="data:image/png;base64,{lisa_b64}" alt="LISA"/>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="font-size:80px;text-align:center;
                        line-height:1;margin-bottom:10px;">🤖</div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align:center; margin-bottom:28px;">
            <div style="font-size:30px;font-weight:900;
                        color:#f0f4ff;letter-spacing:-1px;line-height:1.2;">
                Think you're ready?
            </div>
            <div style="font-size:17px;font-weight:700;
                        color:#00d4ff;margin-top:6px;line-height:1.3;">
                LISA will find out.
            </div>
            <div style="font-size:13px;color:#334155;
                        margin-top:10px;line-height:1.6;
                        max-width:300px;margin-left:auto;margin-right:auto;">
                Upload your resume and face real interview questions
                tailored to your skills. No shortcuts. No hints.
                Just you and LISA.
            </div>
        </div>

        <div style="display:flex;flex-direction:column;gap:16px;padding:0 8px;">
            <div style="border-left:3px solid #00d4ff;padding-left:14px;">
                <div style="color:#f0f4ff;font-weight:700;font-size:14px;">
                    Reads Your Resume
                </div>
                <div style="color:#334155;font-size:12px;margin-top:3px;line-height:1.5;">
                    Every question is based on your actual skills and projects
                </div>
            </div>
            <div style="border-left:3px solid #2563eb;padding-left:14px;">
                <div style="color:#f0f4ff;font-weight:700;font-size:14px;">
                    Voice or Text — Your Choice
                </div>
                <div style="color:#334155;font-size:12px;margin-top:3px;line-height:1.5;">
                    Speak or type. Whisper AI transcribes your answers live
                </div>
            </div>
            <div style="border-left:3px solid #7c3aed;padding-left:14px;">
                <div style="color:#f0f4ff;font-weight:700;font-size:14px;">
                    Adaptive Difficulty
                </div>
                <div style="color:#334155;font-size:12px;margin-top:3px;line-height:1.5;">
                    Questions get harder or easier based on your answers
                </div>
            </div>
            <div style="border-left:3px solid #059669;padding-left:14px;">
                <div style="color:#f0f4ff;font-weight:700;font-size:14px;">
                    Detailed PDF Report
                </div>
                <div style="color:#334155;font-size:12px;margin-top:3px;line-height:1.5;">
                    Scores, feedback and a study plan delivered after every session
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # gap divider
    with gap:
        st.markdown("""
        <div style="height:70vh;width:1px;
            background:linear-gradient(to bottom,transparent,#1e293b,transparent);
            margin:60px auto 0 auto;">
        </div>
        """, unsafe_allow_html=True)

    # ── RIGHT — form ─────────────────────────────────────────────
    with right:
        st.markdown("<br><br>", unsafe_allow_html=True)

        st.markdown("""
        <div style="margin-bottom:28px;">
            <div style="font-size:26px;font-weight:800;
                        color:#f0f4ff;letter-spacing:-0.5px;">
                Welcome to <span style="color:#00d4ff;">Pyspace</span>
            </div>
            <div style="font-size:13px;color:#334155;margin-top:6px;">
                Sign in or create your account to begin
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["Login", "Register"])

        # ── LOGIN ─────────────────────────────────────────────────
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            l_email = st.text_input(
                "Email", placeholder="you@example.com", key="l_email"
            )
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            l_pass = st.text_input(
                "Password", type="password",
                placeholder="Your password", key="l_pass"
            )
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Login to Pyspace", type="primary",
                         use_container_width=True, key="do_login"):
                e = l_email.strip().lower()
                p = l_pass.strip()
                if not e or not p:
                    st.error("Please fill in both fields.")
                else:
                    with st.spinner("Verifying..."):
                        user = login_user(e, p)
                    if user:
                        _set_session(user)
                        st.rerun()
                    else:
                        st.error("Wrong email or password.")

            st.markdown("""
            <p style="text-align:center;font-size:12px;
                      color:#334155;margin-top:16px;">
                No account yet?
                <b style="color:#00d4ff;">Click Register above</b>
            </p>
            """, unsafe_allow_html=True)

        # ── REGISTER ──────────────────────────────────────────────
        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)
            r_name = st.text_input(
                "Full Name", placeholder="Your full name", key="r_name"
            )
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            r_email = st.text_input(
                "Email", placeholder="you@example.com", key="r_email"
            )
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            r_pass = st.text_input(
                "Password", type="password",
                placeholder="Minimum 6 characters", key="r_pass"
            )
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            r_pass2 = st.text_input(
                "Confirm Password", type="password",
                placeholder="Repeat your password", key="r_pass2"
            )
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Create Account", type="primary",
                         use_container_width=True, key="do_register"):
                name  = r_name.strip()
                email = r_email.strip().lower()
                pw, pw2 = r_pass, r_pass2

                if not name:
                    st.error("Please enter your full name.")
                elif not email or "@" not in email:
                    st.error("Please enter a valid email.")
                elif len(pw) < 6:
                    st.error("Password must be at least 6 characters.")
                elif pw != pw2:
                    st.error("Passwords do not match.")
                else:
                    with st.spinner("Creating your account..."):
                        ok, msg = register_user(name, email, pw)
                    if ok:
                        with st.spinner("Logging you in..."):
                            user = login_user(email, pw)
                        if user:
                            _set_session(user)
                            st.rerun()
                        else:
                            st.success("Account created! Please login.")
                    elif msg == "email_exists":
                        st.error("Email already registered. Please login.")
                    else:
                        st.error(f"Registration failed: {msg}")

            st.markdown("""
            <p style="text-align:center;font-size:12px;
                      color:#334155;margin-top:16px;">
                Already registered?
                <b style="color:#00d4ff;">Click Login above</b>
            </p>
            """, unsafe_allow_html=True)


def handle_auth() -> bool:
    if st.session_state.get("logged_in"):
        return True
    login_page()
    return False

# import base64
# import os
# import streamlit as st
# from auth.auth import register_user, login_user


# def logout_user():
#     st.session_state.clear()
#     st.rerun()


# def _set_session(user: dict):
#     st.session_state["logged_in"]  = True
#     st.session_state["user_name"]  = user["name"]
#     st.session_state["user_email"] = user["email"]


# def _get_lisa_b64() -> str:
#     """Load LISA avatar as base64 for inline HTML display."""
#     paths = [
#         "assets/lisa_avatar.png",
#         "lisa_avatar.png",
#     ]
#     for p in paths:
#         if os.path.exists(p):
#             with open(p, "rb") as f:
#                 return base64.b64encode(f.read()).decode()
#     return ""


# def login_page():

#     st.markdown("""
#     <style>
#     /* ── full dark background ── */
#     .stApp,
#     [data-testid="stAppViewContainer"],
#     [data-testid="stMain"],
#     [data-testid="stBottomBlockContainer"],
#     section.main { background-color: #0a0c12 !important; }
#     header, #MainMenu, footer { visibility: hidden !important; }
#     .block-container { padding-top: 0 !important; }

#     /* ── all text ── */
#     .stApp p, .stApp span, .stApp div,
#     .stApp label, .stMarkdown { color: #cbd5e1 !important; }

#     /* ── tabs ── */
#     .stTabs [data-baseweb="tab-list"] {
#         background: transparent !important;
#         border-bottom: 2px solid #1e293b !important;
#         padding: 0 !important; gap: 0 !important;
#     }
#     .stTabs [data-baseweb="tab"] {
#         background: transparent !important;
#         color: #475569 !important;
#         font-size: 15px !important;
#         font-weight: 700 !important;
#         padding: 12px 36px !important;
#         border-bottom: 3px solid transparent !important;
#         border-radius: 0 !important;
#         margin-bottom: -2px !important;
#         letter-spacing: 0.3px !important;
#     }
#     .stTabs [aria-selected="true"] {
#         color: #00d4ff !important;
#         border-bottom: 3px solid #00d4ff !important;
#         background: transparent !important;
#     }

#     /* ── inputs ── */
#     .stTextInput > div > div > input {
#         background: #0f172a !important;
#         border: 1.5px solid #1e293b !important;
#         border-radius: 10px !important;
#         color: #f1f5f9 !important;
#         font-size: 14px !important;
#         padding: 12px 16px !important;
#         height: 46px !important;
#         transition: border-color 0.2s !important;
#     }
#     .stTextInput > div > div > input:focus {
#         border-color: #00d4ff !important;
#         box-shadow: 0 0 0 3px rgba(0,212,255,0.1) !important;
#     }
#     .stTextInput > div > div > input::placeholder { color: #1e293b !important; }
#     .stTextInput label {
#         color: #64748b !important;
#         font-size: 12px !important;
#         font-weight: 600 !important;
#         letter-spacing: 0.5px !important;
#         text-transform: uppercase !important;
#     }

#     /* ── button ── */
#     div.stButton > button[kind="primary"] {
#         background: linear-gradient(135deg,#1d4ed8,#2563eb) !important;
#         border: none !important;
#         color: #fff !important;
#         font-size: 15px !important;
#         font-weight: 700 !important;
#         border-radius: 10px !important;
#         height: 50px !important;
#         width: 100% !important;
#         letter-spacing: 0.3px !important;
#         transition: all 0.25s !important;
#         box-shadow: 0 4px 20px rgba(29,78,216,0.3) !important;
#     }
#     div.stButton > button[kind="primary"]:hover {
#         background: linear-gradient(135deg,#2563eb,#00d4ff) !important;
#         box-shadow: 0 6px 28px rgba(37,99,235,0.5) !important;
#         transform: translateY(-1px) !important;
#     }

#     /* ── alert styling ── */
#     [data-testid="stAlert"] { border-radius: 10px !important; }

#     /* ── LISA glow ring ── */
#     .lisa-ring {
#         width: 130px; height: 130px;
#         border-radius: 50%;
#         padding: 3px;
#         background: linear-gradient(135deg, #00d4ff, #2563eb);
#         margin: 0 auto 6px auto;
#         display: flex; align-items: center; justify-content: center;
#         box-shadow: 0 0 40px rgba(0,212,255,0.25);
#     }
#     .lisa-ring img {
#         width: 124px; height: 124px;
#         border-radius: 50%;
#         object-fit: cover;
#         display: block;
#     }

#     /* ── status dot ── */
#     .lisa-status {
#         display: flex; align-items: center;
#         justify-content: center; gap: 6px;
#         font-size: 12px; color: #10b981;
#         font-weight: 600; letter-spacing: 0.5px;
#         margin-bottom: 20px;
#     }
#     .dot {
#         width: 8px; height: 8px;
#         background: #10b981;
#         border-radius: 50%;
#         animation: pulse 2s infinite;
#     }
#     @keyframes pulse {
#         0%,100% { opacity:1; transform:scale(1); }
#         50%      { opacity:0.4; transform:scale(1.3); }
#     }
#     </style>
#     """, unsafe_allow_html=True)

#     # ── two column layout: LISA left, form right ──────────────────
#     st.markdown("<br>", unsafe_allow_html=True)
#     left, gap, right = st.columns([1.1, 0.15, 1.1])

#     # ════════════════════════════════════════════
#     # LEFT — LISA hero
#     # ════════════════════════════════════════════
#     with left:
#         st.markdown("<br><br><br>", unsafe_allow_html=True)

#         lisa_b64 = _get_lisa_b64()
#         if lisa_b64:
#             st.markdown(f"""
#             <div class="lisa-ring">
#                 <img src="data:image/png;base64,{lisa_b64}" alt="LISA"/>
#             </div>
#             """, unsafe_allow_html=True)
#         else:
#             st.markdown("""
#             <div style="font-size:90px;text-align:center;
#                         line-height:1;margin-bottom:8px;">🤖</div>
#             """, unsafe_allow_html=True)

#         st.markdown("""
#         <div class="lisa-status">
#             <span class="dot"></span> LISA is online
#         </div>

#         <div style="text-align:center;">
#             <div style="font-size:36px;font-weight:900;
#                         color:#f0f4ff;letter-spacing:-1px;line-height:1.1;">
#                 Meet <span style="color:#00d4ff;">LISA</span>
#             </div>
#             <div style="font-size:13px;color:#334155;
#                         letter-spacing:2px;text-transform:uppercase;
#                         margin-top:8px;margin-bottom:24px;">
#                 Learning Intelligent Simulation Assistant
#             </div>
#         </div>

#         <div style="display:flex;flex-direction:column;gap:14px;
#                     padding:0 12px;">
#             <div style="display:flex;align-items:flex-start;gap:12px;">
#                 <span style="font-size:20px;flex-shrink:0;">📄</span>
#                 <div>
#                     <div style="color:#f0f4ff;font-weight:700;font-size:14px;">
#                         Reads Your Resume
#                     </div>
#                     <div style="color:#334155;font-size:12px;margin-top:2px;">
#                         LISA studies your skills and projects to personalise every question
#                     </div>
#                 </div>
#             </div>
#             <div style="display:flex;align-items:flex-start;gap:12px;">
#                 <span style="font-size:20px;flex-shrink:0;">🎙️</span>
#                 <div>
#                     <div style="color:#f0f4ff;font-weight:700;font-size:14px;">
#                         Voice + Text Answers
#                     </div>
#                     <div style="color:#334155;font-size:12px;margin-top:2px;">
#                         Speak naturally or type — Whisper AI transcribes in real time
#                     </div>
#                 </div>
#             </div>
#             <div style="display:flex;align-items:flex-start;gap:12px;">
#                 <span style="font-size:20px;flex-shrink:0;">📊</span>
#                 <div>
#                     <div style="color:#f0f4ff;font-weight:700;font-size:14px;">
#                         Detailed PDF Report
#                     </div>
#                     <div style="color:#334155;font-size:12px;margin-top:2px;">
#                         Scores, ideal answers, and a study plan after every session
#                     </div>
#                 </div>
#             </div>
#             <div style="display:flex;align-items:flex-start;gap:12px;">
#                 <span style="font-size:20px;flex-shrink:0;">🧠</span>
#                 <div>
#                     <div style="color:#f0f4ff;font-weight:700;font-size:14px;">
#                         Adaptive Difficulty
#                     </div>
#                     <div style="color:#334155;font-size:12px;margin-top:2px;">
#                         Questions get harder or easier based on your answers
#                     </div>
#                 </div>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#     # gap column — vertical divider
#     with gap:
#         st.markdown("""
#         <div style="
#             height:70vh;
#             width:1px;
#             background:linear-gradient(to bottom,transparent,#1e293b,transparent);
#             margin:60px auto 0 auto;">
#         </div>
#         """, unsafe_allow_html=True)

#     # ════════════════════════════════════════════
#     # RIGHT — login / register form
#     # ════════════════════════════════════════════
#     with right:
#         st.markdown("<br><br>", unsafe_allow_html=True)

#         st.markdown("""
#         <div style="margin-bottom:28px;">
#             <div style="font-size:26px;font-weight:800;
#                         color:#f0f4ff;letter-spacing:-0.5px;">
#                 Welcome to <span style="color:#00d4ff;">Pyspace</span>
#             </div>
#             <div style="font-size:13px;color:#334155;margin-top:6px;">
#                 Sign in or create an account to start practising
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#         tab_login, tab_register = st.tabs(["Login", "Register"])

#         # ── LOGIN ─────────────────────────────
#         with tab_login:
#             st.markdown("<br>", unsafe_allow_html=True)

#             l_email = st.text_input(
#                 "Email", placeholder="you@example.com", key="l_email"
#             )
#             st.markdown(
#                 "<div style='height:12px'></div>", unsafe_allow_html=True
#             )
#             l_pass = st.text_input(
#                 "Password", type="password",
#                 placeholder="Your password", key="l_pass"
#             )
#             st.markdown("<br>", unsafe_allow_html=True)

#             if st.button("Login to Pyspace", type="primary",
#                          use_container_width=True, key="do_login"):
#                 e = l_email.strip().lower()
#                 p = l_pass.strip()
#                 if not e or not p:
#                     st.error("Please fill in both fields.")
#                 else:
#                     with st.spinner("Verifying..."):
#                         user = login_user(e, p)
#                     if user:
#                         _set_session(user)
#                         st.rerun()
#                     else:
#                         st.error("Wrong email or password.")

#             st.markdown("""
#             <p style="text-align:center;font-size:12px;
#                       color:#334155;margin-top:16px;">
#                 No account yet?
#                 <b style="color:#00d4ff;cursor:pointer;">
#                     Click Register above
#                 </b>
#             </p>
#             """, unsafe_allow_html=True)

#         # ── REGISTER ──────────────────────────
#         with tab_register:
#             st.markdown("<br>", unsafe_allow_html=True)

#             r_name = st.text_input(
#                 "Full Name", placeholder="Your full name", key="r_name"
#             )
#             st.markdown(
#                 "<div style='height:12px'></div>", unsafe_allow_html=True
#             )
#             r_email = st.text_input(
#                 "Email", placeholder="you@example.com", key="r_email"
#             )
#             st.markdown(
#                 "<div style='height:12px'></div>", unsafe_allow_html=True
#             )
#             r_pass = st.text_input(
#                 "Password", type="password",
#                 placeholder="Minimum 6 characters", key="r_pass"
#             )
#             st.markdown(
#                 "<div style='height:12px'></div>", unsafe_allow_html=True
#             )
#             r_pass2 = st.text_input(
#                 "Confirm Password", type="password",
#                 placeholder="Repeat your password", key="r_pass2"
#             )
#             st.markdown("<br>", unsafe_allow_html=True)

#             if st.button("Create Account", type="primary",
#                          use_container_width=True, key="do_register"):

#                 name  = r_name.strip()
#                 email = r_email.strip().lower()
#                 pw    = r_pass
#                 pw2   = r_pass2

#                 if not name:
#                     st.error("Please enter your full name.")
#                 elif not email or "@" not in email:
#                     st.error("Please enter a valid email.")
#                 elif len(pw) < 6:
#                     st.error("Password must be at least 6 characters.")
#                 elif pw != pw2:
#                     st.error("Passwords do not match.")
#                 else:
#                     with st.spinner("Creating your account..."):
#                         ok, msg = register_user(name, email, pw)

#                     if ok:
#                         with st.spinner("Logging you in..."):
#                             user = login_user(email, pw)
#                         if user:
#                             _set_session(user)
#                             st.rerun()
#                         else:
#                             st.success(
#                                 "Account created! Please login."
#                             )
#                     elif msg == "email_exists":
#                         st.error(
#                             "Email already registered. Please login."
#                         )
#                     else:
#                         st.error(f"Registration failed: {msg}")

#             st.markdown("""
#             <p style="text-align:center;font-size:12px;
#                       color:#334155;margin-top:16px;">
#                 Already registered?
#                 <b style="color:#00d4ff;">Click Login above</b>
#             </p>
#             """, unsafe_allow_html=True)


# def handle_auth() -> bool:
#     if st.session_state.get("logged_in"):
#         return True
#     login_page()
#     return False
# # """
# # auth/login.py
# # Clean login/register UI — uses auth/auth.py independently.
# # """
# # import streamlit as st
# # from auth.auth import register_user, login_user


# # # ─────────────────────────────────────────────
# # # LOGOUT
# # # ─────────────────────────────────────────────
# # def logout_user():
# #     st.session_state.clear()
# #     st.rerun()


# # # ─────────────────────────────────────────────
# # # SET SESSION
# # # ─────────────────────────────────────────────
# # def _set_session(user: dict):
# #     st.session_state["logged_in"]  = True
# #     st.session_state["user_name"]  = user["name"]
# #     st.session_state["user_email"] = user["email"]


# # # ─────────────────────────────────────────────
# # # STYLES
# # # ─────────────────────────────────────────────
# # def _inject_styles():
# #     st.markdown("""
# #     <style>
# #     .stApp, [data-testid="stAppViewContainer"],
# #     [data-testid="stMain"] {
# #         background-color: #0d0f14 !important;
# #     }
# #     header, #MainMenu, footer { visibility: hidden !important; }

# #     /* all default text white */
# #     .stApp p, .stApp span, .stApp div,
# #     .stApp label, .stMarkdown { color: #e2e8f0 !important; }

# #     /* tabs */
# #     .stTabs [data-baseweb="tab-list"] {
# #         background: transparent !important;
# #         border-bottom: 2px solid #1e2d47 !important;
# #         padding: 0 !important;
# #         gap: 0 !important;
# #     }
# #     .stTabs [data-baseweb="tab"] {
# #         background: transparent !important;
# #         color: #4b5563 !important;
# #         font-size: 16px !important;
# #         font-weight: 700 !important;
# #         padding: 14px 40px !important;
# #         border-bottom: 3px solid transparent !important;
# #         border-radius: 0 !important;
# #         margin-bottom: -2px !important;
# #     }
# #     .stTabs [aria-selected="true"] {
# #         color: #00d4ff !important;
# #         border-bottom: 3px solid #00d4ff !important;
# #         background: transparent !important;
# #     }

# #     /* inputs */
# #     .stTextInput > div > div > input {
# #         background: #0d1117 !important;
# #         border: 1.5px solid #1e2d47 !important;
# #         border-radius: 10px !important;
# #         color: #f0f4ff !important;
# #         font-size: 15px !important;
# #         padding: 12px 16px !important;
# #         height: 48px !important;
# #     }
# #     .stTextInput > div > div > input:focus {
# #         border-color: #00d4ff !important;
# #         box-shadow: 0 0 0 3px #00d4ff15 !important;
# #     }
# #     .stTextInput > div > div > input::placeholder {
# #         color: #2d3748 !important;
# #     }
# #     .stTextInput label {
# #         color: #9ca3af !important;
# #         font-size: 13px !important;
# #         font-weight: 600 !important;
# #         letter-spacing: 0.3px !important;
# #     }

# #     /* primary button */
# #     div.stButton > button[kind="primary"] {
# #         background: #1d4ed8 !important;
# #         border: none !important;
# #         color: #ffffff !important;
# #         font-size: 15px !important;
# #         font-weight: 700 !important;
# #         border-radius: 10px !important;
# #         height: 50px !important;
# #         width: 100% !important;
# #         letter-spacing: 0.4px !important;
# #         transition: all 0.2s !important;
# #     }
# #     div.stButton > button[kind="primary"]:hover {
# #         background: #2563eb !important;
# #         box-shadow: 0 4px 24px rgba(37,99,235,0.45) !important;
# #         transform: translateY(-1px) !important;
# #     }
# #     div.stButton > button[kind="primary"]:active {
# #         transform: translateY(0px) !important;
# #     }

# #     /* error / success */
# #     .stAlert { border-radius: 10px !important; }
# #     </style>
# #     """, unsafe_allow_html=True)


# # # ─────────────────────────────────────────────
# # # LOGIN PAGE
# # # ─────────────────────────────────────────────
# # def login_page():
# #     _inject_styles()

# #     # vertical centering
# #     st.markdown("<br><br><br>", unsafe_allow_html=True)

# #     _, col, _ = st.columns([1, 1.0, 1])

# #     with col:

# #         # ── LOGO ─────────────────────────────
# #         st.markdown("""
# #         <div style="text-align:center; margin-bottom:36px;">
# #             <div style="font-size:54px; line-height:1.1;">🤖</div>
# #             <div style="
# #                 font-size:32px;
# #                 font-weight:900;
# #                 color:#f0f4ff;
# #                 letter-spacing:-1px;
# #                 margin-top:10px;
# #                 line-height:1;">
# #                 Pyspace <span style="color:#00d4ff;">AI</span>
# #             </div>
# #             <div style="
# #                 font-size:12px;
# #                 color:#374151;
# #                 margin-top:8px;
# #                 letter-spacing:2px;
# #                 text-transform:uppercase;">
# #                 AI Interview Simulator
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #         # ── CARD ─────────────────────────────
# #         st.markdown("""
# #         <div style="
# #             background:#111827;
# #             border:1px solid #1e2d47;
# #             border-radius:20px;
# #             padding:32px 32px 28px 32px;
# #             box-shadow: 0 8px 40px rgba(0,0,0,0.6);">
# #         """, unsafe_allow_html=True)

# #         tab_login, tab_register = st.tabs(["  Login  ", "  Register  "])

# #         # ════════════════════════════════════
# #         # LOGIN
# #         # ════════════════════════════════════
# #         with tab_login:
# #             st.markdown("<br>", unsafe_allow_html=True)

# #             l_email = st.text_input(
# #                 "Email",
# #                 placeholder = "you@example.com",
# #                 key         = "l_email"
# #             )
# #             st.markdown(
# #                 "<div style='height:14px'></div>",
# #                 unsafe_allow_html=True
# #             )
# #             l_pass = st.text_input(
# #                 "Password",
# #                 type        = "password",
# #                 placeholder = "Your password",
# #                 key         = "l_pass"
# #             )
# #             st.markdown("<br>", unsafe_allow_html=True)

# #             if st.button("Login", type="primary",
# #                          use_container_width=True, key="do_login"):
# #                 e = l_email.strip().lower()
# #                 p = l_pass.strip()
# #                 if not e or not p:
# #                     st.error("Please fill in both fields.")
# #                 else:
# #                     with st.spinner("Logging in..."):
# #                         user = login_user(e, p)
# #                     if user:
# #                         _set_session(user)
# #                         st.rerun()
# #                     else:
# #                         st.error("Wrong email or password.")

# #             st.markdown("""
# #             <p style="text-align:center;font-size:12px;
# #                       color:#374151;margin-top:18px;">
# #                 No account?
# #                 <b style="color:#00d4ff;">Click Register above</b>
# #             </p>
# #             """, unsafe_allow_html=True)

# #         # ════════════════════════════════════
# #         # REGISTER
# #         # ════════════════════════════════════
# #         with tab_register:
# #             st.markdown("<br>", unsafe_allow_html=True)

# #             r_name = st.text_input(
# #                 "Full Name",
# #                 placeholder = "Your full name",
# #                 key         = "r_name"
# #             )
# #             st.markdown(
# #                 "<div style='height:14px'></div>",
# #                 unsafe_allow_html=True
# #             )
# #             r_email = st.text_input(
# #                 "Email",
# #                 placeholder = "you@example.com",
# #                 key         = "r_email"
# #             )
# #             st.markdown(
# #                 "<div style='height:14px'></div>",
# #                 unsafe_allow_html=True
# #             )
# #             r_pass = st.text_input(
# #                 "Password",
# #                 type        = "password",
# #                 placeholder = "Minimum 6 characters",
# #                 key         = "r_pass"
# #             )
# #             st.markdown(
# #                 "<div style='height:14px'></div>",
# #                 unsafe_allow_html=True
# #             )
# #             r_pass2 = st.text_input(
# #                 "Confirm Password",
# #                 type        = "password",
# #                 placeholder = "Repeat your password",
# #                 key         = "r_pass2"
# #             )
# #             st.markdown("<br>", unsafe_allow_html=True)

# #             if st.button("Create Account", type="primary",
# #                          use_container_width=True, key="do_register"):

# #                 name  = r_name.strip()
# #                 email = r_email.strip().lower()
# #                 pw    = r_pass
# #                 pw2   = r_pass2

# #                 # ── Validate ─────────────────
# #                 if not name:
# #                     st.error("Please enter your full name.")
# #                 elif not email or "@" not in email:
# #                     st.error("Please enter a valid email.")
# #                 elif len(pw) < 6:
# #                     st.error("Password must be at least 6 characters.")
# #                 elif pw != pw2:
# #                     st.error("Passwords do not match.")
# #                 else:
# #                     # ── Register ─────────────
# #                     with st.spinner("Creating account..."):
# #                         ok, msg = register_user(name, email, pw)

# #                     if ok:
# #                         # ── Auto login ────────
# #                         with st.spinner("Logging you in..."):
# #                             user = login_user(email, pw)
# #                         if user:
# #                             _set_session(user)
# #                             st.rerun()
# #                         else:
# #                             st.success(
# #                                 "Account created! "
# #                                 "Please login with your credentials."
# #                             )
# #                     elif msg == "email_exists":
# #                         st.error(
# #                             "This email is already registered. "
# #                             "Please login instead."
# #                         )
# #                     else:
# #                         st.error(f"Registration failed: {msg}")

# #             st.markdown("""
# #             <p style="text-align:center;font-size:12px;
# #                       color:#374151;margin-top:18px;">
# #                 Already registered?
# #                 <b style="color:#00d4ff;">Click Login above</b>
# #             </p>
# #             """, unsafe_allow_html=True)

# #         st.markdown("</div>", unsafe_allow_html=True)


# # # ─────────────────────────────────────────────
# # # MAIN ENTRY — called from app.py
# # # ─────────────────────────────────────────────
# # def handle_auth() -> bool:
# #     if st.session_state.get("logged_in"):
# #         return True
# #     login_page()
# #     return False

# # import streamlit as st
# # from database.db import (
# #     get_user_by_email,
# #     create_user_with_password,
# #     verify_user_password
# # )


# # # ─────────────────────────────────────────────
# # # LOGOUT
# # # ─────────────────────────────────────────────
# # def logout_user():
# #     st.session_state.clear()
# #     st.rerun()


# # # ─────────────────────────────────────────────
# # # SET SESSION
# # # ─────────────────────────────────────────────
# # def set_session(user: dict):
# #     st.session_state["logged_in"]    = True
# #     st.session_state["user_name"]    = user["name"]
# #     st.session_state["user_email"]   = user["email"]
# #     st.session_state["user_picture"] = user.get("picture", "")


# # # ─────────────────────────────────────────────
# # # LOGIN PAGE
# # # ─────────────────────────────────────────────
# # def login_page():

# #     st.markdown("""
# #     <style>

# #     /* ── dark background ── */
# #     .stApp, [data-testid="stAppViewContainer"] {
# #         background-color: #0d0f14 !important;
# #     }
# #     header, #MainMenu, footer { visibility: hidden !important; }

# #     /* ── all text ── */
# #     .stApp p, .stApp span, .stApp label,
# #     .stApp div, .stMarkdown {
# #         color: #e2e8f0 !important;
# #     }

# #     /* ── tab bar ── */
# #     .stTabs [data-baseweb="tab-list"] {
# #         background: #0d0f14 !important;
# #         border-bottom: 2px solid #1e2d47 !important;
# #         gap: 0 !important;
# #         padding: 0 !important;
# #     }
# #     .stTabs [data-baseweb="tab"] {
# #         background: transparent !important;
# #         color: #6b7280 !important;
# #         font-weight: 700 !important;
# #         font-size: 15px !important;
# #         padding: 14px 32px !important;
# #         border-bottom: 3px solid transparent !important;
# #         border-radius: 0 !important;
# #         margin-bottom: -2px !important;
# #     }
# #     .stTabs [aria-selected="true"] {
# #         color: #00d4ff !important;
# #         border-bottom: 3px solid #00d4ff !important;
# #         background: transparent !important;
# #     }

# #     /* ── input fields ── */
# #     .stTextInput input {
# #         background: #0d0f14 !important;
# #         border: 1px solid #1e2d47 !important;
# #         border-radius: 8px !important;
# #         color: #f0f4ff !important;
# #         font-size: 14px !important;
# #         padding: 10px 14px !important;
# #         height: 44px !important;
# #     }
# #     .stTextInput input:focus {
# #         border-color: #00d4ff !important;
# #         box-shadow: 0 0 0 2px #00d4ff22 !important;
# #     }
# #     .stTextInput input::placeholder { color: #374151 !important; }
# #     .stTextInput label {
# #         color: #9ca3af !important;
# #         font-size: 13px !important;
# #         font-weight: 500 !important;
# #         margin-bottom: 4px !important;
# #     }

# #     /* ── primary button ── */
# #     .stButton > button[kind="primary"] {
# #         background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
# #         border: none !important;
# #         color: white !important;
# #         font-weight: 700 !important;
# #         font-size: 15px !important;
# #         border-radius: 10px !important;
# #         height: 48px !important;
# #         letter-spacing: 0.3px !important;
# #     }
# #     .stButton > button[kind="primary"]:hover {
# #         background: linear-gradient(135deg, #2563eb, #00d4ff) !important;
# #         box-shadow: 0 4px 20px rgba(37,99,235,0.4) !important;
# #     }

# #     /* ── card box ── */
# #     .auth-card {
# #         background: #161b27;
# #         border: 1px solid #1e2d47;
# #         border-radius: 20px;
# #         padding: 36px 36px 28px 36px;
# #         box-shadow: 0 0 60px rgba(0,212,255,0.04);
# #         margin-top: 8px;
# #     }

# #     </style>
# #     """, unsafe_allow_html=True)

# #     # ── LAYOUT ───────────────────────────────
# #     st.markdown("<br><br>", unsafe_allow_html=True)
# #     _, col, _ = st.columns([1, 1.1, 1])

# #     with col:

# #         # ── LOGO ─────────────────────────────
# #         st.markdown("""
# #         <div style="text-align:center; margin-bottom:32px;">
# #             <div style="font-size:52px; margin-bottom:10px;">🤖</div>
# #             <div style="font-size:30px; font-weight:800; color:#f0f4ff;
# #                         letter-spacing:-0.5px; line-height:1;">
# #                 Pyspace <span style="color:#00d4ff;">AI</span>
# #             </div>
# #             <div style="font-size:13px; color:#4b5563; margin-top:8px;
# #                         letter-spacing:0.5px;">
# #                 PRACTICE REAL INTERVIEWS WITH LISA
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #         # ── CARD ─────────────────────────────
# #         st.markdown('<div class="auth-card">', unsafe_allow_html=True)

# #         tab_login, tab_register = st.tabs(["Login", "Register"])

# #         # ════════════════════════════════════
# #         # LOGIN TAB
# #         # ════════════════════════════════════
# #         with tab_login:

# #             # Spacer between tab and first field
# #             st.markdown("<br>", unsafe_allow_html=True)

# #             email = st.text_input(
# #                 "Email Address",
# #                 key         = "li_email",
# #                 placeholder = "you@example.com"
# #             )

# #             # Gap between fields
# #             st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# #             password = st.text_input(
# #                 "Password",
# #                 key         = "li_pass",
# #                 type        = "password",
# #                 placeholder = "Enter your password"
# #             )

# #             # Gap before button
# #             st.markdown("<br>", unsafe_allow_html=True)

# #             login_btn = st.button(
# #                 "Login to Pyspace",
# #                 type             = "primary",
# #                 use_container_width = True,
# #                 key              = "btn_login"
# #             )

# #             if login_btn:
# #                 if not email.strip() or not password.strip():
# #                     st.error("Please enter both email and password.")
# #                 else:
# #                     with st.spinner("Verifying..."):
# #                         user = verify_user_password(
# #                             email.strip().lower(), password
# #                         )
# #                     if user:
# #                         set_session(user)
# #                         st.rerun()
# #                     else:
# #                         st.error("Incorrect email or password. Please try again.")

# #             # Hint
# #             st.markdown("""
# #             <div style="text-align:center; margin-top:20px;
# #                         font-size:12px; color:#4b5563;">
# #                 No account yet?
# #                 <span style="color:#00d4ff; font-weight:600;">
# #                     Click Register above
# #                 </span>
# #             </div>
# #             """, unsafe_allow_html=True)

# #         # ════════════════════════════════════
# #         # REGISTER TAB
# #         # ════════════════════════════════════
# #         with tab_register:

# #             st.markdown("<br>", unsafe_allow_html=True)

# #             reg_name = st.text_input(
# #                 "Full Name",
# #                 key         = "reg_name",
# #                 placeholder = "Your full name"
# #             )

# #             st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# #             reg_email = st.text_input(
# #                 "Email Address",
# #                 key         = "reg_email",
# #                 placeholder = "you@example.com"
# #             )

# #             st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# #             reg_pass = st.text_input(
# #                 "Password",
# #                 key         = "reg_pass",
# #                 type        = "password",
# #                 placeholder = "Minimum 6 characters"
# #             )

# #             st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# #             reg_pass2 = st.text_input(
# #                 "Confirm Password",
# #                 key         = "reg_pass2",
# #                 type        = "password",
# #                 placeholder = "Repeat your password"
# #             )

# #             st.markdown("<br>", unsafe_allow_html=True)

# #             reg_btn = st.button(
# #                 "Create Account & Start",
# #                 type             = "primary",
# #                 use_container_width = True,
# #                 key              = "btn_register"
# #             )

# #             if reg_btn:
# #                 # ── Validate ─────────────────
# #                 if not reg_name.strip():
# #                     st.error("Please enter your full name.")
# #                 elif not reg_email.strip() or "@" not in reg_email:
# #                     st.error("Please enter a valid email address.")
# #                 elif len(reg_pass) < 6:
# #                     st.error("Password must be at least 6 characters.")
# #                 elif reg_pass != reg_pass2:
# #                     st.error("Passwords do not match.")
# #                 else:
# #                     with st.spinner("Creating your account..."):
# #                         existing = get_user_by_email(
# #                             reg_email.strip().lower()
# #                         )

# #                     if existing:
# #                         st.error(
# #                             "This email is already registered. "
# #                             "Please login instead."
# #                         )
# #                     else:
# #                         with st.spinner("Setting up your profile..."):
# #                             success = create_user_with_password(
# #                                 name     = reg_name.strip(),
# #                                 email    = reg_email.strip().lower(),
# #                                 password = reg_pass
# #                             )

# #                         if success:
# #                             # ── Auto-login after register ──
# #                             user = verify_user_password(
# #                                 reg_email.strip().lower(),
# #                                 reg_pass
# #                             )
# #                             if user:
# #                                 set_session(user)
# #                                 st.success(
# #                                     f"Welcome to Pyspace, "
# #                                     f"{reg_name.strip().split()[0]}! "
# #                                     f"Taking you in..."
# #                                 )
# #                                 st.rerun()
# #                             else:
# #                                 st.success(
# #                                     "Account created! "
# #                                     "Please login with your credentials."
# #                                 )
# #                         else:
# #                             st.error(
# #                                 "Registration failed. "
# #                                 "Please check your details and try again."
# #                             )

# #             st.markdown("""
# #             <div style="text-align:center; margin-top:20px;
# #                         font-size:12px; color:#4b5563;">
# #                 Already have an account?
# #                 <span style="color:#00d4ff; font-weight:600;">
# #                     Click Login above
# #                 </span>
# #             </div>
# #             """, unsafe_allow_html=True)

# #         st.markdown('</div>', unsafe_allow_html=True)


# # # ─────────────────────────────────────────────
# # # MAIN ENTRY
# # # ─────────────────────────────────────────────
# # def handle_auth() -> bool:
# #     if st.session_state.get("logged_in"):
# #         return True
# #     login_page()
# #     return False
# # # import streamlit as st
# # # from database.db import (
# # #     get_user_by_email,
# # #     create_user_with_password,
# # #     verify_user_password
# # # )


# # # # ─────────────────────────────────────────────
# # # # LOGOUT
# # # # ─────────────────────────────────────────────
# # # def logout_user():
# # #     st.session_state.clear()
# # #     st.rerun()


# # # # ─────────────────────────────────────────────
# # # # SET SESSION — reused by login + register
# # # # ─────────────────────────────────────────────
# # # def set_session(user: dict):
# # #     st.session_state["logged_in"]    = True
# # #     st.session_state["user_name"]    = user["name"]
# # #     st.session_state["user_email"]   = user["email"]
# # #     st.session_state["user_picture"] = user.get("picture", "")


# # # # ─────────────────────────────────────────────
# # # # LOGIN PAGE
# # # # ─────────────────────────────────────────────
# # # def login_page():

# # #     st.markdown("""
# # #     <style>
# # #     .stApp { background-color: #0d0f14 !important; }

# # #     /* hide streamlit header */
# # #     header, #MainMenu, footer { visibility: hidden !important; }

# # #     /* tab styling */
# # #     .stTabs [data-baseweb="tab-list"] {
# # #         background: #161b27 !important;
# # #         border-radius: 10px !important;
# # #         padding: 4px !important;
# # #         gap: 4px !important;
# # #     }
# # #     .stTabs [data-baseweb="tab"] {
# # #         background: transparent !important;
# # #         color: #6b7280 !important;
# # #         border-radius: 8px !important;
# # #         font-weight: 600 !important;
# # #         font-size: 14px !important;
# # #     }
# # #     .stTabs [aria-selected="true"] {
# # #         background: #1e3a6e !important;
# # #         color: #00d4ff !important;
# # #     }

# # #     /* input fields */
# # #     .stTextInput input {
# # #         background: #161b27 !important;
# # #         border: 1px solid #1e2d47 !important;
# # #         border-radius: 8px !important;
# # #         color: #f0f4ff !important;
# # #         font-size: 14px !important;
# # #     }
# # #     .stTextInput input:focus {
# # #         border-color: #00d4ff !important;
# # #         box-shadow: 0 0 0 1px #00d4ff33 !important;
# # #     }
# # #     .stTextInput label {
# # #         color: #9ca3af !important;
# # #         font-size: 13px !important;
# # #     }

# # #     /* primary button */
# # #     .stButton > button[kind="primary"] {
# # #         background: linear-gradient(135deg, #1e3a6e, #2563eb) !important;
# # #         border: none !important;
# # #         color: white !important;
# # #         font-weight: 700 !important;
# # #         font-size: 15px !important;
# # #         border-radius: 10px !important;
# # #         padding: 12px !important;
# # #         transition: opacity 0.2s !important;
# # #     }
# # #     .stButton > button[kind="primary"]:hover {
# # #         opacity: 0.9 !important;
# # #         border: 1px solid #00d4ff !important;
# # #     }
# # #     </style>
# # #     """, unsafe_allow_html=True)

# # #     # ── PAGE HEADER ──────────────────────────
# # #     st.markdown("<br><br>", unsafe_allow_html=True)
# # #     _, center, _ = st.columns([1, 1.2, 1])

# # #     with center:
# # #         # Logo + title
# # #         st.markdown("""
# # #         <div style="text-align:center; margin-bottom:28px;">
# # #             <div style="font-size:48px; margin-bottom:8px;">🤖</div>
# # #             <div style="font-size:28px; font-weight:800; color:#f0f4ff;
# # #                         letter-spacing:-0.5px;">
# # #                 Pyspace <span style="color:#00d4ff;">AI</span>
# # #             </div>
# # #             <div style="font-size:14px; color:#6b7280; margin-top:6px;">
# # #                 Practice real interviews with LISA
# # #             </div>
# # #         </div>
# # #         """, unsafe_allow_html=True)

# # #         # ── TABS ─────────────────────────────
# # #         tab_login, tab_register = st.tabs(["  Login  ", "  Register  "])

# # #         # ════════════════════════════════════
# # #         # LOGIN TAB
# # #         # ════════════════════════════════════
# # #         with tab_login:
# # #             st.markdown("<br>", unsafe_allow_html=True)

# # #             email    = st.text_input("Email",    key="li_email",
# # #                                      placeholder="you@example.com")
# # #             password = st.text_input("Password", key="li_pass",
# # #                                      type="password",
# # #                                      placeholder="Your password")

# # #             st.markdown("<br>", unsafe_allow_html=True)

# # #             if st.button("Login", type="primary",
# # #                          use_container_width=True, key="btn_login"):
# # #                 if not email.strip() or not password.strip():
# # #                     st.error("Please enter both email and password.")
# # #                 else:
# # #                     user = verify_user_password(email.strip().lower(), password)
# # #                     if user:
# # #                         set_session(user)
# # #                         st.rerun()
# # #                     else:
# # #                         st.error("Incorrect email or password.")

# # #             st.markdown("""
# # #             <div style="text-align:center; margin-top:16px;
# # #                         font-size:12px; color:#4b5563;">
# # #                 Don't have an account? Click <b style="color:#00d4ff;">Register</b> above.
# # #             </div>
# # #             """, unsafe_allow_html=True)

# # #         # ════════════════════════════════════
# # #         # REGISTER TAB — auto-login on success
# # #         # ════════════════════════════════════
# # #         with tab_register:
# # #             st.markdown("<br>", unsafe_allow_html=True)

# # #             reg_name  = st.text_input("Full Name", key="reg_name",
# # #                                       placeholder="Your full name")
# # #             reg_email = st.text_input("Email",     key="reg_email",
# # #                                       placeholder="you@example.com")
# # #             reg_pass  = st.text_input("Password",  key="reg_pass",
# # #                                       type="password",
# # #                                       placeholder="Min 6 characters")
# # #             reg_pass2 = st.text_input("Confirm Password", key="reg_pass2",
# # #                                       type="password",
# # #                                       placeholder="Repeat password")

# # #             st.markdown("<br>", unsafe_allow_html=True)

# # #             if st.button("Create Account & Start", type="primary",
# # #                          use_container_width=True, key="btn_register"):

# # #                 # ── Validation ───────────────
# # #                 if not reg_name.strip():
# # #                     st.error("Please enter your full name.")
# # #                 elif not reg_email.strip() or "@" not in reg_email:
# # #                     st.error("Please enter a valid email address.")
# # #                 elif len(reg_pass) < 6:
# # #                     st.error("Password must be at least 6 characters.")
# # #                 elif reg_pass != reg_pass2:
# # #                     st.error("Passwords do not match.")
# # #                 else:
# # #                     # Check duplicate email
# # #                     existing = get_user_by_email(reg_email.strip().lower())
# # #                     if existing:
# # #                         st.error("An account with this email already exists. Please login.")
# # #                     else:
# # #                         # Create account
# # #                         success = create_user_with_password(
# # #                             name     = reg_name.strip(),
# # #                             email    = reg_email.strip().lower(),
# # #                             password = reg_pass
# # #                         )
# # #                         if success:
# # #                             # ── AUTO LOGIN immediately after register ──
# # #                             user = verify_user_password(
# # #                                 reg_email.strip().lower(),
# # #                                 reg_pass
# # #                             )
# # #                             if user:
# # #                                 set_session(user)
# # #                                 st.success(f"Welcome to Pyspace, {reg_name.split()[0]}!")
# # #                                 st.rerun()
# # #                             else:
# # #                                 st.success("Account created! Please login.")
# # #                         else:
# # #                             st.error("Registration failed. Please try again.")

# # #             st.markdown("""
# # #             <div style="text-align:center; margin-top:16px;
# # #                         font-size:12px; color:#4b5563;">
# # #                 Already have an account? Click <b style="color:#00d4ff;">Login</b> above.
# # #             </div>
# # #             """, unsafe_allow_html=True)


# # # # ─────────────────────────────────────────────
# # # # MAIN ENTRY — called from app.py
# # # # ─────────────────────────────────────────────
# # # def handle_auth() -> bool:
# # #     """
# # #     Returns True if logged in → show dashboard.
# # #     Returns False → show login page.
# # #     """
# # #     if st.session_state.get("logged_in"):
# # #         return True
# # #     login_page()
# # #     return False

# # # # import streamlit as st

# # # # def login_ui():
# # # #     st.markdown("<h1 style='text-align:center;'>🚀 PYSPACE AI Interview</h1>", unsafe_allow_html=True)

# # # #     with st.container():
# # # #         st.subheader("Login to Continue")

# # # #         email = st.text_input("Email")
# # # #         password = st.text_input("Password", type="password")

# # # #         login_btn = st.button("Login")

# # # #         if login_btn:
# # # #             if email and password:
# # # #                 st.session_state["user"] = email
# # # #                 st.success("Login Successful!")
# # # #                 st.rerun()
# # # #             else:
# # # #                 st.error("Please fill all fields")