from config import SCORE_WEAK, SCORE_STRONG


# ─────────────────────────────────────────────
# ADAPTIVE TRIGGER CHECK
# Called after every medium and hard question
# ─────────────────────────────────────────────

def should_trigger_adaptive(level: str, score: float) -> tuple[bool, str]:
    """
    Decide whether to fire an inline adaptive question.

    Returns:
        (True, "easier")  — medium question scored weak  → simplify
        (True, "deeper")  — hard question scored strong  → go deeper
        (False, "")       — no adaptive needed
    """
    if level == "medium" and score < SCORE_WEAK:
        return True, "easier"

    if level == "hard" and score > SCORE_STRONG:
        return True, "deeper"

    return False, ""


# ─────────────────────────────────────────────
# PER-QUESTION SCORE LABEL
# ─────────────────────────────────────────────

def score_label(score: float) -> str:
    """Convert numeric score to human-readable label for the report."""
    if score >= 8.5:
        return "Excellent"
    elif score >= 7.0:
        return "Good"
    elif score >= 5.0:
        return "Average"
    elif score >= 3.0:
        return "Needs Improvement"
    else:
        return "Poor"


# ─────────────────────────────────────────────
# TOTAL SCORE CALCULATION
# Weighted: hard questions count more than easy
# ─────────────────────────────────────────────

LEVEL_WEIGHTS = {
    "easy":     0.5,
    "medium":   1.0,
    "hard":     1.5,
    "adaptive": 1.0,   # adaptive inherits weight of its parent level
}

def calculate_total_score(questions: list[dict]) -> float:
    """
    Calculate weighted total score across all questions.

    Args:
        questions: list of {"difficulty_level": str, "score": float}

    Returns:
        Final score out of 10.0 (rounded to 2 decimal places)

    Example:
        Easy Q scores [6, 7, 8, 9] with weight 0.5
        Medium Q scores [5, 6, 7] with weight 1.0
        Hard Q scores [8, 9, 7] with weight 1.5
        → weighted average out of 10
    """
    total_weighted_score = 0.0
    total_weight         = 0.0

    for q in questions:
        score = q.get("score")
        level = q.get("difficulty_level", "medium")

        if score is None:
            continue

        weight = LEVEL_WEIGHTS.get(level, 1.0)
        total_weighted_score += float(score) * weight
        total_weight         += weight

    if total_weight == 0:
        return 0.0

    final = (total_weighted_score / total_weight)
    return round(min(final, 10.0), 2)


# ─────────────────────────────────────────────
# SKILL BREAKDOWN SCORES
# Maps question topics → 4 report categories
# ─────────────────────────────────────────────

# Topic keywords → which skill category they belong to
TOPIC_CATEGORY_MAP = {
    "technical_knowledge": [
        "python", "sql", "java", "javascript", "machine learning", "ml",
        "deep learning", "data structures", "algorithms", "api", "backend",
        "database", "cloud", "docker", "git", "data analytics", "statistics",
        "neural network", "nlp", "computer vision", "system design"
    ],
    "communication_skills": [
        "introduction", "yourself", "resume", "experience", "background",
        "describe", "explain", "tell me", "walk me through"
    ],
    "problem_solving": [
        "problem", "solution", "approach", "debug", "optimize", "design",
        "implement", "build", "architecture", "tradeoff", "edge case"
    ],
    "project_understanding": [
        "project", "built", "developed", "worked on", "contributed",
        "your project", "describe your", "tell me about your"
    ],
}

def calculate_skill_scores(questions: list[dict]) -> dict:
    """
    Calculate scores for the 4 skill categories shown in the report.

    Args:
        questions: list of {
            "topic": str,
            "question_text": str,
            "score": float,
            "difficulty_level": str
        }

    Returns:
        {
            "technical_knowledge":   float,
            "communication_skills":  float,
            "problem_solving":       float,
            "project_understanding": float
        }
    """
    buckets = {
        "technical_knowledge":  [],
        "communication_skills": [],
        "problem_solving":      [],
        "project_understanding": [],
    }

    for q in questions:
        score = q.get("score")
        if score is None:
            continue

        topic         = (q.get("topic") or "").lower()
        question_text = (q.get("question_text") or "").lower()
        combined      = topic + " " + question_text

        matched = False
        for category, keywords in TOPIC_CATEGORY_MAP.items():
            if any(kw in combined for kw in keywords):
                buckets[category].append(float(score))
                matched = True
                break

        # Default unmapped questions → technical_knowledge
        if not matched:
            buckets["technical_knowledge"].append(float(score))

    # Average each bucket — return 0 if no questions in that category
    result = {}
    for category, scores in buckets.items():
        result[category] = round(sum(scores) / len(scores), 2) if scores else 0.0

    return result


# ─────────────────────────────────────────────
# PERFORMANCE SUMMARY TEXT
# Used as the opening paragraph in the report
# ─────────────────────────────────────────────

def generate_performance_summary(total_score: float, skill_scores: dict) -> str:
    """
    Generate a one-paragraph performance summary based on scores.
    This is rule-based (no AI call) — fast and consistent.
    """

    # Overall performance tier
    if total_score >= 8.5:
        tier = "outstanding"
    elif total_score >= 7.0:
        tier = "strong"
    elif total_score >= 5.0:
        tier = "moderate"
    else:
        tier = "developing"

    # Find best and worst skill
    best_skill  = max(skill_scores, key=skill_scores.get)
    worst_skill = min(skill_scores, key=skill_scores.get)

    skill_labels = {
        "technical_knowledge":   "Technical Knowledge",
        "communication_skills":  "Communication Skills",
        "problem_solving":       "Problem Solving",
        "project_understanding": "Project Understanding",
    }

    summary = (
        f"The candidate demonstrated {tier} overall interview performance "
        f"with a score of {total_score}/10. "
        f"Their strongest area was {skill_labels[best_skill]} "
        f"({skill_scores[best_skill]}/10), while "
        f"{skill_labels[worst_skill]} ({skill_scores[worst_skill]}/10) "
        f"presents the greatest opportunity for growth."
    )

    return summary

# from config import SCORE_WEAK, SCORE_STRONG


# # ─────────────────────────────────────────────
# # ADAPTIVE TRIGGER CHECK
# # Called after every medium and hard question
# # ─────────────────────────────────────────────

# def should_trigger_adaptive(level: str, score: float) -> tuple[bool, str]:
#     """
#     Decide whether to fire an inline adaptive question.

#     Returns:
#         (True, "easier")  — medium question scored weak  → simplify
#         (True, "deeper")  — hard question scored strong  → go deeper
#         (False, "")       — no adaptive needed
#     """
#     if level == "medium" and score < SCORE_WEAK:
#         return True, "easier"

#     if level == "hard" and score > SCORE_STRONG:
#         return True, "deeper"

#     return False, ""


# # ─────────────────────────────────────────────
# # PER-QUESTION SCORE LABEL
# # ─────────────────────────────────────────────

# def score_label(score: float) -> str:
#     """Convert numeric score to human-readable label for the report."""
#     if score >= 8.5:
#         return "Excellent"
#     elif score >= 7.0:
#         return "Good"
#     elif score >= 5.0:
#         return "Average"
#     elif score >= 3.0:
#         return "Needs Improvement"
#     else:
#         return "Poor"


# # ─────────────────────────────────────────────
# # TOTAL SCORE CALCULATION
# # Weighted: hard questions count more than easy
# # ─────────────────────────────────────────────

# LEVEL_WEIGHTS = {
#     "easy":     0.5,
#     "medium":   1.0,
#     "hard":     1.5,
#     "adaptive": 1.0,   # adaptive inherits weight of its parent level
# }

# def calculate_total_score(questions: list[dict]) -> float:
#     """
#     Calculate weighted total score across all questions.

#     Args:
#         questions: list of {"difficulty_level": str, "score": float}

#     Returns:
#         Final score out of 10.0 (rounded to 2 decimal places)

#     Example:
#         Easy Q scores [6, 7, 8, 9] with weight 0.5
#         Medium Q scores [5, 6, 7] with weight 1.0
#         Hard Q scores [8, 9, 7] with weight 1.5
#         → weighted average out of 10
#     """
#     total_weighted_score = 0.0
#     total_weight         = 0.0

#     for q in questions:
#         score = q.get("score")
#         level = q.get("difficulty_level", "medium")

#         if score is None:
#             continue

#         weight = LEVEL_WEIGHTS.get(level, 1.0)
#         total_weighted_score += float(score) * weight
#         total_weight         += weight

#     if total_weight == 0:
#         return 0.0

#     final = (total_weighted_score / total_weight)
#     return round(min(final, 10.0), 2)


# # ─────────────────────────────────────────────
# # SKILL BREAKDOWN SCORES
# # Maps question topics → 4 report categories
# # ─────────────────────────────────────────────

# # Topic keywords → which skill category they belong to
# TOPIC_CATEGORY_MAP = {
#     "technical_knowledge": [
#         "python", "sql", "java", "javascript", "machine learning", "ml",
#         "deep learning", "data structures", "algorithms", "api", "backend",
#         "database", "cloud", "docker", "git", "data analytics", "statistics",
#         "neural network", "nlp", "computer vision", "system design"
#     ],
#     "communication_skills": [
#         "introduction", "yourself", "resume", "experience", "background",
#         "describe", "explain", "tell me", "walk me through"
#     ],
#     "problem_solving": [
#         "problem", "solution", "approach", "debug", "optimize", "design",
#         "implement", "build", "architecture", "tradeoff", "edge case"
#     ],
#     "project_understanding": [
#         "project", "built", "developed", "worked on", "contributed",
#         "your project", "describe your", "tell me about your"
#     ],
# }

# def calculate_skill_scores(questions: list[dict]) -> dict:
#     """
#     Calculate scores for the 4 skill categories shown in the report.

#     Args:
#         questions: list of {
#             "topic": str,
#             "question_text": str,
#             "score": float,
#             "difficulty_level": str
#         }

#     Returns:
#         {
#             "technical_knowledge":   float,
#             "communication_skills":  float,
#             "problem_solving":       float,
#             "project_understanding": float
#         }
#     """
#     buckets = {
#         "technical_knowledge":  [],
#         "communication_skills": [],
#         "problem_solving":      [],
#         "project_understanding": [],
#     }

#     for q in questions:
#         score = q.get("score")
#         if score is None:
#             continue

#         topic         = (q.get("topic") or "").lower()
#         question_text = (q.get("question_text") or "").lower()
#         combined      = topic + " " + question_text

#         matched = False
#         for category, keywords in TOPIC_CATEGORY_MAP.items():
#             if any(kw in combined for kw in keywords):
#                 buckets[category].append(float(score))
#                 matched = True
#                 break

#         # Default unmapped questions → technical_knowledge
#         if not matched:
#             buckets["technical_knowledge"].append(float(score))

#     # Average each bucket — return 0 if no questions in that category
#     result = {}
#     for category, scores in buckets.items():
#         result[category] = round(sum(scores) / len(scores), 2) if scores else 0.0

#     return result


# # ─────────────────────────────────────────────
# # PERFORMANCE SUMMARY TEXT
# # Used as the opening paragraph in the report
# # ─────────────────────────────────────────────

# def generate_performance_summary(total_score: float, skill_scores: dict) -> str:
#     """
#     Generate a one-paragraph performance summary based on scores.
#     This is rule-based (no AI call) — fast and consistent.
#     """

#     # Overall performance tier
#     if total_score >= 8.5:
#         tier = "outstanding"
#     elif total_score >= 7.0:
#         tier = "strong"
#     elif total_score >= 5.0:
#         tier = "moderate"
#     else:
#         tier = "developing"

#     # Find best and worst skill
#     best_skill  = max(skill_scores, key=skill_scores.get)
#     worst_skill = min(skill_scores, key=skill_scores.get)

#     skill_labels = {
#         "technical_knowledge":   "Technical Knowledge",
#         "communication_skills":  "Communication Skills",
#         "problem_solving":       "Problem Solving",
#         "project_understanding": "Project Understanding",
#     }

#     summary = (
#         f"The candidate demonstrated {tier} overall interview performance "
#         f"with a score of {total_score}/10. "
#         f"Their strongest area was {skill_labels[best_skill]} "
#         f"({skill_scores[best_skill]}/10), while "
#         f"{skill_labels[worst_skill]} ({skill_scores[worst_skill]}/10) "
#         f"presents the greatest opportunity for growth."
#     )

#     return summary


# # from interview.lisa_ai import client, MODEL


# # def evaluate_answer(question, answer):

# #     prompt = f"""
# # You are an expert interviewer.

# # Evaluate the candidate answer.

# # Question:
# # {question}

# # Answer:
# # {answer}

# # Return STRICTLY in this format:

# # Score: <number 1-10>
# # Feedback: <short explanation>
# # """

# #     response = client.chat.completions.create(
# #         model=MODEL,
# #         messages=[
# #             {"role": "system", "content": "You evaluate interview answers."},
# #             {"role": "user", "content": prompt}
# #         ],
# #         temperature=0.3
# #     )

# #     text = response.choices[0].message.content.strip()

# #     # Parse result
# #     score = 0
# #     feedback = text

# #     try:
# #         lines = text.split("\n")
# #         for line in lines:
# #             if "Score" in line:
# #                 score = int(line.split(":")[1].strip())
# #             if "Feedback" in line:
# #                 feedback = line.split(":")[1].strip()
# #     except:
# #         pass

# #     return score, feedback
# # # from interview.lisa_ai import client, MODEL


# # # def evaluate_answer(question, answer):

# # #     prompt = f"""
# # # You are an AI interviewer.

# # # Question:
# # # {question}

# # # Candidate Answer:
# # # {answer}

# # # Return in this format:

# # # Score: (0-10)
# # # Ideal Answer: (short professional answer)
# # # """

# # #     response = client.models.generate_content(
# # #         model=MODEL,
# # #         contents=prompt
# # #     )

# # #     text = response.text

# # #     score = 0

# # #     for word in text.split():
# # #         if word.isdigit():
# # #             score = int(word)
# # #             break

# # #     return score, text


# # # # from interview.lisa_ai import model

# # # # def evaluate_answer(question, answer):
# # # #     prompt = f"""
# # # #     Question: {question}
# # # #     User Answer: {answer}

# # # #     Provide:
# # # #     1. Score out of 10
# # # #     2. Ideal Answer
# # # #     """

# # # #     response = model.generate_content(prompt)
# # # #     return response.text