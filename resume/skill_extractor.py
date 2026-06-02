# OLD - OpenAI (cost reason)
# from config import client
#
# def extract_skills_projects(resume_text):
#
#     prompt = f"""
# Extract structured data from this resume.
#
# Return JSON with:
# skills
# projects
# tools
# experience_level
#
# Resume:
# {resume_text}
# """
#
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{"role":"user","content":prompt}]
#     )
#
#     return response.choices[0].message.content

# NEW - Groq Llama 3.3 70B (free tier)
from config import GROQ_API_KEY, GROQ_MODEL
from groq import Groq

client = Groq(api_key=GROQ_API_KEY)

def extract_skills_projects(resume_text):

    prompt = f"""
Extract structured data from this resume.

Return JSON with:
skills
projects
tools
experience_level

Resume:
{resume_text}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role":"user","content":prompt}],
        temperature=0.7,
        max_tokens=1000
    )

    return response.choices[0].message.content