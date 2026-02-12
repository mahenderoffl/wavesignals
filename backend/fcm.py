"""
Updated FCM module with custom notification support and fixed send_multicast
"""
import firebase_admin
from firebase_admin import credentials, messaging
from db import get_db_connection
import os
import json

# Initialize Firebase Admin SDK
firebase_initialized = False
try:
    # Try from service account JSON string in environment variable first
    service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT')
    if service_account_json:
        print(f"🔥 FIREBASE_SERVICE_ACCOUNT found in env ({len(service_account_json)} chars)")
        service_account_dict = json.loads(service_account_json)
        cred = credentials.Certificate(service_account_dict)
        firebase_admin.initialize_app(cred)
        firebase_initialized = True
        print("✅ Firebase Admin SDK initialized from environment variable")
    else:
        # Fallback to file
        print("⚠️ FIREBASE_SERVICE_ACCOUNT not in env, trying local file...")
        cred_path = os.path.join(os.path.dirname(__file__), 'firebase-service-account.json')
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            firebase_initialized = True
            print("✅ Firebase Admin SDK initialized from file")
        else:
            print(f"❌ Firebase credentials file not found at: {cred_path}")
            print("⚠️ Push notifications will NOT work until Firebase is configured!")
except Exception as e:
    print(f"❌ Firebase Admin SDK initialization FAILED: {e}")
    import traceback
    traceback.print_exc()
    print("⚠️ Push notifications will NOT work!")

def send_notification_to_all(title, body, post_url=None):
    """Send push notification to all subscribed users"""
    # Check if Firebase is initialized
    if not firebase_initialized:
        print("❌ Cannot send notifications: Firebase Admin SDK not initialized")
        return {"success": False, "error": "Firebase not configured"}
    
    conn = get_db_connection()
    if not conn:
        return {"success": False, "error": "DB connection failed"}
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT token FROM fcm_subscribers WHERE active = TRUE AND token IS NOT NULL")
        tokens = [row['token'] for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        if not tokens:
            print("ℹ️ No FCM tokens found - no notifications sent")
            return {"success": True, "sent": 0, "message": "No subscribers yet"}
        
        print(f"📬 Sending notifications to {len(tokens)} subscribers...")
        
        # Build notification data
        notification_data = {
            'title': title,
            'body': body[:100] if len(body) > 100 else body
        }
        
        # Create message data
        data_payload = {}
        if post_url:
            data_payload['url'] = post_url
            data_payload['click_action'] = post_url
        
        # Send to each token individually (more reliable than multicast)
        success_count = 0
        failure_count = 0
        failed_tokens = []
        
        for token in tokens:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(**notification_data),
                    data=data_payload,
                    token=token
                )
                messaging.send(message)
                success_count += 1
            except Exception as e:
                failure_count += 1
                failed_tokens.append(token)
                print(f"   Failed to send to token: {e}")
        
        print(f"✅ Successfully sent {success_count} notifications")
        print(f"❌ Failed to send {failure_count} notifications")
        
        # Clean up invalid tokens
        if failed_tokens:
            remove_invalid_tokens(failed_tokens)
        
        return {
            "success": True,
            "sent": success_count,
            "failed": failure_count,
            "total_subscribers": len(tokens)
        }
        
    except Exception as e:
        print(f"❌ FCM send error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def send_custom_notification(title, body, url=None):
    """Send custom notification from admin panel"""
    return send_notification_to_all(title, body, url)

def remove_invalid_tokens(tokens):
    """Remove expired or invalid FCM tokens from database"""
    if not tokens:
        return
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        for token in tokens:
            cur.execute("UPDATE fcm_subscribers SET active = FALSE WHERE token = %s", (token,))
        conn.commit()
        print(f"🗑️ Deactivated {len(tokens)} invalid FCM tokens")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Error removing invalid tokens: {e}")

def send_test_notification():
    """Send a test notification to all subscribers"""
    return send_notification_to_all(
        title="🧪 Test Notification",
        body="This is a test notification from WaveSignals. If you received this, notifications are working!",
        post_url="https://wavesignals.waveseed.app"
    )

def get_subscriber_count():
    """Get count of active FCM subscribers"""
    conn = get_db_connection()
    if not conn:
        return 0
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM fcm_subscribers WHERE active = TRUE AND token IS NOT NULL")
        count = cur.fetchone()['count']
        cur.close()
        conn.close()
        return count
    except:
        return 0
