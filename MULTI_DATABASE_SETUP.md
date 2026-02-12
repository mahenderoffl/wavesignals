# Multi-Database Fallback Setup

## Overview

Your WaveSignals project now supports **multi-database fallback** for high availability:

- **OLD_DATABASE_URL** → Primary database (your existing blogs)
- **NEW_DATABASE_URL** → Secondary/backup database
- **DATABASE_URL** → Tertiary fallback
- **Local JSON** → Final fallback if all databases fail

## How It Works

### Read Operations (GET requests)
Automatically tries databases in order:
1. **OLD_DATABASE_URL** (primary - your existing blog content)
2. **NEW_DATABASE_URL** (backup)
3. **DATABASE_URL** (fallback)
4. **data/posts.json** (local file fallback)

### Write Operations (POST/PUT/DELETE)
Always writes to **PRIMARY database only** (OLD_DATABASE_URL) to avoid data inconsistency.

## Environment Variables Setup

### Vercel Configuration

Go to your Vercel project dashboard:
1. Navigate to **Settings → Environment Variables**
2. Add the following variables:

```env
# PRIMARY DATABASE (your existing blog database)
OLD_DATABASE_URL=postgresql://user:password@host:5432/database_name

# SECONDARY DATABASE (optional - backup)
NEW_DATABASE_URL=postgresql://user:password@host:5432/backup_db

# GROQ API KEY (required for AI content generation)
GROQ_API_KEY=your_groq_api_key_here
```

### Local Development (.env file)

Create a `.env` file in the root directory:

```env
OLD_DATABASE_URL=postgresql://user:password@localhost:5432/wavesignals_old
NEW_DATABASE_URL=postgresql://user:password@localhost:5432/wavesignals_new
GROQ_API_KEY=your_groq_api_key_here
```

## Files Modified

### API Endpoints (Vercel Functions)

1. **`/api/db_multi.py`** (NEW)
   - Multi-database connection manager
   - Fallback logic for reads
   - Primary connection for writes
   - JSON fallback handler

2. **`/api/posts.py`**
   - Returns all posts with database fallback
   - Adds `X-Data-Source` header showing which database was used
   - Returns `source` field in JSON response

3. **`/api/post.py`**
   - Returns single post by slug with fallback
   - Gracefully degrades to JSON if databases fail

4. **`/api/health.py`**
   - Shows which database is currently active
   - Displays data source in response
   - Tests multi-database connectivity

5. **`/api/cron.py`**
   - Writes new posts to PRIMARY database only
   - Uses `get_primary_db_connection()` for writes

### Backend Files (Flask App)

6. **`/backend/db.py`**
   - Added `get_db_connection()` with multi-database support
   - Added `get_primary_db_connection()` for write operations
   - Retry logic for each database

## Testing the Setup

### 1. Test Health Endpoint

```bash
curl https://your-domain.vercel.app/api/health
```

Response should show:
```json
{
  "status": "alive",
  "database": {
    "status": "connected",
    "source": "old_db",  // ← Which database is being used
    "total_posts": 150
  }
}
```

### 2. Test Posts Endpoint

```bash
curl https://your-domain.vercel.app/api/posts
```

Check the `X-Data-Source` header or `source` field to see which database served the data.

### 3. Test Fallback

To test fallback behavior:
1. Temporarily remove `OLD_DATABASE_URL` from Vercel
2. Request should automatically use `NEW_DATABASE_URL`
3. Remove both → should fall back to JSON

## Deployment Steps

### Step 1: Update Environment Variables in Vercel

```bash
# Via Vercel CLI (if installed)
vercel env add OLD_DATABASE_URL
# Paste your old database connection string

vercel env add NEW_DATABASE_URL
# Paste your new database connection string (optional)

vercel env add GROQ_API_KEY
# Paste your GROQ API key
```

Or use the Vercel Dashboard:
- Go to **Project Settings → Environment Variables**
- Add each variable for **Production, Preview, Development**

### Step 2: Deploy to Vercel

```bash
# Commit changes
git add .
git commit -m "Implement multi-database fallback system"
git push origin main

# Or deploy directly
vercel --prod
```

### Step 3: Verify Deployment

1. Check deployment logs in Vercel dashboard
2. Test `/api/health` endpoint
3. Test `/api/posts` endpoint
4. Verify data source in response

## Monitoring Data Sources

Every API response now includes information about which database served the data:

### HTTP Headers
```
X-Data-Source: old_db
```

### JSON Response
```json
{
  "posts": [...],
  "source": "old_db",
  "count": 150
}
```

Possible values:
- `old_db` - Primary database (your existing blogs)
- `new_db` - Secondary database
- `fallback_db` - Tertiary database (DATABASE_URL)
- `json_fallback` - Local JSON file

## Troubleshooting

### All Databases Failing

**Symptoms:** Responses show `source: "json_fallback"`

**Solutions:**
1. Check if database URLs are correctly configured in Vercel
2. Verify database is accepting connections from Vercel IPs
3. Check database credentials are valid
4. Review Vercel function logs for connection errors

### Writes Not Working

**Symptoms:** Automation cron job fails, manual post creation fails

**Solutions:**
1. Verify `OLD_DATABASE_URL` is set and accessible
2. Check database has write permissions
3. Ensure database tables exist (run `/api/init-db` once)

### Old Blog Data Not Showing

**Symptoms:** Only seeing new posts, missing old content

**Solutions:**
1. Confirm `OLD_DATABASE_URL` points to your database with existing blogs
2. Test connection: `psql $OLD_DATABASE_URL -c "SELECT COUNT(*) FROM posts;"`
3. Check Vercel logs to see which database is connecting

## External Cron Job Configuration

Your cron job at cron-job.org should call:
```
URL: https://your-domain.vercel.app/api/cron
Method: GET
Schedule: 0 6 * * * (Daily at 6:00 AM UTC)
```

## Benefits of This Setup

✅ **High Availability** - Site stays up even if one database fails  
✅ **Data Preservation** - Old blog content always accessible  
✅ **Graceful Degradation** - Falls back to JSON if all databases down  
✅ **Flexibility** - Easy to switch between databases  
✅ **No Data Loss** - Writes only to primary, ensuring consistency  
✅ **Transparent Monitoring** - Know which database is serving data  

## Migration Notes

If you want to migrate data from old database to new database:

```sql
-- On new database, copy data from old
pg_dump OLD_DATABASE_URL | psql NEW_DATABASE_URL
```

Or use a migration script (contact for custom migration code).

## Support

For issues:
1. Check Vercel function logs: `vercel logs`
2. Check database connectivity: Test with `psql` or GUI client
3. Verify environment variables are set in all environments (Production, Preview, Development)

---

**Version:** 3.1-multi-db  
**Last Updated:** February 6, 2026  
**Status:** ✅ Production Ready
