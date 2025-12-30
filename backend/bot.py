import os
import time
import requests
import json
import random
from db import get_db_connection
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
API_KEY = os.getenv("GEMINI_API_KEY")

# 🧠 CORE PILLARS (Value-Driven Insights)
# Topics chosen based on trending discussions, search volume, and audience value
PILLARS = {
    "Career": [
        "The Real Reasons Behind Youth Unemployment (That No One Talks About)",
        "Upskilling vs Reskilling: What Actually Works in 2025",
        "Why Your Degree Doesn't Matter Anymore (And What Does)",
        "The Hidden Job Market: How 70% of Jobs Are Never Posted",
        "Remote Work's Dark Side: Mental Health and Productivity"
    ],
    "Money": [
        "Why Making $100K Still Feels Like You're Broke",
        "The Psychology of 'Enough': When More Becomes Less",
        "Credit Score Myths That Cost You Thousands",
        "Side Hustles That Actually Scale (From Reddit Success Stories)",
        "Investing for Beginners: What Finance Influencers Won't Tell You"
    ],
    "Technology": [
        "AI Replacing Jobs: Which Careers Are Actually Safe",
        "Why Free Apps Are More Expensive Than You Think",
        "The Attention Economy: How Apps Steal Your Time",
        "Cybersecurity Basics Everyone Should Know in 2025",
        "The Truth About Social Media Algorithms"
    ],
    "Health & Fitness": [
        "Why 80% of Diets Fail (And What Actually Works)",
        "The Science of Sleep: Why You're Always Tired",
        "Mental Health Red Flags Everyone Should Recognize",
        "Gym vs. Home Workouts: What Research Actually Says",
        "Intermittent Fasting: Hype vs. Science"
    ],
    "Content Creation": [
        "How to Grow on Instagram in 2025 (Without Buying Followers)",
        "YouTube Algorithm Secrets: What Actually Gets Views",
        "Why Most Content Creators Fail in Their First Year",
        "Monetization Strategies Beyond AdSense and Sponsorships",
        "Building a Personal Brand: Lessons from Viral Creators"
    ]
}

# Groq API (FREE alternative - faster than Gemini!)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def call_groq(prompt):
    """Call Groq API - Free and fast alternative to Gemini/OpenAI"""
    if not GROQ_API_KEY:
        print("⚠️ GROQ_API_KEY not configured")
        return None
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",  # Fast and good quality
        "messages": [
            {"role": "system", "content": "You are a thoughtful content writer creating engaging blog posts."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4000,
        "temperature": 0.8
    }
    
    try:
        print(f"🔄 Calling Groq API...")
        response = requests.post(url, json=payload, headers=headers, timeout=90)
        
        if response.status_code != 200:
            print(f"❌ Groq API Error: HTTP {response.status_code}")
            print(f"   Response: {response.text[:300]}")
            return None
        
        response_data = response.json()
        
        if 'choices' not in response_data or len(response_data['choices']) == 0:
            print(f"❌ Unexpected Groq response format")
            return None
        
        content = response_data['choices'][0]['message']['content']
        print(f"✅ Groq responded ({len(content)} chars)")
        return content
        
    except Exception as e:
        print(f"❌ Groq API Error: {e}")
        return None

# API_KEY = os.getenv("GEMINI_API_KEY") # No longer needed
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # No longer needed

# def call_gemini(prompt): # No longer needed
#     """Helper to call Gemini API via REST"""
#     if not API_KEY:
#         print("⚠️ GEMINI_API_KEY not configured")
#         return None

#     # Use v1beta API with gemini-pro model (v1 with 1.5-flash returns 404)
#     url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"
#     payload = {
#         "contents": [{ "parts": [{"text": prompt}] }]
#     }
    
#     try:
#         print(f"🔄 Calling Gemini API...")
#         response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)
        
#         if response.status_code != 200:
#             print(f"❌ Gemini API Error: HTTP {response.status_code}")
#             print(f"   Response: {response.text[:200]}")
#             return None
            
#         response_data = response.json()
        
#         if 'candidates' not in response_data:
#             print(f"❌ Unexpected API response format: {response_data}")
#             return None
            
#         content = response_data['candidates'][0]['content']['parts'][0]['text']
#         print(f"✅ Gemini responded ({len(content)} chars)")
#         return content
        
#     except requests.exceptions.Timeout:
#         print(f"❌ Gemini API Timeout (>60s)")
#         return None
#     except Exception as e:
#         print(f"❌ Gemini API Error: {e}")
#         return None

# def call_openai(prompt): # No longer needed
#     """Call OpenAI API (GPT-3.5-Turbo)"""
#     if not OPENAI_API_KEY:
#         print("⚠️ OPENAI_API_KEY not configured")
#         return None
    
#     url = "https://api.openai.com/v1/chat/completions"
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {OPENAI_API_KEY}"
#     }
#     payload = {
#         "model": "gpt-3.5-turbo",
#         "messages": [
#             {"role": "system", "content": "You are a thoughtful content writer creating engaging blog posts."},
#             {"role": "user", "content": prompt}
#         ],
#         "max_tokens": 4000,
#         "temperature": 0.8
#     }
    
#     try:
#         print(f"🔄 Calling OpenAI API...")
#         response = requests.post(url, json=payload, headers=headers, timeout=90)
        
#         if response.status_code != 200:
#             print(f"❌ OpenAI API Error: HTTP {response.status_code}")
#             print(f"   Response: {response.text[:200]}")
#             return None
        
#         response_data = response.json()
        
#         if 'choices' not in response_data or len(response_data['choices']) == 0:
#             print(f"❌ Unexpected OpenAI response format")
#             return None
        
#         content = response_data['choices'][0]['message']['content']
#         print(f"✅ OpenAI responded ({len(content)} chars)")
#         return content
        
#     except Exception as e:
#         print(f"❌ OpenAI API Error: {e}")
#         return None

# def call_ai_with_fallback(prompt): # No longer needed
#     """Try Gemini first, fall back to OpenAI if it fails"""
#     # Try Gemini
#     result = call_gemini(prompt)
#     if result:
#         return result
    
#     # Fallback to OpenAI
#     print("⚠️ Gemini failed, trying OpenAI fallback...")
#     result = call_openai(prompt)
#     if result:
#         return result
    
#     print("❌ All AI providers failed!")
#     return None

def research_trending_topics():
    """Research what people are actually searching for on social platforms"""
    
    research_prompt = """
    Role: Internet trend researcher analyzing current discussions.
    Task: Research what topics are trending RIGHT NOW across social platforms.
    
    Categories to analyze:
    - Career & Professional Development
    - Personal Finance & Money
    - Technology & AI
    - Health & Fitness  
    - Content Creation & Social Media
    
    Your research sources (simulate searching):
    1. Reddit: What's trending on r/careeradvice, r/personalfinance, r/technology
    2. Twitter/X: Current trending hashtags and discussions
    3. YouTube: Popular searches and rising video topics
    4. Instagram: Viral content themes and hashtags
    5. Google Trends: Rising search queries
    
    Return ONLY JSON:
    {
      "trendingTopics": [
        {"topic": "specific trending topic", "platform": "where it's trending", "reason": "why it's relevant"},
        {"topic": "another topic", "platform": "source", "reason": "context"}
      ],
      "hotKeywords": ["keyword1", "keyword2", "keyword3"],
      "risingQuestions": ["question people are asking", "another question"]
    }
    
    Focus on topics that will generate high engagement and search traffic.
    """
    
    research_data = call_groq(research_prompt)
    
    if research_data:
        try:
            clean = research_data.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except:
            pass
    
    return {"trendingTopics": [], "hotKeywords": [], "risingQuestions": []}

def generate_content(topic, category):
    # Research trends first
    print(f"🔍 Researching internet trends for {category}...")
    trends = research_trending_topics()
    
    trending_context = ""
    if trends.get("trendingTopics"):
        trending_topics = trends["trendingTopics"][:3]
        trending_context = "\n\nCurrent trending discussions:\n"
        for t in trending_topics:
            trending_context += f"- {t['topic']} (trending on {t['platform']})\n"
    
    print(f"🧠 Generating Insight for: '{topic}' ({category})...")
    
    # PASS 1: THE PHILOSOPHER (Insight Focused)
    # Goal: Level 1 & 2 Humanization (Opinionated, No Listicles)
    draft_prompt = f"""
    Role: A cultural critic and thoughtful essayist (like Paul Graham or Naval Ravikant).
    Task: Write a deep, reflective essay about "{topic}".
    Context: This fits into the "{category}" pillar of our publication.
    {trending_context}
    
    CRITICAL RULES (The "Anti-Blog" Manifesto):
    1. **NO Listicles:** Do not use "Top 5 ways" or bullet points as the main structure.
    2. **NO How-To:** We are not teaching. We are observing and analyzing.
    3. **Tone:** Opinionated, contemplative, slightly contrarian. Use "I think" or "We observe", not "You should".
    4. **Structure:** Fluid essay format. Use <h2> headers for major shifts in thought, not for steps.

    Core Question to Answer: What is the second-order effect of this topic on human life?
    
    Length: 800-1200 words.
    Format: HTML only (use <h2>, <p>, <strong>, <em> tags). No markdown.
    """
    
    draft = call_groq(draft_prompt)
    if not draft: return None, None, None, None, None, None, None

    print(f"🔍 Researching Keywords & Tags for '{topic}'...")
    
    # PASS 1.5: KEYWORD RESEARCHER (Dynamic SEO)
    # Goal: Research-based keywords, not generic ones
    keyword_prompt = f"""
    Role: SEO specialist with deep knowledge of search behavior.
    Task: Research and recommend the BEST keywords for this topic.
    
    Topic: "{topic}"
    Category: {category}
    Content Preview: {draft[:500]}...
    
    Your job:
    1. Think like a user searching Google: What would they type?
    2. Consider search intent: Are they looking for definitions, solutions, or insights?
    3. Mix high-volume and long-tail keywords
    4. Include trending terms related to {category}
    
    Return ONLY JSON:
    {{
      "primaryKeywords": ["main keyword 1", "main keyword 2", "main keyword 3"],
      "longTailKeywords": ["specific phrase users might search", "another long-tail query"],
      "trendingTerms": ["current buzzword 1", "current buzzword 2"],
      "hashtags": ["#MostRelevant", "#{category}", "#Trending"],
      "searchQueries": ["exact query users type", "another common search"]
    }}
    
    Be strategic. These keywords determine if people find this post.
    """
    
    keywords_json = call_groq(keyword_prompt)
    
    # Parse keywords or use defaults
    keyword_data = {"primaryKeywords": [], "longTailKeywords": [], "trendingTerms": [], "hashtags": [], "searchQueries": []}
    if keywords_json:
        try:
            clean_kw = keywords_json.replace("```json", "").replace("```", "").strip()
            keyword_data = json.loads(clean_kw)
        except:
            pass

    print(f"✒️ Polishing & Formatting '{topic}'...")

    # PASS 2: THE EDITOR (Structure & Monetization Guard + SEO)
    editor_prompt = f"""
    Polish this essay for publication and optimize for SEO.

    Input Draft:
    {draft[:15000]}

    Return ONLY this JSON structure (no extra text):

    {{
      "title": "Engaging title here",
      "metaDescription": "SEO description 150-160 chars",
      "keywords": ["keyword1", "keyword2", "keyword3"],
      "hashtags": ["#Tag1", "#Tag2"],
      "searchQueries": ["search query"],
      "excerpt": "2-sentence summary",
      "content": "HTML content with <h2><p><blockquote> tags"
    }}
    """
    
    final_json_text = call_groq(editor_prompt)
    if not final_json_text: return None, None, None, None, None, None, None

    import re
    
    # STEP 1: Strip ALL wrapper text before JSON
    clean_text = final_json_text.strip()
    
    # Remove ANY text before the first {
    first_brace = clean_text.find('{')
    if first_brace > 0:
        clean_text = clean_text[first_brace:]
    
    # Remove markdown fences
    clean_text = clean_text.replace('```json', '').replace('```', '')
    
    # Remove anything after closing } that isn't part of JSON
    # Find the last } and check if there's explanatory text after
    last_brace = clean_text.rfind('}')
    if last_brace > 0 and last_brace < len(clean_text) - 1:
        # Check if text after } is explana tory (contains words like "made", "changes", "improved")
        after_text = clean_text[last_brace+1:].strip()
        if any(word in after_text.lower() for word in ['made', 'changes', 'improved', 'following', 'optimized']):
            clean_text = clean_text[:last_brace+1]
    
    clean_text = clean_text.strip()

    try:
        data = json.loads(clean_text)
        
        # STEP 2: Extract fields from JSON
        title = data.get("title", "")
        raw_content = data.get("content", "")
        
        # STEP 3: CRITICAL - Content should be pure HTML, nothing else
        if not isinstance(raw_content, str):
            print("❌ ERROR: Content is not a string")
            return None, None, None, None, None, None, None
        
        raw_content = raw_content.strip()
        
        # REJECT if content contains ANY of these artifacts
        reject_patterns = [
            'Here is', 'Here\'s', 'I made', 'following changes',
            '```json', '```', '"title":', '"metaDescription":',
            'optimized for SEO', 'Removed aggressive', 'Added formatting'
        ]
        
        for pattern in reject_patterns:
            if pattern in raw_content:
                print(f"❌ ERROR: Content contains artifact: '{pattern}'")
                print(f"Content preview: {raw_content[:200]}")
                return None, None, None, None, None, None, None
        
        # Content MUST start with HTML tag
        if not raw_content.startswith('<'):
            print(f"❌ ERROR: Content doesn't start with HTML tag")
            print(f"Starts with: {raw_content[:50]}")
            return None, None, None, None, None, None, None
        
        # Content MUST end with HTML tag
        if not raw_content.endswith('>'):
            print(f"⚠️ WARNING: Content doesn't end with HTML tag, trimming...")
            # Find last closing tag
            last_close_tag = max(
                raw_content.rfind('</p>'),
                raw_content.rfind('</blockquote>'),
                raw_content.rfind('</h2>'),
                raw_content.rfind('</ul>'),
                raw_content.rfind('</ol>')
            )
            if last_close_tag > 0:
                raw_content = raw_content[:last_close_tag + 4]  # Include closing tag
        
        content = raw_content
        print(f"✅ Clean content extracted: {len(content)} chars, starts with: {content[:30]}")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        print(f"Attempted to parse: {clean_text[:200]}")
        return None, None, None, None, None, None, None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None, None, None, None, None, None, None
    
    print(f"🎭 Humanizing & Paraphrasing '{title}'...")
    
    # PASS 3: THE HUMANIZER (Anti-AI Detection)
    # Goal: Make it sound 100% human-written
    humanize_prompt = f"""
        Role: Expert writer who makes AI content undetectable.
        Task: Rewrite this content to sound genuinely human-written.
        
        Original Content:
        {content[:12000]}
        
        Your mission:
        1. **Remove AI patterns:**
           - No "In conclusion" or "In summary"
           - No "It's important to note"
           - No repetitive sentence structures
           - No overly formal transitions
        
        2. **Add human elements:**
           - Use contractions (it's, don't, we're)
           - Vary sentence length dramatically
           - Add occasional rhetorical questions
           - Use active voice, not passive
           - Include subtle personality quirks
        
        3. **Paraphrase strategically:**
           - Reword clichés into fresh metaphors
           - Break up long paragraphs
           - Add 1-2 personal observations ("I've noticed...", "We often forget...")
        
        4. **Keep structure:**
           - Maintain all <h2>, <p>, <blockquote> tags
           - Preserve the core argument
           - Don't change the main ideas
        
    Return ONLY the humanized HTML content (no JSON, just the content).
    Make it sound like a smart human wrote it naturally.
    """
    
    humanized_content = call_groq(humanize_prompt)
    
    # Use humanized version if successful and clean
    if humanized_content and len(humanized_content) > 200:
        # Final cleanup - remove any JSON/markdown artifacts
        humanized_content = humanized_content.strip()
        
        # Remove code fences if AI added them
        humanized_content = humanized_content.replace("```html", "").replace("```", "")
        
        # Remove JSON wrappers if present
        if humanized_content.startswith('{') and '"content"' in humanized_content:
            try:
                temp_json = json.loads(humanized_content)
                humanized_content = temp_json.get("content", humanized_content)
            except:
                pass
        
        # Remove any "Note:" sections
        if "Note:" in humanized_content:
            humanized_content = humanized_content.split("Note:")[0].strip()
        
        # Final sanitization - remove any code artifacts
        import re
        humanized_content = humanized_content.rstrip()
        humanized_content = re.sub(r'[}"\'\s;]+$', '', humanized_content)
        humanized_content = re.sub(r'^[{"\s]+', '', humanized_content)
        
        # Ensure ends with HTML tag
        if not humanized_content.endswith('>'):
            last_tag = humanized_content.rfind('</p>')
            if last_tag == -1:
                last_tag = humanized_content.rfind('</blockquote>')
            if last_tag == -1:
                last_tag = humanized_content.rfind('</h2>')
            if last_tag > 0:
                humanized_content = humanized_content[:last_tag + 4]
        
        content = humanized_content.strip()
    
    # Combine keywords from both passes
    all_keywords = list(set(keyword_data.get("primaryKeywords", []) + keyword_data.get("longTailKeywords", []) + keyword_data.get("trendingTerms", []) + data.get("keywords", [])))
    
    hashtags = keyword_data.get("hashtags", []) or data.get("hashtags", [])
    search_queries = keyword_data.get("searchQueries", []) or data.get("searchQueries", [])
    
    return (
        title,
        content,
        data.get("metaDescription", ""),
        all_keywords[:7],  # Max 7 keywords
        hashtags[:5],  # Max 5 hashtags
        search_queries[:3],  # Max 3 queries
        data.get("excerpt", "")
    )

def publish_post(emergency_override=False):
    # RATE LIMITING: Check if last post was within 23 hours (unless emergency override)
    if not emergency_override:
        conn = get_db_connection()
        if not conn:
            print("❌ Database connection failed")
            return {"success": False, "error": "Database connection failed"}

        try:
            cur = conn.cursor()
            
            # Check last post timestamp
            cur.execute("""
                SELECT created_at FROM posts 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            last_post = cur.fetchone()
            
            if last_post:
                from datetime import datetime, timezone
                last_post_time = last_post['created_at']
                
                # Handle both timezone-aware and naive datetimes
                if last_post_time.tzinfo is None:
                    last_post_time = last_post_time.replace(tzinfo=timezone.utc)
                
                now = datetime.now(timezone.utc)
                hours_since = (now - last_post_time).total_seconds() / 3600
                
                if hours_since < 23:
                    remaining = 23 - hours_since
                    print(f"⏳ Rate limit: Last post was {hours_since:.1f}h ago. Wait {remaining:.1f}h more.")
                    cur.close()
                    conn.close()
                    return {
                        "success": False, 
                        "error": f"Rate limit: Must wait {remaining:.1f} hours before next post",
                        "hours_remaining": remaining
                    }
            
            print("✅ Rate limit passed, proceeding with generation...")
            cur.close()
            
        except Exception as e:
            print(f"⚠️ Rate limit check error: {e}")
            # Continue anyway if rate limit check fails
    else:
        print("🚨 EMERGENCY OVERRIDE: Bypassing rate limit check")
        conn = get_db_connection()
        if not conn:
            print("❌ Database connection failed")
            return {"success": False, "error": "Database connection failed"}
    
    # LEVEL 4: Randomized Behavior
    # Select a random Category, then a random Topic from that category
    category = random.choice(list(PILLARS.keys()))
    topic = random.choice(PILLARS[category])
    
    # Get SEO-optimized content
    try:
        title, content, meta_desc, keywords, hashtags, search_queries, excerpt = generate_content(topic, category)
    except Exception as e:
        conn.close()
        return {"success": False, "error": f"Content Generation Error: {str(e)}"}

    if not title:
        print("❌ Generation failed.")
        conn.close()
        return {"success": False, "error": "Generation produced no title/content"}

    slug = title.lower().replace(" ", "-").replace(":", "").replace("?", "").replace("(", "").replace(")", "").replace("'", "")
    
    # Reuse existing connection
    if not conn:
        conn = get_db_connection()
        if not conn:
            print("❌ Database connection failed")
            return {"success": False, "error": "Database connection failed"}

    try:
        cur = conn.cursor()
        
        # Insert post with SEO metadata
        cur.execute("""
            INSERT INTO posts (
                slug, title, excerpt, content, published, author, tags,
                meta_description, keywords, hashtags, search_queries
            )
            VALUES (%s, %s, %s, %s, TRUE, 'WaveSignals', %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            slug, 
            title, 
            excerpt or f"Insights on {topic}",
            content, 
            category,
            meta_desc,
            json.dumps(keywords),
            json.dumps(hashtags),
            json.dumps(search_queries)
        ))
        
        post_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Published Insight: {title} [{category}]")
        print(f"   📊 SEO Data:")
        print(f"      Keywords: {', '.join(keywords[:3])}...")
        print(f"      Hashtags: {' '.join(hashtags)}")
        print(f"      Target Queries: {search_queries[0] if search_queries else 'N/A'}")
        
        return {"success": True, "id": post_id, "title": title}
        
    except Exception as e:
        print(f"❌ Database Insert Error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": f"Database Insert Error: {str(e)}"}

if __name__ == "__main__":
    publish_post()
