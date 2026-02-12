import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import time
import json

load_dotenv()

# Multi-database support
OLD_DATABASE_URL = os.getenv("OLD_DATABASE_URL")
NEW_DATABASE_URL = os.getenv("NEW_DATABASE_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection(retry_count=3, prefer_old=True):
    """
    Get database connection with multi-database fallback
    Priority: OLD_DATABASE_URL -> NEW_DATABASE_URL -> DATABASE_URL
    
    Args:
        retry_count: Number of retry attempts per database
        prefer_old: If True, prioritize old database (default for reads)
    
    Returns: connection or None
    """
    databases = [
        (OLD_DATABASE_URL, "old_db"),
        (NEW_DATABASE_URL, "new_db"),
        (DATABASE_URL, "fallback_db")
    ]
    
    for db_url, db_name in databases:
        if not db_url:
            continue
            
        for attempt in range(retry_count):
            try:
                conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
                if attempt > 0:
                    print(f"✅ {db_name} connected on attempt {attempt + 1}")
                else:
                    print(f"✅ Connected to {db_name}")
                return conn
            except Exception as e:
                print(f"❌ {db_name} connection attempt {attempt + 1}/{retry_count} failed: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2)
        
        print(f"🔴 All {retry_count} attempts failed for {db_name}, trying next database...")
    
    print("🔴 All database connections failed")
    return None

def get_primary_db_connection(retry_count=3):
    """
    Get PRIMARY database connection for WRITE operations.
    Prioritizes OLD_DATABASE_URL (primary) for writes.
    """
    primary_url = OLD_DATABASE_URL or NEW_DATABASE_URL or DATABASE_URL
    
    if not primary_url:
        print("❌ No primary database URL configured")
        return None
    
    db_name = "primary_db"
    for attempt in range(retry_count):
        try:
            conn = psycopg2.connect(primary_url, cursor_factory=RealDictCursor)
            if attempt > 0:
                print(f"✅ {db_name} connected on attempt {attempt + 1}")
            else:
                print(f"✅ Connected to {db_name} for write")
            return conn
        except Exception as e:
            print(f"❌ {db_name} connection attempt {attempt + 1}/{retry_count} failed: {e}")
            if attempt < retry_count - 1:
                time.sleep(2)
    
    print(f"🔴 All {retry_count} connection attempts failed for primary database")
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
        
        # Create FCM Subscribers Table for Push Notifications
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fcm_subscribers (
                id SERIAL PRIMARY KEY,
                token TEXT UNIQUE NOT NULL,
                device_type VARCHAR(100),
                user_agent TEXT,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                preferences JSONB DEFAULT '{}'::jsonb
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_fcm_active ON fcm_subscribers(active);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_fcm_token ON fcm_subscribers(token);")
        
        # Migrate old fcm_tokens to fcm_subscribers if needed (safe migration)
        try:
            cur.execute("""
                INSERT INTO fcm_subscribers (token, user_agent, device_type, created_at, last_used)
                SELECT token, user_agent, device_type, created_at, last_used
                FROM fcm_tokens
                WHERE NOT EXISTS (SELECT 1 FROM fcm_subscribers WHERE fcm_subscribers.token = fcm_tokens.token)
                ON CONFLICT (token) DO NOTHING;
            """)
        except:
            # fcm_tokens table doesn't exist yet, that's okay
            pass
        
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
        print("   - fcm_subscribers table created")
    except Exception as e:
        print(f"❌ Error initializing DB: {e}")

if __name__ == "__main__":
    init_db()
