# 🚀 Deployment Checklist - Multi-Database Fallback

## Pre-Deployment

### ✅ 1. Gather Database Connection Strings

- [ ] **Old Database URL** (your existing blog database)
  ```
  postgresql://user:pass@host:5432/db_name
  ```
  
- [ ] **GROQ API Key** (from https://console.groq.com/keys)
  ```
  gsk_xxxxxxxxxxxxxxxxxxxxx
  ```

- [ ] **New Database URL** (optional backup)
  ```
  postgresql://user:pass@host2:5432/backup_db
  ```

### ✅ 2. Verify Database Access

Test OLD_DATABASE_URL connection:
```bash
psql $OLD_DATABASE_URL -c "SELECT COUNT(*) FROM posts;"
```

Expected: Should show count of your existing blog posts.

---

## Vercel Deployment

### ✅ 3. Set Environment Variables

**Via Vercel Dashboard:**
1. Go to: https://vercel.com/dashboard
2. Select your project → **Settings** → **Environment Variables**
3. Add these variables:

| Variable Name      | Value                          | Environments        |
|-------------------|--------------------------------|---------------------|
| OLD_DATABASE_URL  | Your old database URL          | All (Prod/Prev/Dev) |
| GROQ_API_KEY      | Your GROQ API key              | All (Prod/Prev/Dev) |
| NEW_DATABASE_URL  | Your backup database URL (opt) | All (Prod/Prev/Dev) |

**Via Vercel CLI:**
```bash
vercel env add OLD_DATABASE_URL production
# Paste your connection string when prompted

vercel env add GROQ_API_KEY production
# Paste your API key when prompted
```

### ✅ 4. Deploy Code

```bash
# Commit all changes
git add .
git commit -m "Implement multi-database fallback system"
git push origin main

# Deploy to Vercel
vercel --prod
```

### ✅ 5. Verify Deployment

**Check deployment status:**
```bash
vercel logs --prod
```

**Test API endpoints:**
```bash
# Test health endpoint
curl https://your-domain.vercel.app/api/health

# Should return:
# {
#   "status": "alive",
#   "database": {
#     "status": "connected",
#     "source": "old_db",  ← Verify this says "old_db"
#     "total_posts": 150
#   }
# }
```

**Test posts endpoint:**
```bash
curl https://your-domain.vercel.app/api/posts

# Check response headers for:
# X-Data-Source: old_db
```

---

## External Cron Setup

### ✅ 6. Configure Cron Job at cron-job.org

1. Go to: https://cron-job.org
2. Create account / Login
3. Click **Create Cron Job**
4. Configure:
   - **Title:** WaveSignals Daily Post
   - **URL:** `https://your-domain.vercel.app/api/cron`
   - **Schedule:** 
     - Type: **Every day**
     - At: **06:00** (6 AM UTC)
   - **Request Method:** GET
   - **Notifications:** Enable email on failure
5. Click **Create**
6. **Enable** the cron job

### ✅ 7. Test Cron Manually

Trigger a manual run:
```bash
curl https://your-domain.vercel.app/api/cron
```

Expected response:
```json
{
  "success": true,
  "id": 123,
  "title": "Your Generated Post Title",
  "timestamp": "2026-02-06T..."
}
```

---

## Post-Deployment Verification

### ✅ 8. Verify Old Blog Data

1. Visit your blog: `https://your-domain.vercel.app/blog`
2. **Check:** Do you see your old blog posts?
3. **Click** on an old post to verify content loads
4. **Inspect** response headers (F12 → Network):
   - Should show: `X-Data-Source: old_db`

### ✅ 9. Test Fallback System

**Temporarily disable OLD_DATABASE_URL:**
1. Vercel Dashboard → Environment Variables
2. **Rename** `OLD_DATABASE_URL` to `OLD_DATABASE_URL_DISABLED`
3. **Redeploy** (or wait for automatic deployment)
4. **Test:** `curl https://your-domain.vercel.app/api/health`
5. **Verify:** Response should show `"source": "new_db"` or `"json_fallback"`
6. **Re-enable:** Rename back to `OLD_DATABASE_URL`
7. **Redeploy** again

### ✅ 10. Monitor for 24 Hours

- [ ] Check if cron job runs successfully tomorrow at 6 AM UTC
- [ ] Verify new post appears on blog
- [ ] Check health endpoint shows recent post
- [ ] Monitor Vercel function logs for errors

---

## Troubleshooting

### ❌ "Database connection failed"

**Solution:**
1. Check if `OLD_DATABASE_URL` is set in Vercel
2. Verify connection string has no typos
3. Test connection: `psql $OLD_DATABASE_URL -c "\conninfo"`
4. Check if database requires IP whitelisting

### ❌ Old posts not showing

**Solution:**
1. Verify `OLD_DATABASE_URL` points to correct database
2. Run: `psql $OLD_DATABASE_URL -c "SELECT COUNT(*) FROM posts;"`
3. Check posts have `published = TRUE`
4. Review Vercel logs: `vercel logs --prod`

### ❌ Cron not generating posts

**Solution:**
1. Check if `GROQ_API_KEY` is set in Vercel
2. Test manually: `curl https://your-domain.vercel.app/api/cron`
3. Check external cron job is enabled at cron-job.org
4. Verify cron job URL is correct
5. Check rate limiting (20-hour minimum between posts)

### ❌ API returning 500 errors

**Solution:**
1. Check Vercel function logs: `vercel logs --prod`
2. Verify all required environment variables are set
3. Test database connections manually
4. Ensure `api/db_multi.py` is deployed

---

## Success Criteria ✅

Your deployment is successful when:

- [x] Health endpoint returns `"status": "alive"`
- [x] Health endpoint shows `"source": "old_db"`
- [x] All old blog posts are visible on `/blog`
- [x] Individual post pages load correctly
- [x] External cron job is enabled and scheduled
- [x] Manual cron trigger generates a new post
- [x] No errors in Vercel logs
- [x] Response headers include `X-Data-Source`

---

## Quick Links

- **Vercel Dashboard:** https://vercel.com/dashboard
- **Cron-Job.org:** https://cron-job.org
- **GROQ Console:** https://console.groq.com/keys
- **Full Setup Guide:** [MULTI_DATABASE_SETUP.md](./MULTI_DATABASE_SETUP.md)
- **Env Variables:** [ENV_VARIABLES.md](./ENV_VARIABLES.md)

---

## Rollback Plan

If issues occur:

1. **Revert code:**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Or restore single database:**
   - Remove `NEW_DATABASE_URL` from Vercel
   - Rename `OLD_DATABASE_URL` to `DATABASE_URL`
   - Use previous code version

3. **Emergency:** Set site to maintenance mode via custom 404 page

---

**Deployment Date:** _____________  
**Deployed By:** _____________  
**Verification Status:** ⬜ Pending / ✅ Verified / ❌ Failed  

---

Need help? Check logs:
```bash
vercel logs --prod --follow
```
