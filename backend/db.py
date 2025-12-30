import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import time

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection(retry_count=3):
    """Get database connection with retry logic"""
    for attempt in range(retry_count):
        try:
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            if attempt > 0:
                print(f"✅ Database connected on attempt {attempt + 1}")
            return conn
        except Exception as e:
            print(f"❌ Database connection attempt {attempt + 1}/{retry_count} failed: {e}")
            if attempt < retry_count - 1:
                time.sleep(2)  # Wait 2 seconds before retry
            else:
                print(f"🔴 All {retry_count} connection attempts failed")
                return None

def init_db():
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        # Create Posts Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                slug TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                excerpt TEXT,
                content TEXT NOT NULL,
                published BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                author TEXT DEFAULT 'WaveSignals',
                tags TEXT,
                meta_description TEXT,
                keywords TEXT,
                hashtags TEXT,
                search_queries TEXT,
                image TEXT
            );
        """)

        # Create Settings Table (Singleton)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id SERIAL PRIMARY KEY,
                config JSONB DEFAULT '{}'::jsonb
            );
        """)
        
        # Create Subscribers Table - CRITICAL FIX
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            );
        """)
        
        # Ensure one row exists
        cur.execute("SELECT COUNT(*) as count FROM settings")
        if cur.fetchone()['count'] == 0:
            cur.execute("INSERT INTO settings (id, config) VALUES (1, '{}')")
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database initialized successfully")
        print("   - posts table created")
        print("   - settings table created") 
        print("   - subscribers table created")
    except Exception as e:
        print(f"❌ Error initializing DB: {e}")

if __name__ == "__main__":
    init_db()
