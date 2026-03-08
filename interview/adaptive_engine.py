from config import client

def adaptive_followup(question, answer):

    prompt = f"""
Candidate answered:

Question:
{question}

Answer:
{answer}

Ask a deeper follow-up question to test knowledge.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return response.choices[0].message.content