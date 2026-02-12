"""
POST /api/fcm-subscribe - Subscribe to push notifications
Standalone version with inline DB connection for Vercel
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Get database connection"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}
            
            token = data.get('token')
            user_agent = data.get('userAgent', '')
            
            if not token:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Token required"}).encode())
                return
            
            print(f"📱 FCM token received: {token[:30]}...")
            
            conn = get_db_connection()
            if not conn:
                print("❌ FCM subscribe: Database connection failed")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Database connection failed"}).encode())
                return
            
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO fcm_subscribers (token, user_agent, device_type, last_used) 
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (token) 
                DO UPDATE SET last_used = NOW(), user_agent = EXCLUDED.user_agent, device_type = EXCLUDED.device_type, active = TRUE
            """, (token, user_agent, user_agent))
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"✅ FCM token subscribed successfully")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "message": "Subscribed to notifications"}).encode())
            
        except Exception as e:
            print(f"❌ FCM subscription error: {e}")
            import traceback
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
