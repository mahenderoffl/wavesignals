# Daily Blog Posting Scheduler
# Runs twice daily at optimal times for maximum engagement

import schedule
import time
from bot import publish_post

# Best times to post blogs based on research:
# Morning: 6-8 AM (people checking news/social before work)
# Evening: 6-8 PM (people unwinding after work)

def job():
    """Generate and publish one blog post"""
    print(f"🕐 Scheduler triggered at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        publish_post()
        print("✅ Scheduled post published successfully")
    except Exception as e:
        print(f"❌ Scheduled post failed: {e}")

# Schedule posts for optimal engagement times
# Post once daily at 6:00 AM UTC (11:30 AM IST) - Morning reading time
schedule.every().day.at("06:00").do(job)

# ❌ REMOVED: Evening post to reduce to 1/day for AdSense compliance
# schedule.every().day.at("18:00").do(job)

# Alternative: Schedule in IST (if deploying in IST timezone)
# Morning: 6:00 AM IST
# schedule.every().day.at("00:30").do(job)  # 6:00 AM IST = 00:30 UTC

print("📅 Scheduler initialized:")
print("   - Daily post: 6:00 AM UTC (11:30 AM IST)")
print("   - Frequency: 1 post per day")
print("   - Rate limit: 23 hours enforced by database")
print("\n⏰ Waiting for scheduled time...")

# Keep the script running
while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute
