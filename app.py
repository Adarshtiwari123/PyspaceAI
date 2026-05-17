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

# Hardcode user state to bypass login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = True
if "user_email" not in st.session_state:
    st.session_state.user_email = "guest@example.com"
if "user_name" not in st.session_state:
    st.session_state.user_name = "Guest"

# Force interview to start directly
st.session_state.interview_started = True

# Provide a default resume text if none exists to ensure the AI has context
if "resume_text" not in st.session_state:
    st.session_state.resume_text = "Experienced Software Engineer with a background in Python, machine learning, and web development."

from interview.interview_engine import interview_flow

# Run the interview flow directly
interview_flow()
