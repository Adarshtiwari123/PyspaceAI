"""
Run this before deploying to verify your REDIRECT_URI is correct.

Usage:
    python check_redirect.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*50)
print("  PYSPACE — REDIRECT URI CHECK")
print("="*50)

redirect = os.getenv("REDIRECT_URI", "NOT SET")
client_id = os.getenv("GOOGLE_CLIENT_ID", "NOT SET")
db = os.getenv("DATABASE_URL", "NOT SET")
openai = os.getenv("OPENAI_API_KEY", "NOT SET")

print(f"\n  REDIRECT_URI         : {redirect}")
print(f"  GOOGLE_CLIENT_ID     : {client_id[:30]}..." if client_id != "NOT SET" else f"  GOOGLE_CLIENT_ID     : NOT SET")
print(f"  DATABASE_URL         : {'SET ✅' if db != 'NOT SET' else 'NOT SET ❌'}")
print(f"  OPENAI_API_KEY       : {'SET ✅' if openai != 'NOT SET' else 'NOT SET ❌'}")

print("\n" + "-"*50)

# Validation
errors = []

if redirect == "NOT SET":
    errors.append("❌ REDIRECT_URI is missing from .env")
elif "localhost" in redirect:
    print("  Environment : LOCAL ✅")
    print(f"  Google Console must have: {redirect}")
elif "streamlit.app" in redirect:
    print("  Environment : STREAMLIT CLOUD ✅")
    print(f"  Google Console must have: {redirect}")
else:
    errors.append(f"❌ REDIRECT_URI looks wrong: {redirect}")

if client_id == "NOT SET":
    errors.append("❌ GOOGLE_CLIENT_ID is missing")

if errors:
    print("\n  ISSUES FOUND:")
    for e in errors:
        print(f"  {e}")
else:
    print("\n  All checks passed ✅")

print("="*50 + "\n")