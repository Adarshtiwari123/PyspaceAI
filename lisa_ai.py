# OLD - OpenAI (cost reason)
# import os
# from openai import OpenAI
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# MODEL = "gpt-4o-mini"
# def generate_question(level, resume, previous_answer=None):
#    ...
#    response = client.chat.completions.create(...)
#    return response.choices[0].message.content.strip()

# NEW - Groq Llama 3.3 70B (free tier)
import streamlit as st
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)

def generate_question(level, resume, previous_answer=None):
    prompt = f"""
You are LISA, a professional AI technical interviewer.

Your task is to ask ONE interview question.

Rules:
- Difficulty: {level}
- Question should relate to the candidate's resume
- If previous answer is weak → ask easier follow-up
- If strong → ask deeper question
- Only return the question text

Candidate Resume:
{resume}

Previous Answer:
{previous_answer}
"""
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You are LISA, a professional AI interviewer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()
