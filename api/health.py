"""
GET /api/health - Health check endpoint
Multi-database fallback: OLD_DB -> NEW_DB -> JSON
"""
from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_multi_db_connection():
    """Try to connect to databases in priority order"""
    databases = [
        (os.getenv("OLD_DATABASE_URL"), "old_db"),
        (os.getenv("NEW_DATABASE_URL"), "new_db"),
        (os.getenv("DATABASE_URL"), "fallback_db")
    ]
    
    for db_url, db_name in databases:
        if not db_url:
            continue
        try:
            conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
            print(f"✅ Connected to {db_name}")
            return conn, db_name
        except Exception as e:
            print(f"⚠️ {db_name} connection failed: {e}")
            continue
    
    return None, 'none'

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Check database with fallback
            conn, db_source = get_multi_db_connection()
            db_status = "connected" if conn else "disconnected"
            total_posts = 0
            recent_posts = 0
            last_post = None
            
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT COUNT(*) as count FROM posts")
                    total_posts = cur.fetchone()['count']
                    
                    cur.execute("SELECT COUNT(*) as count FROM posts WHERE created_at > NOW() - INTERVAL '24 hours'")
                    recent_posts = cur.fetchone()['count']
                    
                    cur.execute("SELECT title, created_at FROM posts ORDER BY created_at DESC LIMIT 1")
                    last_post_data = cur.fetchone()
                    if last_post_data:
                        last_post = {
                            "title": last_post_data['title'],
                            "date": last_post_data['created_at'].isoformat()
                        }
                    cur.close()
                    conn.close()
                except Exception as e:
                    print(f"DB query error: {e}")
            else:
                # Fallback to JSON
                try:
                    json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'posts.json')
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        json_posts = data.get('posts', [])
                        total_posts = len(json_posts)
                        db_source = "json_fallback"
                        if json_posts:
                            last_post = {
                                "title": json_posts[0].get('title', 'Unknown'),
                                "date": json_posts[0].get('date', 'Unknown')
                            }
                except Exception as e:
                    print(f"JSON fallback error: {e}")
            
            response = {
                "status": "alive",
                "message": "WaveSignals Backend (Vercel Multi-DB)",
                "timestamp": datetime.utcnow().isoformat(),
                "database": {
                    "status": db_status,
                    "source": db_source,
                    "total_posts": total_posts,
                    "posts_24h": recent_posts,
                    "last_post": last_post
                },
                "cron": {
                    "status": "External cron-job.org",
                    "endpoint": "/api/cron",
                    "schedule": "Daily at 6:00 AM UTC"
                },
                "version": "3.1-multi-db"
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            import traceback
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "error": str(e), "trace": traceback.format_exc()}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.end_headers()
