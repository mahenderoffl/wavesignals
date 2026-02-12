"""
API endpoint to get FCM push notification subscribers
GET /api/fcm-subscribers - Returns list of FCM subscribers with tokens
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2
from urllib.parse import parse_qs

def get_db_connection():
    """Get database connectionwith multi-database fallback."""
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
        """Get FCM subscribers list."""
        try:
            # Simple admin authentication (check for admin key)
            admin_key = self.headers.get('X-Admin-Key')
            expected_key = os.getenv('ADMIN_PASSWORD', 'admin123')
            
            if not admin_key or admin_key != expected_key:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'Unauthorized'
                }).encode())
                return

            conn, connected = get_db_connection()
            
            if not connected or not conn:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'Database connection failed',
                    'subscribers': []
                }).encode())
                return

            cursor = conn.cursor()
            
            # Get FCM subscribers (push notification tokens)
            cursor.execute("""
                SELECT token, device_type, created_at, last_used 
                FROM fcm_subscribers 
                WHERE active = TRUE
                ORDER BY created_at DESC
            """)
            
            fcm_subscribers = []
            for row in cursor.fetchall():
                fcm_subscribers.append({
                    'token': row[0],
                    'device_type': row[1],
                    'created_at': row[2].isoformat() if row[2] else None,
                    'last_used': row[3].isoformat() if row[3] else None
                })
            
            cursor.close()
            conn.close()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps({
                'success': True,
                'subscribers': fcm_subscribers,
                'total': len(fcm_subscribers)
            }).encode())

        except Exception as e:
            print(f"Error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': str(e),
                'subscribers': []
            }).encode())
