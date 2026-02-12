"""
GET /api/posts - Get all published posts
Multi-database fallback: OLD_DB -> NEW_DB -> JSON
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_posts_with_fallback():
    """Get posts with multi-database fallback"""
    # Try databases in order
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
            cur = conn.cursor()
            cur.execute("""
                SELECT id, slug, title, excerpt, content, published, 
                       created_at as date, author, tags, meta_description,
                       keywords, hashtags, search_queries, image
                FROM posts 
                WHERE published = TRUE 
                ORDER BY created_at DESC
            """)
            posts = cur.fetchall()
            cur.close()
            conn.close()
            
            # Convert datetime to ISO string
            for post in posts:
                if post.get('date'):
                    post['date'] = post['date'].isoformat()
            
            print(f"✅ Retrieved {len(posts)} posts from {db_name}")
            return posts, db_name
        except Exception as e:
            print(f"⚠️ {db_name} failed: {e}")
            continue
    
    # Fallback to JSON
    try:
        json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'posts.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            posts = data.get('posts', [])
            print(f"✅ Loaded {len(posts)} posts from JSON fallback")
            return posts, 'json_fallback'
    except Exception as e:
        print(f"❌ JSON fallback failed: {e}")
        return [], 'error'

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            posts, source = get_posts_with_fallback()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('X-Data-Source', source)
            self.end_headers()
            self.wfile.write(json.dumps({
                "posts": posts,
                "source": source,
                "count": len(posts)
            }).encode())
            
        except Exception as e:
            print(f"❌ Error in posts endpoint: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
