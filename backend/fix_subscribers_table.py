"""
Quick script to drop and recreate subscribers table with correct column names
"""

# First, try to install psycopg2-binary if not already installed
import subprocess
import sys

try:
    import psycopg2
except ImportError:
    print("Installing psycopg2-binary...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2

# Database connection
DATABASE_URL = "postgresql://neondb_owner:npg_kbJ0CXZwTV6d@ep-crimson-frog-aexv6lr8-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require"

print("Connecting to database...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Drop old table
print("Dropping old subscribers table...")
cur.execute("DROP TABLE IF EXISTS subscribers")

# Create new table with correct column names
print("Creating new subscribers table with correct columns...")
cur.execute("""
    CREATE TABLE subscribers (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active'
    )
""")

conn.commit()
cur.close()
conn.close()

print("✅ SUCCESS! Subscribers table recreated with 'created_at' column")
print("\nTest it:")
print('Invoke-WebRequest -Uri "https://mahendercreates-wavesignals-backend.hf.space/api/subscribers" -UseBasicParsing')
