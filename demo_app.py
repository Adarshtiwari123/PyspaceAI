"""
demo_app.py — Run this to test the Student Dashboard UI
without needing a real database connection.

Usage:  streamlit run demo_app.py
"""
import os
import sys
import types
import time
import streamlit as st

# ── Page config MUST be first Streamlit call ──
st.set_page_config(
    page_title="Pyspace AI Interview (Demo)",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if not os.path.exists("user_resumes"):
    os.makedirs("user_resumes")

# ═══════════════════════════════════════════════
# MOCK DATABASE MODULE — replaces database.db
# ═══════════════════════════════════════════════
mock_db = types.ModuleType("database.db")

# Sample interview data for history
_SAMPLE_INTERVIEWS = [
    # (id, status, total_score, start_time, end_time, resume_filename)
]

def _mock_get_user_interviews(email):
    return _SAMPLE_INTERVIEWS

def _mock_has_used_interview(email):
    return False  # Allow starting interviews in demo

def _mock_create_interview(user_email, resume_text, resume_filename):
    return 999  # Fake interview ID

def _mock_save_question(**kwargs):
    pass

def _mock_complete_interview(iid, score):
    pass

def _mock_save_report(**kwargs):
    pass

def _mock_get_interview_questions(iid):
    return []

def _mock_get_all_user_questions(email):
    return []

def _mock_create_tables():
    pass

# Attach all mock functions
mock_db.get_user_interviews = _mock_get_user_interviews
mock_db.has_used_interview = _mock_has_used_interview
mock_db.create_interview = _mock_create_interview
mock_db.save_question = lambda *a, **kw: None
mock_db.complete_interview = _mock_complete_interview
mock_db.save_report = lambda *a, **kw: None
mock_db.get_interview_questions = _mock_get_interview_questions
mock_db.get_all_user_questions = _mock_get_all_user_questions
mock_db.create_tables = _mock_create_tables
mock_db.get_report = lambda *a: None
mock_db.get_report_pdf = lambda *a: None
mock_db.get_user = lambda *a: None
mock_db.save_user = lambda *a: None
mock_db.get_user_by_email = lambda *a: None
mock_db.create_user_with_password = lambda *a: True
mock_db.verify_user_password = lambda *a: None
mock_db.has_used_free_interview = lambda *a: False
mock_db.get_interview_count = lambda *a: 0
mock_db.abandon_interview = lambda *a: None
mock_db.get_interview = lambda *a: None
mock_db.SessionLocal = None
mock_db.engine = None
mock_db.connection_pool = None
mock_db.get_connection = lambda: None
mock_db.release_connection = lambda c: None
mock_db.DATABASE_URL = "mock://localhost"
mock_db.FREE_TIER_ENABLED = False

# Inject mock into sys.modules BEFORE any import
sys.modules["database.db"] = mock_db
sys.modules["database"] = types.ModuleType("database")
sys.modules["database"].db = mock_db

# ═══════════════════════════════════════════════
# AUTO-LOGIN — skip auth, go straight to dashboard
# ═══════════════════════════════════════════════
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = True
    st.session_state["user_name"] = "Demo User"
    st.session_state["user_email"] = "demo@pyspace.ai"

# Now import and render the dashboard
from dashboard.student_dashboard import student_dashboard
student_dashboard()
