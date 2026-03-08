import streamlit as st
from authlib.integrations.requests_client import OAuth2Session
from dotenv import load_dotenv
from database.db import save_user
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, REDIRECT_URI

load_dotenv()

# ─────────────────────────────────────────────
# GOOGLE OAUTH ENDPOINTS
# ─────────────────────────────────────────────
AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL              = "https://oauth2.googleapis.com/token"
USER_INFO_URL          = "https://www.googleapis.com/oauth2/v2/userinfo"


# ─────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────
def logout_user():
    st.session_state.clear()
    st.rerun()


# ─────────────────────────────────────────────
# GOOGLE LOGIN
# ─────────────────────────────────────────────
def google_login():

    # Page heading
    st.markdown("""
        <div style="text-align:center; padding: 60px 0 20px 0;">
            <h1>🚀 Pyspace AI Interview</h1>
            <p style="color: gray; font-size: 16px;">
                Practice real interviews with LISA — your AI interviewer
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Already logged in — nothing to do
    if st.session_state.get("logged_in"):
        return

    # ── Build OAuth session ──────────────────
    oauth = OAuth2Session(
        GOOGLE_CLIENT_ID,
        GOOGLE_CLIENT_SECRET,
        scope        = "openid email profile",
        redirect_uri = REDIRECT_URI
    )

    authorization_url, state = oauth.create_authorization_url(
        AUTHORIZATION_BASE_URL,
        access_type = "offline",
        prompt      = "select_account"
    )

    # ── Login button ─────────────────────────
    st.markdown(f"""
        <div style="text-align:center; margin-top: 20px;">
            <a href="{authorization_url}" target="_self">
                <button style="
                    background-color: #4285F4;
                    color: white;
                    padding: 12px 32px;
                    border: none;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    box-shadow: 0 2px 8px rgba(66,133,244,0.4);
                ">
                    🔐 Sign in with Google
                </button>
            </a>
        </div>
    """, unsafe_allow_html=True)

    # ── Handle OAuth callback ────────────────
    query_params = st.query_params

    if "code" not in query_params:
        return

    try:
        code = query_params["code"]

        # Clear code from URL immediately so it doesn't re-run
        st.query_params.clear()

        # Exchange code for token
        token = oauth.fetch_token(
            TOKEN_URL,
            code         = code,
            redirect_uri = REDIRECT_URI
        )

        # Fetch user info
        resp      = oauth.get(USER_INFO_URL)
        user_info = resp.json()

        # Validate required fields
        if "email" not in user_info:
            st.error("Could not retrieve Google account info. Please try again.")
            return

        # Save user to Supabase (skips if already exists)
        save_user(
            name    = user_info.get("name", "User"),
            email   = user_info["email"],
            picture = user_info.get("picture", "")
        )

        # Store in session state
        st.session_state["logged_in"]     = True
        st.session_state["user_name"]     = user_info.get("name", "User")
        st.session_state["user_email"]    = user_info["email"]
        st.session_state["user_picture"]  = user_info.get("picture", "")

        st.rerun()

    except Exception as e:
        st.error(f"Login failed. Please try again.")
        print(f"[GoogleLogin] OAuth error: {e}")

# import streamlit as st
# from authlib.integrations.requests_client import OAuth2Session
# from dotenv import load_dotenv
# from database.db import save_user
# from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, REDIRECT_URI

# load_dotenv()

# # ─────────────────────────────────────────────
# # GOOGLE OAUTH ENDPOINTS
# # ─────────────────────────────────────────────
# AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/auth"
# TOKEN_URL              = "https://oauth2.googleapis.com/token"
# USER_INFO_URL          = "https://www.googleapis.com/oauth2/v2/userinfo"


# # ─────────────────────────────────────────────
# # LOGOUT
# # ─────────────────────────────────────────────
# def logout_user():
#     st.session_state.clear()
#     st.rerun()


# # ─────────────────────────────────────────────
# # GOOGLE LOGIN
# # ─────────────────────────────────────────────
# def google_login():

#     # Page heading
#     st.markdown("""
#         <div style="text-align:center; padding: 60px 0 20px 0;">
#             <h1>🚀 Pyspace AI Interview</h1>
#             <p style="color: gray; font-size: 16px;">
#                 Practice real interviews with LISA — your AI interviewer
#             </p>
#         </div>
#     """, unsafe_allow_html=True)

#     # Already logged in — nothing to do
#     if st.session_state.get("logged_in"):
#         return

#     # ── Build OAuth session ──────────────────
#     oauth = OAuth2Session(
#         GOOGLE_CLIENT_ID,
#         GOOGLE_CLIENT_SECRET,
#         scope        = "openid email profile",
#         redirect_uri = REDIRECT_URI
#     )

#     authorization_url, state = oauth.create_authorization_url(
#         AUTHORIZATION_BASE_URL,
#         access_type = "offline",
#         prompt      = "select_account"
#     )

#     # ── Login button ─────────────────────────
#     st.markdown(f"""
#         <div style="text-align:center; margin-top: 20px;">
#             <a href="{authorization_url}" target="_self">
#                 <button style="
#                     background-color: #4285F4;
#                     color: white;
#                     padding: 12px 32px;
#                     border: none;
#                     border-radius: 8px;
#                     font-size: 16px;
#                     font-weight: 600;
#                     cursor: pointer;
#                     box-shadow: 0 2px 8px rgba(66,133,244,0.4);
#                 ">
#                     🔐 Sign in with Google
#                 </button>
#             </a>
#         </div>
#     """, unsafe_allow_html=True)

#     # ── Handle OAuth callback ────────────────
#     query_params = st.query_params

#     if "code" not in query_params:
#         return

#     try:
#         code = query_params["code"]

#         # Clear code from URL immediately so it doesn't re-run
#         st.query_params.clear()

#         # Exchange code for token
#         token = oauth.fetch_token(
#             TOKEN_URL,
#             code         = code,
#             redirect_uri = REDIRECT_URI
#         )

#         # Fetch user info
#         resp      = oauth.get(USER_INFO_URL)
#         user_info = resp.json()

#         # Validate required fields
#         if "email" not in user_info:
#             st.error("Could not retrieve Google account info. Please try again.")
#             return

#         # Save user to Supabase (skips if already exists)
#         save_user(
#             name    = user_info.get("name", "User"),
#             email   = user_info["email"],
#             picture = user_info.get("picture", "")
#         )

#         # Store in session state
#         st.session_state["logged_in"]     = True
#         st.session_state["user_name"]     = user_info.get("name", "User")
#         st.session_state["user_email"]    = user_info["email"]
#         st.session_state["user_picture"]  = user_info.get("picture", "")

#         st.rerun()

#     except Exception as e:
#         st.error(f"Login failed. Please try again.")
#         print(f"[GoogleLogin] OAuth error: {e}")



# # import streamlit as st
# # from authlib.integrations.requests_client import OAuth2Session
# # import os
# # from dotenv import load_dotenv
# # from database.db import save_user

# # load_dotenv()

# # CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
# # CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# # AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/auth"
# # TOKEN_URL = "https://oauth2.googleapis.com/token"
# # USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# # REDIRECT_URI = "http://localhost:8501"


# # # -----------------------------
# # # LOGOUT
# # # -----------------------------
# # def logout_user():
# #     st.session_state.clear()
# #     st.rerun()


# # # -----------------------------
# # # GOOGLE LOGIN
# # # -----------------------------
# # def google_login():

# #     st.markdown("""
# #         <div style="text-align:center;">
# #             <h1>🚀 Pyspace AI Interview</h1>
# #             <p>Login securely with Google</p>
# #         </div>
# #     """, unsafe_allow_html=True)

# #     # If already logged in
# #     if st.session_state.get("logged_in"):
# #         return

# #     oauth = OAuth2Session(
# #         CLIENT_ID,
# #         CLIENT_SECRET,
# #         scope="openid email profile",
# #         redirect_uri=REDIRECT_URI
# #     )

# #     authorization_url, state = oauth.create_authorization_url(
# #         AUTHORIZATION_BASE_URL,
# #         access_type="offline",
# #         prompt="select_account"
# #     )

# #     st.markdown(f"""
# #         <div style="text-align:center;">
# #             <a href="{authorization_url}">
# #                 <button style="
# #                     background-color:#4285F4;
# #                     color:white;
# #                     padding:12px 24px;
# #                     border:none;
# #                     border-radius:8px;
# #                     font-size:16px;
# #                     cursor:pointer;">
# #                     Sign in with Google
# #                 </button>
# #             </a>
# #         </div>
# #     """, unsafe_allow_html=True)
# #     query_params = st.query_params

# #     if "code" in query_params:

# #      code = query_params.get("code")

# #     # remove code so it doesn't run again
# #      st.query_params.clear()

# #      token = oauth.fetch_token(
# #         TOKEN_URL,
# #         code=code
# #      )

# #      resp = oauth.get(USER_INFO_URL)
# #      user_info = resp.json()

# #      save_user(
# #         user_info["name"],
# #         user_info["email"],
# #         user_info["picture"]
# #      )

# #      st.session_state["logged_in"] = True
# #      st.session_state["user_name"] = user_info["name"]
# #      st.session_state["user_email"] = user_info["email"]
# #      st.session_state["user_picture"] = user_info["picture"]

# #      st.rerun()

# #     # query_params = st.query_params

# #     # if "code" in query_params:

# #     #     code = query_params["code"]

# #     #     token = oauth.fetch_token(
# #     #         TOKEN_URL,
# #     #         code=code
# #     #     )

# #     #     resp = oauth.get(USER_INFO_URL)
# #     #     user_info = resp.json()

# #     #     # Save user in database
# #     #     save_user(
# #     #         user_info["name"],
# #     #         user_info["email"],
# #     #         user_info["picture"]
# #     #     )

# #     #     # Save session
# #     #     st.session_state["logged_in"] = True
# #     #     st.session_state["user_name"] = user_info["name"]
# #     #     st.session_state["user_email"] = user_info["email"]
# #     #     st.session_state["user_picture"] = user_info["picture"]

# #     #     st.rerun()