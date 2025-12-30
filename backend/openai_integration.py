# OpenAI Integration Addition for bot.py
# Add this right after the Gemini function

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def call_openai(prompt):
    """Call OpenAI API (GPT-4 or GPT-3.5 Turbo)"""
    if not OPENAI_API_KEY:
        print("⚠️ OPENAI_API_KEY not configured")
        return None
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    payload = {
        "model": "gpt-4-turbo-preview",  # or "gpt-3.5-turbo" for cheaper
        "messages": [
            {"role": "system", "content": "You are a thoughtful content writer."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4000,
        "temperature": 0.8
    }
    
    try:
        print(f"🔄 Calling OpenAI API...")
        response = requests.post(url, json=payload, headers=headers, timeout=90)
        
        if response.status_code != 200:
            print(f"❌ OpenAI API Error: HTTP {response.status_code}")
            return None
        
        response_data = response.json()
        content = response_data['choices'][0]['message']['content']
        print(f"✅ OpenAI responded ({len(content)} chars)")
        return content
        
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return None

def call_ai_with_fallback(prompt):
    """Try Gemini first, fall back to OpenAI if it fails"""
    # Try Gemini
    result = call_gemini(prompt)
    if result:
        return result
    
    # Fallback to OpenAI
    print("⚠️ Gemini failed, trying OpenAI fallback...")
    result = call_openai(prompt)
    if result:
        return result
    
    print("❌ Both AI providers failed!")
    return None

# Then in generate_content, replace:
# draft = call_gemini(draft_prompt)
# with:
# draft = call_ai_with_fallback(draft_prompt)

# And same for all other call_gemini() calls
