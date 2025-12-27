# Google Analytics 4 Setup Guide

## What You Need
1. Google Analytics account
2. Your GA4 Measurement ID (format: `G-XXXXXXXXXX`)

---

## Step 1: Create GA4 Property

1. Go to [Google Analytics](https://analytics.google.com/)
2. Click **Admin** (bottom left)
3. Click **Create Property**
4. Enter property name: `WaveSignals`
5. Select timezone and currency
6. Click **Next**
7. Select  "Content" as business category
8. Click **Create**
9. Accept Terms of Service

## Step 2: Set Up Data Stream

1. Click **Web** under "Choose a platform"
2. Enter website URL: `https://wavesignals.waveseed.app`
3. Enter stream name: `WaveSignals Blog`
4. Click **Create stream**
5. **COPY YOUR MEASUREMENT ID** (looks like `G-XXXXXXXXXX`)

---

## Step 3: Add Tracking Code to Website

The tracking code is ALREADY integrated in your frontend files with a placeholder.

**To activate:**
1. Open each of these files:
   - `app/index.html`
   - `app/blog.html`
   - `app/post.html`
   - `about.html`
   - `contact.html`

2. Find the comment: `<!-- Google Analytics 4 Tracking -->`

3. Replace `G-XXXXXXXXXX` with your actual Measurement ID

4. Commit and deploy changes

---

## Step 4: Verify Data Collection

After deploying:

1. Visit your live site
2. Return to Google Analytics
3. Go to **Reports** → **Realtime**
4. You should see yourself as an active user within 30 seconds

---

## Step 5: (Optional) Advanced Features

### Enable Enhanced Measurement
- File downloads tracking
- Outbound clicks
- Site search
- Video engagement

**How:**
1. In GA4 → **Admin** → **Data Streams**
2. Click your stream
3. Toggle **Enhanced measurement** ON

### Set Up Conversions
Track newsletter signups:
1. Go to **Admin** → **Events**
2. Click **Create event**
3. Name: `newsletter_signup`
4. Match conditions when form submitted

---

## What You'll Get

With GA4 enabled you can track:
- ✅ Page views
- ✅ Session duration
- ✅ Traffic sources (Google, social, direct)
- ✅ Demographics (age, gender, location)
- ✅ Device types (mobile vs desktop)
- ✅ Most popular posts
- ✅ User retention
- ✅ Real-time visitors

All data appears in your admin panel's Analytics tab automatically.

---

## Privacy Compliance

GA4 is GDPR compliant by default. Configure:
1. Admin → Data Settings → Data Retention
2. Set to **2 months** for privacy-first approach
3. Enable **IP Anonymization** (on by default in GA4)

Done! Your analytics are now tracking.
