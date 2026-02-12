-- Migration: Add FCM push notification subscribers table
-- This table stores Firebase Cloud Messaging tokens for push notifications

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

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_fcm_active ON fcm_subscribers(active);
CREATE INDEX IF NOT EXISTS idx_fcm_created ON fcm_subscribers(created_at DESC);

-- Add comments
COMMENT ON TABLE fcm_subscribers IS 'Stores Firebase Cloud Messaging tokens for push notifications';
COMMENT ON COLUMN fcm_subscribers.token IS 'FCM device token';
COMMENT ON COLUMN fcm_subscribers.device_type IS 'Device type (Chrome, Firefox, Safari, etc.)';
COMMENT ON COLUMN fcm_subscribers.active IS 'Whether subscription is still active';
COMMENT ON COLUMN fcm_subscribers.last_used IS 'Last time notification was sent to this token';
COMMENT ON COLUMN fcm_subscribers.preferences IS 'User notification preferences (JSON)';
