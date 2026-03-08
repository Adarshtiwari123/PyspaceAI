import os
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env")

client = OpenAI(api_key=OPENAI_API_KEY)
MODEL = "gpt-4o-mini"

LISA_SYSTEM = "You are LISA (Learning Intelligent Simulation Assistant), a professional and encouraging AI technical interviewer. Be concise and clear."


# ─────────────────────────────────────────────
# QUESTION GENERATION
# ─────────────────────────────────────────────
def generate_question(
    level: str,
    resume: str,
    previous_answer: str = None,
    previous_score: float = None,
    asked_questions: list = None
) -> str:
    """
    Generate one interview question based on level, resume, and previous performance.
    asked_questions: list of recently asked questions to prevent duplicates.
    """

    # Adaptive branching based on score
    adaptive_instruction = ""
    if level == "adaptive" and previous_score is not None:
        if previous_score < 4:
            adaptive_instruction = "The candidate struggled (score < 4/10). Ask an easier clarifying follow-up on the same topic."
        elif previous_score > 7:
            adaptive_instruction = "The candidate answered well (score > 7/10). Go deeper — ask an advanced follow-up that tests system-level or edge-case understanding."
        else:
            adaptive_instruction = "The candidate gave a decent answer (score 4–7/10). Ask a follow-up that probes their understanding a bit further."

    # Build do-not-repeat instruction
    avoid_block = ""
    if asked_questions:
        avoid_list = "\n".join(f"- {q}" for q in asked_questions[-8:])
        avoid_block = f"""
IMPORTANT — Do NOT ask any of these already-asked questions or close variations:
{avoid_list}
"""

    messages = [{"role": "system", "content": LISA_SYSTEM}]

    if previous_answer:
        messages.append({"role": "assistant", "content": f"[Previous question at {level} level]"})
        messages.append({"role": "user", "content": previous_answer})

    prompt = f"""
Generate ONE interview question. Return ONLY the question — no preamble, no numbering, no quotes.

Difficulty: {level.upper()}
{adaptive_instruction}
{avoid_block}
Candidate Resume:
{resume}
"""
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()

    except OpenAIError as e:
        # Graceful fallback so interview doesn't crash
        print(f"[LISA] OpenAI error generating question: {e}")
        return f"Tell me about your experience with the technologies listed on your resume."


# ─────────────────────────────────────────────
# ANSWER EVALUATION
# ─────────────────────────────────────────────
def evaluate_answer(question: str, user_answer: str) -> dict:
    """
    Evaluate a candidate's answer.

    Returns:
        {
            "score": float (0–10),
            "ideal_answer": str,
            "feedback": str
        }
    """

    prompt = f"""
You are evaluating a technical interview answer.

Question:
{question}

Candidate's Answer:
{user_answer}

Respond in this EXACT format (no extra text):
SCORE: [0-10]
IDEAL: [A concise ideal answer in 2-4 sentences]
FEEDBACK: [One specific, actionable improvement tip]
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": LISA_SYSTEM},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temp for consistent scoring
            max_tokens=400
        )

        content = response.choices[0].message.content.strip()
        return _parse_evaluation(content)

    except OpenAIError as e:
        print(f"[LISA] OpenAI error evaluating answer: {e}")
        return {
            "score": 0.0,
            "ideal_answer": "Unable to generate at this time.",
            "feedback": "Please try again."
        }


def _parse_evaluation(raw: str) -> dict:
    """Parse the structured evaluation response from GPT."""
    result = {"score": 0.0, "ideal_answer": "", "feedback": ""}

    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("SCORE:"):
            try:
                result["score"] = float(line.replace("SCORE:", "").strip())
            except ValueError:
                result["score"] = 0.0
        elif line.startswith("IDEAL:"):
            result["ideal_answer"] = line.replace("IDEAL:", "").strip()
        elif line.startswith("FEEDBACK:"):
            result["feedback"] = line.replace("FEEDBACK:", "").strip()

    return result


# ─────────────────────────────────────────────
# FULL SESSION FEEDBACK (post-interview)
# ─────────────────────────────────────────────
def generate_session_feedback(qa_pairs: list[dict]) -> dict:
    """
    Generate an overall feedback summary after the interview.

    Args:
        qa_pairs: List of {"question": str, "user_answer": str, "score": float}

    Returns:
        {
            "strengths": str,
            "improvements": str,
            "study_plan": str
        }
    """

    summary = "\n\n".join([
        f"Q: {qa['question']}\nA: {qa['user_answer']}\nScore: {qa['score']}/10"
        for qa in qa_pairs
    ])

    prompt = f"""
Based on this interview session, generate a feedback summary.

Interview Transcript:
{summary}

Respond in EXACT format:
STRENGTHS: [2-3 things the candidate did well]
IMPROVEMENTS: [2-3 specific weaknesses or knowledge gaps]
STUDY_PLAN: [3 concrete topics or resources to study]
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": LISA_SYSTEM},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )
        return _parse_feedback(response.choices[0].message.content.strip())

    except OpenAIError as e:
        print(f"[LISA] OpenAI error generating session feedback: {e}")
        return {
            "strengths": "Unable to generate.",
            "improvements": "Unable to generate.",
            "study_plan": "Unable to generate."
        }


def _parse_feedback(raw: str) -> dict:
    result = {"strengths": "", "improvements": "", "study_plan": ""}

    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("STRENGTHS:"):
            result["strengths"] = line.replace("STRENGTHS:", "").strip()
        elif line.startswith("IMPROVEMENTS:"):
            result["improvements"] = line.replace("IMPROVEMENTS:", "").strip()
        elif line.startswith("STUDY_PLAN:"):
            result["study_plan"] = line.replace("STUDY_PLAN:", "").strip()

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
# def generate_question(level: str, resume: str, previous_answer: str = None, previous_score: float = None) -> str:
#     """
#     Generate one interview question based on level, resume, and previous performance.

#     Args:
#         level:           "easy" | "medium" | "hard" | "adaptive"
#         resume:          Candidate's resume text
#         previous_answer: The candidate's last answer (optional)
#         previous_score:  Score for the last answer 0–10 (optional)
#                          Used for adaptive branching:
#                          < 4 → easier follow-up
#                          4–7 → same level
#                          > 7 → harder follow-up
#     """

#     # Adaptive branching based on score, not vague LLM judgment
#     adaptive_instruction = ""
#     if level == "adaptive" and previous_score is not None:
#         if previous_score < 4:
#             adaptive_instruction = "The candidate struggled (score < 4/10). Ask an easier clarifying follow-up on the same topic."
#         elif previous_score > 7:
#             adaptive_instruction = "The candidate answered well (score > 7/10). Go deeper — ask an advanced follow-up that tests system-level or edge-case understanding."
#         else:
#             adaptive_instruction = "The candidate gave a decent answer (score 4–7/10). Ask a follow-up that probes their understanding a bit further."

#     messages = [
#         {"role": "system", "content": LISA_SYSTEM},
#     ]

#     # Inject conversation history if we have it
#     if previous_answer:
#         messages.append({"role": "assistant", "content": f"[Previous question was asked at {level} level]"})
#         messages.append({"role": "user", "content": previous_answer})

#     prompt = f"""
# Generate ONE interview question. Return only the question text — no preamble, no numbering.

# Difficulty level: {level.upper()}
# {adaptive_instruction}

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

 
