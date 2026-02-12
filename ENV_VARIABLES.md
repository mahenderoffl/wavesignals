# Environment Variables - Quick Reference

## Required for Vercel Deployment

Add these in **Vercel Dashboard → Project Settings → Environment Variables**:

### 1. OLD_DATABASE_URL (PRIMARY - REQUIRED)
```
postgresql://user:password@host.region.postgres.vercel-storage.com:5432/database
```
**Purpose:** Your existing database with all blog posts  
**Used for:** Read operations (priority #1) + Write operations

---

### 2. GROQ_API_KEY (REQUIRED)
```
gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
**Purpose:** AI content generation for automated posts  
**Get it from:** https://console.groq.com/keys

---

### 3. NEW_DATABASE_URL (OPTIONAL)
```
postgresql://user:password@host2.region.postgres.vercel-storage.com:5432/backup_db
```
**Purpose:** Backup database (fallback if OLD_DATABASE_URL fails)  
**Used for:** Read operations only (priority #2)

---

### 4. DATABASE_URL (OPTIONAL)
```
postgresql://user:password@host3.region.postgres.vercel-storage.com:5432/tertiary_db
```
**Purpose:** Tertiary fallback  
**Used for:** Read operations only (priority #3)

---

## Vercel Setup Commands

### Via Vercel CLI:
```bash
# Set OLD_DATABASE_URL (paste your connection string when prompted)
vercel env add OLD_DATABASE_URL production

# Set GROQ_API_KEY
vercel env add GROQ_API_KEY production

# Optional: Set NEW_DATABASE_URL
vercel env add NEW_DATABASE_URL production
```

### Via Vercel Dashboard:
1. Go to: https://vercel.com/dashboard
2. Select your project
3. Navigate to: **Settings → Environment Variables**
4. Click **Add New**
5. Enter:
   - **Name:** `OLD_DATABASE_URL`
   - **Value:** Your database connection string
   - **Environment:** Select all (Production, Preview, Development)
6. Click **Save**
7. Repeat for `GROQ_API_KEY`

---

## How to Get Your Database Connection String

### If using Vercel Postgres:
1. Go to: https://vercel.com/dashboard
2. Select **Storage** tab
3. Click your Postgres database
4. Copy the connection string from **Connection String** section
5. Format: `postgresql://user:password@host:5432/database`

### If using external provider (Neon, Supabase, etc):
1. Login to your database provider dashboard
2. Find connection details or connection string
3. Copy the full PostgreSQL connection URL

---

## Database Priority Order

```
┌─────────────────────────────────────┐
│  READ Operations (GET requests)    │
├─────────────────────────────────────┤
│  1. OLD_DATABASE_URL (Primary)      │
│  2. NEW_DATABASE_URL (Backup)       │
│  3. DATABASE_URL (Tertiary)         │
│  4. data/posts.json (File fallback) │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  WRITE Operations (POST/PUT/DELETE) │
├─────────────────────────────────────┤
│  → OLD_DATABASE_URL only            │
│    (Primary database for writes)    │
└─────────────────────────────────────┘
```

---

## Minimum Required Configuration

To get your site working, you **MUST** set:

1. ✅ **OLD_DATABASE_URL** - Your existing database
2. ✅ **GROQ_API_KEY** - For AI content generation

**NEW_DATABASE_URL** and **DATABASE_URL** are optional backups.

---

## After Setting Environment Variables

1. **Redeploy your site:**
   ```bash
   vercel --prod
   ```

2. **Test the setup:**
   ```bash
   curl https://your-domain.vercel.app/api/health
   ```

3. **Check which database is connected:**
   Look for `"source": "old_db"` in the response

---

## Troubleshooting

### "Database connection failed"
- Verify connection string is correct (no typos)
- Check database accepts connections from Vercel IPs
- Ensure database is online and accessible

### "All database connections failed"
- At least `OLD_DATABASE_URL` must be set
- Test connection locally: `psql $OLD_DATABASE_URL`
- Check if database requires IP whitelisting

### Old blogs not showing
- Confirm `OLD_DATABASE_URL` points to database with your existing posts
- Run query: `SELECT COUNT(*) FROM posts;`
- Verify environment variable is set in **Production** environment

---

**Need Help?**  
See full documentation: [MULTI_DATABASE_SETUP.md](./MULTI_DATABASE_SETUP.md)
