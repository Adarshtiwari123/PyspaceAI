import os
import psycopg2
from psycopg2 import pool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env")

# ─────────────────────────────────────────────
# CONNECTION POOL (psycopg2 — for raw queries)
# ─────────────────────────────────────────────
connection_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL
)

def get_connection():
    return connection_pool.getconn()

def release_connection(conn):
    connection_pool.putconn(conn)


# ─────────────────────────────────────────────
# SQLALCHEMY (for ORM / create_tables)
# ─────────────────────────────────────────────
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


# ─────────────────────────────────────────────
# CREATE ALL TABLES
# ─────────────────────────────────────────────
def create_tables():
    from database.models import Base
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully.")


# ═════════════════════════════════════════════
# USERS
# ═════════════════════════════════════════════

def save_user(name: str, email: str, picture: str):
    """Insert user on first Google login. Skip if already exists."""
    from database.models import User
    session = SessionLocal()
    try:
        existing = session.query(User).filter(User.email == email).first()
        if not existing:
            session.add(User(name=name, email=email, picture=picture))
            session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_user(email: str):
    """Fetch user by email. Returns User object or None."""
    from database.models import User
    session = SessionLocal()
    try:
        return session.query(User).filter(User.email == email).first()
    finally:
        session.close()


# ═════════════════════════════════════════════
# INTERVIEWS
# ═════════════════════════════════════════════

def create_interview(user_email: str, resume_text: str, resume_filename: str) -> int:
    """Start a new interview session. Returns the new interview ID."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO interviews (user_email, resume_text, resume_filename, status)
            VALUES (%s, %s, %s, 'ongoing')
            RETURNING id
            """,
            (user_email, resume_text, resume_filename)
        )
        interview_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return interview_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_connection(conn)


def complete_interview(interview_id: int, total_score: float):
    """Mark interview as completed, set end_time and total_score."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE interviews
            SET status = 'completed',
                end_time = NOW(),
                total_score = %s
            WHERE id = %s
            """,
            (total_score, interview_id)
        )
        conn.commit()
        cur.close()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_connection(conn)


def abandon_interview(interview_id: int):
    """Mark interview as abandoned if user exits early."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE interviews SET status = 'abandoned', end_time = NOW() WHERE id = %s",
            (interview_id,)
        )
        conn.commit()
        cur.close()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_connection(conn)


def get_user_interviews(user_email: str) -> list:
    """
    Fetch all past interviews for dashboard history.
    Returns list of (id, status, total_score, start_time, end_time, resume_filename)
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, status, total_score, start_time, end_time, resume_filename
            FROM interviews
            WHERE user_email = %s
            ORDER BY created_at DESC
            """,
            (user_email,)
        )
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        release_connection(conn)


def get_interview(interview_id: int):
    """Fetch single interview by ID."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, user_email, resume_text, resume_filename,
                   start_time, end_time, status, total_score
            FROM interviews WHERE id = %s
            """,
            (interview_id,)
        )
        row = cur.fetchone()
        cur.close()
        return row
    finally:
        release_connection(conn)


# ═════════════════════════════════════════════
# INTERVIEW QUESTIONS
# ═════════════════════════════════════════════

def save_question(
    interview_id: int,
    question_number: int,
    difficulty_level: str,
    topic: str,
    question_text: str,
    user_answer: str,
    ai_suggested_answer: str,
    score: float,
    feedback: str
):
    """Save a single completed Q&A pair."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO interview_questions (
                interview_id, question_number, difficulty_level, topic,
                question_text, user_answer, ai_suggested_answer, score, feedback
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                interview_id, question_number, difficulty_level, topic,
                question_text, user_answer, ai_suggested_answer, score, feedback
            )
        )
        conn.commit()
        cur.close()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_connection(conn)


def get_interview_questions(interview_id: int) -> list:
    """
    Fetch all Q&A pairs for a session.
    Returns list of (question_number, difficulty_level, topic,
                     question_text, user_answer, ai_suggested_answer, score, feedback)
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT question_number, difficulty_level, topic,
                   question_text, user_answer, ai_suggested_answer, score, feedback
            FROM interview_questions
            WHERE interview_id = %s
            ORDER BY question_number ASC
            """,
            (interview_id,)
        )
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        release_connection(conn)


# ═════════════════════════════════════════════
# INTERVIEW REPORTS
# ═════════════════════════════════════════════

def save_report(
    interview_id: int,
    overall_score: float,
    performance_summary: str,
    technical_knowledge: float,
    communication_skills: float,
    problem_solving: float,
    project_understanding: float,
    strengths: str,
    areas_for_improvement: str,
    actionable_suggestions: str,
    report_pdf: bytes
):
    """Save the final generated report."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO interview_reports (
                interview_id, overall_score, performance_summary,
                technical_knowledge, communication_skills,
                problem_solving, project_understanding,
                strengths, areas_for_improvement, actionable_suggestions,
                report_pdf
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                interview_id, overall_score, performance_summary,
                technical_knowledge, communication_skills,
                problem_solving, project_understanding,
                strengths, areas_for_improvement, actionable_suggestions,
                psycopg2.Binary(report_pdf)
            )
        )
        conn.commit()
        cur.close()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_connection(conn)


def get_report(interview_id: int):
    """Fetch full report for a given interview."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT overall_score, performance_summary,
                   technical_knowledge, communication_skills,
                   problem_solving, project_understanding,
                   strengths, areas_for_improvement,
                   actionable_suggestions, generated_at
            FROM interview_reports
            WHERE interview_id = %s
            """,
            (interview_id,)
        )
        row = cur.fetchone()
        cur.close()
        return row
    finally:
        release_connection(conn)


def get_report_pdf(interview_id: int):
    """Returns raw PDF bytes for download button."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT report_pdf FROM interview_reports WHERE interview_id = %s",
            (interview_id,)
        )
        row = cur.fetchone()
        cur.close()
        return bytes(row[0]) if row and row[0] else None
    finally:
        release_connection(conn)
#import os
# import psycopg2
# from psycopg2 import pool
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from dotenv import load_dotenv

# load_dotenv()

# # ─────────────────────────────────────────────
# # SUPABASE CONNECTION  (replaces local postgres)
# # Use the "Transaction Mode" pooler URL from Supabase dashboard
# # Dashboard → Project → Settings → Database → Connection Pooling
# # ─────────────────────────────────────────────
# DATABASE_URL = os.getenv("DATABASE_URL")
# # Format: postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

# if not DATABASE_URL:
#     raise ValueError("DATABASE_URL not found in .env")

# # ─────────────────────────────────────────────
# # CONNECTION POOL  (replaces open/close per call)
# # ─────────────────────────────────────────────
# connection_pool = psycopg2.pool.SimpleConnectionPool(
#     minconn=1,
#     maxconn=10,
#     dsn=DATABASE_URL
# )

# def get_connection():
#     return connection_pool.getconn()

# def release_connection(conn):
#     connection_pool.putconn(conn)

# # ─────────────────────────────────────────────
# # SQLALCHEMY (for User ORM only)
# # ─────────────────────────────────────────────
# engine = create_engine(DATABASE_URL, pool_pre_ping=True)
# SessionLocal = sessionmaker(bind=engine)

# # ─────────────────────────────────────────────
# # CREATE TABLES
# # ─────────────────────────────────────────────
# def create_tables():
#     from database.models import Base
#     Base.metadata.create_all(bind=engine)

# # ─────────────────────────────────────────────
# # USER (Google OAuth)
# # ─────────────────────────────────────────────
# def save_user(name, email, picture):
#     from database.models import User
#     session = SessionLocal()
#     try:
#         existing = session.query(User).filter(User.email == email).first()
#         if not existing:
#             session.add(User(name=name, email=email, picture=picture))
#             session.commit()
#     except Exception as e:
#         session.rollback()
#         raise e
#     finally:
#         session.close()

# def get_user(email):
#     from database.models import User
#     session = SessionLocal()
#     try:
#         return session.query(User).filter(User.email == email).first()
#     finally:
#         session.close()

# # ─────────────────────────────────────────────
# # INTERVIEW SESSION
# # ─────────────────────────────────────────────
# def create_interview(user_email):
#     conn = get_connection()
#     try:
#         cur = conn.cursor()
#         cur.execute(
#             "INSERT INTO interviews (user_email) VALUES (%s) RETURNING id",
#             (user_email,)
#         )
#         interview_id = cur.fetchone()[0]
#         conn.commit()
#         cur.close()
#         return interview_id
#     except Exception as e:
#         conn.rollback()
#         raise e
#     finally:
#         release_connection(conn)

# def get_user_interviews(user_email):
#     """Fetch all past interviews for dashboard history."""
#     conn = get_connection()
#     try:
#         cur = conn.cursor()
#         cur.execute(
#             """
#             SELECT id, created_at, total_score
#             FROM interviews
#             WHERE user_email = %s
#             ORDER BY created_at DESC
#             """,
#             (user_email,)
#         )
#         rows = cur.fetchall()
#         cur.close()
#         return rows
#     finally:
#         release_connection(conn)

# # ─────────────────────────────────────────────
# # INTERVIEW DETAILS (per question)
# # ─────────────────────────────────────────────
# def save_interview_detail(interview_id, question, user_answer, ai_answer, score):
#     conn = get_connection()
#     try:
#         cur = conn.cursor()
#         cur.execute(
#             """
#             INSERT INTO interview_details
#                 (interview_id, question, user_answer, ai_suggested_answer, score)
#             VALUES (%s, %s, %s, %s, %s)
#             """,
#             (interview_id, question, user_answer, ai_answer, score)
#         )
#         conn.commit()
#         cur.close()
#     except Exception as e:
#         conn.rollback()
#         raise e
#     finally:
#         release_connection(conn)

# def get_interview_details(interview_id):
#     """Fetch all Q&A pairs for a given session (used in report generation)."""
#     conn = get_connection()
#     try:
#         cur = conn.cursor()
#         cur.execute(
#             """
#             SELECT question, user_answer, ai_suggested_answer, score
#             FROM interview_details
#             WHERE interview_id = %s
#             ORDER BY id ASC
#             """,
#             (interview_id,)
#         )
#         rows = cur.fetchall()
#         cur.close()
#         return rows
#     finally:
#         release_connection(conn)

# # ─────────────────────────────────────────────
# # REPORT
# # Note: PDF bytes stored in DB is fine for MVP.
# # For production → use Supabase Storage and store URL instead.
# # ─────────────────────────────────────────────
# def save_report(interview_id, total_score, pdf_bytes):
#     conn = get_connection()
#     try:
#         cur = conn.cursor()
#         cur.execute(
#             """
#             UPDATE interviews
#             SET total_score = %s, report_pdf = %s
#             WHERE id = %s
#             """,
#             (total_score, psycopg2.Binary(pdf_bytes), interview_id)
#         )
#         conn.commit()
#         cur.close()
#     except Exception as e:
#         conn.rollback()
#         raise e
#     finally:
#         release_connection(conn)

# def get_report_pdf(interview_id):
#     """Returns raw PDF bytes for download."""
#     conn = get_connection()
#     try:
#         cur = conn.cursor()
#         cur.execute(
#             "SELECT report_pdf FROM interviews WHERE id = %s",
#             (interview_id,)
#         )
#         row = cur.fetchone()
#         cur.close()
#         return bytes(row[0]) if row and row[0] else None
#     finally:
#         release_connection(conn)

# # Supabase- password :Adarsh@Pyspace
# # from sqlalchemy import create_engine
# # from sqlalchemy.orm import sessionmaker
# # from config import DATABASE_URL
# # from database.models import Base, User

# # engine = create_engine(DATABASE_URL)
# # SessionLocal = sessionmaker(bind=engine)

# # #New code inserted from (9)#
# # import psycopg2
# # from config import DB_HOST, DB_NAME, DB_USER,DB_PASSWORD


# # def get_connection():
# #     return psycopg2.connect(
# #         host=DB_HOST,
# #         database=DB_NAME,
# #         user=DB_USER,
# #         password=DB_PASSWORD
# #     )


# # # Create interview session
# # def create_interview(user_email):

# #     conn = get_connection()
# #     cur = conn.cursor()

# #     cur.execute(
# #         """
# #         INSERT INTO interviews (user_email)
# #         VALUES (%s)
# #         RETURNING id
# #         """,
# #         (user_email,)
# #     )

# #     interview_id = cur.fetchone()[0]

# #     conn.commit()
# #     cur.close()
# #     conn.close()

# #     return interview_id


# # # Save each question answer
# # def save_interview_detail(
# #         interview_id,
# #         question,
# #         user_answer,
# #         ai_answer,
# #         score
# # ):

# #     conn = get_connection()
# #     cur = conn.cursor()

# #     cur.execute(
# #         """
# #         INSERT INTO interview_details
# #         (interview_id, question, user_answer, ai_suggested_answer, score)
# #         VALUES (%s,%s,%s,%s,%s)
# #         """,
# #         (interview_id, question, user_answer, ai_answer, score)
# #     )

# #     conn.commit()
# #     cur.close()
# #     conn.close()


# # # Save final report
# # def save_report(interview_id, total_score, pdf_bytes):

# #     conn = get_connection()
# #     cur = conn.cursor()

# #     cur.execute(
# #         """
# #         UPDATE interviews
# #         SET total_score=%s, report_pdf=%s
# #         WHERE id=%s
# #         """,
# #         (total_score, pdf_bytes, interview_id)
# #     )

# #     conn.commit()
# #     cur.close()
# #     conn.close()
# # #Code to 90#
# # # -------------------------
# # # CREATE TABLES
# # # -------------------------
# # def create_tables():
# #     Base.metadata.create_all(bind=engine)


# # # -------------------------
# # # SAVE USER (Google Login)
# # # -------------------------
# # def save_user(name, email, picture):
# #     session = SessionLocal()
# #     try:
# #         existing_user = session.query(User).filter(User.email == email).first()

# #         if not existing_user:
# #             new_user = User(
# #                 name=name,
# #                 email=email,
# #                 picture=picture
# #             )
# #             session.add(new_user)
# #             session.commit()
# #     finally:
# #         session.close()