import os
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv

load_dotenv()

def _get_client():
    try:
        import streamlit as st
        key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        key = None
    if not key:
        key = os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=key)

MODEL = "gpt-4o-mini"

# ── LISA SYSTEM — warm, human, female, slightly challenging ──────────
LISA_SYSTEM = """You are LISA, a senior technical interviewer at a top tech company.
You are warm, professional, and genuinely encouraging — but also sharp and precise.
You speak in a natural, conversational female tone. You never sound robotic or stiff.
You care about helping candidates grow, but you never lower the bar.
You ask one focused question at a time. You never reveal scores during the interview.
Your language is clear, confident, and feels like it comes from a real person — not an AI."""


# ─────────────────────────────────────────────
# DETECT DOMAIN FROM RESUME (point 7)
# ─────────────────────────────────────────────
def detect_domain(resume: str) -> str:
    """Detect job domain from resume text for PDF report."""
    resume_lower = resume.lower()
    if any(w in resume_lower for w in ["software", "developer", "engineer", "python",
                                        "java", "react", "frontend", "backend", "devops",
                                        "machine learning", "data science", "cloud", "aws"]):
        return "Information Technology"
    if any(w in resume_lower for w in ["sales", "revenue", "crm", "business development",
                                        "account manager", "quota", "pipeline"]):
        return "Sales"
    if any(w in resume_lower for w in ["hr", "human resources", "recruitment", "talent",
                                        "payroll", "onboarding", "employee relations"]):
        return "Human Resources"
    if any(w in resume_lower for w in ["marketing", "seo", "campaign", "brand",
                                        "content", "social media", "digital marketing"]):
        return "Marketing"
    if any(w in resume_lower for w in ["finance", "accounting", "audit", "tax",
                                        "cfa", "balance sheet", "investment"]):
        return "Finance"
    if any(w in resume_lower for w in ["design", "ui", "ux", "figma", "adobe",
                                        "graphic", "creative", "illustrator"]):
        return "Design"
    if any(w in resume_lower for w in ["operations", "supply chain", "logistics",
                                        "procurement", "warehouse", "inventory"]):
        return "Operations"
    return "General"


# ─────────────────────────────────────────────
# QUESTION GENERATION — with cross-session dedup (point 9)
# ─────────────────────────────────────────────
def generate_question(
    level: str,
    resume: str,
    previous_answer: str = None,
    previous_score: float = None,
    asked_questions: list = None   # all questions ever asked to this user
) -> str:

    adaptive_instruction = ""
    if level == "adaptive" and previous_score is not None:
        if previous_score < 4:
            adaptive_instruction = "The candidate is struggling. Ask a simpler clarifying follow-up on the same concept — help them think through it step by step."
        elif previous_score > 7:
            adaptive_instruction = "Strong answer. Go deeper — push them to think about edge cases, system design, or real-world trade-offs."
        else:
            adaptive_instruction = "Decent answer with gaps. Probe a bit further — ask them to elaborate on the part they glossed over."

    avoid_block = ""
    if asked_questions:
        # Send last 12 to cover cross-session repeats
        avoid_list = "\n".join(f"- {q}" for q in asked_questions[-12:])
        avoid_block = f"""
IMPORTANT — These questions have already been asked. Do NOT repeat them or ask close variations:
{avoid_list}
"""

    messages = [{"role": "system", "content": LISA_SYSTEM}]

    if previous_answer:
        messages.append({"role": "assistant", "content": f"[Previous {level} question]"})
        messages.append({"role": "user", "content": previous_answer})

    prompt = f"""
Generate ONE {level.upper()} interview question for this candidate.
Return ONLY the question itself — no preamble, no numbering, no quotes, no emoji.
{adaptive_instruction}
{avoid_block}
Resume:
{resume[:3000]}
"""
    messages.append({"role": "user", "content": prompt})

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model       = MODEL,
            messages    = messages,
            temperature = 0.75,
            max_tokens  = 200
        )
        return response.choices[0].message.content.strip()
    except OpenAIError as e:
        print(f"[LISA] Question gen error: {e}")
        return "Walk me through a challenging project from your resume and what you learned from it."


# ─────────────────────────────────────────────
# ANSWER EVALUATION
# ─────────────────────────────────────────────
def evaluate_answer(question: str, user_answer: str) -> dict:

    prompt = f"""
You are evaluating a candidate's interview answer. Be fair but rigorous.

Question: {question}
Candidate's Answer: {user_answer}

Respond in EXACT format (no extra text):
SCORE: [0-10]
IDEAL: [Ideal answer in 2-4 clear sentences covering what should have been said]
FEEDBACK: [One specific, constructive improvement. Be direct but kind — like a mentor.]
"""
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model       = MODEL,
            messages    = [
                {"role": "system", "content": LISA_SYSTEM},
                {"role": "user",   "content": prompt}
            ],
            temperature = 0.3,
            max_tokens  = 500
        )
        return _parse_evaluation(response.choices[0].message.content.strip())
    except OpenAIError as e:
        print(f"[LISA] Eval error: {e}")
        return {"score": 0.0, "ideal_answer": "Unable to generate.", "feedback": "Please try again."}


def _parse_evaluation(raw: str) -> dict:
    result = {"score": 0.0, "ideal_answer": "", "feedback": ""}
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("SCORE:"):
            try:
                result["score"] = float(line.replace("SCORE:", "").strip())
            except ValueError:
                pass
        elif line.startswith("IDEAL:"):
            result["ideal_answer"] = line.replace("IDEAL:", "").strip()
        elif line.startswith("FEEDBACK:"):
            result["feedback"] = line.replace("FEEDBACK:", "").strip()
    return result


# ─────────────────────────────────────────────
# FULL SESSION FEEDBACK — motivational + actionable (points 5, 6, 8)
# ─────────────────────────────────────────────
def generate_session_feedback(qa_pairs: list[dict]) -> dict:
    """
    Returns rich feedback with LISA's human, warm tone.
    Includes communication phrases, specific gaps, and a real study plan.
    """

    summary = "\n\n".join([
        f"Q: {qa['question']}\nA: {qa['user_answer']}\nScore: {qa['score']}/10"
        for qa in qa_pairs
    ])

    avg_score = sum(q["score"] for q in qa_pairs) / len(qa_pairs) if qa_pairs else 0

    prompt = f"""
You are LISA, a warm and encouraging senior interviewer giving post-interview feedback.
Speak directly to the candidate in second person ("you"). Be human, motivating, and specific.
Average score: {avg_score:.1f}/10

Interview Transcript:
{summary}

Respond in EXACT format (no extra text, no markdown headers):

STRENGTHS: [2-3 specific things done well. Start with something genuinely positive and encouraging. Be warm and human — not robotic.]

IMPROVEMENTS: [2-3 specific knowledge gaps or weak areas. Be honest but kind. Say exactly what topic needs work and why it matters.]

STUDY_PLAN: [3-5 concrete topics to study with specific suggestions. Example: "Study Python decorators — practice writing one from scratch. Read about REST API design principles — try building a simple CRUD API this week."]

COMMUNICATION_TIPS: [3-5 professional phrases and communication habits that will make the candidate sound more confident and polished in real interviews. Example: "Instead of saying 'I think it works like...', say 'Based on my experience...'". Give real before/after examples.]

MOTIVATION: [2-3 sentences of genuine encouragement. Acknowledge where they are, validate their effort, and give them a clear, specific next step that builds confidence. Make them feel capable and energised — not patronised.]
"""

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model       = MODEL,
            messages    = [
                {"role": "system", "content": LISA_SYSTEM},
                {"role": "user",   "content": prompt}
            ],
            temperature = 0.6,
            max_tokens  = 900
        )
        return _parse_feedback(response.choices[0].message.content.strip())
    except OpenAIError as e:
        print(f"[LISA] Feedback error: {e}")
        return {
            "strengths": "Unable to generate.",
            "improvements": "Unable to generate.",
            "study_plan": "Unable to generate.",
            "communication_tips": "",
            "motivation": ""
        }


def _parse_feedback(raw: str) -> dict:
    result = {
        "strengths": "",
        "improvements": "",
        "study_plan": "",
        "communication_tips": "",
        "motivation": ""
    }
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("STRENGTHS:"):
            result["strengths"] = line.replace("STRENGTHS:", "").strip()
        elif line.startswith("IMPROVEMENTS:"):
            result["improvements"] = line.replace("IMPROVEMENTS:", "").strip()
        elif line.startswith("STUDY_PLAN:"):
            result["study_plan"] = line.replace("STUDY_PLAN:", "").strip()
        elif line.startswith("COMMUNICATION_TIPS:"):
            result["communication_tips"] = line.replace("COMMUNICATION_TIPS:", "").strip()
        elif line.startswith("MOTIVATION:"):
            result["motivation"] = line.replace("MOTIVATION:", "").strip()
    return result


# import os
# from openai import OpenAI, OpenAIError
# from dotenv import load_dotenv

# load_dotenv()

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# if not OPENAI_API_KEY:
#     raise ValueError("OPENAI_API_KEY not found in .env")

# client = OpenAI(api_key=OPENAI_API_KEY)
# MODEL = "gpt-4o-mini"

# LISA_SYSTEM = "You are LISA (Learning Intelligent Simulation Assistant), a professional and encouraging AI technical interviewer. Be concise and clear."


# # ─────────────────────────────────────────────
# # QUESTION GENERATION
# # ─────────────────────────────────────────────
# def generate_question(
#     level: str,
#     resume: str,
#     previous_answer: str = None,
#     previous_score: float = None,
#     asked_questions: list = None
# ) -> str:
#     """
#     Generate one interview question based on level, resume, and previous performance.
#     asked_questions: list of recently asked questions to prevent duplicates.
#     """

#     # Adaptive branching based on score
#     adaptive_instruction = ""
#     if level == "adaptive" and previous_score is not None:
#         if previous_score < 4:
#             adaptive_instruction = "The candidate struggled (score < 4/10). Ask an easier clarifying follow-up on the same topic."
#         elif previous_score > 7:
#             adaptive_instruction = "The candidate answered well (score > 7/10). Go deeper — ask an advanced follow-up that tests system-level or edge-case understanding."
#         else:
#             adaptive_instruction = "The candidate gave a decent answer (score 4–7/10). Ask a follow-up that probes their understanding a bit further."

#     # Build do-not-repeat instruction
#     avoid_block = ""
#     if asked_questions:
#         avoid_list = "\n".join(f"- {q}" for q in asked_questions[-8:])
#         avoid_block = f"""
# IMPORTANT — Do NOT ask any of these already-asked questions or close variations:
# {avoid_list}
# """

#     messages = [{"role": "system", "content": LISA_SYSTEM}]

#     if previous_answer:
#         messages.append({"role": "assistant", "content": f"[Previous question at {level} level]"})
#         messages.append({"role": "user", "content": previous_answer})

#     prompt = f"""
# Generate ONE interview question. Return ONLY the question — no preamble, no numbering, no quotes.

# Difficulty: {level.upper()}
# {adaptive_instruction}
# {avoid_block}
# Candidate Resume:
# {resume}
# """
#     messages.append({"role": "user", "content": prompt})

#     try:
#         response = client.chat.completions.create(
#             model=MODEL,
#             messages=messages,
#             temperature=0.7,
#             max_tokens=200
#         )
#         return response.choices[0].message.content.strip()

#     except OpenAIError as e:
#         # Graceful fallback so interview doesn't crash
#         print(f"[LISA] OpenAI error generating question: {e}")
#         return f"Tell me about your experience with the technologies listed on your resume."


# # ─────────────────────────────────────────────
# # ANSWER EVALUATION
# # ─────────────────────────────────────────────
# def evaluate_answer(question: str, user_answer: str) -> dict:
#     """
#     Evaluate a candidate's answer.

#     Returns:
#         {
#             "score": float (0–10),
#             "ideal_answer": str,
#             "feedback": str
#         }
#     """

#     prompt = f"""
# You are evaluating a technical interview answer.

# Question:
# {question}

# Candidate's Answer:
# {user_answer}

# Respond in this EXACT format (no extra text):
# SCORE: [0-10]
# IDEAL: [A concise ideal answer in 2-4 sentences]
# FEEDBACK: [One specific, actionable improvement tip]
# """

#     try:
#         response = client.chat.completions.create(
#             model=MODEL,
#             messages=[
#                 {"role": "system", "content": LISA_SYSTEM},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.3,  # Lower temp for consistent scoring
#             max_tokens=400
#         )

#         content = response.choices[0].message.content.strip()
#         return _parse_evaluation(content)

#     except OpenAIError as e:
#         print(f"[LISA] OpenAI error evaluating answer: {e}")
#         return {
#             "score": 0.0,
#             "ideal_answer": "Unable to generate at this time.",
#             "feedback": "Please try again."
#         }


# def _parse_evaluation(raw: str) -> dict:
#     """Parse the structured evaluation response from GPT."""
#     result = {"score": 0.0, "ideal_answer": "", "feedback": ""}

#     for line in raw.splitlines():
#         line = line.strip()
#         if line.startswith("SCORE:"):
#             try:
#                 result["score"] = float(line.replace("SCORE:", "").strip())
#             except ValueError:
#                 result["score"] = 0.0
#         elif line.startswith("IDEAL:"):
#             result["ideal_answer"] = line.replace("IDEAL:", "").strip()
#         elif line.startswith("FEEDBACK:"):
#             result["feedback"] = line.replace("FEEDBACK:", "").strip()

#     return result


# # ─────────────────────────────────────────────
# # FULL SESSION FEEDBACK (post-interview)
# # ─────────────────────────────────────────────
# def generate_session_feedback(qa_pairs: list[dict]) -> dict:
#     """
#     Generate an overall feedback summary after the interview.

#     Args:
#         qa_pairs: List of {"question": str, "user_answer": str, "score": float}

#     Returns:
#         {
#             "strengths": str,
#             "improvements": str,
#             "study_plan": str
#         }
#     """

#     summary = "\n\n".join([
#         f"Q: {qa['question']}\nA: {qa['user_answer']}\nScore: {qa['score']}/10"
#         for qa in qa_pairs
#     ])

#     prompt = f"""
# Based on this interview session, generate a feedback summary.

# Interview Transcript:
# {summary}

# Respond in EXACT format:
# STRENGTHS: [2-3 things the candidate did well]
# IMPROVEMENTS: [2-3 specific weaknesses or knowledge gaps]
# STUDY_PLAN: [3 concrete topics or resources to study]
# """

#     try:
#         response = client.chat.completions.create(
#             model=MODEL,
#             messages=[
#                 {"role": "system", "content": LISA_SYSTEM},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.5,
#             max_tokens=500
#         )
#         return _parse_feedback(response.choices[0].message.content.strip())

#     except OpenAIError as e:
#         print(f"[LISA] OpenAI error generating session feedback: {e}")
#         return {
#             "strengths": "Unable to generate.",
#             "improvements": "Unable to generate.",
#             "study_plan": "Unable to generate."
#         }


# def _parse_feedback(raw: str) -> dict:
#     result = {"strengths": "", "improvements": "", "study_plan": ""}

#     for line in raw.splitlines():
#         line = line.strip()
#         if line.startswith("STRENGTHS:"):
#             result["strengths"] = line.replace("STRENGTHS:", "").strip()
#         elif line.startswith("IMPROVEMENTS:"):
#             result["improvements"] = line.replace("IMPROVEMENTS:", "").strip()
#         elif line.startswith("STUDY_PLAN:"):
#             result["study_plan"] = line.replace("STUDY_PLAN:", "").strip()

#     return result

# # import os
# # from openai import OpenAI, OpenAIError
# # from dotenv import load_dotenv

# # load_dotenv()

# # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# # if not OPENAI_API_KEY:
# #     raise ValueError("OPENAI_API_KEY not found in .env")

# # client = OpenAI(api_key=OPENAI_API_KEY)
# # MODEL = "gpt-4o-mini"

# # LISA_SYSTEM = "You are LISA (Learning Intelligent Simulation Assistant), a professional and encouraging AI technical interviewer. Be concise and clear."


# # # ─────────────────────────────────────────────
# # # QUESTION GENERATION
# # # ─────────────────────────────────────────────
# # def generate_question(level: str, resume: str, previous_answer: str = None, previous_score: float = None) -> str:
# #     """
# #     Generate one interview question based on level, resume, and previous performance.

# #     Args:
# #         level:           "easy" | "medium" | "hard" | "adaptive"
# #         resume:          Candidate's resume text
# #         previous_answer: The candidate's last answer (optional)
# #         previous_score:  Score for the last answer 0–10 (optional)
# #                          Used for adaptive branching:
# #                          < 4 → easier follow-up
# #                          4–7 → same level
# #                          > 7 → harder follow-up
# #     """

# #     # Adaptive branching based on score, not vague LLM judgment
# #     adaptive_instruction = ""
# #     if level == "adaptive" and previous_score is not None:
# #         if previous_score < 4:
# #             adaptive_instruction = "The candidate struggled (score < 4/10). Ask an easier clarifying follow-up on the same topic."
# #         elif previous_score > 7:
# #             adaptive_instruction = "The candidate answered well (score > 7/10). Go deeper — ask an advanced follow-up that tests system-level or edge-case understanding."
# #         else:
# #             adaptive_instruction = "The candidate gave a decent answer (score 4–7/10). Ask a follow-up that probes their understanding a bit further."

# #     messages = [
# #         {"role": "system", "content": LISA_SYSTEM},
# #     ]

# #     # Inject conversation history if we have it
# #     if previous_answer:
# #         messages.append({"role": "assistant", "content": f"[Previous question was asked at {level} level]"})
# #         messages.append({"role": "user", "content": previous_answer})

# #     prompt = f"""
# # Generate ONE interview question. Return only the question text — no preamble, no numbering.

# # Difficulty level: {level.upper()}
# # {adaptive_instruction}

# # Candidate Resume:
# # {resume}
# # """
# #     messages.append({"role": "user", "content": prompt})

# #     try:
# #         response = client.chat.completions.create(
# #             model=MODEL,
# #             messages=messages,
# #             temperature=0.7,
# #             max_tokens=200
# #         )
# #         return response.choices[0].message.content.strip()

# #     except OpenAIError as e:
# #         # Graceful fallback so interview doesn't crash
# #         print(f"[LISA] OpenAI error generating question: {e}")
# #         return f"Tell me about your experience with the technologies listed on your resume."


# # # ─────────────────────────────────────────────
# # # ANSWER EVALUATION
# # # ─────────────────────────────────────────────
# # def evaluate_answer(question: str, user_answer: str) -> dict:
# #     """
# #     Evaluate a candidate's answer.

# #     Returns:
# #         {
# #             "score": float (0–10),
# #             "ideal_answer": str,
# #             "feedback": str
# #         }
# #     """

# #     prompt = f"""
# # You are evaluating a technical interview answer.

# # Question:
# # {question}

# # Candidate's Answer:
# # {user_answer}

# # Respond in this EXACT format (no extra text):
# # SCORE: [0-10]
# # IDEAL: [A concise ideal answer in 2-4 sentences]
# # FEEDBACK: [One specific, actionable improvement tip]
# # """

# #     try:
# #         response = client.chat.completions.create(
# #             model=MODEL,
# #             messages=[
# #                 {"role": "system", "content": LISA_SYSTEM},
# #                 {"role": "user", "content": prompt}
# #             ],
# #             temperature=0.3,  # Lower temp for consistent scoring
# #             max_tokens=400
# #         )

# #         content = response.choices[0].message.content.strip()
# #         return _parse_evaluation(content)

# #     except OpenAIError as e:
# #         print(f"[LISA] OpenAI error evaluating answer: {e}")
# #         return {
# #             "score": 0.0,
# #             "ideal_answer": "Unable to generate at this time.",
# #             "feedback": "Please try again."
# #         }


# # def _parse_evaluation(raw: str) -> dict:
# #     """Parse the structured evaluation response from GPT."""
# #     result = {"score": 0.0, "ideal_answer": "", "feedback": ""}

# #     for line in raw.splitlines():
# #         line = line.strip()
# #         if line.startswith("SCORE:"):
# #             try:
# #                 result["score"] = float(line.replace("SCORE:", "").strip())
# #             except ValueError:
# #                 result["score"] = 0.0
# #         elif line.startswith("IDEAL:"):
# #             result["ideal_answer"] = line.replace("IDEAL:", "").strip()
# #         elif line.startswith("FEEDBACK:"):
# #             result["feedback"] = line.replace("FEEDBACK:", "").strip()

# #     return result


# # # ─────────────────────────────────────────────
# # # FULL SESSION FEEDBACK (post-interview)
# # # ─────────────────────────────────────────────
# # def generate_session_feedback(qa_pairs: list[dict]) -> dict:
# #     """
# #     Generate an overall feedback summary after the interview.

# #     Args:
# #         qa_pairs: List of {"question": str, "user_answer": str, "score": float}

# #     Returns:
# #         {
# #             "strengths": str,
# #             "improvements": str,
# #             "study_plan": str
# #         }
# #     """

# #     summary = "\n\n".join([
# #         f"Q: {qa['question']}\nA: {qa['user_answer']}\nScore: {qa['score']}/10"
# #         for qa in qa_pairs
# #     ])

# #     prompt = f"""
# # Based on this interview session, generate a feedback summary.

# # Interview Transcript:
# # {summary}

# # Respond in EXACT format:
# # STRENGTHS: [2-3 things the candidate did well]
# # IMPROVEMENTS: [2-3 specific weaknesses or knowledge gaps]
# # STUDY_PLAN: [3 concrete topics or resources to study]
# # """

# #     try:
# #         response = client.chat.completions.create(
# #             model=MODEL,
# #             messages=[
# #                 {"role": "system", "content": LISA_SYSTEM},
# #                 {"role": "user", "content": prompt}
# #             ],
# #             temperature=0.5,
# #             max_tokens=500
# #         )
# #         return _parse_feedback(response.choices[0].message.content.strip())

# #     except OpenAIError as e:
# #         print(f"[LISA] OpenAI error generating session feedback: {e}")
# #         return {
# #             "strengths": "Unable to generate.",
# #             "improvements": "Unable to generate.",
# #             "study_plan": "Unable to generate."
# #         }


# # def _parse_feedback(raw: str) -> dict:
# #     result = {"strengths": "", "improvements": "", "study_plan": ""}

# #     for line in raw.splitlines():
# #         line = line.strip()
# #         if line.startswith("STRENGTHS:"):
# #             result["strengths"] = line.replace("STRENGTHS:", "").strip()
# #         elif line.startswith("IMPROVEMENTS:"):
# #             result["improvements"] = line.replace("IMPROVEMENTS:", "").strip()
# #         elif line.startswith("STUDY_PLAN:"):
# #             result["study_plan"] = line.replace("STUDY_PLAN:", "").strip()

# #     return result

 
