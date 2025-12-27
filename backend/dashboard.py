"""
WaveSignals System Monitor and Dashboard
Provides real-time monitoring interface for backend health, blog generation, and system status
"""

import gradio as gr
from bot import publish_post
from db import get_db_connection
import os
from datetime import datetime
import json

# Simple in-memory event log (last 100 events)
event_log = []

def log_event(event_type, data):
    """Log system events"""
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "data": data
    }
    event_log.append(event)
    if len(event_log) > 100:
        event_log.pop(0)  # Keep only last 100 events

def generate_blog_manual():
    """Manual blog generation with real-time status"""
    try:
        log_event("manual_trigger", {"source": "dashboard", "time": datetime.now().isoformat()})
        
        # Show starting message
        yield "🚀 **Starting blog generation...**\n\nThis may take 30-60 seconds.\n", ""
        
        result = publish_post()
        
        if isinstance(result, dict) and result.get("success"):
            message = f"""✅ **Success!**

**Post ID:** {result['id']}
**Title:** {result['title']}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The blog post has been saved to the database and should appear on the frontend within a minute.
"""
            log_event("post_generated", result)
            yield message, "✅ Post generated successfully"
        else:
            error_msg = result.get('error', 'Unknown error') if isinstance(result, dict) else "No response from bot"
            message = f"""❌ **Failed**

**Error:** {error_msg}

**Troubleshooting:**
1. Check if GEMINI_API_KEY is configured
2. Verify database connection
3. Check Hugging Face Space logs for details
"""
            log_event("post_failed", {"error": error_msg})
            yield message, "❌ Generation failed"
            
    except Exception as e:
        message = f"""❌ **Error**

**Exception:** {str(e)}

**Stack trace logged** - Check Hugging Face logs for full details.
"""
        log_event("exception", {"error": str(e)})
        yield message, f"❌ Error: {str(e)}"

def get_system_status():
    """Get current system health"""
    try:
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                
                # Get recent posts
                cur.execute("SELECT title, date FROM posts ORDER BY date DESC LIMIT 5")
                recent = cur.fetchall()
                
                # Get total post count
                cur.execute("SELECT COUNT(*) as count FROM posts")
                total_posts = cur.fetchone()['count']
                
                # Get posts today
                cur.execute("SELECT COUNT(*) as count FROM posts WHERE date > NOW() - INTERVAL '24 hours'")
                posts_today = cur.fetchone()['count']
                
                cur.close()
                conn.close()
                
                posts_list = "\n".join([f"• **{p['title']}** ({p['date'].strftime('%Y-%m-%d %H:%M')})" for p in recent]) if recent else "No posts yet"
                
                gemini_key = os.getenv('GEMINI_API_KEY', '')
                gemini_status = f"Configured ({gemini_key[:15]}...)" if gemini_key else "❌ NOT CONFIGURED"
                
                return f"""## 🟢 System Status: HEALTHY

### Database
✅ **Connected** | Total Posts: **{total_posts}** | Posts (24h): **{posts_today}**

### APIs
🔑 **Gemini API:** {gemini_status}

### Recent Posts (Last 5)
{posts_list}

---
*Last checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
            except Exception as e:
                return f"""## 🟡 System Status: PARTIAL

### Database
⚠️ **Connected but query failed:** {str(e)}

Try running `init_db()` to initialize tables.
"""
        else:
            return """## 🔴 System Status: DATABASE ERROR

### Database
❌ **Disconnected**

**Action Required:**
1. Check DATABASE_URL environment variable
2. Verify PostgreSQL server is running
3. Check network connectivity

*Last checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    except Exception as e:
        return f"""## 🔴 System Status: ERROR

**Critical Error:** {str(e)}

Check Hugging Face Space logs for details.
"""

def get_activity_log():
    """Get recent activity logs"""
    if not event_log:
        return "No recent activity. Generate a blog post to see logs here."
    
    log_lines = []
    for event in reversed(event_log[-20:]):  # Last 20 events
        timestamp = event['timestamp'].split('T')[1][:8] if 'T' in event['timestamp'] else event['timestamp']
        event_type = event['type']
        
        # Format based on event type
        if event_type == "post_generated":
            title = event.get('data', {}).get('title', 'N/A')
            log_lines.append(f"✅ `[{timestamp}]` **Generated:** {title}")
        elif event_type == "post_failed":
            error = event.get('data', {}).get('error', 'Unknown')
            log_lines.append(f"❌ `[{timestamp}]` **Failed:** {error[:50]}...")
        elif event_type == "manual_trigger":
            log_lines.append(f"🚀 `[{timestamp}]` **Manual trigger** from dashboard")
        elif event_type == "exception":
            error = event.get('data', {}).get('error', 'Unknown')
            log_lines.append(f"⚠️ `[{timestamp}]` **Exception:** {error[:50]}...")
        else:
            log_lines.append(f"ℹ️ `[{timestamp}]` **{event_type}**")
    
    return "\n".join(log_lines)

def check_frontend_sync():
    """Check if posts are reaching the frontend"""
    try:
        import requests
        
        # Check if Netlify site is accessible
        response = requests.get("https://wavesignals.netlify.app", timeout=5)
        
        if response.status_code == 200:
            frontend_status = "✅ Frontend is online"
        else:
            frontend_status = f"⚠️ Frontend returned status {response.status_code}"
            
        # Check database posts
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as count FROM posts WHERE published = TRUE")
            published_count = cur.fetchone()['count']
            cur.close()
            conn.close()
            
            return f"""## Frontend Sync Status

{frontend_status}

**Published Posts in Database:** {published_count}

**Note:** Posts in the database should automatically appear on the frontend after the next deployment or page refresh.

**Frontend URL:** https://wavesignals.netlify.app

*Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        else:
            return "❌ Cannot check - database disconnected"
            
    except Exception as e:
        return f"""## Frontend Sync Status

⚠️ **Could not reach frontend:** {str(e)}

This is normal if:
- Frontend is not deployed yet
- Network timeout

**Database Status:** Will check when connection is available.
"""

# Create Gradio Interface
with gr.Blocks(title="WaveSignals Control Dashboard", theme=gr.themes.Soft()) as dashboard:
    gr.Markdown("""
    # 🌊 WaveSignals Control Dashboard
    **Real-time monitoring and control for your automated blog**
    """)
    
    with gr.Tab("🚀 Generate Blog"):
        gr.Markdown("### Manual Blog Post Generation")
        gr.Markdown("Click the button below to manually generate a new AI blog post. This process takes 30-60 seconds.")
        
        generate_btn = gr.Button("🚀 Generate New Blog Post", variant="primary", size="lg")
        output_markdown = gr.Markdown(label="Generation Status")
        output_status = gr.Textbox(label="Quick Status", interactive=False)
        
        generate_btn.click(
            fn=generate_blog_manual,
            outputs=[output_markdown, output_status]
        )
    
    with gr.Tab("💚 System Health"):
        gr.Markdown("### Backend & Database Status")
        
        status_display = gr.Markdown()
        
        with gr.Row():
            refresh_btn = gr.Button("🔄 Refresh Status", size="sm")
            
        refresh_btn.click(
            fn=get_system_status,
            outputs=[status_display]
        )
        
        # Auto-load on page load
        dashboard.load(fn=get_system_status, outputs=[status_display])
    
    with gr.Tab("📊 Activity Log"):
        gr.Markdown("### Recent System Events")
        gr.Markdown("Track blog generation attempts, successes, and failures.")
        
        activity_log = gr.Markdown()
        refresh_log_btn = gr.Button("🔄 Refresh Log")
        
        refresh_log_btn.click(
            fn=get_activity_log,
            outputs=[activity_log]
        )
        
        dashboard.load(fn=get_activity_log, outputs=[activity_log])
    
    with gr.Tab("🌐 Frontend Sync"):
        gr.Markdown("### Check if Posts Reach Frontend")
        
        sync_status = gr.Markdown()
        check_sync_btn = gr.Button("🔍 Check Sync Status")
        
        check_sync_btn.click(
            fn=check_frontend_sync,
            outputs=[sync_status]
        )
        
        dashboard.load(fn=check_frontend_sync, outputs=[sync_status])
    
    gr.Markdown("""
    ---
    ### 📌 Quick Links
    - [Frontend Site](https://wavesignals.netlify.app)
    - [Admin Panel](https://wavesignals.netlify.app/admin)
    - [Hugging Face Space Settings](https://huggingface.co/spaces/mahendercreates/wavesignals-backend/settings)
    
    ### ⚙️ External Setup Required
    - **Cron Job:** Setup at [cron-job.org](https://cron-job.org) to ping `/health` every 5 minutes
    - **Make.com:** Create automation for 2x daily post generation (optional backup)
    """)

if __name__ == "__main__":
    print("🌊 Starting Wave Signals Dashboard...")
    print("📍 Dashboard will be available at: http://localhost:7860")
    print("🔗 Or on Hugging Face Space URL")
    dashboard.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
