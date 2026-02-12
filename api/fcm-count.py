"""
API endpoint to get FCM push notification subscriber count
GET /api/fcm/count - Returns count of active FCM subscribers
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2

def get_db_connection():
    """Get database connection with multi-database fallback."""
    db_urls = [
        os.getenv('OLD_DATABASE_URL'),
        os.getenv('NEW_DATABASE_URL'),
        os.getenv('DATABASE_URL')
    ]
    
    for db_url in db_urls:
        if db_url:
            try:
                conn = psycopg2.connect(db_url)
                return conn, True
            except Exception as e:
                print(f"Failed to connect to DB: {e}")
                continue
    
    return None, False

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Admin-Key')
        self.end_headers()

    def do_GET(self):
        """Get FCM subscriber count."""
        try:
            conn, success = get_db_connection()
            if not conn:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'Database connection failed'
                }).encode())
                return

            cursor = conn.cursor()
            
            # Count active FCM subscribers
            cursor.execute("SELECT COUNT(*) FROM fcm_subscribers WHERE active = TRUE")
            count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps({
                'success': True,
                'count': count
            }).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': str(e)
            }).encode())
