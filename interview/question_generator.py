from config import client

def generate_questions(skill_data):

    prompt = f"""
Generate interview questions.

Skills:
{skill_data}

Rules:
4 Easy questions
3 Medium questions
3 Hard questions

Also include project based questions.

Return JSON format:
easy
medium
hard
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return response.choices[0].message.content