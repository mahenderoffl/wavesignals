# Custom Notification Sender - User Guide

## Overview
The admin panel now includes a custom notification sender that allows you to send push notifications to specific subscribers instead of broadcasting to everyone.

## Features

### 1. **Individual Subscriber Selection**
- View all active FCM push notification subscribers
- Select specific subscribers using checkboxes
- "Select All" option for bulk operations
- Real-time counter showing selected subscribers

### 2. **Custom Notification Content**
- **Title**: Notification heading (max 100 characters)
- **Message**: Notification body content (max 500 characters)
- **URL** (Optional): Target page when notification is clicked

### 3. **Visual Interface**
- Beautiful gradient design (purple theme)
- Real-time subscriber list with device information
- Success/error status messages
- Clear button to reset form

## How to Use

### Step 1: Access the Notification Manager
1. Log in to your admin panel (`/admin/panel.html`)
2. Click on **"Notifications"** in the left sidebar
3. Scroll to the **"Send Custom Notification"** section (purple gradient box)

### Step 2: Compose Your Message
1. **Enter Title**: Write a compelling notification title
   - Example: "New Feature Released!"
   - Keep it short and attention-grabbing

2. **Enter Message**: Write the notification body
   - Example: "Check out our new dark mode feature. Click to learn more!"
   - Be clear and actionable

3. **Add URL** (Optional): Link to specific content
   - Example: `https://wave-signals.vercel.app/blog/new-feature`
   - Leave empty for homepage

### Step 3: Select Recipients
1. **View Subscriber List**: All active subscribers appear below the message fields
2. **Select Specific Users**: Check boxes next to individual subscribers
3. **Select All**: Use the "Select All Subscribers" checkbox at the top
4. **Monitor Selection**: Counter shows "(X of Y selected)"

### Step 4: Send Notification
1. Click **"📤 Send Notification"** button
2. Wait for confirmation message
3. Check success status: "✅ Notification sent to X subscriber(s)!"

### Step 5: Clear Form
- Click **"Clear"** button to reset all fields and selections
- Form also auto-clears after successful send

## API Endpoints

### Get FCM Subscribers
```
GET /api/fcm-subscribers
Headers: X-Admin-Key: <your-admin-password>
Response: { success: true, subscribers: [...], total: N }
```

### Send Targeted Notification
```
POST /api/send-notification
Headers: 
  X-Admin-Key: <your-admin-password>
  Content-Type: application/json
Body: {
  "title": "Notification Title",
  "body": "Notification message content",
  "url": "https://optional-url.com",
  "tokens": ["fcm_token_1", "fcm_token_2", ...]
}
Response: { success: true, sent: N, failed: M, total: X }
```

## Database Schema

### fcm_subscribers Table
```sql
CREATE TABLE fcm_subscribers (
    id SERIAL PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    device_type VARCHAR(100),
    user_agent TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    preferences JSONB DEFAULT '{}'::jsonb
);
```

## Setup Instructions

### 1. Run Database Migration
Execute the SQL migration to create the FCM subscribers table:
```bash
psql "YOUR_DATABASE_URL" -f backend/add_fcm_subscribers_table.sql
```

### 2. Verify Firebase Configuration
Ensure `FIREBASE_SERVICE_ACCOUNT` environment variable is set in Vercel:
```bash
# Check in Vercel Dashboard > Settings > Environment Variables
FIREBASE_SERVICE_ACCOUNT={"type":"service_account",...}
```

### 3. Test the Feature
1. Open admin panel notifications section
2. Check if subscribers load correctly
3. Send a test notification to yourself
4. Verify delivery on your device

## Troubleshooting

### No Subscribers Showing
- **Cause**: Table doesn't exist or is empty
- **Solution**: Run migration script and add test subscriber
```sql
INSERT INTO fcm_subscribers (token, device_type, active) 
VALUES ('test_token_123', 'Chrome/Windows', true);
```

### "Unauthorized" Error
- **Cause**: Missing or incorrect admin key
- **Solution**: Ensure you're logged in to admin panel with correct password

### "Firebase initialization failed"
- **Cause**: Missing Firebase service account credentials
- **Solution**: Set `FIREBASE_SERVICE_ACCOUNT` in Vercel environment variables

### Notifications Not Delivered
- **Cause**: Invalid FCM tokens or expired subscriptions
- **Solution**: Check browser console for service worker registration
- Users may need to re-subscribe if tokens expired

### "Database connection failed"
- **Cause**: No valid database URL configured
- **Solution**: Verify `OLD_DATABASE_URL` or `DATABASE_URL` is set correctly

## Best Practices

### 1. Notification Content
- Keep titles under 50 characters for better display
- Be specific and actionable in message body
- Always include a relevant URL for context
- Test on multiple devices before mass sending

### 2. Audience Targeting
- Segment subscribers by device type or subscription date
- Don't send duplicate notifications to same users
- Respect unsubscribe requests by setting `active=false`

### 3. Timing
- Avoid late-night notifications (check subscriber timezones)
- Send during peak engagement hours (9 AM - 5 PM)
- Limit frequency to prevent notification fatigue

### 4. Privacy
- Never share subscriber tokens publicly
- Regularly clean up inactive/expired tokens
- Allow users to manage notification preferences

## Advanced Features (Coming Soon)

- 📊 Notification analytics (open rates, click rates)
- ⏰ Schedule notifications for future delivery
- 🎯 Subscriber segmentation by preferences
- 📁 Template library for common messages
- 🔔 A/B testing for notification copy
- 🌐 Multi-language support

## Support

For issues or questions:
1. Check Vercel deployment logs: `vercel logs`
2. Inspect browser console in admin panel
3. Review API endpoint responses in Network tab
4. Check database connection with `/api/health`

## Changelog

### Version 1.0 (Jan 2026)
- ✅ Individual subscriber selection with checkboxes
- ✅ Custom title, message, and URL fields
- ✅ Real-time selection counter
- ✅ Beautiful gradient UI design
- ✅ Multi-database fallback support
- ✅ Firebase Cloud Messaging integration
- ✅ Batch sending (up to 500 subscribers)
- ✅ Success/error status messages
