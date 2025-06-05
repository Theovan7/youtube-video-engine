# YouTube Video Engine - Production Testing Guide

## Production URL
https://youtube-video-engine.fly.dev/

## Deployment Info
- **Deployment Date**: May 29, 2025
- **Version**: 1.0.0
- **Region**: IAD (US East)
- **Status**: ✅ Healthy

## All Services Connected
- ✅ Airtable
- ✅ ElevenLabs
- ✅ GoAPI
- ✅ NCA Toolkit

## Testing Production Endpoints

### 1. Health Check
```bash
curl https://youtube-video-engine.fly.dev/health
```

### 2. API Documentation
Visit: https://youtube-video-engine.fly.dev/api/docs

### 3. Generate Video (from existing segment)
```bash
curl -X POST "https://youtube-video-engine.fly.dev/api/v2/generate-video" \
  -H "Content-Type: application/json" \
  -d '{
    "segment_id": "recxGRBRi1Qe9sLDn"
  }'
```

### 4. Process Complete Script
```bash
curl -X POST "https://youtube-video-engine.fly.dev/api/v2/process-script" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "Your video script here"
  }'
```

## Important Notes

1. **Webhooks**: Production webhooks will now work correctly as the app is publicly accessible at https://youtube-video-engine.fly.dev

2. **Monitoring**: 
   - Live logs: `fly logs -a youtube-video-engine`
   - App status: `fly status -a youtube-video-engine`
   - Monitoring dashboard: https://fly.io/apps/youtube-video-engine/monitoring

3. **Scaling**: The app is currently running on 1 machine. To scale:
   ```bash
   fly scale count 2 -a youtube-video-engine  # Scale to 2 machines
   ```

4. **Environment Variables**: All secrets are securely stored in Fly.io. To update:
   ```bash
   fly secrets set KEY=value -a youtube-video-engine
   ```

## Production Checklist
- [x] App deployed successfully
- [x] All services connected
- [x] Health endpoint working
- [x] Webhook URL accessible from external services
- [ ] Test video generation with real Airtable data
- [ ] Monitor logs for any errors
- [ ] Set up external monitoring (optional)

## Troubleshooting

If you encounter any issues:

1. Check logs:
   ```bash
   fly logs -a youtube-video-engine
   ```

2. SSH into the machine:
   ```bash
   fly ssh console -a youtube-video-engine
   ```

3. Restart the app:
   ```bash
   fly apps restart youtube-video-engine
   ```

4. Roll back to previous version:
   ```bash
   fly releases -a youtube-video-engine
   fly deploy --image <previous-image-id> -a youtube-video-engine
   ```
