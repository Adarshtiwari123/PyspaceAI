import streamlit as st
import requests
import json
import time
from urllib.parse import unquote
import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

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

import base64

session_id_param = params.get("session_id")
token_param = params.get("token")
token = None
userid = "0"
real_session_id = "0"
duration = 10
total_questions = 5
questions_list = []
ai_greeting = "Hello! I am your AI interviewer."
conversation_history = []

if session_id_param:
    jwt_to_decode = None
    
    # If session_id is a simple integer, we need to call launch-and-confirm to generate the questions
    if "." not in session_id_param and token_param:
        try:
            # Decode token_param to get userid
            token_payload_b64 = token_param.split(".")[1]
            token_payload_b64 += "=" * ((4 - len(token_payload_b64) % 4) % 4)
            token_payload = json.loads(base64.urlsafe_b64decode(token_payload_b64).decode("utf-8"))
            userid = str(token_payload.get("userid", "0"))
            token = token_param
            
            # Call launch-and-confirm
            launch_url = f"{BACKEND_URL}/interview/launch-and-confirm"
            launch_res = requests.post(
                launch_url,
                json={"session_id": int(session_id_param), "userid": int(userid)},
                headers={"Authorization": f"Bearer {token}"},
                timeout=30
            )
            
            if launch_res.status_code == 200:
                launch_data = launch_res.json()
                pyspace_url = launch_data.get("Pyspace_interview_url", "")
                if "session_id=" in pyspace_url:
                    jwt_to_decode = pyspace_url.split("session_id=")[1].split("&")[0]
                else:
                    st.error("Error: Pyspace_interview_url from backend did not contain a session_id!")
                    st.stop()
            else:
                st.error(f"Backend API Error: launch-and-confirm returned status {launch_res.status_code}. Response: {launch_res.text}")
                st.stop()
        except Exception as e:
            st.error(f"Failed to launch and confirm session: {str(e)}")
            st.stop()
    elif "." in session_id_param:
        # It's already the giant JWT
        jwt_to_decode = session_id_param

    # Now decode the giant JWT
    if jwt_to_decode:
        try:
            payload_b64 = jwt_to_decode.split(".")[1]
            payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64).decode("utf-8")
            
            # The backend's launch-and-confirm API sometimes generates invalid JSON escape sequences
            # like "\2014" instead of "\u2014" for em-dashes. This crashes json.loads().
            # We fix this by converting invalid numeric escapes to \u escapes.
            import re
            payload_json = re.sub(r'\\(?=[0-9]{4})', r'\\u', payload_json)
            
            payload = json.loads(payload_json)
            
            token = payload.get("token", token_param)
            userid = str(payload.get("userid", userid))
            real_session_id = payload.get("session_id", session_id_param)
            duration = payload.get("duration_minutes", 10)
            total_questions = payload.get("total_questions", 5)
            
            # Replace current question fetching logic with API call
            questions_list = []
            try:
                sq_url = f"{BACKEND_URL}/interview/session-questions/{real_session_id}"
                sq_res = requests.get(sq_url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
                if sq_res.status_code == 200:
                    sq_data = sq_res.json()
                    # Determine where the list is
                    raw_list = []
                    if isinstance(sq_data, list):
                        raw_list = sq_data
                    elif isinstance(sq_data, dict):
                        raw_list = sq_data.get("questions", sq_data.get("session_questions", sq_data.get("questions_list", [])))
                    
                    # Sort questions to use them in order (question_order 1 to 5)
                    if raw_list:
                        raw_list.sort(key=lambda x: x.get("question_order", 0) if isinstance(x, dict) else 0)
                        questions_list = raw_list
            except Exception as e:
                print(f"Failed to fetch session questions: {e}")
                
            ai_greeting = payload.get("ai_greeting", "Hello! I am your AI interviewer.")
            conversation_history = payload.get("history", payload.get("conversation_history", []))
        except Exception as e:
            st.error(f"Critical Error: Failed to parse the backend session data. Your backend generated invalid JSON! Error: {str(e)}")
            st.stop()

if not token or not session_id_param:
    st.error("Please start your interview from the portal.")
    st.markdown("[← Go to Portal](https://interviewflow-suite-one.vercel.app)")
    st.stop()

# Get Session Summary for accurate info directly from Database as fallback
session_summary = {}
try:
    # Use verify-session which exists in the backend and accepts the encoded session_id_param
    summary_url = f"{BACKEND_URL}/interview/verify-session?session_id={session_id_param}&userid={userid}"
    summary_res = requests.get(summary_url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
    if summary_res.status_code == 200:
        session_summary = summary_res.json()
except Exception as e:
    pass

# STEP 2: INITIALIZE SESSION STATE (only once)
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.token = token
    st.session_state.session_id = real_session_id
    st.session_state.userid = int(userid)
    
    # Priority: JWT payload -> Session Summary API -> Default 10
    dur = duration if (duration != 10) else session_summary.get("duration_minutes", 10)
    st.session_state.duration_minutes = int(dur)
    
    t_qs = total_questions if (total_questions != 5) else session_summary.get("total_questions", 5)
    st.session_state.total_questions = int(len(questions_list)) if questions_list else int(t_qs)
    st.session_state.questions_list = questions_list
    
    # Priority: JWT payload -> Session Summary API -> Default greeting
    final_greeting = ai_greeting if (ai_greeting != "Hello! I am your AI interviewer.") else session_summary.get("ai_greeting", "Hello! I am your AI interviewer.")
    
    # NEW FIX: If greeting is generic, try to extract the actual personalized first question
    if final_greeting == "Hello! I am your AI interviewer.":
        if questions_list and isinstance(questions_list[0], dict):
            first_q = questions_list[0].get("question", questions_list[0].get("question_text", ""))
            if first_q:
                final_greeting = first_q
                
        # If still generic, check conversation history for the first assistant message
        if final_greeting == "Hello! I am your AI interviewer." and conversation_history:
            for msg in conversation_history:
                if msg.get("role") == "assistant":
                    final_greeting = msg.get("content", final_greeting)
                    break

    st.session_state.ai_greeting = final_greeting
    
    st.session_state.topic = session_summary.get("topic", "")
    st.session_state.role_title = session_summary.get("role", "AI Interview")
    
    st.session_state.conversation_history = conversation_history
        
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
def handle_manual_end():
    st.session_state.interview_complete = True
    if st.session_state.get("interview_active", True):
        st.session_state.interview_active = False
        _call_end_interview()

# Handle manual end triggered by state
if st.session_state.get("interview_complete", False) or st.session_state.get("end_btn_header", False):
    handle_manual_end()

# Add Dark Mode Toggle
col_t1, col_t2 = st.columns([8, 2])
with col_t2:
    is_dark = st.toggle("🌙 Dark Mode", value=True)

# Call styles
inject_interview_styles(is_dark)




# TIMER CALCULATION
elapsed = int(time.time() - st.session_state.start_time)
remaining = max(st.session_state.duration_minutes * 60 - elapsed, 0)
mins, secs = divmod(remaining, 60)

# Extract user's first name from JWT token or fallback to API parsing
user_first_name = "User"
if st.session_state.get("token"):
    try:
        token_payload_b64 = st.session_state.token.split(".")[1]
        token_payload_b64 += "=" * ((4 - len(token_payload_b64) % 4) % 4)
        token_payload = json.loads(base64.urlsafe_b64decode(token_payload_b64).decode("utf-8"))
        if "sub" in token_payload:
            user_first_name = token_payload["sub"].title()
    except:
        pass

if user_first_name == "User" and st.session_state.ai_greeting and "Hello " in st.session_state.ai_greeting:
    try:
        user_first_name = st.session_state.ai_greeting.split("Hello ")[1].split("!")[0].title()
    except:
        pass

# Parse role from system prompt for header title
role_title = "AI Interview"
if st.session_state.get("conversation_history") and st.session_state.conversation_history[0].get("role") == "system":
    import re
    match = re.search(r"role of (.*?)\.", st.session_state.conversation_history[0]["content"], re.IGNORECASE)
    if match:
        role_title = match.group(1).title() + " Interview"
    else:
        # Fallback to parsing from ai_greeting if possible
        if "Welcome to your " in st.session_state.ai_greeting:
            try:
                role_title = st.session_state.ai_greeting.split("Welcome to your ")[1].split(" interview")[0].title() + " Interview"
            except:
                pass

# Use the actual level from the session summary
difficulty_level = st.session_state.get("level", "Medium")

render_interview_header(
    title=role_title,
    q_num=st.session_state.current_question_number,
    total_q=st.session_state.total_questions,
    level=difficulty_level,
    timer_str=f"{mins:02d}:{secs:02d}",
    remaining=remaining,
    user_name=user_first_name,
    on_end_callback=handle_manual_end
)

# CHAT MESSAGES
for i, msg in enumerate(st.session_state.messages):
    is_assistant = msg["role"] == "assistant"
    role_str = "assistant" if is_assistant else "user"
    
    with st.chat_message(role_str, avatar=None):
        # Inject hidden span for CSS targeting
        st.markdown(f'<span class="chat-role-{role_str}"></span>', unsafe_allow_html=True)
        
        if i == len(st.session_state.messages) - 1 and is_assistant and st.session_state.get("animate_last", False):
            # Play audio immediately before streaming text so they sync up
            if st.session_state.get("audio_to_play"):
                speak(st.session_state.audio_to_play)
                st.session_state.audio_to_play = None

            # Apply bold to highlight project names
            import re
            content = msg["content"]
            content = re.sub(r'(worked on )(.*?)( — )', r'\1**\2**\3', content)

            def stream_data():
                for word in content.split():
                    yield word + " "
            st.write_stream(stream_data)
            st.session_state.animate_last = False
            
            if st.session_state.get("pending_end_interview", False):
                time.sleep(8)
                st.session_state.interview_active = False
                st.session_state.pending_end_interview = False
                _call_end_interview()
                st.rerun()
        else:
            # Apply bold for past messages too
            import re
            content = msg["content"]
            if is_assistant:
                content = re.sub(r'(worked on )(.*?)( — )', r'\1**\2**\3', content)
            st.write(content)

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

    # Fixed Bottom Input Container
    with st.container():
        st.markdown('<div class="fixed-bottom-input"></div>', unsafe_allow_html=True)
        
        # 3 columns: Mic, Input Box, Buttons
        col_mic, col_input, col_actions = st.columns([2, 7, 1.5])
        
        with col_mic:
            st.audio_input("Record", key="voice_mic", label_visibility="collapsed")
            
        with col_input:
            st.text_area(
                "Type your answer or use voice...", 
                key="answer_input",
                label_visibility="collapsed",
                height=68
            )
            
        with col_actions:
            st.button("Send", type="primary", on_click=on_send, key="btn_send", use_container_width=True)
            st.button("Skip", on_click=on_skip, key="btn_skip", use_container_width=True)

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
            with st.chat_message("user", avatar=None):
                st.markdown('<span class="chat-role-user"></span>', unsafe_allow_html=True)
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
                    
                    if data.get("interview_complete") or st.session_state.current_question_number > st.session_state.total_questions:
                        st.session_state.pending_end_interview = True
                        st.session_state.interview_active = False
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
# (Removed to allow interview to continue beyond the time limit)
# The timer now serves as a visual indicator only.

# STEP 7: INTERVIEW COMPLETE SCREEN
if not st.session_state.interview_active:
    st.markdown('<meta http-equiv="refresh" content="120; url=https://interviewflow-suite-one.vercel.app/analytics">', unsafe_allow_html=True)
    st.success("✅ Interview complete! Your evaluation is ready. You will be redirected shortly.")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.spinner("Preparing your detailed PDF report..."):
            for attempt in range(2):
                try:
                    report_url = f"{BACKEND_URL}/api/interview/generate-report?session_id={st.session_state.session_id}&userid={st.session_state.userid}"
                    report_res = requests.get(report_url, headers={"Authorization": f"Bearer {st.session_state.token}"}, timeout=90)
                    if report_res.status_code == 200:
                        st.download_button(
                            label="📄 Download Detailed PDF Report",
                            data=report_res.content,
                            file_name="Interview_Evaluation_Report.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            type="primary"
                        )
                        break
                    else:
                        if attempt == 1:
                            try:
                                err_data = report_res.json()
                                err_detail = err_data.get("detail", "Failed to fetch the PDF report.")
                            except Exception:
                                err_detail = "Failed to fetch the PDF report."
                            st.error(f"Error: {err_detail}")
                        else:
                            time.sleep(2)
                except Exception as e:
                    if attempt == 1:
                        st.error(f"Connection error while fetching the report: {str(e)}")
                    else:
                        time.sleep(2)

