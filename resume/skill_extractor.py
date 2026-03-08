from config import client

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
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return response.choices[0].message.content