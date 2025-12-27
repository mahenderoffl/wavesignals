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
# Morning post: 6:00 AM UTC (11:30 AM IST)
schedule.every().day.at("06:00").do(job)

# Evening post: 18:00 UTC (11:30 PM IST)
schedule.every().day.at("18:00").do(job)

# Alternative: Schedule in IST (if deploying in IST timezone)
# Morning: 6:00 AM IST
# schedule.every().day.at("00:30").do(job)  # 6:00 AM IST = 00:30 UTC

# Evening: 6:00 PM IST  
# schedule.every().day.at("12:30").do(job)  # 6:00 PM IST = 12:30 UTC

print("📅 Scheduler initialized:")
print("   - Morning post: 6:00 AM UTC (11:30 AM IST)")
print("   - Evening post: 6:00 PM UTC (11:30 PM IST)")
print("   - Frequency: 2 posts per day")
print("\n⏰ Waiting for scheduled times...")

# Keep the script running
while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute
