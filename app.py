import streamlit as st
import requests
import json
import time
from urllib.parse import unquote
import os

# From config.py
from config import BACKEND_URL

# Import styles
from assets.interview_style import inject_interview_styles, render_interview_header

# Voice input import (do not remove)
from utils.speech_to_text import transcribe_audio
from utils.text_to_speech import speak

# Set page config
st.set_page_config(
    page_title="Interview Chat",
    page_icon="⏱️",
    layout="wide"
)

# STEP 1: READ URL PARAMS
# Save params to session state on first load and clear URL to hide sensitive info
if "url_params" not in st.session_state:
    st.session_state.url_params = st.query_params.to_dict()
    st.query_params.clear()

params = st.session_state.url_params

token = params.get("token")
session_id = params.get("session_id")
userid = params.get("userid", "0")

if not token or not session_id:
    st.error("Please start your interview from the portal.")
    st.markdown("[← Go to Portal](https://interviewflow-suite-one.vercel.app)")
    st.stop()

# 1. Call backend to verify session is valid
session_ended = False
try:
    verify_url = f"{BACKEND_URL}/interview/verify-session?session_id={session_id}&userid={userid}"
    verify_res = requests.get(verify_url, headers={"Authorization": f"Bearer {token}"}, timeout=60)
    
    try:
        res_data = verify_res.json()
    except json.JSONDecodeError:
        res_data = {}

    if verify_res.status_code != 200 or not res_data.get("success"):
        st.error("Invalid or unauthorized session.")
        st.stop()
        
    if res_data.get("status") == "ended":
        st.warning("This interview has already been completed.")
        st.markdown('<meta http-equiv="refresh" content="3; url=https://interviewflow-suite-one.vercel.app/analytics">', unsafe_allow_html=True)
        st.success("✅ Redirecting to your results...")
        st.stop()

except Exception as e:
    st.error(f"Security check failed: {str(e)}")
    st.stop()

# 2. Verify token is valid
try:
    me_url = f"{BACKEND_URL}/me"
    me_res = requests.get(me_url, headers={"Authorization": f"Bearer {token}"}, timeout=60)
    if me_res.status_code != 200:
        st.error("Session expired. Please login again.")
        st.markdown("[← Go to Portal](https://interviewflow-suite-one.vercel.app)")
        st.stop()
except Exception as e:
    st.error(f"Authentication check failed: {str(e)}")
    st.stop()

# STEP 2: INITIALIZE SESSION STATE (only once)
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.token = params.get("token")
    st.session_state.session_id = params.get("session_id", "0")
    st.session_state.userid = int(params.get("userid", 0))
    st.session_state.duration_minutes = int(params.get("duration", 15))
    st.session_state.total_questions = int(params.get("total_questions", 5))
    
    # Fetch questions and greeting from backend instead of URL params
    try:
        confirm_url = f"{BACKEND_URL}/api/interview/confirm-start"
        confirm_res = requests.post(
            confirm_url,
            json={
                "session_id": st.session_state.session_id,
                "userid": st.session_state.userid
            },
            headers={"Authorization": f"Bearer {st.session_state.token}"},
            timeout=15
        )
        if confirm_res.status_code == 200:
            confirm_data = confirm_res.json()
            st.session_state.questions_list = confirm_data.get("questions_list", [])
            st.session_state.ai_greeting = confirm_data.get("ai_greeting", "Hello!")
            st.session_state.conversation_history = confirm_data.get("conversation_history", [])
        else:
            # Fallback to URL params if API fails
            st.session_state.questions_list = json.loads(unquote(params.get("questions", "[]")))
            st.session_state.ai_greeting = unquote(params.get("ai_greeting", "Hello!"))
            st.session_state.conversation_history = json.loads(unquote(params.get("history", "[]")))
    except Exception as e:
        st.session_state.questions_list = json.loads(unquote(params.get("questions", "[]")))
        st.session_state.ai_greeting = unquote(params.get("ai_greeting", "Hello!"))
        st.session_state.conversation_history = json.loads(unquote(params.get("history", "[]")))

    # Enhance system prompt to sound more like a Senior Authority
    if st.session_state.conversation_history and st.session_state.conversation_history[0].get("role") == "system":
        if "Senior Authority" not in st.session_state.conversation_history[0]["content"]:
            st.session_state.conversation_history[0]["content"] += " You are a Senior Authority and Expert in this domain. Conduct the interview as a highly experienced industry veteran. Be highly professional, realistic, and evaluate the candidate strictly but constructively. Ask only one question at a time and wait for the user to answer."
        
    st.session_state.current_question_number = 1
    st.session_state.interview_active = True
    st.session_state.start_time = time.time()
    st.session_state.messages = [
        {"role": "assistant", "content": st.session_state.ai_greeting}
    ]
    st.session_state.animate_last = True
    st.session_state.audio_to_play = st.session_state.ai_greeting


# STEP 6: END INTERVIEW FUNCTION
def _call_end_interview():
    try:
        requests.post(
            f"{BACKEND_URL}/api/interview/end",
            json={
                "session_id": st.session_state.session_id,
                "userid": st.session_state.userid,
                "conversation_history": st.session_state.conversation_history
            },
            headers={"Authorization": f"Bearer {st.session_state.token}"},
            timeout=15
        )
    except:
        pass
# Handle manual end
if st.session_state.get("interview_complete", False):
    if st.session_state.interview_active:
        st.session_state.interview_active = False
        _call_end_interview()

# Call styles
inject_interview_styles()

# TIMER CALCULATION
elapsed = int(time.time() - st.session_state.start_time)
remaining = max(st.session_state.duration_minutes * 60 - elapsed, 0)
mins, secs = divmod(remaining, 60)

# Parse role from system prompt for header title
role_title = "AI Interview"
if st.session_state.get("conversation_history") and st.session_state.conversation_history[0].get("role") == "system":
    import re
    match = re.search(r"role of (.*?)\.", st.session_state.conversation_history[0]["content"], re.IGNORECASE)
    if match:
        role_title = match.group(1).title() + " Interview"

render_interview_header(
    title=role_title,
    q_num=st.session_state.current_question_number,
    total_q=st.session_state.total_questions,
    level="medium",
    timer_str=f"{mins:02d}:{secs:02d}",
    remaining=remaining
)

# PROGRESS BAR
st.progress(
    (st.session_state.current_question_number - 1) / st.session_state.total_questions,
    text=f"Question {st.session_state.current_question_number} of {st.session_state.total_questions}"
)

# CHAT MESSAGES
for i, msg in enumerate(st.session_state.messages):
    avatar = "assets/lisa_avatar.png" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        if i == len(st.session_state.messages) - 1 and msg["role"] == "assistant" and st.session_state.get("animate_last", False):
            # Play audio immediately before streaming text so they sync up
            if st.session_state.get("audio_to_play"):
                speak(st.session_state.audio_to_play)
                st.session_state.audio_to_play = None

            def stream_data():
                import time
                for word in msg["content"].split():
                    yield word + " "
                    time.sleep(0.04)
            st.write_stream(stream_data)
            st.session_state.animate_last = False
        else:
            st.write(msg["content"])

# INPUT AREA (only if interview_active is True)
if st.session_state.interview_active:
    # Callbacks for clearing inputs (avoids StreamlitAPIException)
    def on_send():
        val = st.session_state.get("answer_input", "").strip()
        if val:
            st.session_state.submit_clicked = True
            st.session_state.user_message = val
            st.session_state.answer_input = ""
            st.session_state.last_transcribed = ""

    def on_skip():
        st.session_state.skip_clicked = True
        st.session_state.answer_input = ""
        st.session_state.last_transcribed = ""

    # Process voice input from state
    if "voice_mic" in st.session_state and st.session_state.voice_mic:
        audio_bytes = st.session_state.voice_mic
        # Only transcribe if it's a new recording
        if audio_bytes != st.session_state.get("last_audio_bytes", b""):
            transcribed_text = transcribe_audio(audio_bytes)
            if transcribed_text:
                st.session_state.answer_input = transcribed_text
                st.session_state.last_audio_bytes = audio_bytes

    # Record answer above the input box (make it small)
    col_rec, _ = st.columns([3, 7])
    with col_rec:
        st.audio_input("Record Answer", key="voice_mic", label_visibility="collapsed")
        
    # Input box and buttons below
    col_input, col_actions = st.columns([8, 2])
    with col_input:
        st.text_area(
            "Type your answer or use voice...", 
            key="answer_input",
            label_visibility="collapsed",
            height=100
        )
        
    with col_actions:
        st.button("Send", type="primary", on_click=on_send, key="btn_send", use_container_width=True)
        st.button("⏭️ Skip", on_click=on_skip, key="btn_skip", use_container_width=True)

    # STEP 4: HANDLE ANSWER SUBMISSION
    send_clicked = st.session_state.get("submit_clicked", False)
    skip_clicked = st.session_state.get("skip_clicked", False)
    
    if send_clicked or skip_clicked:
        # Reset triggers
        st.session_state.submit_clicked = False
        st.session_state.skip_clicked = False
        
        user_input = st.session_state.get("user_message", "") if send_clicked else ""
        answer_text = user_input.strip() if user_input else ""
        is_skipped = True if skip_clicked else False

        if not is_skipped:
            st.session_state.messages.append({"role": "user", "content": answer_text})
            # Render user message immediately
            with st.chat_message("user", avatar="👤"):
                st.write(answer_text)

        with st.spinner("LISA is thinking..."):
            try:
                res = requests.post(
                    f"{BACKEND_URL}/api/interview/answer",
                    json={
                        "session_id": st.session_state.session_id,
                        "userid": st.session_state.userid,
                        "answer": answer_text,
                        "question_number": st.session_state.current_question_number,
                        "is_skipped": is_skipped,
                        "conversation_history": st.session_state.conversation_history
                    },
                    headers={"Authorization": f"Bearer {st.session_state.token}"},
                    timeout=30
                )
                
                if res.status_code == 200:
                    data = res.json()
                    
                    st.session_state.conversation_history = data.get("conversation_history", st.session_state.conversation_history)
                    st.session_state.current_question_number = data.get("question_number", st.session_state.current_question_number)
                    
                    if data.get("next_ai_message"):
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": data["next_ai_message"]
                        })
                        st.session_state.animate_last = True
                        st.session_state.audio_to_play = data["next_ai_message"]
                    
                    if data.get("interview_complete"):
                        st.session_state.interview_active = False
                        _call_end_interview()
                else:
                    st.error(f"API Error: {res.status_code} - {res.text}")
                    if not is_skipped:
                        st.session_state.messages.pop() # Remove user message so they can retry
                    
            except Exception as e:
                st.error(f"Connection error: {str(e)}")
                if not is_skipped:
                    st.session_state.messages.pop() # Remove user message so they can retry

        st.rerun()

# STEP 5: AUTO-END ON TIMER
if remaining <= 0 and st.session_state.interview_active:
    st.session_state.interview_active = False
    _call_end_interview()
    st.rerun()

# STEP 7: INTERVIEW COMPLETE SCREEN
if not st.session_state.interview_active:
    st.markdown('<meta http-equiv="refresh" content="3; url=https://interviewflow-suite-one.vercel.app/analytics">', unsafe_allow_html=True)
    st.success("✅ Interview complete! Redirecting to your results...")


