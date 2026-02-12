"""
Setup script for FCM subscribers table
Run this to initialize the database for custom notifications
"""

import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('../.env.local')

# Get database connection string from environment
DATABASE_URL = os.getenv('OLD_DATABASE_URL') or os.getenv('DATABASE_URL')

def setup_fcm_table():
    """Create FCM subscribers table in database."""
    
    if not DATABASE_URL:
        print("❌ No database URL found")
        print("   Run 'vercel env pull .env.local' from project root first")
        return False
    
    try:
        print("🔗 Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("📋 Creating fcm_subscribers table...")
        
        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fcm_subscribers (
                id SERIAL PRIMARY KEY,
                token TEXT UNIQUE NOT NULL,
                device_type VARCHAR(100),
                user_agent TEXT,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                preferences JSONB DEFAULT '{}'::jsonb
            );
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fcm_active ON fcm_subscribers(active);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fcm_created ON fcm_subscribers(created_at DESC);
        """)
        
        conn.commit()
        print("✅ Table created successfully!")
        
        # Check if table has any data
        cursor.execute("SELECT COUNT(*) FROM fcm_subscribers;")
        count = cursor.fetchone()[0]
        print(f"📊 Current subscribers: {count}")
        
        cursor.close()
        conn.close()
        
        print("\n✨ Setup complete!")
        print("\nNext steps:")
        print("1. Deploy to Vercel: vercel --prod")
        print("2. Open admin panel: https://wave-signals.vercel.app/admin/panel.html")
        print("3. Go to Notifications section")
        print("4. Users can subscribe via the subscribe button on your blog")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 FCM Notifications Setup")
    print("=" * 50)
    setup_fcm_table()
