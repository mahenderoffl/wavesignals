# WaveSignals Backend - Deployment Options

This backend can be deployed in two modes:

## Mode 1: Flask API Only (Current)
- Runs the REST API for admin panel
- APScheduler handles automated posting
- Good for: Production deployment with external monitoring

**Run command:**
```bash
gunicorn -b 0.0.0.0:7860 app:app
```

## Mode 2: Gradio Dashboard (Recommended for Testing)
- **Monitoring UI** with real-time health checks
- Manual blog generation button
- Activity logs
- Frontend sync verification

**Run command:**
```bash
python dashboard.py
```

## Recommended Deployment Strategy

### On Hugging Face Space (Production):
Use **Mode 2 (Gradio Dashboard)** 
- Provides visual monitoring
- Easy manual testing
- Keep-alive functionality
- Flask API still accessible on port 7861 (optional)

### Alternative Dockerfile
For dual-mode (both Flask API + Gradio):
```dockerfile
# ... existing setup ...

# Expose both ports
EXPOSE 7860 7861

# Start both services
CMD ["sh", "-c", "python dashboard.py & gunicorn -b 0.0.0.0:7861 app:app"]
```

## Current Dockerfile Uses:
- **Gradio Dashboard** on port 7860 (primary)
- Provides full monitoring and manual control
