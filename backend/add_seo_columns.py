"""
Add missing SEO columns to posts table
"""
import subprocess
import sys

try:
    import psycopg2
except ImportError:
    print("Installing psycopg2-binary...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2

DATABASE_URL = "postgresql://neondb_owner:npg_kbJ0CXZwTV6d@ep-crimson-frog-aexv6lr8-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require"

print("Connecting to database...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("Adding SEO columns to posts table...")

# Add columns if they don't exist
cur.execute("ALTER TABLE posts ADD COLUMN IF NOT EXISTS meta_description TEXT")
cur.execute("ALTER TABLE posts ADD COLUMN IF NOT EXISTS keywords TEXT")
cur.execute("ALTER TABLE posts ADD COLUMN IF NOT EXISTS hashtags TEXT")
cur.execute("ALTER TABLE posts ADD COLUMN IF NOT EXISTS search_queries TEXT")

conn.commit()
cur.close()
conn.close()

print("✅ SUCCESS! SEO columns added to posts table")
print("\nNow test blog generation:")
print('Invoke-WebRequest -Uri "https://mahendercreates-wavesignals-backend.hf.space/api/generate-post" -Method POST -Headers @{"X-Admin-Key"="wavesignals@2025"} -UseBasicParsing -TimeoutSec 120')
