# WaveSignals

Static blog platform powered by JSON with multi-database fallback support.

## Features
- 🎯 **Multi-Database Fallback** - High availability with automatic database failover
- 📊 **PostgreSQL Backend** - Primary database with backup support
- 🤖 **AI Content Generation** - Automated blog posts via GROQ API
- 📱 **Push Notifications** - Firebase Cloud Messaging
- 🔄 **Automated Publishing** - Daily content via external cron

## Structure
- `/api` → Vercel serverless functions (multi-DB support)
- `/admin` → Content management panel
- `/app` → Public blog pages
- `/data` → JSON fallback data
- `/backend` → Flask app (legacy/optional)
- `/scripts` → Utilities (sitemap generation)

## Multi-Database Architecture

Read operations use automatic fallback:
1. **OLD_DATABASE_URL** (your existing blogs)
2. **NEW_DATABASE_URL** (backup)
3. **data/posts.json** (local fallback)

Write operations always go to primary database only.

See [MULTI_DATABASE_SETUP.md](./MULTI_DATABASE_SETUP.md) for details.

## Setup

### Environment Variables
```env
OLD_DATABASE_URL=postgresql://...  # Required: Your existing database
GROQ_API_KEY=gsk_...              # Required: AI content generation
NEW_DATABASE_URL=postgresql://...  # Optional: Backup database
```

See [ENV_VARIABLES.md](./ENV_VARIABLES.md) for complete guide.

### Deployment
```bash
# Deploy to Vercel
vercel --prod

# Configure environment variables in Vercel Dashboard
# Settings → Environment Variables
```

### External Cron Job
Configure at [cron-job.org](https://cron-job.org):
- **URL:** `https://your-domain.vercel.app/api/cron`
- **Schedule:** Daily at 6:00 AM UTC
- **Method:** GET

## Local Development
```bash
# Install dependencies
npm install

# Serve locally
python -m http.server 8080
# or
npx serve .
```

## API Endpoints
- `GET /api/health` - Health check + database status
- `GET /api/posts` - All published posts (with fallback)
- `GET /api/post?slug=X` - Single post by slug
- `GET /api/cron` - Trigger post generation
- `POST /api/subscribers` - Email subscription

## Documentation
- [Multi-Database Setup Guide](./MULTI_DATABASE_SETUP.md)
- [Environment Variables Reference](./ENV_VARIABLES.md)
- [Backend README](./backend/README.md)

## Tech Stack
- **Frontend:** Vanilla JS, Static HTML/CSS
- **Backend:** Vercel Serverless Functions (Python)
- **Database:** PostgreSQL (multi-DB fallback)
- **AI:** GROQ API (Llama 3.3)
- **Hosting:** Vercel
- **Notifications:** Firebase Cloud Messaging

---

**Version:** 3.1-multi-db  
**Status:** ✅ Production Ready with High Availability
