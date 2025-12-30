"""
Test Gemini API directly to see exact error
"""
import requests
import os

# Read API key from environment or use test key
API_KEY = os.getenv("GEMINI_API_KEY", "")

if not API_KEY:
    print("❌ GEMINI_API_KEY not set in environment")
    print("Set it with: $env:GEMINI_API_KEY='your_key_here'")
    API_KEY = input("Or paste your Gemini API key here: ").strip()

url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"

# Simple test prompt
payload = {
    "contents": [{
        "parts": [{"text": "Write a short 100-word essay about the future of AI."}]
    }]
}

print(f"\n🔄 Testing Gemini API...")
print(f"URL: {url[:80]}...")
print(f"API Key: {API_KEY[:15]}...\n")

try:
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=30)
    
    print(f"HTTP Status: {response.status_code}")
    print(f"\nFull Response:")
    print("=" * 60)
    print(response.text)
    print("=" * 60)
    
    if response.status_code == 200:
        data = response.json()
        if 'candidates' in data:
            content = data['candidates'][0]['content']['parts'][0]['text']
            print(f"\n✅ SUCCESS! Generated content:")
            print(content)
        else:
            print(f"\n❌ Unexpected response format")
    else:
        print(f"\n❌ API Error:HTTP {response.status_code}")
        
except Exception as e:
    print(f"\n❌ Exception: {e}")
