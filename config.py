import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# OPENAI
# ─────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env")

# ─────────────────────────────────────────────
# GOOGLE OAUTH
# ─────────────────────────────────────────────
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI         = os.getenv("REDIRECT_URI", "http://localhost:8501")

# ─────────────────────────────────────────────
# SUPABASE / POSTGRESQL
# ─────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env")

# ─────────────────────────────────────────────
# INTERVIEW STRUCTURE
# ─────────────────────────────────────────────

# Fixed question counts per level
QUESTIONS_PER_LEVEL = {
    "easy":   4,   # Q1 = intro/non-tech, Q2-Q4 = resume-based easy tech
    "medium": 3,
    "hard":   3,
}

# Adaptive questions fire INLINE after medium/hard — not at the end
# Range: min 0, max 1 adaptive per medium/hard question
ADAPTIVE_TRIGGER = {
    "medium": {"min_score": None, "max_score": 4.0},  # score < 4  → 1 adaptive (easier)
    "hard":   {"min_score": 7.0,  "max_score": None},  # score > 7  → 1 adaptive (deeper)
}

# Session size
MIN_QUESTIONS = 10   # 4 easy + 3 medium + 3 hard (no adaptives triggered)
MAX_QUESTIONS = 16   # + up to 6 adaptive (1 per each medium/hard question)

# Score thresholds for adaptive branching
SCORE_WEAK   = 4.0   # Below this on medium → fire easier follow-up immediately
SCORE_STRONG = 7.0   # Above this on hard   → fire deeper follow-up immediately

# First question is always this — every real interview starts here
INTRO_QUESTION = "Tell me about yourself and walk me through your resume."

# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────
APP_NAME    = "Pyspace"
APP_VERSION = "1.0.0"

# import os
# from dotenv import load_dotenv

# load_dotenv()

# # ─────────────────────────────────────────────
# # OPENAI
# # ─────────────────────────────────────────────
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# if not OPENAI_API_KEY:
#     raise ValueError("OPENAI_API_KEY not found in .env")

# # ─────────────────────────────────────────────
# # GOOGLE OAUTH
# # ─────────────────────────────────────────────
# GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID")
# GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# REDIRECT_URI         = os.getenv("REDIRECT_URI", "http://localhost:8501")

# # ─────────────────────────────────────────────
# # SUPABASE / POSTGRESQL
# # ─────────────────────────────────────────────
# DATABASE_URL = os.getenv("DATABASE_URL")
# if not DATABASE_URL:
#     raise ValueError("DATABASE_URL not found in .env")

# # ─────────────────────────────────────────────
# # INTERVIEW STRUCTURE
# # ─────────────────────────────────────────────

# # Fixed question counts per level
# QUESTIONS_PER_LEVEL = {
#     "easy":   4,   # Q1 = intro/non-tech, Q2-Q4 = resume-based easy tech
#     "medium": 3,
#     "hard":   3,
# }

# # Adaptive questions fire INLINE after medium/hard — not at the end
# # Range: min 0, max 1 adaptive per medium/hard question
# ADAPTIVE_TRIGGER = {
#     "medium": {"min_score": None, "max_score": 4.0},  # score < 4  → 1 adaptive (easier)
#     "hard":   {"min_score": 7.0,  "max_score": None},  # score > 7  → 1 adaptive (deeper)
# }

# # Session size
# MIN_QUESTIONS = 10   # 4 easy + 3 medium + 3 hard (no adaptives triggered)
# MAX_QUESTIONS = 16   # + up to 6 adaptive (1 per each medium/hard question)

# # Score thresholds for adaptive branching
# SCORE_WEAK   = 4.0   # Below this on medium → fire easier follow-up immediately
# SCORE_STRONG = 7.0   # Above this on hard   → fire deeper follow-up immediately

# # First question is always this — every real interview starts here
# INTRO_QUESTION = "Tell me about yourself and walk me through your resume."

# # ─────────────────────────────────────────────
# # APP
# # ─────────────────────────────────────────────
# APP_NAME    = "Pyspace"
# APP_VERSION = "1.0.0"



# # import os
# # from dotenv import load_dotenv
# # from openai import OpenAI
# # load_dotenv()
# # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# # client = OpenAI(api_key=OPENAI_API_KEY)
# # # -------------------------------
# # # GEMINI API
# # # -------------------------------
# # GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# # # -------------------------------
# # # DATABASE CONFIG
# # # -------------------------------
# # DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
# # DB_PORT = os.getenv("DB_PORT", "5432")
# # DB_NAME = os.getenv("DB_NAME", "pyspace")
# # DB_USER = os.getenv("DB_USER", "postgres")
# # DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")

# # # PostgreSQL connection string
# # DATABASE_URL = (
# #     f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# # )

# # # -------------------------------
# # # DEEPGRAM (future voice feature)
# # # -------------------------------
# # DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# # # import os
# # # from dotenv import load_dotenv

# # # load_dotenv()
# # # from dotenv import load_dotenv
# # # import os

# # # load_dotenv()

# # # DATABASE_URL = (
# # #     f"postgresql://{os.getenv('DB_USER')}:"
# # #     f"{os.getenv('DB_PASSWORD')}@"
# # #     f"{os.getenv('DB_HOST')}:"
# # #     f"{os.getenv('DB_PORT')}/"
# # #     f"{os.getenv('DB_NAME')}"
# # # )
# # # GEMINI_API_KEY = os.getenv("AIzaSyAKje6lujTWAMnna1URSWZ9qB1G_uW-i7A")

# # # #DATABASE_URL = "postgresql://postgres:password@localhost:5432/pyspace"
# # # DATABASE_URL = "postgresql://postgres:1234@127.0.0.1:5432/pyspace"