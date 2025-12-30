"""
WaveSignals Testing Dashboard for Hugging Face Space
Shows test buttons and error console for debugging
"""

import gradio as gr
from bot import publish_post, PILLARS
from db import get_db_connection, init_db
import os
from datetime import datetime
import traceback

def test_database():
    """Test database connection"""
    try:
        conn = get_db_connection()
        if not conn:
            return "❌ Database connection failed\n\nCheck DATABASE_URL secret in HF Space settings"
        
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM posts")
        count = cur.fetchone()['count']
        cur.close()
        conn.close()
        
        return f"✅ Database connected!\n\nTotal posts in database: {count}"
    except Exception as e:
        return f"❌ Database error:\n\n{str(e)}\n\n{traceback.format_exc()}"

def test_gemini_api():
    """Test Gemini API key"""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return "❌ GEMINI_API_KEY not configured\n\nGo to Settings → Repository secrets → Add GEMINI_API_KEY"
    
    # Test actual API call
    try:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": "Test"}]}]}
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return f"✅ Gemini API working!\n\nAPI Key: {api_key[:15]}...\nStatus: {response.status_code}"
        else:
            return f"❌ Gemini API error\n\nHTTP {response.status_code}\n\n{response.text[:500]}"
            
    except Exception as e:
        return f"❌ Gemini API test failed:\n\n{str(e)}"

def test_blog_generation():
    """Test full blog generation"""
    try:
        yield "🚀 Starting blog generation...\n\nThis will take 30-60 seconds.\n", ""
        
        result = publish_post()
        
        if isinstance(result, dict) and result.get("success"):
            output = f"""✅ Blog post generated successfully!

**Post ID:** {result['id']}
**Title:** {result['title']}
**Generated at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The post has been saved to the database!

Check your database or visit the frontend to see it.
"""
            yield output, "✅ Generation successful!"
        else:
            error = result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)
            output = f"""❌ Generation failed

**Error:** {error}

**Troubleshooting:**
1. Check Gemini API key is valid
2. Check database connection
3. View detailed logs below
"""
            yield output, f"❌ Error: {error}"
            
    except Exception as e:
        error_output = f"""❌ Exception during generation

**Error:** {str(e)}

**Stack trace:**
{traceback.format_exc()}

**Common fixes:**
- Check GEMINI_API_KEY secret
- Check DATABASE_URL secret
- Restart the Space
"""
        yield error_output, f"❌ Exception: {str(e)}"

def get_system_status():
    """Get comprehensive system status"""
    status_lines = []
    
    # Check secrets
    status_lines.append("## 🔐 Environment Variables\n")
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    db_url = os.getenv("DATABASE_URL")
    admin_pass = os.getenv("ADMIN_PASSWORD")
    
    status_lines.append(f"- GEMINI_API_KEY: {'✅ Set' if gemini_key else '❌ Missing'}")
    status_lines.append(f"- DATABASE_URL: {'✅ Set' if db_url else '❌ Missing'}")
    status_lines.append(f"- ADMIN_PASSWORD: {'✅ Set' if admin_pass else '❌ Missing'}\n")
    
    # Check database
    status_lines.append("## 💾 Database\n")
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as count FROM posts")
            total_posts = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM posts WHERE date > NOW() - INTERVAL '24 hours'")
            posts_24h = cur.fetchone()['count']
            
            cur.close()
            conn.close()
            
            status_lines.append(f"- Connection: ✅ Connected")
            status_lines.append(f"- Total posts: {total_posts}")
            status_lines.append(f"- Posts (24h): {posts_24h}\n")
        else:
            status_lines.append("- Connection: ❌ Failed\n")
    except Exception as e:
        status_lines.append(f"- Error: ❌ {str(e)}\n")
    
    # Check API
    status_lines.append("## 🤖 AI Provider\n")
    if gemini_key:
        status_lines.append(f"- Gemini: ✅ Configured")
        status_lines.append(f"- Key preview: {gemini_key[:15]}...\n")
    else:
        status_lines.append("- Gemini: ❌ Not configured\n")
    
    status_lines.append(f"## ⏰ Current Time\n")
    status_lines.append(f"- UTC: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    status_lines.append(f"- Local: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return "\n".join(status_lines)

# Create Gradio interface
with gr.Blocks(title="WaveSignals Testing Console", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🌊 WaveSignals Testing Console")
    gr.Markdown("Debug and test your blog automation system")
    
    with gr.Tab("🧪 Tests"):
        gr.Markdown("### Run System Tests")
        
        with gr.Row():
            with gr.Column():
                db_test_btn = gr.Button("Test Database Connection", variant="primary")
                db_output = gr.Textbox(label="Database Test Result", lines=5)
                
            with gr.Column():
                api_test_btn = gr.Button("Test Gemini API", variant="primary")
                api_output = gr.Textbox(label="API Test Result", lines=5)
        
        gr.Markdown("---")
        gr.Markdown("### Generate Test Blog Post")
        
        gen_btn = gr.Button("🚀 Generate Blog Post", variant="primary", size="lg")
        gen_output = gr.Markdown(label="Generation Output")
        gen_status = gr.Textbox(label="Quick Status", lines=1)
        
        # Wire up buttons
        db_test_btn.click(fn=test_database, outputs=[db_output])
        api_test_btn.click(fn=test_gemini_api, outputs=[api_output])
        gen_btn.click(fn=test_blog_generation, outputs=[gen_output, gen_status])
    
    with gr.Tab("📊 System Status"):
        gr.Markdown("### Current System Configuration")
        
        status_display = gr.Markdown()
        refresh_btn = gr.Button("🔄 Refresh Status")
        
        refresh_btn.click(fn=get_system_status, outputs=[status_display])
        app.load(fn=get_system_status, outputs=[status_display])
    
    with gr.Tab("📖 Help"):
        gr.Markdown("""
        ## How to Use This Console
        
        ### 1. Test Database
        - Verifies DATABASE_URL secret
        - Checks if posts table exists
        - Shows total post count
        
        ### 2. Test Gemini API
        - Verifies GEMINI_API_KEY secret
        - Makes test API call
        - Shows if key is valid
        
        ### 3. Generate Blog Post
        - Full end-to-end test
        - Generates actual blog post
        - Saves to database
        - Shows detailed errors if fails
        
        ### Common Issues
        
        **"GEMINI_API_KEY not configured"**
        - Go to Settings → Repository secrets
        - Add secret: GEMINI_API_KEY
        - Value: Get from https://aistudio.google.com/app/apikey
        
        **"Database connection failed"**
        - Check DATABASE_URL secret is set
        - Format: `postgresql://user:pass@host/db?sslmode=require`
        - No `&channel_binding=require` at end!
        
        **"Generation produced no title/content"**
        - Gemini API is failing
        - Check API key is valid
        - Check API quota (60 requests/min limit)
        
        ### Backend API Endpoints
        
        All these work even without this UI:
        - `GET /` - Status
        - `GET /health` - Health check
        - `GET /api/posts` - List posts
        - `POST /api/generate-post` - Generate post (needs X-Admin-Key header)
        
        ### Next Steps
        
        After all tests pass:
        1. Setup cron-job.org to ping `/health` every 5 min
        2. Configure GitHub Actions
        3. Test admin panel at your Netlify site
        """)
    
    gr.Markdown("---")
    gr.Markdown("**Backend URL:** https://mahendercreates-wavesignals-backend.hf.space")

if __name__ == "__main__":
    print("🌊 WaveSignals Testing Console Starting...")
    print("🔧 This Gradio UI provides testing and debugging tools")
    print("📊 Access at: http://localhost:7860 or your HF Space URL")
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
