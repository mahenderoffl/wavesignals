"""
/api/cron - Full Cron Job handler for daily AI post generation
Call this from cron-job.org at 6 AM UTC daily

Multi-database support:
- WRITES: Always go to primary database (OLD_DATABASE_URL)
- READS: Use fallback (OLD_DB -> NEW_DB -> JSON)

This is a complete standalone version that generates AI blog posts.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import time
import random
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import RealDictCursor
import requests

# ============================================================
# DATABASE
# ============================================================
def get_primary_db_connection():
    """Get PRIMARY database connection for WRITE operations"""
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

# ============================================================
# FIREBASE CLOUD MESSAGING (FCM)
# ============================================================
def send_push_notification(title, body, post_url):
    """Send push notification to all FCM subscribers using Firebase Admin SDK"""
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging
        
        # Initialize Firebase if not already done
        if not firebase_admin._apps:
            service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT')
            if service_account_json:
                service_account_dict = json.loads(service_account_json)
                cred = credentials.Certificate(service_account_dict)
                firebase_admin.initialize_app(cred)
                print("✅ Firebase initialized for notifications")
            else:
                return {"success": False, "error": "Firebase credentials not configured"}
        
        # Get active FCM tokens from database
        conn = get_primary_db_connection()
        if not conn:
            return {"success": False, "error": "Database connection failed"}
        
        cur = conn.cursor()
        cur.execute("SELECT token FROM fcm_subscribers WHERE active = TRUE AND token IS NOT NULL")
        tokens = [row['token'] for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        if not tokens:
            return {"success": True, "sent": 0, "message": "No subscribers yet"}
        
        print(f"📬 Sending notifications to {len(tokens)} subscribers...")
        
        # Send notifications
        success_count = 0
        failure_count = 0
        
        for token in tokens:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body[:100] if len(body) > 100 else body
                    ),
                    data={
                        'url': post_url,
                        'click_action': post_url
                    },
                    webpush=messaging.WebpushConfig(
                        notification=messaging.WebpushNotification(
                            title=title,
                            body=body[:100] if len(body) > 100 else body,
                            icon='/favicon.ico'
                        ),
                        fcm_options=messaging.WebpushFCMOptions(
                            link=post_url
                        )
                    ),
                    token=token
                )
                messaging.send(message)
                success_count += 1
            except Exception as e:
                failure_count += 1
                print(f"   Failed to send to token: {e}")
        
        return {
            "success": True,
            "sent": success_count,
            "failed": failure_count,
            "total": len(tokens)
        }
        
    except Exception as e:
        print(f"❌ FCM notification error: {e}")
        return {"success": False, "error": str(e)}

# ============================================================
# GROQ AI API
# ============================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def call_groq(prompt, max_retries=2):
    """Call Groq API with retry logic"""
    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY not configured")
        return None
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a thoughtful content writer."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 3000,
        "temperature": 0.8
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=25)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            elif response.status_code == 429:
                time.sleep(5)
                continue
            else:
                print(f"❌ Groq API Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Groq API Error: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
    return None

# ============================================================
# CONTENT PILLARS
# ============================================================
PILLARS = {
    "Career": [
        "The Real Reasons Behind Youth Unemployment",
        "Upskilling vs Reskilling: What Actually Works in 2025",
        "Why Your Degree Doesn't Matter Anymore",
        "The Hidden Job Market: How 70% of Jobs Are Never Posted"
    ],
    "Money": [
        "Why Making $100K Still Feels Like You're Broke",
        "The Psychology of 'Enough': When More Becomes Less",
        "Credit Score Myths That Cost You Thousands",
        "Side Hustles That Actually Scale"
    ],
    "Technology": [
        "AI Replacing Jobs: Which Careers Are Actually Safe",
        "Why Free Apps Are More Expensive Than You Think",
        "The Attention Economy: How Apps Steal Your Time",
        "Cybersecurity Basics Everyone Should Know in 2025"
    ],
    "Health": [
        "Why 80% of Diets Fail (And What Actually Works)",
        "The Science of Sleep: Why You're Always Tired",
        "Mental Health Red Flags Everyone Should Recognize",
        "Gym vs. Home Workouts: What Research Actually Says"
    ]
}

# ============================================================
# POST GENERATION
# ============================================================
def generate_post():
    """Generate a complete blog post using AI"""
    category = random.choice(list(PILLARS.keys()))
    topic = random.choice(PILLARS[category])
    
    print(f"📝 Generating post on: {topic} ({category})")
    
    # Simple prompt for faster generation
    prompt = f"""Write a blog post about "{topic}".

Requirements:
- 600-800 words
- Engaging and insightful
- Use HTML tags: <h2>, <p>, <strong>, <em>
- Return ONLY JSON format:

{{
  "title": "Your engaging title here",
  "excerpt": "A 2-sentence summary",
  "content": "<p>Your HTML content here...</p>",
  "metaDescription": "SEO description 150 chars",
  "keywords": ["keyword1", "keyword2", "keyword3"]
}}

Return ONLY the JSON, no other text."""

    result = call_groq(prompt)
    if not result:
        return None
    
    # Parse JSON
    try:
        # Clean up response
        clean = result.strip()
        if clean.startswith('```'):
            clean = clean.split('```')[1]
            if clean.startswith('json'):
                clean = clean[4:]
        clean = clean.strip()
        
        # Find JSON
        start = clean.find('{')
        end = clean.rfind('}') + 1
        if start >= 0 and end > start:
            clean = clean[start:end]
        
        data = json.loads(clean)
        
        # Create slug
        title = data.get('title', topic)
        slug = title.lower()
        for char in [':', '?', '(', ')', "'", '"', ',', '.']:
            slug = slug.replace(char, '')
        slug = slug.replace(' ', '-').replace('--', '-')
        
        return {
            'title': title,
            'slug': slug,
            'excerpt': data.get('excerpt', f"Insights on {topic}"),
            'content': data.get('content', ''),
            'meta_description': data.get('metaDescription', ''),
            'keywords': json.dumps(data.get('keywords', [])),
            'category': category
        }
    except Exception as e:
        print(f"❌ JSON parse error: {e}")
        return None

def publish_post():
    """Generate and save a post to PRIMARY database"""
    conn = get_primary_db_connection()
    if not conn:
        return {"success": False, "error": "Database connection failed"}
    
    try:
        # Check if post exists in last 20 hours
        cur = conn.cursor()
        cur.execute("SELECT created_at FROM posts ORDER BY created_at DESC LIMIT 1")
        last = cur.fetchone()
        
        if last:
            last_time = last['created_at']
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=timezone.utc)
            hours = (datetime.now(timezone.utc) - last_time).total_seconds() / 3600
            if hours < 20:
                cur.close()
                conn.close()
                return {"success": True, "skipped": True, "reason": f"Post exists ({hours:.1f}h ago)"}
        cur.close()
        
        # Generate post (outside transaction)
        post = generate_post()
        if not post or not post.get('content'):
            conn.close()
            return {"success": False, "error": "Post generation failed"}
        
        # Save to database
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO posts (slug, title, excerpt, content, published, author, tags, meta_description, keywords)
            VALUES (%s, %s, %s, %s, TRUE, 'WaveSignals', %s, %s, %s)
            RETURNING id
        """, (
            post['slug'],
            post['title'],
            post['excerpt'],
            post['content'],
            post['category'],
            post['meta_description'],
            post['keywords']
        ))
        post_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Published: {post['title']}")
        
        # Send push notifications to subscribers
        try:
            # Import notification function
            notification_result = send_push_notification(
                title=post['title'],
                body=post['excerpt'],
                post_url=f"https://wavesignals.waveseed.app/app/post.html?slug={post['slug']}"
            )
            if notification_result.get('success'):
                print(f"   📬 Push notifications sent: {notification_result.get('sent', 0)} delivered")
            else:
                print(f"   ⚠️ Push notification warning: {notification_result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"   ⚠️ Push notification failed (non-critical): {e}")
            # Don't fail the post if notification fails
        
        return {"success": True, "id": post_id, "title": post['title']}
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return {"success": False, "error": str(e)}

# ============================================================
# HTTP HANDLER
# ============================================================
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"⏰ CRON TRIGGERED at {datetime.now(timezone.utc).isoformat()}")
        
        try:
            result = publish_post()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                **result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }).encode())
                
        except Exception as e:
            import traceback
            print(f"❌ Error: {e}")
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": str(e)
            }).encode())
    
    def do_POST(self):
        self.do_GET()
