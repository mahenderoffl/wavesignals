# Troubleshooting Guide - Multi-Database Fallback

## Quick Diagnostics

### Check Current Status

```bash
# Test health endpoint
curl https://your-domain.vercel.app/api/health | jq

# Expected output:
{
  "status": "alive",
  "database": {
    "status": "connected",
    "source": "old_db",  # ← Should be "old_db" for normal operation
    "total_posts": 150
  }
}
```

### Check Data Source

```bash
# Test posts endpoint
curl -I https://your-domain.vercel.app/api/posts | grep X-Data-Source

# Expected output:
X-Data-Source: old_db
```

---

## Common Issues & Solutions

### 1. ❌ "All database connections failed"

**Symptoms:**
- API returns `"source": "json_fallback"`
- Health endpoint shows `"status": "disconnected"`
- Posts show but data is stale

**Causes:**
- Environment variables not set in Vercel
- Database URLs are incorrect
- Database is rejecting connections
- Network/firewall issues

**Solutions:**

**A. Verify environment variables are set:**
```bash
# Check via Vercel CLI
vercel env ls

# Should see:
# OLD_DATABASE_URL (Production, Preview, Development)
# GROQ_API_KEY (Production, Preview, Development)
```

**B. Test database connection locally:**
```bash
# Test OLD_DATABASE_URL
psql $OLD_DATABASE_URL -c "SELECT 1;"

# If it works locally but not on Vercel:
# → Database may need IP whitelisting
```

**C. Check Vercel logs:**
```bash
vercel logs --prod | grep "Database connection"
```

**D. Verify connection string format:**
```
✅ Correct: postgresql://user:pass@host.com:5432/dbname
❌ Wrong:   postgres://user:pass@host.com:5432/dbname?sslmode=disable
```

---

### 2. 🔄 Old Blog Posts Not Showing

**Symptoms:**
- New posts appear but old posts are missing
- Post count is lower than expected
- Specific old posts return 404

**Causes:**
- OLD_DATABASE_URL not pointing to correct database
- Posts marked as `published = FALSE`
- Different database schema

**Solutions:**

**A. Verify OLD_DATABASE_URL points to correct database:**
```bash
# Check post count
psql $OLD_DATABASE_URL -c "SELECT COUNT(*) FROM posts;"

# List recent posts
psql $OLD_DATABASE_URL -c "SELECT id, title, published FROM posts ORDER BY created_at DESC LIMIT 5;"
```

**B. Check published status:**
```sql
-- See unpublished posts
SELECT COUNT(*) FROM posts WHERE published = FALSE;

-- If many unpublished, publish them:
UPDATE posts SET published = TRUE WHERE published = FALSE;
```

**C. Verify table schema matches:**
```bash
psql $OLD_DATABASE_URL -c "\d posts"

# Should have columns:
# - id, slug, title, excerpt, content, published
# - created_at, author, tags, meta_description, keywords
```

**D. Check which database is actually being used:**
```bash
curl https://your-domain.vercel.app/api/health | jq '.database.source'

# Should return: "old_db"
# If returns "new_db" or "json_fallback", OLD_DATABASE_URL is failing
```

---

### 3. 🤖 Automation Not Creating Posts

**Symptoms:**
- Cron job runs but no new posts appear
- `/api/cron` returns success but nothing published
- Manual trigger doesn't create posts

**Causes:**
- GROQ_API_KEY not set or invalid
- Rate limiting (< 20 hours since last post)
- Database write permissions issue
- API quota exceeded

**Solutions:**

**A. Test GROQ API key:**
```bash
# Manual test of GROQ API
curl -X POST https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 50
  }'

# Should return JSON with completion
```

**B. Check rate limiting:**
```bash
# See last post timestamp
curl https://your-domain.vercel.app/api/health | jq '.database.last_post'

# If less than 20 hours ago, post generation is skipped
```

**C. Test cron endpoint manually:**
```bash
curl -v https://your-domain.vercel.app/api/cron

# Should return:
# {"success": true, "id": 123, "title": "..."}
```

**D. Check Vercel function logs:**
```bash
vercel logs --prod | grep cron
```

**E. Verify database write permissions:**
```bash
psql $OLD_DATABASE_URL -c "INSERT INTO posts (slug, title, content, published) VALUES ('test-post', 'Test', 'Content', TRUE);"

# If INSERT fails, check database user permissions
```

---

### 4. 🔐 Environment Variables Not Working

**Symptoms:**
- Logs show "Environment variable not configured"
- Functions can't connect despite setting env vars
- Works locally but not on Vercel

**Causes:**
- Env vars set in wrong environment
- Recent deployment didn't pick up changes
- Typo in variable name

**Solutions:**

**A. Check environment scope:**
```bash
vercel env ls

# Ensure variables are set for:
# ✅ Production
# ✅ Preview
# ✅ Development
```

**B. Redeploy after changing env vars:**
```bash
# Environment variable changes require redeployment
vercel --prod --force
```

**C. Verify variable names (case-sensitive):**
```
✅ Correct: OLD_DATABASE_URL
❌ Wrong:   old_database_url
❌ Wrong:   OLD_DB_URL
```

**D. Check for hidden characters:**
```bash
# Test if value has trailing spaces/newlines
echo "$OLD_DATABASE_URL" | od -c
```

---

### 5. 🌐 API Returning 404 Errors

**Symptoms:**
- `/api/health` returns 404
- All API endpoints return page not found
- Static files work but API doesn't

**Causes:**
- Vercel deployment failed
- Python functions not building
- Missing dependencies
- Route configuration issue

**Solutions:**

**A. Check deployment status:**
```bash
vercel ls

# Look for latest deployment status
# Should show: Ready (✅)
```

**B. Check build logs:**
```bash
vercel logs --prod --since 1h
```

**C. Verify requirements.txt exists:**
```bash
cat api/requirements.txt

# Should contain:
# psycopg2-binary
# python-dotenv
# requests
# firebase-admin
```

**D. Check vercel.json routes:**
```json
{
  "routes": [
    {
      "src": "/api/health",
      "dest": "/api/health.py"
    }
  ]
}
```

**E. Redeploy from scratch:**
```bash
vercel --prod --force
```

---

### 6. 📊 Data Source Shows "json_fallback"

**Symptoms:**
- API works but shows `"source": "json_fallback"`
- Data is served from files instead of database
- Posts don't update

**Causes:**
- All database connections failing
- Network connectivity issues
- Database maintenance/downtime

**Solutions:**

**A. Test each database individually:**
```bash
# Test OLD_DATABASE_URL
psql $OLD_DATABASE_URL -c "SELECT 1;"

# Test NEW_DATABASE_URL
psql $NEW_DATABASE_URL -c "SELECT 1;"
```

**B. Check database status pages:**
- Vercel Postgres: https://vercel.com/dashboard → Storage
- Neon: https://console.neon.tech
- Supabase: https://app.supabase.com

**C. Temporary fix - update JSON:**
```bash
# Export latest data from database
psql $OLD_DATABASE_URL -c "COPY (SELECT row_to_json(t) FROM posts t WHERE published = TRUE) TO STDOUT" > posts.json
```

---

### 7. 🚨 Cron Job Failing at cron-job.org

**Symptoms:**
- Cron job shows "Execution failed"
- Email notifications about failures
- No new posts generated

**Causes:**
- Wrong URL configured
- Timeout (function takes too long)
- Rate limiting triggered
- Database or API issue

**Solutions:**

**A. Verify cron job URL:**
```
Correct: https://your-domain.vercel.app/api/cron
Wrong:   https://your-domain.vercel.app/cron
Wrong:   http://your-domain.vercel.app/api/cron (must be HTTPS)
```

**B. Check cron-job.org execution logs:**
1. Login to cron-job.org
2. Click on your job
3. View "History" tab
4. Check error messages

**C. Test endpoint responds within 30 seconds:**
```bash
time curl https://your-domain.vercel.app/api/cron
```

**D. Check if rate limiting is triggered:**
```bash
# See last post time
curl https://your-domain.vercel.app/api/health | jq '.database.last_post'
```

---

## Diagnostic Commands Cheat Sheet

```bash
# === Health Check ===
curl https://your-domain.vercel.app/api/health | jq

# === Data Source Check ===
curl -I https://your-domain.vercel.app/api/posts | grep X-Data-Source

# === Database Connection Test ===
psql $OLD_DATABASE_URL -c "SELECT COUNT(*) FROM posts;"

# === Vercel Logs ===
vercel logs --prod --follow

# === Environment Variables ===
vercel env ls

# === Deployment Status ===
vercel ls

# === Test Cron Manually ===
curl -v https://your-domain.vercel.app/api/cron

# === Test GROQ API ===
curl -X POST https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":"test"}]}'
```

---

## Emergency Procedures

### Situation: Complete Site Down

```bash
# 1. Check if it's Vercel-wide
curl https://vercel-status.com

# 2. Redeploy immediately
vercel --prod --force

# 3. If still down, enable maintenance mode
# (Edit 404.html to show maintenance message)
```

### Situation: Database Completely Inaccessible

```bash
# 1. Update posts.json with latest data
# (Manual export from database backup)

# 2. Site will automatically fall back to JSON

# 3. Disable cron job temporarily at cron-job.org

# 4. Fix database issues
# 5. Re-enable cron job
```

### Situation: Automated Posts Generating Errors

```bash
# 1. Disable cron job at cron-job.org

# 2. Check GROQ API status
curl https://status.groq.com

# 3. Test API key
# (Follow GROQ API test in cheat sheet above)

# 4. Check rate limits
# 5. Re-enable once resolved
```

---

## Getting Help

### Information to Collect

Before asking for help, gather:

```bash
# 1. Health status
curl https://your-domain.vercel.app/api/health > health.json

# 2. Vercel logs
vercel logs --prod --since 24h > vercel-logs.txt

# 3. Environment variables list (without values!)
vercel env ls > env-list.txt

# 4. Database connection test
psql $OLD_DATABASE_URL -c "\conninfo" > db-info.txt

# 5. Recent deployment info
vercel ls > deployments.txt
```

### Support Channels

- **Vercel Support:** https://vercel.com/support
- **GROQ Support:** https://console.groq.com/docs
- **GitHub Issues:** (your repository)

---

## Monitoring Setup

### Recommended Monitoring

1. **Uptime Monitor (UptimeRobot)**
   - URL: `https://your-domain.vercel.app/api/health`
   - Check interval: 5 minutes
   - Alert: Email/SMS if down

2. **Cron Job Monitor**
   - Enable email notifications at cron-job.org
   - Alert if execution fails

3. **Database Monitoring**
   - Set up alerts for your database provider
   - Monitor connection count and disk usage

---

**Last Updated:** February 6, 2026  
**Version:** 3.1-multi-db
