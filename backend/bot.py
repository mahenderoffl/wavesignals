import os
import time
import requests
import json
from db import get_db_connection
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
API_KEY = os.getenv("GEMINI_API_KEY")

TOPICS = [
    "AI Coding Agents", "DevOps Automation", "Future of React", "WebAssembly",
    "Rust vs Go", "Serverless Architecture", "Edge Computing", "Cybersecurity in 2025",
    "Quantum Computing", "No-Code Revolution", "Tech Layoffs & Hiring", "Green Tech"
]

def generate_content(topic):
    if not API_KEY:
        print("CRITICAL: GEMINI_API_KEY is missing!")
        return None, None

    try:
        print(f"🤖 Generating content for: {topic}")
        
        # 1. Research & Draft
        prompt = f"""
        Role: Senior Tech Journalist.
        Task: Write a deep, analytical blog post about "{topic}".
        
        Requirements:
        1. Title: Catchy H2 style.
        2. Content: 800+ words, detailed, authoritative.
        3. Structure: Use HTML tags <h2> for sections, <h3> for sub-sections, <p> for paragraphs, <ul> for lists.
        4. Key Takeaways: End with a <h2>Key Takeaways</h2> section.
        5. Tone: Professional, slightly cynical but optimistic (like TheVerge).
        
        Output: JSON format {{ "title": "...", "content": "..." }}
        """

        # Direct REST API Call (No SDK needed)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        response_data = response.json()
        
        # Parse Response
        try:
            text = response_data['candidates'][0]['content']['parts'][0]['text']
        except KeyError:
            print("API Error:", response_data)
            return None, None
        
        # Simple cleanup
        clean_text = text.replace("```json", "").replace("```", "").strip()
        
        try:
            data = json.loads(clean_text)
            title = data.get("title", topic)
            content = data.get("content", text)
        except:
            title = f"Deep Dive: {topic}"
            content = clean_text

        return title, content
    except Exception as e:
        print(f"AI Generation Error: {e}")
        return None, None

def publish_post():
    import random
    topic = random.choice(TOPICS)
    
    title, content = generate_content(topic)
    if not title:
        return

    slug = title.lower().replace(" ", "-").replace(":", "").replace("?", "")
    
    conn = get_db_connection()
    if not conn:
        return

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO posts (slug, title, content, published, author, tags)
            VALUES (%s, %s, %s, TRUE, 'WaveSignals AI', 'Tech, AI, Future')
            RETURNING id;
        """, (slug, title, content))
        
        post_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Published Post ID: {post_id} - {title}")
    except Exception as e:
        print(f"Database Insert Error: {e}")

if __name__ == "__main__":
    publish_post()
