"""
Multi-Database Connection Manager with Fallback
Priority: OLD_DATABASE_URL -> NEW_DATABASE_URL -> Local JSON

Environment Variables:
- OLD_DATABASE_URL: Primary database (your existing blogs)
- NEW_DATABASE_URL: Secondary/backup database
- DATABASE_URL: Fallback (if old/new not specified)
"""
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def get_multi_db_connection():
    """
    Try to connect to databases in order of priority:
    1. OLD_DATABASE_URL (primary - your existing blog data)
    2. NEW_DATABASE_URL (secondary - backup)
    3. DATABASE_URL (fallback)
    
    Returns: (connection, source_name) or (None, 'none')
    """
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
            print(f"✅ Connected to {db_name}")
            return conn, db_name
        except Exception as e:
            print(f"⚠️ {db_name} connection failed: {e}")
            continue
    
    print("❌ All database connections failed")
    return None, 'none'

def get_primary_db_connection():
    """
    Get primary database connection for WRITE operations.
    Always uses OLD_DATABASE_URL (primary) or falls back to NEW_DATABASE_URL.
    """
    primary_url = os.getenv("OLD_DATABASE_URL") or os.getenv("NEW_DATABASE_URL") or os.getenv("DATABASE_URL")
    
    if not primary_url:
        print("❌ No primary database URL configured")
        return None
    
    try:
        conn = psycopg2.connect(primary_url, cursor_factory=RealDictCursor)
        print(f"✅ Connected to primary database for write")
        return conn
    except Exception as e:
        print(f"❌ Primary database connection failed: {e}")
        return None

def get_posts_from_json():
    """
    Fallback: Load posts from local JSON file
    Returns: list of posts
    """
    try:
        json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'posts.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            posts = data.get('posts', [])
            print(f"✅ Loaded {len(posts)} posts from JSON fallback")
            return posts
    except Exception as e:
        print(f"❌ JSON fallback failed: {e}")
        return []

def get_posts_with_fallback():
    """
    Get all published posts with multi-database fallback:
    1. Try old database
    2. Try new database
    3. Try local JSON
    
    Returns: (posts_list, source)
    """
    # Try database connections
    conn, source = get_multi_db_connection()
    
    if conn:
        try:
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
            
            print(f"✅ Retrieved {len(posts)} posts from {source}")
            return posts, source
        except Exception as e:
            print(f"❌ Database query failed: {e}")
            conn.close()
    
    # Fallback to JSON
    posts = get_posts_from_json()
    return posts, 'json_fallback'

def get_single_post_with_fallback(slug):
    """
    Get a single post by slug with fallback
    Returns: (post_dict, source) or (None, source)
    """
    # Try database connections
    conn, source = get_multi_db_connection()
    
    if conn:
        try:
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
            
            return post, source
        except Exception as e:
            print(f"❌ Database query failed: {e}")
            conn.close()
    
    # Fallback to JSON
    posts = get_posts_from_json()
    for post in posts:
        if post.get('slug') == slug and post.get('published'):
            return post, 'json_fallback'
    
    return None, 'json_fallback'
