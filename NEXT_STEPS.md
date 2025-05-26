# YouTube Video Engine - Next Steps for Full Pipeline Testing

## Current Status ✅
- All services connected and healthy
- Script processing working
- Voiceover generation working with webhook callbacks
- Ready for full pipeline testing

## What's Needed for Complete Testing

### 1. Background Videos for Segments
The segment combination endpoint requires background video URLs. You need to:

a) **Upload background videos to a publicly accessible location**:
   - Digital Ocean Spaces
   - AWS S3 
   - Or any public URL

b) **Background video requirements**:
   - Format: MP4 preferred
   - Duration: Should be at least as long as segment duration
   - Resolution: 1920x1080 recommended
   - One video per segment OR reusable videos

c) **Test endpoint**: `/api/v1/combine-segment-media`
```json
{
  "segment_id": "SEGMENT_ID_FROM_AIRTABLE",
  "background_video_url": "https://your-storage.com/background-video.mp4"
}
```

### 2. Airtable Manual Configuration
Add linked fields to Jobs table:
- Related Video (Link to Videos table)
- Related Segment (Link to Segments table)

This is a manual task in Airtable interface.

### 3. Webhook Registration
Register these webhook URLs with external services:

**ElevenLabs**:
- URL: `https://youtube-video-engine.fly.dev/webhooks/elevenlabs`
- Method: POST
- Include job_id as query parameter

**NCA Toolkit**:
- URL: `https://youtube-video-engine.fly.dev/webhooks/nca`
- Method: POST

**GoAPI**:
- URL: `https://youtube-video-engine.fly.dev/webhooks/goapi`
- Method: POST

### 4. Full Pipeline Test Sequence

Once background videos are available:

1. **Process Script** → Creates video and segments
2. **Generate Voiceovers** → For each segment
3. **Combine Segment Media** → Merge voiceover with background video
4. **Combine All Segments** → Concatenate all segments
5. **Generate and Add Music** → Create background music

### 5. Monitoring Setup

**UptimeRobot/Pingdom**:
- Monitor: `https://youtube-video-engine.fly.dev/health`
- Alert threshold: 5 minutes
- Check interval: 1 minute

**Error Tracking (Sentry)**:
```bash
fly secrets set SENTRY_DSN=your-sentry-dsn
```

## Testing Commands

### Quick Health Check
```bash
curl https://youtube-video-engine.fly.dev/health
```

### Test Script Processing
```bash
curl -X POST https://youtube-video-engine.fly.dev/api/v1/process-script \
  -H "Content-Type: application/json" \
  -d '{
    "script_text": "Test script content",
    "video_name": "Test Video",
    "target_segment_duration": 30
  }'
```

### Test Voiceover Generation
```bash
curl -X POST https://youtube-video-engine.fly.dev/api/v1/generate-voiceover \
  -H "Content-Type: application/json" \
  -d '{
    "segment_id": "SEGMENT_ID",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "stability": 0.5,
    "similarity_boost": 0.5
  }'
```

## Resources Needed from Client

1. **Background Videos** - Upload to cloud storage
2. **Airtable Access** - To add linked fields
3. **External Service Accounts** - To register webhooks
4. **Monitoring Service Account** - UptimeRobot/Pingdom/Sentry

## Estimated Timeline

- Background video setup: 1-2 hours
- Airtable configuration: 30 minutes
- Webhook registration: 1 hour
- Full pipeline testing: 2-3 hours
- Monitoring setup: 1 hour

**Total: ~6-8 hours** for complete production readiness

## Support Needed

If you need help with:
- Setting up cloud storage for videos
- Configuring Airtable fields
- Registering webhooks
- Running tests

Please let me know and I can provide detailed instructions or assist directly.
