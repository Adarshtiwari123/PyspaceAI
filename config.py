import os
from dotenv import load_dotenv

load_dotenv()

#BACKEND_URL = "https://productionai1.onrender.com"
BACKEND_URL = "http://localhost:8000"

# OLD - OpenAI (cost reason) (Keep for TTS if needed)
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 

# NEW - Groq Llama 3.3 70B (free tier)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
