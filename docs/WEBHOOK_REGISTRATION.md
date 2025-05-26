# 🔗 Webhook Registration Guide

## Overview
This guide provides step-by-step instructions for registering webhook URLs with all external services to enable asynchronous processing and real-time status updates.

## 🌐 Webhook Endpoints

All webhook endpoints are available at the base URL: `https://youtube-video-engine.fly.dev`

### Available Webhook Endpoints:
1. **ElevenLabs**: `/webhooks/elevenlabs`
2. **NCA Toolkit**: `/webhooks/nca`  
3. **GoAPI (Suno)**: `/webhooks/goapi`

## 🎤 ElevenLabs Webhook Registration

### Step 1: Access ElevenLabs Dashboard
1. Log in to [ElevenLabs.io](https://elevenlabs.io)
2. Navigate to **Settings** → **API Keys**
3. Go to **Webhooks** section

### Step 2: Add Webhook URL
1. Click **Add Webhook**
2. **URL**: `https://youtube-video-engine.fly.dev/webhooks/elevenlabs`
3. **Events**: Select "Speech Generation Completed"
4. **Method**: POST
5. **Headers**: Leave default (Content-Type: application/json)

### Step 3: Configure Security (Optional)
If webhook signing is available:
1. Enable webhook signature validation
2. Copy the webhook secret
3. Add to environment variables:
```bash
fly secrets set WEBHOOK_SECRET_ELEVENLABS=your_webhook_secret
fly secrets set WEBHOOK_VALIDATION_ELEVENLABS_ENABLED=true
```

### Step 4: Test Webhook
1. Use ElevenLabs test functionality
2. Monitor webhook events in Airtable "Webhook Events" table
3. Verify successful processing

## 🎥 NCA Toolkit Webhook Registration

### Step 1: Access NCA Toolkit Dashboard
1. Log in to [NCA Toolkit](https://ncatoolkit.com) dashboard
2. Navigate to **Account Settings** → **Webhooks**

### Step 2: Add Webhook Configurations

**For Media Combination Operations:**
1. **URL**: `https://youtube-video-engine.fly.dev/webhooks/nca`
2. **Events**: FFmpeg job completion
3. **Method**: POST
4. **Parameters**: Include job metadata in payload

**For Video Concatenation:**
1. Same URL as above
2. **Events**: Video concatenation completion
3. System will differentiate based on operation parameter

**For Music Addition:**
1. Same URL as above  
2. **Events**: Audio mixing completion

### Step 3: Configure Authentication
1. If API key authentication is available:
```bash
fly secrets set WEBHOOK_SECRET_NCA=your_webhook_secret
fly secrets set WEBHOOK_VALIDATION_NCA_ENABLED=true
```

### Step 4: Test Integration
1. Submit a test media processing job
2. Monitor webhook reception in logs
3. Verify job status updates in Airtable

## 🎵 GoAPI (Suno) Webhook Registration

### Step 1: Access GoAPI Dashboard
1. Log in to your GoAPI account
2. Navigate to **API Settings** → **Webhooks**

### Step 2: Configure Music Generation Webhooks
1. **URL**: `https://youtube-video-engine.fly.dev/webhooks/goapi`
2. **Events**: "Music Generation Complete"
3. **Method**: POST
4. **Format**: JSON payload

### Step 3: Set Authentication
1. Configure webhook secret if available:
```bash
fly secrets set WEBHOOK_SECRET_GOAPI=your_webhook_secret
fly secrets set WEBHOOK_VALIDATION_GOAPI_ENABLED=true
```

### Step 4: Test Music Generation
1. Submit test music generation request
2. Verify webhook delivery
3. Check job completion in system

## 🔒 Security Configuration

### Webhook Signature Validation

The system supports optional webhook signature validation for enhanced security:

**Environment Variables:**
```bash
# Enable validation per service
WEBHOOK_VALIDATION_ELEVENLABS_ENABLED=true
WEBHOOK_VALIDATION_NCA_ENABLED=true  
WEBHOOK_VALIDATION_GOAPI_ENABLED=true

# Webhook secrets (obtain from service providers)
WEBHOOK_SECRET_ELEVENLABS=your_elevenlabs_secret
WEBHOOK_SECRET_NCA=your_nca_secret
WEBHOOK_SECRET_GOAPI=your_goapi_secret
```

**Signature Verification Process:**
1. Each service sends signature in specific header:
   - ElevenLabs: `X-ElevenLabs-Signature`
   - NCA Toolkit: `X-NCA-Signature`  
   - GoAPI: `X-GoAPI-Signature`

2. System validates using HMAC-SHA256
3. Invalid signatures return 401 Unauthorized
4. Valid requests proceed with processing

### IP Whitelisting (if supported)
Add these Fly.io IP ranges to service allowlists:
- Check current Fly.io IP ranges in their documentation
- Configure in each service's security settings

## 📊 Monitoring & Debugging

### Webhook Event Logging
All webhook events are automatically logged in the **Webhook Events** table:
- Raw payload data
- Processing status
- Success/failure indicators
- Related job information

### Testing Webhooks Locally

**1. Using ngrok for local testing:**
```bash
# Install ngrok
brew install ngrok

# Expose local port
ngrok http 5000

# Use ngrok URL for webhook registration
https://abc123.ngrok.io/webhooks/elevenlabs
```

**2. Manual webhook testing:**
```bash
# Test ElevenLabs webhook format
curl -X POST https://youtube-video-engine.fly.dev/webhooks/elevenlabs?job_id=test-123 \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "output": {"url": "https://example.com/audio.mp3"}}'

# Test NCA webhook format
curl -X POST https://youtube-video-engine.fly.dev/webhooks/nca?job_id=test-456&operation=combine \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "output_url": "https://example.com/video.mp4"}'

# Test GoAPI webhook format
curl -X POST https://youtube-video-engine.fly.dev/webhooks/goapi?job_id=test-789 \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "output": {"url": "https://example.com/music.mp3"}}'
```

## 🚨 Troubleshooting

### Common Issues

**1. Webhook Not Received**
- Verify URL is correctly registered
- Check service webhook configuration
- Confirm webhook endpoint is accessible
- Review firewall/security settings

**2. Authentication Failures**
- Verify webhook secrets are correctly set
- Check signature validation settings
- Ensure headers are properly formatted
- Test with signature validation disabled temporarily

**3. Processing Failures**
- Check webhook payload format
- Verify required fields are present
- Review job status in Airtable
- Check system logs for detailed errors

### Debugging Steps

**1. Check Webhook Reception:**
```bash
# Monitor webhook events table in Airtable
# Look for new entries with service and payload data
```

**2. Verify Job Processing:**
```bash
# Check job status via API
curl https://youtube-video-engine.fly.dev/api/v1/jobs/{job_id}
```

**3. Review System Health:**
```bash
# Check overall system health
curl https://youtube-video-engine.fly.dev/health
```

## 📋 Webhook Registration Checklist

### Pre-Registration
- [ ] System deployed and accessible
- [ ] Health check endpoint responding
- [ ] All services connected and healthy
- [ ] Webhook endpoints tested manually

### ElevenLabs
- [ ] Webhook URL registered
- [ ] Events configured (speech generation complete)
- [ ] Authentication configured (if available)
- [ ] Test webhook received and processed

### NCA Toolkit  
- [ ] Webhook URL registered
- [ ] Events configured (FFmpeg completion)
- [ ] Authentication configured (if available)
- [ ] Test webhook received and processed

### GoAPI
- [ ] Webhook URL registered  
- [ ] Events configured (music generation complete)
- [ ] Authentication configured (if available)
- [ ] Test webhook received and processed

### Post-Registration
- [ ] Full pipeline test completed
- [ ] Webhook events logged in Airtable
- [ ] Job status updates working
- [ ] Error handling verified
- [ ] Monitoring configured

## 🎯 Success Criteria

Webhooks are successfully configured when:
1. ✅ All three services can deliver webhooks to system
2. ✅ Webhook events appear in Airtable logging table
3. ✅ Job statuses update automatically
4. ✅ Processing pipeline completes end-to-end
5. ✅ Error conditions are handled gracefully

## 📞 Support Resources

**Service Documentation:**
- [ElevenLabs API Docs](https://docs.elevenlabs.io/api-reference)
- NCA Toolkit webhook documentation
- GoAPI webhook configuration guide

**System Monitoring:**
- Health Check: `https://youtube-video-engine.fly.dev/health`
- Webhook Events: Airtable "Webhook Events" table
- Job Status: `/api/v1/jobs/{job_id}` endpoint

---
*Proper webhook configuration enables real-time processing updates and complete automation of the video production pipeline.*
