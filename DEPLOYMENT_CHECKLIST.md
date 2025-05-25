# YouTube Video Engine - Production Deployment Checklist

## Pre-Deployment Requirements

### 1. Airtable Setup
- [ ] Create new Airtable base for production
- [ ] Create **Videos** table with fields:
  - Name (Single line text)
  - Script (Long text)
  - Status (Single select: pending, processing, completed, failed)
  - Segments (Link to Segments)
  - Combined Segments Video (Attachment)
  - Music Prompt (Long text)
  - Music (Attachment)
  - Final Video (Attachment)
  - Error Details (Long text)
- [ ] Create **Segments** table with fields:
  - Name (Formula/Auto)
  - Video (Link to Videos)
  - Text (Long text)
  - Order (Number)
  - Start Time (Number)
  - End Time (Number)
  - Duration (Formula)
  - Voice ID (Single line)
  - Base Video (Attachment)
  - Voiceover (Attachment)
  - Combined (Attachment)
  - Status (Single select)
- [ ] Create **Jobs** table with fields:
  - Job ID (Formula/Auto)
  - Type (Single select)
  - Status (Single select)
  - Related Video (Link to Videos)
  - Related Segment (Link to Segments)
  - External Job ID (Single line)
  - Webhook URL (URL)
  - Request Payload (Long text)
  - Response Payload (Long text)
  - Error Details (Long text)
- [ ] Create **Webhook Events** table with fields:
  - Event ID (Autonumber)
  - Service (Single select: nca, elevenlabs, goapi)
  - Endpoint (Single line)
  - Raw Payload (Long text)
  - Processed (Checkbox)
  - Related Job (Link to Jobs)
  - Success (Checkbox)

### 2. API Keys
- [ ] Obtain Airtable API key from https://airtable.com/account
- [ ] Get Airtable Base ID from your base URL
- [ ] Register for NCA Toolkit API key at https://ncatoolkit.com
- [ ] Get ElevenLabs API key from https://elevenlabs.io
- [ ] Obtain GoAPI API key from https://goapi.io

### 3. Environment Variables
- [ ] Copy production values from coding_resources/.env
- [ ] Verify all required variables are set:
  - AIRTABLE_API_KEY
  - AIRTABLE_BASE_ID
  - AIRTABLE_VIDEOS_TABLE
  - AIRTABLE_SEGMENTS_TABLE
  - AIRTABLE_JOBS_TABLE
  - AIRTABLE_WEBHOOK_EVENTS_TABLE
  - NCA_API_KEY
  - ELEVENLABS_API_KEY
  - GOAPI_API_KEY
  - WEBHOOK_BASE_URL (will be your Fly.io app URL)

## Deployment Steps

### 1. Fly.io Setup
- [ ] Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
- [ ] Login to Fly: `fly auth login`
- [ ] Create app: `fly launch --name youtube-video-engine`

### 2. Configure Secrets
```bash
fly secrets set AIRTABLE_API_KEY="your_key"
fly secrets set AIRTABLE_BASE_ID="your_base_id"
fly secrets set AIRTABLE_VIDEOS_TABLE="Videos"
fly secrets set AIRTABLE_SEGMENTS_TABLE="Segments"
fly secrets set AIRTABLE_JOBS_TABLE="Jobs"
fly secrets set AIRTABLE_WEBHOOK_EVENTS_TABLE="Webhook Events"
fly secrets set NCA_API_KEY="your_key"
fly secrets set ELEVENLABS_API_KEY="your_key"
fly secrets set GOAPI_API_KEY="your_key"
fly secrets set WEBHOOK_BASE_URL="https://youtube-video-engine.fly.dev"
```

### 3. Deploy Application
- [ ] Deploy: `fly deploy`
- [ ] Check deployment: `fly status`
- [ ] View logs: `fly logs`

## Post-Deployment Verification

### 1. Basic Checks
- [ ] Health check endpoint: `curl https://youtube-video-engine.fly.dev/health`
- [ ] API docs accessible: `https://youtube-video-engine.fly.dev/api/docs`

### 2. Integration Tests
- [ ] Test Airtable connection
- [ ] Verify webhook endpoints are accessible
- [ ] Test each external service connection

### 3. End-to-End Test
- [ ] Process a test script
- [ ] Generate voiceover for a segment
- [ ] Combine segment media
- [ ] Combine all segments
- [ ] Generate and add music
- [ ] Verify final video is produced

## Monitoring Setup

### 1. Fly.io Monitoring
- [ ] Set up alerts for app crashes
- [ ] Configure autoscaling if needed
- [ ] Set up log aggregation

### 2. External Monitoring
- [ ] Set up uptime monitoring (e.g., UptimeRobot)
- [ ] Configure webhook endpoint monitoring
- [ ] Set up error tracking (optional)

## Rollback Plan

If issues occur:
1. `fly releases` - view all releases
2. `fly deploy --image <previous-image>` - rollback to previous version
3. Check logs: `fly logs`
4. Verify health: `fly status`

## Support Contacts

- Fly.io Support: https://fly.io/docs
- NCA Toolkit: support@ncatoolkit.com
- ElevenLabs: https://elevenlabs.io/support
- GoAPI: https://goapi.io/support
