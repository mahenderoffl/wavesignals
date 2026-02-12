"""
API endpoint for FCM (Firebase Cloud Messaging) operations
Handles all FCM-related operations in a single serverless function

Routes:
- GET /api/fcm?action=count - Get subscriber count
- POST /api/fcm?action=subscribe - Subscribe to push notifications
- POST /api/fcm?action=test - Send test notification (admin only)
- GET /api/fcm?action=subscribers - Get subscriber list (admin only)
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2
from urllib.parse import parse_qs, urlparse

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
            cred_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'firebase-service-account.json')
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
            else:
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
        
        # Create test notification messages for each token
        messages = []
        for token in tokens:
            messages.append(messaging.Message(
                notification=messaging.Notification(
                    title='🧪 Test Notification',
                    body='This is a test notification from WaveSignals admin panel!'
                ),
                data={
                    'url': 'https://wavesignals.waveseed.app',
                    'test': 'true'
                },
                token=token
            ))
        
        # Send notifications
        response = messaging.send_each(messages)
        
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
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Admin-Key')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests - count and subscribers list."""
        try:
            # Parse query parameters
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            action = params.get('action', ['count'])[0]
            
            if action == 'count':
                # Get subscriber count
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
            
            elif action == 'subscribers':
                # Get subscriber list (admin only)
                admin_key = self.headers.get('X-Admin-Key')
                expected_key = os.getenv('ADMIN_PASSWORD', 'wavesignals@2025')
                
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
                cursor.execute("""
                    SELECT token, user_agent, device_type, created_at, last_used, active 
                    FROM fcm_subscribers 
                    ORDER BY created_at DESC
                """)
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
                
                subscribers = []
                for row in rows:
                    subscribers.append({
                        'token': row[0],  # Full token for sending notifications
                        'token_preview': row[0][:20] + '...',  # Preview for display
                        'user_agent': row[1],
                        'device_type': row[2],
                        'created_at': row[3].isoformat() if row[3] else None,
                        'last_used': row[4].isoformat() if row[4] else None,
                        'active': row[5]
                    })
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'subscribers': subscribers,
                    'count': len(subscribers)
                }).encode())
            
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'Invalid action'
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

    def do_POST(self):
        """Handle POST requests - subscribe and test."""
        try:
            # Parse query parameters
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            action = params.get('action', ['subscribe'])[0]
            
            if action == 'subscribe':
                # Subscribe to push notifications
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode())
                
                token = data.get('token')
                user_agent = data.get('userAgent', '')
                
                if not token:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False,
                        'error': 'Token is required'
                    }).encode())
                    return
                
                # Detect device type
                device_type = 'unknown'
                if 'Mobile' in user_agent or 'Android' in user_agent:
                    device_type = 'mobile'
                elif 'Tablet' in user_agent or 'iPad' in user_agent:
                    device_type = 'tablet'
                else:
                    device_type = 'desktop'
                
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
                cursor.execute("""
                    INSERT INTO fcm_subscribers (token, user_agent, device_type, last_used)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (token) 
                    DO UPDATE SET 
                        last_used = NOW(), 
                        user_agent = EXCLUDED.user_agent,
                        device_type = EXCLUDED.device_type,
                        active = TRUE
                    RETURNING id
                """, (token, user_agent, device_type))
                
                subscriber_id = cursor.fetchone()[0]
                conn.commit()
                cursor.close()
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'message': 'Subscribed successfully',
                    'id': subscriber_id
                }).encode())
            
            elif action == 'test':
                # Send test notification (admin only)
                admin_key = self.headers.get('X-Admin-Key')
                expected_key = os.getenv('ADMIN_PASSWORD', 'wavesignals@2025')
                
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
                
                result = send_test_push_notification()
                
                status_code = 200 if result.get('success') else 500
                self.send_response(status_code)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'Invalid action'
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
