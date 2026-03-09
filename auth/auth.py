"""
auth/auth.py — standalone auth using auth_users table.
On login, also syncs user into the main `users` table
so that interviews foreign key never breaks.
"""
import os
import bcrypt
import psycopg2
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _get_conn():
    try:
        url = st.secrets.get("DATABASE_URL")
    except Exception:
        url = None
    if not url:
        url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL not found")
    return psycopg2.connect(url)


# ─────────────────────────────────────────────
# SYNC INTO users TABLE
# Interviews FK references users(email).
# Call this every time a user logs in.
# ─────────────────────────────────────────────
def _sync_to_users(conn, full_name: str, email: str):
    """Insert into users table if not already there."""
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (name, email, picture)
            VALUES (%s, %s, '')
            ON CONFLICT (email) DO NOTHING
            """,
            (full_name, email)
        )
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"[AUTH] _sync_to_users error: {e}")


# ─────────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────────
def register_user(full_name: str, email: str, password: str):
    try:
        pw_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        conn = _get_conn()
        cur  = conn.cursor()

        # 1. Insert into auth_users
        cur.execute(
            """
            INSERT INTO auth_users (full_name, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (full_name.strip(), email.strip().lower(), pw_hash)
        )
        conn.commit()
        cur.close()

        # 2. Sync into users table immediately
        _sync_to_users(conn, full_name.strip(), email.strip().lower())

        conn.close()
        return True, "ok"

    except psycopg2.errors.UniqueViolation:
        return False, "email_exists"
    except Exception as e:
        print(f"[AUTH] register error: {e}")
        return False, str(e)


# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────
def login_user(email: str, password: str):
    try:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute(
            """
            SELECT full_name, email, password_hash
            FROM auth_users WHERE email = %s
            """,
            (email.strip().lower(),)
        )
        row = cur.fetchone()
        cur.close()

        if not row:
            conn.close()
            return None

        full_name, db_email, pw_hash = row

        match = bcrypt.checkpw(
            password.encode("utf-8"),
            pw_hash.encode("utf-8")
        )

        if match:
            # Sync into users table so FK never breaks
            _sync_to_users(conn, full_name, db_email)
            conn.close()
            return {"name": full_name, "email": db_email}

        conn.close()
        return None

    except Exception as e:
        print(f"[AUTH] login error: {e}")
        return None

# """
# auth/auth.py
# Standalone auth module — uses its own auth_users table.
# No dependency on users table or models.py.
# """
# import os
# import bcrypt
# import psycopg2
# import streamlit as st
# from dotenv import load_dotenv

# load_dotenv()


# # ─────────────────────────────────────────────
# # DB CONNECTION — reads st.secrets first
# # ─────────────────────────────────────────────
# def _get_conn():
#     try:
#         url = st.secrets.get("DATABASE_URL")
#     except Exception:
#         url = None
#     if not url:
#         url = os.getenv("DATABASE_URL")
#     if not url:
#         raise ValueError("DATABASE_URL not found")
#     return psycopg2.connect(url)


# # ─────────────────────────────────────────────
# # REGISTER
# # Returns (True, "ok") or (False, "error msg")
# # ─────────────────────────────────────────────
# def register_user(full_name: str, email: str, password: str):
#     try:
#         pw_hash = bcrypt.hashpw(
#             password.encode("utf-8"),
#             bcrypt.gensalt()
#         ).decode("utf-8")

#         conn = _get_conn()
#         cur  = conn.cursor()
#         cur.execute(
#             """
#             INSERT INTO auth_users (full_name, email, password_hash)
#             VALUES (%s, %s, %s)
#             """,
#             (full_name.strip(), email.strip().lower(), pw_hash)
#         )
#         conn.commit()
#         cur.close()
#         conn.close()
#         return True, "ok"

#     except psycopg2.errors.UniqueViolation:
#         return False, "email_exists"
#     except Exception as e:
#         print(f"[AUTH] register error: {e}")
#         return False, str(e)


# # ─────────────────────────────────────────────
# # LOGIN
# # Returns user dict or None
# # ─────────────────────────────────────────────
# def login_user(email: str, password: str):
#     try:
#         conn = _get_conn()
#         cur  = conn.cursor()
#         cur.execute(
#             "SELECT full_name, email, password_hash FROM auth_users WHERE email = %s",
#             (email.strip().lower(),)
#         )
#         row = cur.fetchone()
#         cur.close()
#         conn.close()

#         if not row:
#             return None  # email not found

#         full_name, db_email, pw_hash = row

#         match = bcrypt.checkpw(
#             password.encode("utf-8"),
#             pw_hash.encode("utf-8")
#         )

#         if match:
#             return {"name": full_name, "email": db_email}
#         return None

#     except Exception as e:
#         print(f"[AUTH] login error: {e}")
#         return None