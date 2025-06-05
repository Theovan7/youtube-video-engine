# Webhook Setup Guide for Local Development

## The Problem
When developing locally, external services like GoAPI cannot reach your localhost endpoints. This causes webhooks to fail.

## Solutions

### Option 1: Use ngrok (Recommended for Testing)
1. Install ngrok: `brew install ngrok`
2. Start your app: `python run.py`
3. In another terminal: `ngrok http 8080`
4. Copy the ngrok URL (e.g., https://abc123.ngrok.io)
5. Update your `.env` file:
   ```
   WEBHOOK_BASE_URL=https://abc123.ngrok.io
   ```
6. Restart your app

### Option 2: Manual Update Script
Use the provided `manual_update_video.py` script to manually update Airtable after video generation:
```bash
python manual_update_video.py
```

### Option 3: Deploy to a Staging Server
Deploy your app to a cloud service (Heroku, Railway, etc.) for testing with real webhooks.

## Current Video Generation Result
- **Segment ID**: recxGRBRi1Qe9sLDn
- **Generated Video URL**: https://storage.theapi.app/videos/280466557533844.mp4
- **Job ID**: recS3bE7bF2xZHW6D
- **Status**: Successfully uploaded to Airtable

## Testing the Generate Video Endpoint
```bash
curl -X POST "http://localhost:8080/api/v2/generate-video" \
  -H "Content-Type: application/json" \
  -d '{
    "segment_id": "recxGRBRi1Qe9sLDn"
  }'
```

## Important Notes
- Always ensure your webhook URL is accessible from the internet when using external services
- The application needs to be restarted after changing the WEBHOOK_BASE_URL in .env
- Check the logs for webhook reception: webhooks appear in the console output
