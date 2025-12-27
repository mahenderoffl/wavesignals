# Google Search Console Integration Guide

## Quick Setup (5 minutes)

### Step 1: Add Your Site to Google Search Console

1. Go to [Google Search Console](https://search.google.com/search-console/)
2. Click **"Add Property"**
3. Choose **"URL prefix"**
4. Enter: `https://wavesignals.waveseed.app`
5. Click **Continue**

---

### Step 2: Verify Ownership

**Method 1: HTML File Upload** (Easiest)

1. Google will provide a verification file (e.g., `google1234abcd.html`)
2. Download the file
3. Upload it to your site's root directory
4. Access it at: `https://wavesignals.waveseed.app/google1234abcd.html`
5. Click **Verify** in Search Console

**Method 2: HTML Tag** (Alternative)

1. Google provides a meta tag
2. Add it to the `<head>` section of `app/index.html`:
   ```html
   <meta name="google-site-verification" content="YOUR_CODE_HERE" />
   ```
3. Deploy changes
4. Click **Verify**

---

### Step 3: Submit Sitemaps

After verification:

1. In Search Console, go to **Sitemaps** (left sidebar)
2. Click **"Add a new sitemap"**
3. Submit these URLs:
   - `sitemap.xml`
   - `sitemap-pages.xml`
   - `sitemap-posts.xml`
4. Click **Submit**

Google will start indexing within 24-48 hours.

---

### Step 4: Generate Dynamic Post Sitemap

Before deploying, generate the posts sitemap:

```bash
node generate-sitemap.js
```

This creates `sitemap-posts.xml` with all your published posts.

**Automate:** Run this script whenever you publish new posts, or set up a GitHub Action to regenerate on deployment.

---

## What You Get

Once indexed, Google Search Console provides:

✅ **Performance Reports**
- Total clicks from Google
- Impressions (how often your site appears)
- Average position in search results
- Click-through rate (CTR)

✅ **Coverage Report**
- Which pages are indexed
- Indexing errors (if any)
- Pages excluded from search

✅ **URL Inspection**
- Check how Google sees individual pages
- Request re-indexing after updates

✅ **Search Queries**
- What keywords bring traffic
- Which posts rank for what terms

---

## SEO Best Practices (Already Implemented)

✅ `robots.txt` - Allows all search engines, blocks admin  
✅ `sitemap.xml` - Main sitemap index  
✅ `sitemap-pages.xml` - Static pages  
✅ `sitemap-posts.xml` - Dynamic blog posts  
✅ Clean URLs with slugs  
✅ Meta descriptions on all pages  
✅ Mobile-responsive design  

---

## Optional Enhancements

### 1. Rich Results (Structured Data)

Add JSON-LD to post pages for better search appearance:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Post Title",
  "datePublished": "2025-12-26",
  "author": {
    "@type": "Organization",
    "name": "WaveSignals"
  }
}
</script>
```

### 2. Open Graph Tags

Already good for social sharing, also helps SEO:
```html
<meta property="og:title" content="WaveSignals" />
<meta property="og:description" content="Minimal editorial blog" />
<meta property="og:url" content="https://wavesignals.waveseed.app" />
```

### 3. Canonical URLs

Add to prevent duplicate content:
```html
<link rel="canonical" href="https://wavesignals.waveseed.app/app/post.html?slug=your-post" />
```

---

## Monitoring

After 7-14 days, check:

1. **Search Console → Coverage**
   - Target: 100% of pages indexed
   
2. **Search Console → Performance**
   - Track clicks and impressions growth
   
3. **Google Analytics**
   - Compare organic search traffic

---

## Common Issues

**"Page not indexed"**
- Wait 48 hours after sitemap submission
- Use URL Inspection tool → Request Indexing

**"Crawl Error"**
- Check robots.txt isn't blocking
- Verify all links work (no 404s)

**"Duplicate content"**
- Add canonical tags
- Ensure single URL per post

---

## Files Created

- ✅ `sitemap.xml` - Main index
- ✅ `sitemap-pages.xml` - Static pages
- ✅ `generate-sitemap.js` - Post sitemap generator
- ✅ `robots.txt` - Crawler directives

**Next:** Deploy to production, then verify in Search Console.
