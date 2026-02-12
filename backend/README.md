---
title: WaveSignals Backend API
emoji: 🌊
colorFrom: blue
colorTo: green
sdk: docker  
app_port: 7860
---

# WaveSignals Backend API

Flask-based REST API backend for WaveSignals automated blog platform.

## Features

- ✅ **Automated Blog Generation** - AI-powered content creation with Gemini API
- ✅ **PostgreSQL Database** - Persistent storage for posts and subscribers
- ✅ **Daily Scheduler** - APScheduler cron job for automated posting
- ✅ **Push Notifications** - Firebase Cloud Messaging integration
- ✅ **RESTful API** - Clean endpoints for frontend integration

## API Endpoints

### Public Endpoints
- `GET /health` - Health check and system status
- `GET /api/posts` - List all published posts
- `GET /api/posts/:slug` - Get single post by slug
- `POST /api/subscribers` - Subscribe to email newsletter
- `POST /api/fcm/subscribe` - Subscribe to push notifications

### Admin Endpoints (Require X-Admin-Key header)
- `POST /api/generate-post` - Manually trigger post generation
- `POST /api/posts` - Create post
- `PUT /api/posts/:id` - Update post
- `DELETE /api/posts/:id` - Delete post
- `POST /api/notifications/send` - Send custom push notification

## Environment Variables

### Required
- `DATABASE_URL` - PostgreSQL connection string
- `GEMINI_API_KEY` - Google Gemini API key for content generation
- `ADMIN_PASSWORD` - Admin authentication password

### Optional
- `OPENAI_API_KEY` - OpenAI API key (fallback, not currently used)
- `PORT` - Server port (default: 7860)

## Scheduler

Automated post generation runs daily at **6:00 AM UTC (11:30 AM IST)** using APScheduler.

## Health Monitoring

**External Ping Recommended:**  
Setup a cron job at [cron-job.org](https://cron-job.org) to ping `/health` every 5 minutes to keep the Space awake.

## Frontend

This backend serves: [https://wavesignals.waveseed.app](https://wavesignals.waveseed.app)

## Deployment

This Space uses a custom Dockerfile for deployment. The entrypoint is `app.py`.

## Support

For issues or questions, check the [Hugging Face Space logs](https://huggingface.co/spaces/mahendercreates/wavesignals-backend/logs).
