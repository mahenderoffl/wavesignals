from flask import Flask, jsonify, request
from flask_cors import CORS
from db import get_db_connection
from bot import publish_post
from apscheduler.schedulers.background import BackgroundScheduler
import os
import atexit
from functools import wraps

app = Flask(__name__)
# Enable CORS for all domains (or restrict to your specific Netlify domain for extra security)
CORS(app) 

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

# --- AUTOMATION (INTERNAL CRON) ---
# Runs the bot every 24 hours to generate a new post
def daily_auto_post():
   print("⏰ Internal Cron Triggered: Publishing new post...")
   publish_post()

# Start Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=daily_auto_post, trigger="interval", hours=12) 
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

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
        api_key_configured = bool(os.getenv('GEMINI_API_KEY'))
        gemini_key = os.getenv('GEMINI_API_KEY', '')
        
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
                "gemini_configured": api_key_configured,
                "gemini_key_preview": gemini_key[:15] + "..." if gemini_key else "NOT SET"
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
        cur.execute("SELECT * FROM posts WHERE published = TRUE ORDER BY date DESC")
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
@app.route('/api/generate-post', methods=['POST'])
def generate_post_api():
    """Manual trigger for AI post generation"""
    try:
        from bot import publish_post
        import traceback
        
        print("🚀 Manual post generation triggered...")
        result = publish_post()
        
        if isinstance(result, dict) and result.get("success"):
            return jsonify({
                'status': 'success', 
                'message': 'Post generated and published successfully',
                'post_id': result.get("id"),
                'title': result.get("title")
            }), 200
        elif isinstance(result, dict) and not result.get("success"):
            return jsonify({
                'status': 'error',
                'message': f"Generation failed: {result.get('error')}"
            }), 500
        else:
            return jsonify({
                'status': 'error', 
                'message': 'publish_post returned unexpected format - check logs'
            }), 500
            
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"❌ Post generation error: {error_trace}")
        return jsonify({
            'status': 'error', 
            'message': str(e),
            'traceback': error_trace
        }), 500

@app.route('/api/bot-status', methods=['GET'])
def bot_status():
    """Check if GEMINI_API_KEY is configured"""
    import os
    has_key = bool(os.getenv('GEMINI_API_KEY'))
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
        
        return jsonify({
            'success': True,
            'message': 'Successfully subscribed!',
            'id': subscriber_id
        }), 201
        
    except Exception as e:
        print(f"❌ Subscription error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
