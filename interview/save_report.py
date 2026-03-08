from database.db import get_connection

def save_interview(email, total_score, pdf_data):
    conn = get_connection()
    conn.execute(
        "INSERT INTO interviews (user_email, total_score, report_pdf) VALUES (%s, %s, %s)",
        (email, total_score, pdf_data)
    )
    conn.commit()
    conn.close()