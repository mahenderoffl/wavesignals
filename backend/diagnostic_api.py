"""
Enhanced diagnostic version of bot.py with detailed error reporting
This will help us see EXACTLY what's going wrong
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from db import get_db_connection, init_db
from apscheduler.schedulers.background import BackgroundScheduler
import os
import requests

app = Flask(__name__)
CORS(app)

# Initialize database
init_db()

API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "wavesignals@2025")

def require_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Admin-Key')
        if not token or token != ADMIN_PASSWORD:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/test-ai', methods=['POST'])
@require_auth
def test_ai():
    """Test both AI providers with simple prompts and return detailed diagnostics"""
    results = {
        "gemini": {"configured": bool(API_KEY), "test": None},
        "openai": {"configured": bool(OPENAI_API_KEY), "test": None}
    }
    
    # Test Gemini
    if API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
            payload = {"contents": [{"parts": [{"text": "Write one sentence about AI."}]}]}
            
            response = requests.post(url, json=payload, timeout=30)
            results["gemini"]["test"] = {
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text[:500],
                "success": response.status_code == 200
            }
        except Exception as e:
            results["gemini"]["test"] = {"error": str(e), "success": False}
    
    # Test OpenAI
    if OPENAI_API_KEY:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Write one sentence about AI."}],
                "max_tokens": 50
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            results["openai"]["test"] = {
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text[:500],
                "success": response.status_code == 200
            }
        except Exception as e:
            results["openai"]["test"] = {"error": str(e), "success": False}
    
    return jsonify(results)

@app.route('/api/test-simple-generation', methods=['POST'])
@require_auth
def test_simple_generation():
    """Test with the simplest possible prompt to see if safety filters are the issue"""
    
    # Ultra-simple prompt
    simple_prompt = "Write a 100-word essay about technology."
    
    results = {"prompt": simple_prompt, "gemini": None, "openai": None}
    
    # Try Gemini
    if API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
            payload = {"contents": [{"parts": [{"text": simple_prompt}]}]}
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and len(data['candidates']) > 0:
                    content = data['candidates'][0]['content']['parts'][0]['text']
                    results["gemini"] = {"success": True, "content": content[:200] + "..."}
                else:
                    results["gemini"] = {"success": False, "error": "No candidates in response", "full_response": data}
            else:
                results["gemini"] = {"success": False, "status": response.status_code, "error": response.text[:500]}
        except Exception as e:
            results["gemini"] = {"success": False, "error": str(e)}
    
    # Try OpenAI
    if OPENAI_API_KEY:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": simple_prompt}],
                "max_tokens": 200
            }
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                results["openai"] = {"success": True, "content": content[:200] + "..."}
            else:
                results["openai"] = {"success": False, "status": response.status_code, "error": response.text[:500]}
        except Exception as e:
            results["openai"] = {"success": False, "error": str(e)}
    
    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
