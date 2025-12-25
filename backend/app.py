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
scheduler.add_job(func=daily_auto_post, trigger="interval", hours=24) 
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def home():
    return jsonify({
        "status": "WaveSignals Brain Online", 
        "version": "2.1 (Secured)",
        "scheduler": "Running (Daily)"
    })

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
