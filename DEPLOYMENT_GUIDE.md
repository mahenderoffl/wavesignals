# WaveSignals - COMPLETE Deployment & Troubleshooting Guide

> **CRITICAL FIXES IMPLEMENTED - DEPLOY NOW**

---

## 🚨 CRITICAL FIX: Dockerfile Changed

**Problem:** Dashboard.py doesn't include Flask API → Admin panel can't connect

**Solution:** Reverted to Flask API (Gunicorn)

```dockerfile
# NOW RUNS (CORRECT):
CMD ["gunicorn", "-b", "0.0.0.0:7860", "--timeout", "120", "--workers", "2", "app:app"]

# DON'T USE (BROKEN):
# CMD ["python", "dashboard.py"]
```

---

## 🔧 Step-by-Step Deployment

### 1. Push ALL Code to Hugging Face Space

```bash
cd c:\WaveSignals\backend
git add .
git commit -m "Critical fix: Flask API + health endpoint + GitHub Actions"
git push origin main
```

**Wait 3-5 minutes for rebuild**

---

### 2. Configure Secrets in HF Space

Go to: https://huggingface.co/spaces/mahendercreates/wavesignals-backend/settings

**Add these secrets:**

| Name | Value | Notes |
|------|-------|-------|
| `DATABASE_URL` | `postgresql://...` | Your Neon/Supabase connection string |
| `GEMINI_API_KEY` | `AIza...` | Google Gemini API key |
| `ADMIN_PASSWORD` | `wavesignals@2025` | For admin panel authentication |

---

### 3. Test Backend Health

```bash
curl https://mahendercreates-wavesignals-backend.hf.space/health
```

**Expected Response:**
```json
{
  "status": "alive",
  "message": "WaveSignals Backend is running",
  "database": {
    "status": "connected",
    "total_posts": 10,
    "posts_24h": 2
  },
  "scheduler": {
    "status": "running",
    "interval": "Every 12 hours"
  },
  "apis": {
    "gemini_configured": true
  }
}
```

**If you get 404:** Space is still building. Wait 2 more minutes.

**If you get 500:** Check HF Space logs → Settings → Logs

---

### 4. Setup Cron-Job.org (Keep Alive)

1. **Register:** https://cron-job.org/en/signup

2. **Create Job:**
   - **Title:** `WaveSignals Keep Alive`
   - **URL:** `https://mahendercreates-wavesignals-backend.hf.space/health`
   - **Schedule:** Every 5 minutes (`*/5 * * * *`)
   - **Enabled:** ✅ Yes

3. **Test:** Click "Execute now" → Should show green ✅

---

### 5. Setup GitHub Actions (Backup Automation)

**Already created:** `.github/workflows/auto-post.yml`

**Setup Secrets in GitHub:**

1. Go to your GitHub repo → Settings → Secrets and variables → Actions
2. Add secret:
   - **Name:** `ADMIN_PASSWORD`
   - **Value:** `wavesignals@2025`

3. **Test manually:**
   - Actions tab → "Auto Post Blog & Monitor"
   - Click "Run workflow"
   - Watch it execute

**Runs automatically:** 6 AM & 6 PM UTC (11:30 AM & 11:30 PM IST)

---

### 6. Deploy Frontend to Netlify

```bash
cd c:\WaveSignals
git add .
git commit -m "Fixed Google Sheets URL + admin enhancements"
git push origin main
```

Netlify auto-deploys in 1-2 minutes.

---

## 🐛 Troubleshooting Common Issues

### ❌ "Generation Error" in Admin Panel

**Cause:** GEMINI_API_KEY not set or invalid

**Fix:**
1. Check HF Space secrets → Verify `GEMINI_API_KEY` exists
2. Test API key: https://ai.google.dev/gemini-api/docs/quickstart
3. Restart HF Space: Settings → Factory Reboot

---

### ❌ "Subscribe Button Not Working"

**Cause:** Google Sheets URL 404 or CORS issue

**Fix:**
1. **Verify Google Apps Script is deployed:**
   - Open your Google Sheet
   - Extensions → Apps Script
   - Click "Deploy" → "New deployment"
   - Type: "Web app"
   - Access: "Anyone"
   - Copy the URL (ends with `/exec`)

2. **Update in `subscribe.js`:**
   ```javascript
   const GOOGLE_SCRIPT_URL = "YOUR_NEW_URL_HERE";
   ```

3. **Test in browser console:**
   ```javascript
   fetch("YOUR_GOOGLE_SCRIPT_URL", {
     method: "POST",
     mode: "no-cors",
     body: JSON.stringify({email: "test@example.com"})
   })
   ```

---

### ❌ "/health Not Found" (404)

**Cause:** Old Dockerfile still running (dashboard.py instead of app.py)

**Fix:**
1. Verify Dockerfile has:
   ```dockerfile
   CMD ["gunicorn", "-b", "0.0.0.0:7860", "--timeout", "120", "--workers", "2", "app:app"]
   ```

2. Push to HF Space:
   ```bash
   git add backend/Dockerfile
   git commit -m "Fix: Run Flask API not dashboard"
   git push
   ```

3. **Force rebuild:** HF Space → Settings → Factory Reboot

---

### ❌ "Pending Sync" in Admin Panel

**Cause:** Admin panel can't reach HF Space API

**Possible Reasons:**
1. **HF Space is sleeping** → Setup cron-job.org (see Step 4)
2. **API URL wrong** → Should be `https://mahendercreates-wavesignals-backend.hf.space/api`
3. **CORS issue** → Flask-CORS should handle this (already installed)

**Debug:**
1. Open browser console (F12)
2. Go to admin panel → Settings tab
3. Look for red errors

**Common fixes:**
- Clear browser cache (Ctrl+F5)
- Check HF Space is awake: `curl https://mahendercreates-wavesignals-backend.hf.space/health`
- Verify CORS is enabled in `app.py`: `CORS(app)` on line 12

---

### ❌ GitHub Actions Failing

**Cause:** Missing `ADMIN_PASSWORD` secret

**Fix:**
1. GitHub repo → Settings → Secrets and variables → Actions
2. Add: `ADMIN_PASSWORD` = `wavesignals@2025`
3. Re-run workflow

---

## ✅ Verification Checklist

After deployment, verify these:

- [ ] **Backend Health:**
  ```bash
  curl https://mahendercreates-wavesignals-backend.hf.space/health
  # Status: 200, database: connected
  ```

- [ ] **Manual Post Generation:**
  ```bash
  curl -X POST https://mahendercreates-wavesignals-backend.hf.space/api/generate-post \
    -H "X-Admin-Key: wavesignals@2025"
  # Should return: {"success": true, "id": 123, "title": "..."}
  ```

- [ ] **Admin Panel Loads:**
  - Visit: https://wavesignals.netlify.app/admin
  - Login with: `wavesignals@2025`
  - No "Pending sync" errors

- [ ] **Subscribe Works:**
  - Go to homepage
  - Enter test email
  - Check Google Sheets for new row

- [ ] **Cron Job Running:**
  - cron-job.org dashboard shows green checkmarks every 5 min

- [ ] **GitHub Actions:**
  - Actions tab shows green checkmark
  - Runs at 6 AM & 6 PM UTC

---

## 📊 Expected Behavior After Setup

### Automated Posts:
- **APScheduler:** Every 12 hours (HF Space internal)
- **GitHub Actions:** 6 AM & 6 PM UTC (backup)
- **Result:** ~2 posts per day automatically

### System Health:
- **Uptime:** 99%+ (cron keeps HF Space awake)
- **Database:** Always connected (retry logic)
- **Admin Panel:** Fast sync (no delays)

---

## 🎯 Final Deployment Command Sequence

Copy-paste these commands in order:

```bash
# 1. Backend
cd c:\WaveSignals\backend
git add .
git commit -m "Production ready: Flask API + health + workflows"
git push origin main

# 2. Frontend
cd c:\WaveSignals
git add .
git commit -m "Fixed Google Sheets + admin enhancements"
git push origin main

# 3. Wait for builds (3-5 min)
# Then test health:
curl https://mahendercreates-wavesignals-backend.hf.space/health

# 4. Test post generation:
curl -X POST https://mahendercreates-wavesignals-backend.hf.space/api/generate-post \
  -H "X-Admin-Key: wavesignals@2025"
```

---

## 🆘 If Still Broken

1. **Check HF Space Logs:**
   - Space → Settings → Logs
   - Look for Python errors
   - Common: `DATABASE_URL not set` or `GEMINI_API_KEY invalid`

2. **Restart Everything:**
   ```bash
   # HF Space
   Settings → Factory Reboot (wait 5 min)
   
   # Netlify
   Site settings → Deploys → Trigger deploy
   ```

3. **Test Individual Components:**
   - Database: `python backend/db.py`
   - Bot: `python backend/bot.py`
   - API: `gunicorn app:app` (locally)

---

## 🚀 You're Ready!

Once all checkboxes above are ✅, your system is:
- ✅ Automated (2 posts/day)
- ✅ Monitored (GitHub Actions)
- ✅ Reliable (99% uptime)
- ✅ Synced (admin panel works)

**Total setup time:** 20-30 minutes

**Any issues?** Check logs first → They'll tell you exactly what's wrong.
