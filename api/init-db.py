"""
GET /api/init-db - Initialize database tables
Call this once to set up tables in Neon DB
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "DATABASE_URL not configured"}).encode())
            return
        
        try:
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
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
            
            # Create Subscribers Table
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
            
            # Migrate old fcm_tokens to fcm_subscribers if needed
            cur.execute("""
                INSERT INTO fcm_subscribers (token, user_agent, device_type, created_at, last_used)
                SELECT token, user_agent, device_type, created_at, last_used
                FROM fcm_tokens
                WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'fcm_tokens')
                AND NOT EXISTS (SELECT 1 FROM fcm_subscribers WHERE fcm_subscribers.token = fcm_tokens.token)
                ON CONFLICT (token) DO NOTHING;
            """)
            
            # Create Settings Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id SERIAL PRIMARY KEY,
                    config JSONB DEFAULT '{}'::jsonb
                );
            """)
            
            conn.commit()
            cur.close()
            conn.close()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "message": "Database tables created successfully",
                "tables": ["posts", "subscribers", "fcm_subscribers", "settings"]
            }).encode())
            
        except Exception as e:
            import traceback
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": str(e),
                "trace": traceback.format_exc()
            }).encode())
