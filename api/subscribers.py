"""
POST /api/subscribers - Subscribe to newsletter
Multi-database fallback: OLD_DB -> NEW_DB -> DATABASE_URL
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Get database connection with multi-database fallback"""
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
            print(f"✅ Subscribers connected to {db_name}")
            return conn
        except Exception as e:
            print(f"⚠️ {db_name} connection failed: {e}")
            continue
    
    print("❌ All database connections failed")
    return None

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}
            
            email = data.get('email', '').strip()
            
            if not email:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Email is required"}).encode())
                return
            
            conn = get_db_connection()
            if not conn:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Database connection failed"}).encode())
                return
            
            cur = conn.cursor()
            
            # Check if already subscribed
            cur.execute('SELECT id FROM subscribers WHERE email = %s', (email,))
            existing = cur.fetchone()
            
            if existing:
                cur.close()
                conn.close()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Already subscribed", "already_subscribed": True}).encode())
                return
            
            # Add new subscriber
            cur.execute(
                'INSERT INTO subscribers (email, created_at) VALUES (%s, NOW()) RETURNING id',
                (email,)
            )
            subscriber_id = cur.fetchone()['id']
            conn.commit()
            cur.close()
            conn.close()
            
            self.send_response(201)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "message": "Successfully subscribed!",
                "id": subscriber_id
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        # Return list of subscribers (for admin)
        conn = get_db_connection()
        if not conn:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Database error"}).encode())
            return
        
        try:
            cur = conn.cursor()
            cur.execute('SELECT id, email, created_at, status FROM subscribers ORDER BY created_at DESC')
            subscribers = cur.fetchall()
            cur.close()
            conn.close()
            
            for sub in subscribers:
                if sub.get('created_at'):
                    sub['created_at'] = sub['created_at'].isoformat()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"subscribers": subscribers}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
