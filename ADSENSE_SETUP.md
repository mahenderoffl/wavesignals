# Google AdSense Integration Guide

## Overview
Your site has **8 strategic ad placements** ready to activate:
- Homepage: 3 spots
- Blog Archive: 2 spots  
- Single Posts: 4 spots
- Mobile-optimized: 2 spots

Currently **disabled** and invisible. Activate when ready.

---

## Step 1: Create Google AdSense Account

1. Go to [Google AdSense](https://www.google.com/adsense/)
2. Click **"Get Started"**
3. Enter your site URL: `https://wavesignals.waveseed.app`
4. Submit application
5. **Wait for approval** (usually 1-2 weeks)

### Approval Requirements:
✅ Original, quality content  
✅ Sufficient content volume (at least 20-30 posts)  
✅ Privacy policy page  
✅ Terms of service page  
✅ Contact information  
✅ Site is live and publicly accessible  

---

## Step 2: Get Your Publisher ID

After approval:
1. Login to AdSense dashboard
2. Go to **Account → Account Information**
3. Copy your **Publisher ID** (format: `ca-pub-XXXXXXXXXXXXXXXX`)

---

## Step 3: Create Ad Units

For each placement, create an ad unit:

1. In AdSense dashboard → **Ads → By ad unit**
2. Click **"Display ads"**
3. Create these 8 units:

| Ad Unit Name | Size | Type |
|--------------|------|------|
| WaveSignals Header Leaderboard | 728×90 | Responsive/Fixed |
| WaveSignals Sidebar Rectangle | 300×250 | Fixed |
| WaveSignals Footer Leaderboard | 728×90 | Responsive/Fixed |
| WaveSignals In-Feed | 300×250 | In-feed |
| WaveSignals In-Content | 336×280 | In-article |
| WaveSignals Sidebar Half Page | 300×600 | Fixed |
| WaveSignals End of Post | 300×250 | Fixed |
| WaveSignals Mobile Banner | 320×50 | Anchor/Fixed |

4. For each unit, **copy the Ad Slot ID** (format: `1234567890`)

---

## Step 4: Configure `data/ads.json`

Update the file with your IDs:

```json
{
  "enabled": true,
  "adsenseId": "ca-pub-XXXXXXXXXXXXXXXX",
  "placements": {
    "homepage": {
      "headerLeaderboard": {
        "enabled": true,
        "size": "728x90",
        "position": "top",
        "adSlot": "1234567890"
      },
      // ... add other ad slots
    }
  }
}
```

**Set `enabled: true`** to activate ads globally.

---

## Step 5: Add Ad Script to Pages

The ad script (`scripts/ads.js`) is already integrated. Just verify it's included:

```html
<script src="/scripts/ads.js"></script>
<script>
  adManager.init();
  // Render specific ads per page
</script>
```

---

## Ad Placements Map

### Homepage (`app/index.html`)
- **Top Header**: 728×90 leaderboard
- **Sidebar**: 300×250 rectangle
- **Footer**: 728×90 leaderboard

### Blog Archive (`app/blog.html`)
- **Top Header**: 728×90 leaderboard
- **In-Feed**: 300×250 every 3 posts

### Single Post (`app/post.html`)
- **Top Header**: 728×90 leaderboard
- **Mid-Article**: 336×280 large rectangle (after 2nd paragraph)
- **Sticky Sidebar**: 300×600 half page
- **End of Post**: 300×250 rectangle

### Mobile (Auto-detected)
- **Top Banner**: 320×50 mobile banner
- **In-Content**: 300×250 rectangle

---

## Admin Control Panel

**Settings → Monetization Tab** (to be added):
- Toggle ads on/off globally
- Enable/disable specific placements
- View estimated earnings
- Update AdSense ID

---

## Revenue Optimization Tips

1. **Most Valuable Positions:**
   - Above the fold (header)
   - In-content (mid-article)
   - Sticky sidebar

2. **Best Performing Sizes:**
   - 300×250 (highest fill rate)
   - 336×280 (highest CPM)
   - 728×90 (good visibility)

3. **Placement Rules:**
   - Max 3 ads above the fold
   - Don't overload (degrades UX)
   - Space ads 800px apart minimum

4. **Content Guidelines:**
   - More content = more ad inventory
   - Long-form posts (1500+ words) = 3-4 ads
   - Short posts (<500 words) = 1-2 ads

---

## Testing Before Going Live

1. **Set `enabled: false` in ads.json**
2. Add test ad code (AdSense provides test mode)
3. Verify ad positions look good
4. Check mobile responsiveness
5. Test page load speed (ads shouldn't slow site significantly)

---

## Compliance

### Required Pages (Already Created):
✅ `/privacy.html` - Privacy Policy  
✅ `/terms.html` - Terms of Service  
✅ `/contact.html` - Contact Form  

### Content Policies:
- No prohibited content (adult, violence, illegal)
- Original content (no plagiarism)
- No click manipulation ("Click here" near ads)
- No placement that misleads users

---

## Expected Revenue

**Realistic Estimates:**
- **1,000 page views/month** = $5-15
- **10,000 page views/month** = $50-150
- **100,000 page views/month** = $500-1500

**Factors:**
- Niche (Career/Tech = higher CPM)
- Traffic quality (US/UK traffic = higher)
- Ad placement optimization
- Content length

---

## Activation Checklist

When ready to monetize:

- [ ] Have 30+ published posts
- [ ] Averaging 1000+ visitors/month
- [ ] AdSense account approved
- [ ] Publisher ID obtained
- [ ] 8 ad units created in AdSense
- [ ] Ad slot IDs copied
- [ ] `ads.json` updated with IDs
- [ ] Set `enabled: true`
- [ ] Deploy to production
- [ ] Verify ads display correctly
- [ ] Check AdSense dashboard for impressions

---

**Status:** Pre-configured, currently disabled. Activate when traffic justifies monetization.
