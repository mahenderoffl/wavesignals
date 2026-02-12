"""
API endpoint for site settings
GET /api/settings - Returns site settings
PUT /api/settings - Update site settings (requires admin key)
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
        self.send_header('Access-Control-Allow-Methods', 'GET, PUT, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Admin-Key')
        self.end_headers()

    def do_GET(self):
        """Get site settings."""
        try:
            conn, success = get_db_connection()
            if not conn:
                # Return default settings if database connection fails
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'siteName': 'WaveSignals',
                    'siteDescription': 'One signal per day. No noise.',
                    'siteUrl': 'https://wavesignals.waveseed.app',
                    'contactEmail': '',
                    'gaId': 'G-RGL9J7FMMN',
                    'gscVerification': '',
                    'metaDescription': 'One signal per day. No noise.',
                    'metaKeywords': 'career, money, technology, behavior',
                    'twitter': '',
                    'linkedin': '',
                    'github': '',
                    'facebook': '',
                    'defaultCategory': 'Career',
                    'postsPerPage': '10',
                    'autoPublish': False,
                    'showExcerpts': True,
                    'customCss': '',
                    'customJs': '',
                    'webhookUrl': ''
                }).encode())
                return

            cursor = conn.cursor()
            
            # Check if settings table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'settings'
                )
            """)
            
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                # Create settings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        id SERIAL PRIMARY KEY,
                        key VARCHAR(100) UNIQUE NOT NULL,
                        value TEXT,
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                conn.commit()
            
            # Get all settings
            cursor.execute("SELECT key, value FROM settings")
            rows = cursor.fetchall()
            
            settings = {}
            for row in rows:
                try:
                    settings[row[0]] = json.loads(row[1])
                except:
                    settings[row[0]] = row[1]
            
            cursor.close()
            conn.close()

            # Return default values for missing settings
            default_settings = {
                'siteName': 'WaveSignals',
                'siteDescription': 'One signal per day. No noise.',
                'siteUrl': 'https://wavesignals.waveseed.app',
                'contactEmail': '',
                'gaId': 'G-RGL9J7FMMN',
                'gscVerification': '',
                'metaDescription': 'One signal per day. No noise.',
                'metaKeywords': 'career, money, technology, behavior',
                'twitter': '',
                'linkedin': '',
                'github': '',
                'facebook': '',
                'defaultCategory': 'Career',
                'postsPerPage': '10',
                'autoPublish': False,
                'showExcerpts': True,
                'customCss': '',
                'customJs': '',
                'webhookUrl': ''
            }
            
            # Merge with defaults
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(settings).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': str(e)
            }).encode())

    def do_PUT(self):
        """Update site settings (admin only)."""
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
            
            # Parse request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            settings_data = json.loads(post_data.decode())
            
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
            
            # Ensure settings table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR(100) UNIQUE NOT NULL,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
            
            # Update each setting
            for key, value in settings_data.items():
                value_str = json.dumps(value) if not isinstance(value, str) else value
                cursor.execute("""
                    INSERT INTO settings (key, value, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (key) 
                    DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
                """, (key, value_str))
            
            conn.commit()
            cursor.close()
            conn.close()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': True,
                'message': 'Settings updated successfully'
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
