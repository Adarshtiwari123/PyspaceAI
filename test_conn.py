import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("🔍 Testing Supabase connection...")
print(f"URL found: {'✅ Yes' if DATABASE_URL else '❌ No DATABASE_URL in .env'}")

try:
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
    cur = conn.cursor()
    
    # Test 1: Basic connection
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"✅ Connected! PostgreSQL version: {version[0][:30]}...")
    
    # Test 2: Check your tables exist
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    
    if tables:
        print(f"✅ Tables found: {[t[0] for t in tables]}")
    else:
        print("⚠️  Connected but NO tables yet — run create_tables() first")
    
    cur.close()
    conn.close()
    print("\n🎉 Supabase is fully connected and ready!")

except psycopg2.OperationalError as e:
    print(f"\n❌ Connection FAILED: {e}")
    print("\nPossible fixes:")
    print("  1. Check DATABASE_URL in .env is correct")
    print("  2. Add ?sslmode=require at end of URL")
    print("  3. Reset DB password: Supabase → Settings → Database")

#password=Pyspace202400