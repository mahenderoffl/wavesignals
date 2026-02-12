"""
API endpoint to send push notifications to specific FCM tokens
POST /api/send-notification - Send notification to selected subscribers
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import firebase_admin
from firebase_admin import credentials, messaging

# Initialize Firebase Admin (singleton pattern)
def init_firebase():
    """Initialize Firebase Admin SDK."""
    if not firebase_admin._apps:
        try:
            # Try to load from environment variable (JSON string)
            firebase_json = os.getenv('FIREBASE_SERVICE_ACCOUNT')
            if firebase_json:
                cred_dict = json.loads(firebase_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                return True
        except Exception as e:
            print(f"Failed to initialize Firebase: {e}")
            return False
    return True

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Admin-Key')
        self.end_headers()

    def do_POST(self):
        """Send notification to selected FCM tokens."""
        try:
            # Simple admin authentication
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

            # Parse request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            title = data.get('title', '').strip()
            body = data.get('body', '').strip()
            url = data.get('url', '').strip()
            tokens = data.get('tokens', [])

            if not title or not body:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'Title and body are required'
                }).encode())
                return

            if not tokens or len(tokens) == 0:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'At least one token is required'
                }).encode())
                return

            # Initialize Firebase
            if not init_firebase():
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'Firebase initialization failed'
                }).encode())
                return

            # Prepare notification payload
            notification_payload = messaging.Notification(
                title=title,
                body=body
            )

            # Prepare data payload (for click action)
            data_payload = {}
            if url:
                data_payload['click_action'] = url
                data_payload['url'] = url

            # Send to each token (batch sending with multicast)
            success_count = 0
            failed_count = 0
            
            # Firebase supports sending to up to 500 tokens at once
            batch_size = 500
            for i in range(0, len(tokens), batch_size):
                batch_tokens = tokens[i:i + batch_size]
                
                try:
                    message = messaging.MulticastMessage(
                        tokens=batch_tokens,
                        notification=notification_payload,
                        data=data_payload,
                        webpush=messaging.WebpushConfig(
                            notification=messaging.WebpushNotification(
                                title=title,
                                body=body,
                                icon='/favicon.ico',
                                badge='/favicon.ico'
                            ),
                            fcm_options=messaging.WebpushFCMOptions(
                                link=url if url else '/'
                            )
                        )
                    )
                    
                    response = messaging.send_multicast(message)
                    success_count += response.success_count
                    failed_count += response.failure_count

                    # Log any failures
                    if response.failure_count > 0:
                        for idx, resp in enumerate(response.responses):
                            if not resp.success:
                                print(f"Failed to send to token {batch_tokens[idx]}: {resp.exception}")
                
                except Exception as e:
                    print(f"Error sending batch: {e}")
                    failed_count += len(batch_tokens)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps({
                'success': True,
                'sent': success_count,
                'failed': failed_count,
                'total': len(tokens),
                'message': f'Notification sent to {success_count} out of {len(tokens)} subscribers'
            }).encode())

        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': 'Invalid JSON in request body'
            }).encode())

        except Exception as e:
            print(f"Error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': str(e)
            }).encode())
