"""
API endpoint to send test push notifications
POST /api/fcm/test - Send a test notification to all FCM subscribers
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

def send_test_push_notification():
    """Send test push notification using Firebase Admin SDK."""
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging
        
        # Initialize Firebase Admin SDK if not already initialized
        if not firebase_admin._apps:
            # Get Firebase credentials from environment or file
            cred_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'firebase-service-account.json')
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
            else:
                # Try to use environment variable
                cred_json = os.getenv('FIREBASE_SERVICE_ACCOUNT')
                if cred_json:
                    cred = credentials.Certificate(json.loads(cred_json))
                else:
                    return {'success': False, 'error': 'Firebase credentials not found'}
            
            firebase_admin.initialize_app(cred)
        
        # Get all active FCM tokens from database
        conn, success = get_db_connection()
        if not conn:
            return {'success': False, 'error': 'Database connection failed'}
        
        cursor = conn.cursor()
        cursor.execute("SELECT token FROM fcm_subscribers WHERE active = TRUE")
        tokens = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        if not tokens:
            return {'success': True, 'sent': 0, 'failed': 0, 'total_subscribers': 0, 'message': 'No subscribers found'}
        
        # Create test notification message
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title='🧪 Test Notification',
                body='This is a test notification from WaveSignals admin panel!'
            ),
            data={
                'url': 'https://wavesignals.waveseed.app',
                'test': 'true'
            },
            tokens=tokens
        )
        
        # Send notification
        response = messaging.send_multicast(message)
        
        # Mark failed tokens as inactive
        if response.failure_count > 0:
            failed_tokens = []
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    failed_tokens.append(tokens[idx])
            
            if failed_tokens:
                conn, _ = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    for token in failed_tokens:
                        cursor.execute("UPDATE fcm_subscribers SET active = FALSE WHERE token = %s", (token,))
                    conn.commit()
                    cursor.close()
                    conn.close()
        
        return {
            'success': True,
            'sent': response.success_count,
            'failed': response.failure_count,
            'total_subscribers': len(tokens)
        }
        
    except ImportError:
        return {'success': False, 'error': 'Firebase Admin SDK not installed'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Admin-Key')
        self.end_headers()

    def do_POST(self):
        """Send test notification to all subscribers."""
        try:
            # Check admin authentication
            admin_key = self.headers.get('X-Admin-Key')
            expected_key = os.getenv('ADMIN_PASSWORD', 'wavesignals@2025')
            
            if not admin_key or admin_key != expected_key:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'Unauthorized - Invalid admin key'
                }).encode())
                return
            
            # Send test notification
            result = send_test_push_notification()
            
            status_code = 200 if result.get('success') else 500
            self.send_response(status_code)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': str(e)
            }).encode())
