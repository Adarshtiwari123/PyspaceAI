import os
import streamlit as st

st.set_page_config(
    page_title = "Pyspace AI Interview",
    page_icon  = "🤖",
    layout     = "wide",
    initial_sidebar_state = "collapsed"
)

if not os.path.exists("user_resumes"):
    os.makedirs("user_resumes")

from auth.login import handle_auth
from dashboard.student_dashboard import student_dashboard

if handle_auth():
    student_dashboard()
# import os
# import streamlit as st

# st.set_page_config(
#     page_title = "Pyspace AI Interview",
#     page_icon  = "🤖",
#     layout     = "wide"
# )

# # Create resume folder if not exists
# if not os.path.exists("user_resumes"):
#     os.makedirs("user_resumes")

# from auth.login import handle_auth
# from dashboard.student_dashboard import student_dashboard

# # Auth FIRST — only one call, never duplicated
# if handle_auth():
#     student_dashboard()
# import streamlit as st
# from auth.google_login import google_login
# from dashboard.student_dashboard import student_dashboard
# import os

# st.set_page_config(
#     page_title="Pyspace",
#     layout="wide"
# )
# google_login()         # ← checks ?code= FIRST before anything
# # if st.session_state.get("logged_in"):
# #     student_dashboard()
# # create resume folder
# if not os.path.exists("user_resumes"):
#     os.makedirs("user_resumes")

# if "logged_in" not in st.session_state:
#     st.session_state.logged_in = False

# if st.session_state.logged_in:
#     student_dashboard()
# else:
#     google_login()
# import streamlit as st
# from auth.google_login import google_login
# from dashboard.student_dashboard import student_dashboard

# st.set_page_config(page_title="Pyspace", layout="wide")

# if st.session_state.get("logged_in"):
#     student_dashboard()
# else:
#     google_login()