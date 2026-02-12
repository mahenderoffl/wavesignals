"""
GET /api/post?slug=X - Get a single post by slug
Multi-database fallback: OLD_DB -> NEW_DB -> JSON
"""
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_single_post_with_fallback(slug):
    """Get single post with multi-database fallback"""
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
                WHERE slug = %s AND published = TRUE
            """, (slug,))
            post = cur.fetchone()
            cur.close()
            conn.close()
            
            if post and post.get('date'):
                post['date'] = post['date'].isoformat()
            
            return post, db_name
        except Exception as e:
            print(f"⚠️ {db_name} failed: {e}")
            continue
    
    # Fallback to JSON
    try:
        json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'posts.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            posts = data.get('posts', [])
            for post in posts:
                if post.get('slug') == slug and post.get('published'):
                    return post, 'json_fallback'
    except Exception as e:
        print(f"❌ JSON fallback failed: {e}")
    
    return None, 'error'

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse slug from query params
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        slug = params.get('slug', [None])[0]
        
        if not slug:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Slug parameter required"}).encode())
            return
        
        try:
            post, source = get_single_post_with_fallback(slug)
            
            if post:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('X-Data-Source', source)
                self.end_headers()
                self.wfile.write(json.dumps(post).encode())
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Post not found"}).encode())
                
        except Exception as e:
            print(f"❌ Error in post endpoint: {e}")
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
