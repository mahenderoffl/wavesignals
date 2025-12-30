# Test which Gemini models work with your activated API

import requests

# Your activated Gemini API key (from HF Space)
API_KEY = input("Paste your NEW activated Gemini API key: ")

models_to_test = [
    "gemini-pro",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro-latest"
]

apis_to_test = [
    "https://generativelanguage.googleapis.com/v1",
    "https://generativelanguage.googleapis.com/v1beta"
]

print("\n🔍 Testing Gemini Models...\n")

for api_base in apis_to_test:
    print(f"\nAPI: {api_base}")
    print("=" * 60)
    
    for model in models_to_test:
        url = f"{api_base}/models/{model}:generateContent?key={API_KEY}"
        payload = {"contents": [{"parts": [{"text": "Say hi"}]}]}
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {model:30} - WORKS!")
            else:
                print(f"❌ {model:30} - HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {model:30} - Error: {str(e)[:50]}")

print("\n✅ Use the model that shows 'WORKS!' in bot.py")
