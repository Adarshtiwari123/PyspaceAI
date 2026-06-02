import os
from dotenv import load_dotenv

load_dotenv()

# Fallback to the production URL if the environment variable isn't set.
# If testing locally, you can set BACKEND_URL="http://localhost:8000" in your .env file
BACKEND_URL = os.getenv("BACKEND_URL", "https://productionai1.onrender.com")

# OLD - OpenAI (cost reason) (Keep for TTS if needed)
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 

# NEW - Groq Llama 3.3 70B (free tier)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
