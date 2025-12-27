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

# 🧠 CORE PILLARS (The "Thinking Publication")
PILLARS = {
    "Career": [
        "The Myth of 'Meritocracy' in Tech Careers",
        "Why Visibility Beats Competence",
        "The Silent Cost of 'Optimization' Culture",
        "Career Leverage vs. Career Ladder"
    ],
    "Money": [
        "Why High Income Doesn't Fix Scarcity Mindset",
        "The Psychology of 'Enough'",
        "Status Signaling and Financial Suicide",
        "Incentives: Why We Do What We Do"
    ],
    "Technology": [
        "The Hidden Cost of 'Free' Software",
        "Why Convenience is the Enemy of Competence",
        "Algorithms are the New Middle Management",
        "The Death of Boredom and Creativity"
    ],
    "Behavior": [
        "The Comfort Fallacy: Why Easy Choices Kill Growth",
        "Decision Fatigue in the Age of Abundance",
        "Why We Prefer Comfortable Lies to Hard Truths",
        "The Art of Doing Nothing (Intentionally)"
    ]
}

def call_gemini(prompt):
    """Helper to call Gemini API via REST"""
    if not API_KEY:
        print("CRITICAL: GEMINI_API_KEY is missing!")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    payload = {
        "contents": [{ "parts": [{"text": prompt}] }]
    }
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        response_data = response.json()
        return response_data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None

def generate_content(topic, category):
    print(f"🧠 Generating Insight for: '{topic}' ({category})...")
    
    # PASS 1: THE PHILOSOPHER (Insight Focused)
    # Goal: Level 1 & 2 Humanization (Opinionated, No Listicles)
    draft_prompt = f"""
    Role: A cultural critic and thoughtful essayist (like Paul Graham or Naval Ravikant).
    Task: Write a deep, reflective essay about "{topic}".
    Context: This fits into the "{category}" pillar of our publication.
    
    CRITICAL RULES (The "Anti-Blog" Manifesto):
    1. **NO Listicles:** Do not use "Top 5 ways" or bullet points as the main structure.
    2. **NO How-To:** We are not teaching. We are observing and analyzing.
    3. **Tone:** Opinionated, contemplative, slightlycontrarian. Use "I think" or "We observe", not "You should".
    4. **Structure:** Fluid essay format. Use <h2> headers for major shifts in thought, not for steps.

    Core Question to Answer: What is the second-order effect of this topic on human life?

    Output Format: raw text body only.
    """
    
    draft = call_gemini(draft_prompt)
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
    
    keywords_json = call_gemini(keyword_prompt)
    
    # Parse keywords or use defaults
    keyword_data = {{"primaryKeywords": [], "longTailKeywords": [], "trendingTerms": [], "hashtags": [], "searchQueries": []}}
    if keywords_json:
        try:
            clean_kw = keywords_json.replace("```json", "").replace("```", "").strip()
            keyword_data = json.loads(clean_kw)
        except:
            pass

    print(f"✒️ Polishing & Formatting '{topic}'...")

    # PASS 2: THE EDITOR (Structure & Monetization Guard + SEO)
    # Goal: Level 3, 4, 5 (Flow, Formatting, Soft Monetization) + SEO Optimization
    editor_prompt = f"""
    Role: Editor-in-Chief of a high-end magazine (e.g., The Atlantic) with SEO expertise.
    Task: Polish this essay for publication AND optimize for search engines and social media.

    Input Draft:
    {draft[:15000]}

    Guidelines:
    1. **Human Flow:** Ensure paragraphs flow logically. Remove robotic transitions like "In conclusion".
    2. **Formatting:** Return VALID JSON with these keys:
       - "title" (Provocative/Abstract, 50-60 characters)
       - "content" (HTML Body with <h2>, <p>, <blockquote> tags)
       - "metaDescription" (Compelling 150-160 char summary)
       - "keywords" (Array of 5-7 relevant SEO keywords)
       - "hashtags" (Array of 3-5 hashtags with # prefix)
       - "searchQueries" (Array of 2-3 search queries this should rank for)
       - "excerpt" (2-sentence summary)
       
    3. **Content Quality:**
       - Use <h2> for section breaks (concept shifts)
       - Use <blockquote> for the most powerful sentence
       - **NO aggressive CTAs.**
    
    Output JSON Example:
    {{
      "title": "The Hidden Cost of Productivity",
      "metaDescription": "Discover why understanding productivity changes everything. A deep dive into second-order effects.",
      "keywords": ["{category.lower()}", "personal growth", "modern life", "productivity"],
      "hashtags": ["#{category}", "#PersonalGrowth", "#DeepThinking"],
      "searchQueries": ["productivity second order effects", "hidden cost of efficiency"],
      "excerpt": "We think we understand productivity. But beneath the surface lies a reshaping force",
      "content": "<p>It starts subtly...</p><blockquote>Efficiency kills creativity.</blockquote>..."
    }}
    """

    final_json_text = call_gemini(editor_prompt)
    if not final_json_text: return None, None, None, None, None, None, None

    # Cleanup JSON
    clean_text = final_json_text.replace("```json", "").replace("```", "").strip()
    
    try:
        data = json.loads(clean_text)
        
        # Extract initial content
        title = data.get("title")
        content = data.get("content")
        
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
        
        humanized_content = call_gemini(humanize_prompt)
        
        # Use humanized version if successful
        if humanized_content and len(humanized_content) > 200:
            content = humanized_content.strip()
        
        # Combine researched keywords with editor-generated ones
        all_keywords = keyword_data.get("primaryKeywords", []) + keyword_data.get("longTailKeywords", [])[:2]
        if not all_keywords:
            all_keywords = data.get("keywords", [])
        
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
    except json.JSONDecodeError:
        print("Error parsing JSON. Returning basic data.")
        return f"Reflections on {topic}", final_json_text, "", [], [], [], ""

def publish_post():
    # LEVEL 4: Randomized Behavior
    # Select a random Category, then a random Topic from that category
    category = random.choice(list(PILLARS.keys()))
    topic = random.choice(PILLARS[category])
    
    # Get SEO-optimized content
    try:
        title, content, meta_desc, keywords, hashtags, search_queries, excerpt = generate_content(topic, category)
    except Exception as e:
        return {"success": False, "error": f"Content Generation Error: {str(e)}"}

    if not title:
        print("❌ Generation failed.")
        return {"success": False, "error": "Generation produced no title/content"}

    slug = title.lower().replace(" ", "-").replace(":", "").replace("?", "").replace("(", "").replace(")", "").replace("'", "")
    
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
