from flask import Flask, jsonify, request
from flask_cors import CORS
from db import get_db_connection, init_db  # Added init_db import
from bot import publish_post
from apscheduler.schedulers.background import BackgroundScheduler
import os
import atexit
import requests
from datetime import datetime
from functools import wraps

app = Flask(__name__)
# CORS restricted to known frontend domains for security
CORS(app, origins=[
    "https://wavesignals.waveseed.app",
    "https://wavesignals.netlify.app",
    "https://project3test.netlify.app",
    "http://localhost:3000"  # For local development
])

# Initialize database tables on startup
print("🔧 Initializing database tables...")
try:
    init_db()
    print("✅ Database initialization complete")
except Exception as e:
    print(f"❌ CRITICAL: Database initialization failed: {e}")
    print("⚠️ App may not function correctly! Check DATABASE_URL environment variable.")
    # Don't exit - let health check report the issue

# ==================================================================
# BUTTONDOWN NEWSLETTER INTEGRATION
# ==================================================================
BUTTONDOWN_API_KEY = os.getenv("BUTTONDOWN_API_KEY")

def subscribe_to_buttondown(email):
    """
    Subscribe email to Buttondown newsletter.
    Called AFTER successful PostgreSQL insert (non-blocking).
    Failures are logged but don't affect the main signup flow.
    """
    if not BUTTONDOWN_API_KEY:
        print("⚠️ BUTTONDOWN_API_KEY not configured - skipping Buttondown sync")
        return {"success": False, "error": "API key not configured"}
    
    url = "https://api.buttondown.email/v1/subscribers"
    headers = {
        "Authorization": f"Token {BUTTONDOWN_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "email": email,
        "tags": ["wavesignals"],
        "notes": f"Subscribed from WaveSignals website on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
    }
    
    try:
        print(f"📧 Syncing to Buttondown: {email}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 201:
            print(f"✅ Buttondown sync successful: {email}")
            return {"success": True, "response": response.json()}
        elif response.status_code == 409:
            # Already subscribed in Buttondown (not an error)
            print(f"ℹ️ Already subscribed in Buttondown: {email}")
            return {"success": True, "already_subscribed": True}
        else:
            print(f"❌ Buttondown API error: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
    
    except requests.exceptions.Timeout:
        print(f"⚠️ Buttondown API timeout for: {email}")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"❌ Buttondown error for {email}: {e}")
        return {"success": False, "error": str(e)}
 

# --- SECURITY ---
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "wavesignals@2025") # Default fallback, User must change this!

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Admin-Key')
        if not token or token != ADMIN_PASSWORD:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# --- AUTOMATION (DAILY CRON) ---
# Runs the bot every day at 6:00 AM UTC (11:30 AM IST)
def daily_auto_post():
    """Automated daily post generation - MUST NOT crash scheduler"""
    from datetime import datetime, timezone as tz
    trigger_time = datetime.now(tz.utc).isoformat()
    print(f"="*60)
    print(f"⏰ SCHEDULER TRIGGERED at {trigger_time}")
    print(f"="*60)
    try:
        result = publish_post()  # No parameters - rate limiting removed
        if result and result.get('success'):
            print(f"✅ Scheduled post published: {result.get('title')}")
        elif result and result.get('skipped'):
            print(f"ℹ️ Post skipped: {result.get('reason')}")
        else:
            error = result.get('error', 'Unknown error') if result else 'No result returned'
            print(f"❌ Scheduled post failed: {error}")
    except Exception as e:
        import traceback
        print(f"🚨 CRITICAL SCHEDULER ERROR: {e}")
        print(traceback.format_exc())
        # Scheduler continues - tomorrow will try again

# Start Scheduler with cron trigger
from apscheduler.triggers.cron import CronTrigger
import pytz

scheduler = BackgroundScheduler()

# Primary: Daily at 6 AM UTC
scheduler.add_job(
    func=daily_auto_post, 
    trigger=CronTrigger(hour=6, minute=0, timezone=pytz.UTC),  # Explicit UTC
    id='daily_post',
    name='Daily Auto Post',
    replace_existing=True
)

# Backup: Daily at 12 PM UTC (safety net)
scheduler.add_job(
    func=daily_auto_post,
    trigger=CronTrigger(hour=12, minute=0, timezone=pytz.UTC),
    id='backup_post',
    name='Backup Post Check',
    replace_existing=True
)

scheduler.start()
print("✅ Scheduler started: Daily posts at 6:00 AM UTC (11:30 AM IST)")
print("✅ Backup scheduler: 12:00 PM UTC (5:30 PM IST)")
atexit.register(lambda: scheduler.shutdown())

# Startup recovery: Check if we missed today's post due to restart
def check_and_recover_missed_post():
    """Ultra-aggressive recovery - generates if ANY condition met"""
    try:
        conn = get_db_connection()
        if not conn:
            return
        
        cur = conn.cursor()
        
        # Check if we have any post from today
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        today_str = now.strftime('%Y-%m-%d')
        
        cur.execute("""
            SELECT created_at FROM posts 
            WHERE DATE(created_at) = %s
        """, (today_str,))
        today_post = cur.fetchone()
        
        # Get last post time
        cur.execute("SELECT created_at FROM posts ORDER BY created_at DESC LIMIT 1")
        last_post = cur.fetchone()
        
        should_generate = False
        reason = ""
        
        # Condition 1: No post today
        if not today_post:
            should_generate = True
            reason = "No post published today"
        
        # Condition 2: >23h since last post (even if posted yesterday late)
        if last_post and not should_generate:
            last_time = last_post['created_at']
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=timezone.utc)
            
            hours_since = (now - last_time).total_seconds() / 3600
            
            if hours_since > 23:
                should_generate = True
                reason = f"Last post was {hours_since:.1f}h ago (>23h threshold)"
        
        # Condition 3: Past 6 AM and no post today
        today_scheduled = now.replace(hour=6, minute=0, second=0, microsecond=0)
        if now >= today_scheduled and not today_post:
            should_generate = True
            reason = f"Past scheduled time (6 AM) and no post today"
        
        if should_generate:
            print(f"⚠️ AGGRESSIVE RECOVERY: {reason}")
            print(f"   Generating post NOW...")
            daily_auto_post()
        else:
            print(f"✅ Recovery check: Post already exists for today")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Recovery check error: {e}")
        # If recovery fails, try to generate anyway (ultra-safe)
        try:
            daily_auto_post()
        except:
            pass

check_and_recover_missed_post()

# External cron can call this to force a recovery check
@app.route('/api/trigger-check', methods=['POST', 'GET'])
def trigger_recovery_check():
    """Endpoint for external cron to trigger recovery check - keeps space alive AND checks for missed posts"""
    from datetime import datetime, timezone as tz
    print(f"🔄 External trigger-check called at {datetime.now(tz.utc).isoformat()}")
    try:
        check_and_recover_missed_post()
        return jsonify({"success": True, "message": "Recovery check executed", "timestamp": datetime.now(tz.utc).isoformat()}), 200
    except Exception as e:
        import traceback
        print(f"❌ Trigger-check error: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        "status": "WaveSignals Brain Online", 
        "version": "2.1 (Secured)",
        "scheduler": "Running (Daily)"
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to keep Space alive and monitor system"""
    from datetime import datetime
    
    try:
        # Check database connection
        conn = get_db_connection()
        db_status = "connected" if conn else "disconnected"
        recent_posts = 0
        last_post = None
        total_posts = 0
        
        if conn:
            try:
                cur = conn.cursor()
                # Get total posts
                cur.execute("SELECT COUNT(*) as count FROM posts")
                total_posts = cur.fetchone()['count']
                
                # Get posts from last 24 hours
                cur.execute("SELECT COUNT(*) as count FROM posts WHERE date > NOW() - INTERVAL '24 hours'")
                recent_posts = cur.fetchone()['count']
                
                # Get last post info
                cur.execute("SELECT title, date FROM posts ORDER BY date DESC LIMIT 1")
                last_post_data = cur.fetchone()
                if last_post_data:
                    last_post = {
                        "title": last_post_data['title'],
                        "date": last_post_data['date'].isoformat()
                    }
                cur.close()
                conn.close()
            except Exception as e:
                print(f"Error querying database in health check: {e}")
        
        # Check scheduler status
        scheduler_status = "running" if scheduler.running else "stopped"
        next_job = None
        try:
            jobs = scheduler.get_jobs()
            if jobs:
                next_job = jobs[0].next_run_time.isoformat() if jobs[0].next_run_time else None
        except:
            next_job = "N/A"
        
        # Check API key
        groq_key_configured = bool(os.getenv('GROQ_API_KEY'))
        
        response = {
            "status": "alive",
            "message": "WaveSignals Backend is running",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "status": db_status,
                "total_posts": total_posts,
                "posts_24h": recent_posts,
                "last_post": last_post
            },
            "scheduler": {
                "status": scheduler_status,
                "next_run": next_job,
                "interval": "Every 12 hours"
            },
            "apis": {
                "groq_configured": groq_key_configured
            },
            "version": "2.2"
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/auth/verify', methods=['POST'])
@require_auth
def verify_auth():
    return jsonify({"valid": True})

@app.route('/api/posts', methods=['GET'])
def get_posts():
    conn = get_db_connection()
    if not conn:
        print("DB Connection failed in get_posts")
        return jsonify({"error": "Database error"}), 500
    
    try:
        cur = conn.cursor()
        # Fetch published posts, newest first
        # Include created_at as 'date' for frontend compatibility
        cur.execute("""
            SELECT *, created_at as date 
            FROM posts 
            WHERE published = TRUE 
            ORDER BY created_at DESC
        """)
        posts = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"posts": posts})
    except Exception as e:
        print(f"Error serving posts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/posts/<slug>', methods=['GET'])
def get_post(slug):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database error"}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM posts WHERE slug = %s", (slug,))
        post = cur.fetchone()
        cur.close()
        conn.close()
        
        if post:
            return jsonify(post)
        else:
            return jsonify({"error": "Post not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/posts', methods=['POST'])
@require_auth
def create_post():
    data = request.json
    required = ['title', 'slug', 'content']
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400
    
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Error"}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO posts (slug, title, excerpt, content, tags, image, published, date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """, (
            data['slug'], data['title'], data.get('excerpt', ''), 
            data['content'], data.get('tags', ''), data.get('image', ''),
            data.get('published', True)
        ))
        new_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Created", "id": new_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/posts/<int:id>', methods=['PUT'])
@require_auth
def update_post(id):
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Error"}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE posts 
            SET title=%s, slug=%s, excerpt=%s, content=%s, tags=%s, image=%s, published=%s
            WHERE id = %s
        """, (
            data['title'], data['slug'], data.get('excerpt', ''), 
            data['content'], data.get('tags', ''), data.get('image', ''),
            data.get('published', True), id
        ))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/posts/<int:id>', methods=['DELETE'])
@require_auth
def delete_post(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Error"}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM posts WHERE id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/settings', methods=['GET'])
def get_settings():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Error"}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT config FROM settings WHERE id = 1")
        row = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify(row['config'] if row else {})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/settings', methods=['PUT'])
@require_auth
def update_settings():
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Error"}), 500
    
    try:
        cur = conn.cursor()
        # Merge existing config with new data using JSONB concatenation (||) is one way, 
        # but here we'll just replace or update top-level keys. 
        # Ideally, we read, merge in python, and write back, OR use jsonb_set.
        # Simple approach: Overwrite or Merge in Python.
        
        cur.execute("SELECT config FROM settings WHERE id = 1")
        current_config = cur.fetchone()['config']
        
        # Merge in Python to allow partial updates
        updated_config = {**current_config, **data}
        
        import json
        cur.execute("UPDATE settings SET config = %s WHERE id = 1", (json.dumps(updated_config),))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Settings Updated", "config": updated_config}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === BOT ENDPOINTS ===
@app.route('/api/rate-limit-status', methods=['GET'])
def rate_limit_status():
    """Get current rate limit status"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT created_at FROM posts ORDER BY created_at DESC LIMIT 1")
        last_post = cur.fetchone()
        cur.close()
        conn.close()
        
        if last_post:
            from datetime import datetime, timezone
            last_post_time = last_post['created_at']
            
            if last_post_time.tzinfo is None:
                last_post_time = last_post_time.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            hours_since = (now - last_post_time).total_seconds() / 3600
            hours_remaining = max(0, 23 - hours_since)
            can_post = hours_since >= 23
            
            return jsonify({
                "success": True,
                "hours_since_last": hours_since,
                "hours_remaining": hours_remaining,
                "can_post": can_post,
                "last_post_time": last_post_time.isoformat()
            })
        else:
            return jsonify({
                "success": True,
                "hours_since_last": None,
                "hours_remaining": 0,
                "can_post": True,
                "last_post_time": None
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-post', methods=['POST'])
@require_auth
def generate_post_api():
    """Manual trigger for AI post generation with emergency override support"""
    try:
        from bot import publish_post
        import traceback
        
        # Check for emergency override header
        # No emergency override needed - rate limiting removed from publish_post()
        print("🚀 Manual post generation triggered...")
        
        result = publish_post()  # No parameters needed
        
        if isinstance(result, dict) and result.get("success"):
            return jsonify({
                'success': True,
                'status': 'success', 
                'message': 'Post generated and published successfully',
                'post_id': result.get("id"),
                'title': result.get("title")
            }), 200
        elif isinstance(result, dict) and not result.get("success"):
            return jsonify({
                'success': False,
                'status': 'error',
                'error': result.get('error'),
                'message': f"Generation failed: {result.get('error')}"
            }), 400
        else:
            return jsonify({
                'success': False,
                'status': 'error', 
                'message': 'publish_post returned unexpected format - check logs'
            }), 500
            
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"❌ Post generation error: {error_trace}")
        return jsonify({
            'success': False,
            'status': 'error', 
            'message': str(e),
            'traceback': error_trace
        }), 500

@app.route('/api/bot-status', methods=['GET'])
def bot_status():
    """Check if GROQ_API_KEY is configured"""
    import os
    has_key = bool(os.getenv('GROQ_API_KEY'))
    return jsonify({
        'api_key_configured': has_key,
        'status': 'ready' if has_key else 'missing_api_key'
    })

# === SUBSCRIBERS ===
@app.route('/api/subscribers', methods=['GET'])
def get_subscribers():
    """Get all subscribers"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM subscribers ORDER BY created_at DESC')
        subscribers = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({'subscribers': subscribers})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/subscribers', methods=['POST'])
def add_subscriber():
    """Add a new subscriber"""
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cur = conn.cursor()
        # Check if already subscribed
        cur.execute('SELECT id FROM subscribers WHERE email = %s', (email,))
        existing = cur.fetchone()
        
        if existing:
            cur.close()
            conn.close()
            return jsonify({'message': 'Already subscribed', 'already_subscribed': True}), 200
        
        # Add new subscriber
        cur.execute(
            'INSERT INTO subscribers (email, created_at) VALUES (%s, NOW()) RETURNING id',
            (email,)
        )
        subscriber_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ New subscriber: {email} (ID: {subscriber_id})")
        
        # ===== BUTTONDOWN SYNC (NON-BLOCKING) =====
        # Sync to Buttondown newsletter (best-effort, doesn't affect signup success)
        try:
            buttondown_result = subscribe_to_buttondown(email)
            if not buttondown_result.get('success'):
                print(f"⚠️ Buttondown sync failed (non-critical): {buttondown_result.get('error')}")
                # Don't fail the request - PostgreSQL succeeded, which is what matters
        except Exception as e:
            print(f"❌ Buttondown exception (non-critical): {e}")
            # Continue - user subscription is valid in PostgreSQL
        # ===== END BUTTONDOWN SYNC =====
        
        return jsonify({
            'success': True,
            'message': 'Successfully subscribed!',
            'id': subscriber_id
        }), 201
        
    except Exception as e:
        print(f"❌ Subscription error: {e}")
        return jsonify({'error': str(e)}), 500

# === PUSH NOTIFICATIONS (FCM) ===
@app.route('/api/fcm/subscribe', methods=['POST'])
def fcm_subscribe():
    """Subscribe to push notifications"""
    import traceback
    print(f"📱 FCM subscribe request received")
    
    try:
        data = request.json
        if not data:
            print("❌ FCM subscribe: No JSON data in request")
            return jsonify({"error": "No data provided"}), 400
            
        token = data.get('token')
        user_agent = data.get('userAgent', '')
        
        if not token:
            print("❌ FCM subscribe: Token missing from request")
            return jsonify({"error": "Token required"}), 400
        
        print(f"📱 FCM token received: {token[:30]}...")
        
        conn = get_db_connection()
        if not conn:
            print("❌ FCM subscribe: Database connection failed")
            return jsonify({"error": "Database connection failed"}), 500
        
        cur = conn.cursor()
        # Insert or update token
        cur.execute("""
            INSERT INTO fcm_subscribers (token, user_agent, device_type, last_used) 
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (token) 
            DO UPDATE SET last_used = NOW(), user_agent = EXCLUDED.user_agent, device_type = EXCLUDED.device_type, active = TRUE
        """, (token, user_agent, user_agent))
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ FCM token subscribed successfully: {token[:20]}...")
        return jsonify({"success": True, "message": "Subscribed to notifications"})
        
    except Exception as e:
        print(f"❌ FCM subscription error: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e), "details": traceback.format_exc()}), 500

@app.route('/api/notifications/send', methods=['POST'])
@require_auth
def send_custom_notification():
    """Send custom push notification to all subscribers"""
    try:
        from fcm import send_custom_notification
        
        data = request.json
        title = data.get('title', '').strip()
        body = data.get('body', '').strip()
        url = data.get('url', '').strip()
        
        if not title or not body:
            return jsonify({"error": "Title and body are required"}), 400
        
        print(f"📩 Admin sending custom notification: {title}")
        result = send_custom_notification(title, body, url if url else None)
        
        if result.get('success'):
            return jsonify({
                "success": True,
                "sent": result.get('sent', 0),
                "failed": result.get('failed', 0),
                "message": f"Notification sent to {result.get('sent', 0)} subscribers"
            }), 200
        else:
            return jsonify({"error": result.get('error', 'Unknown error')}), 500
            
    except Exception as e:
        print(f"❌ Custom notification error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/notifications/subscribers', methods=['GET'])
@require_auth
def get_notification_subscribers():
    """Get list of notification subscribers"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB error"}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, token, created_at, last_used, user_agent, device_type 
            FROM fcm_subscribers 
            WHERE active = TRUE
            ORDER BY created_at DESC
        """)
        subscribers = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"subscribers": subscribers})
    except Exception as e:
        print(f"❌ Error fetching subscribers: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fcm/test', methods=['POST'])
@require_auth
def fcm_test():
    """Send test notification to all subscribers (admin only)"""
    try:
        from fcm import send_test_notification
        result = send_test_notification()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/fcm/count', methods=['GET'])
def fcm_count():
    """Get count of FCM subscribers"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB error"}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM fcm_subscribers WHERE active = TRUE")
        count = cur.fetchone()['count']
        cur.close()
        conn.close()
        return jsonify({"success": True, "count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860))  # Default to 7860 for Hugging Face Spaces
    print("=" * 60)
    print("🚀 Starting WaveSignals Backend API Server")
    print("=" * 60)
    print(f"📡 Port: {port}")
    print(f"🏥 Health Check: http://0.0.0.0:{port}/health")
    print(f"📊 API Base: http://0.0.0.0:{port}/api")
    print(f"⏰ Scheduler: Running (Daily at 6:00 AM UTC)")
    print(f"🔐 Admin Auth: Enabled (X-Admin-Key header required)")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False)
