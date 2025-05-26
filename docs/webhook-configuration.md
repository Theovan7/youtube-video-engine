# Webhook Configuration Guide

This guide explains how to configure webhooks for the YouTube Video Engine with external services.

## Webhook URLs

The YouTube Video Engine provides the following webhook endpoints:

- **ElevenLabs**: `https://youtube-video-engine.fly.dev/webhooks/elevenlabs`
- **NCA Toolkit**: `https://youtube-video-engine.fly.dev/webhooks/nca-toolkit`
- **GoAPI**: `https://youtube-video-engine.fly.dev/webhooks/goapi`

## Service Configuration

### 1. ElevenLabs Webhook Configuration

To configure webhooks in ElevenLabs:

1. Log in to your ElevenLabs account
2. Go to Settings → API Settings
3. Find the Webhook Configuration section
4. Add the webhook URL: `https://youtube-video-engine.fly.dev/webhooks/elevenlabs`
5. Enable webhook events for:
   - Voice generation completed
   - Voice generation failed

**Webhook Signature Validation** (Optional):
- If you want to enable webhook signature validation, generate a webhook secret in ElevenLabs
- Add it to your Fly.io secrets:
  ```bash
  fly secrets set WEBHOOK_SECRET_ELEVENLABS=your-secret-here
  fly secrets set WEBHOOK_VALIDATION_ELEVENLABS_ENABLED=True
  ```

### 2. NCA Toolkit Webhook Configuration

To configure webhooks in NCA Toolkit:

1. Access your NCA Toolkit dashboard
2. Navigate to API Settings
3. Add webhook endpoint: `https://youtube-video-engine.fly.dev/webhooks/nca-toolkit`
4. Enable notifications for:
   - Media processing completed
   - Media processing failed
   - File upload completed

**Webhook Signature Validation** (Optional):
- Generate a webhook secret in NCA Toolkit
- Add it to your Fly.io secrets:
  ```bash
  fly secrets set WEBHOOK_SECRET_NCA=your-secret-here
  fly secrets set WEBHOOK_VALIDATION_NCA_ENABLED=True
  ```

### 3. GoAPI (Suno) Webhook Configuration

To configure webhooks in GoAPI:

1. Log in to your GoAPI account
2. Go to API Configuration
3. Add webhook URL: `https://youtube-video-engine.fly.dev/webhooks/goapi`
4. Enable webhook events for:
   - Music generation completed
   - Music generation failed

**Webhook Signature Validation** (Optional):
- Generate a webhook secret in GoAPI
- Add it to your Fly.io secrets:
  ```bash
  fly secrets set WEBHOOK_SECRET_GOAPI=your-secret-here
  fly secrets set WEBHOOK_VALIDATION_GOAPI_ENABLED=True
  ```

## Testing Webhooks

### 1. Test Webhook Connectivity

Use the following curl command to test webhook endpoints:

```bash
# Test ElevenLabs webhook
curl -X POST https://youtube-video-engine.fly.dev/webhooks/elevenlabs?job_id=test-job \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "output": {"url": "https://example.com/test.mp3"}}'

# Test NCA Toolkit webhook
curl -X POST https://youtube-video-engine.fly.dev/webhooks/nca-toolkit?job_id=test-job&operation=combine \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "output": {"url": "https://example.com/test.mp4"}}'

# Test GoAPI webhook
curl -X POST https://youtube-video-engine.fly.dev/webhooks/goapi?job_id=test-job \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "output": {"audio_url": "https://example.com/music.mp3"}}'
```

### 2. Test with Signature Validation

If you've enabled signature validation, include the appropriate signature header:

```bash
# Calculate signature
PAYLOAD='{"status": "completed", "output": {"url": "https://example.com/result.mp3"}}'
SECRET="your-webhook-secret"
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/^.*= //')

# Send webhook with signature
curl -X POST https://youtube-video-engine.fly.dev/webhooks/elevenlabs?job_id=test-job \
  -H "Content-Type: application/json" \
  -H "X-ElevenLabs-Signature: $SIGNATURE" \
  -d "$PAYLOAD"
```

## Monitoring Webhooks

### Check Webhook Events in Airtable

All webhook events are logged in the `Webhook Events` table in Airtable with:
- Event ID
- Service (elevenlabs, nca, goapi)
- Endpoint
- Raw Payload
- Processed status
- Success status
- Related Job (if applicable)

### View Application Logs

Monitor webhook processing in real-time:

```bash
fly logs -a youtube-video-engine
```

## Troubleshooting

### Common Issues

1. **Webhook not being called**
   - Verify the webhook URL is correctly configured in the external service
   - Check that the service has the correct permissions to call webhooks
   - Ensure the job includes the webhook URL in the initial request

2. **401 Unauthorized (when signature validation is enabled)**
   - Verify the webhook secret matches between the service and Fly.io
   - Check that the signature header name is correct for each service
   - Ensure the signature calculation method matches the expected format

3. **Job not found errors**
   - Verify the job_id parameter is included in the webhook URL
   - Check that the job exists in the Airtable Jobs table
   - Ensure the job hasn't been deleted or expired

4. **Webhook processed but no updates**
   - Check the Webhook Events table for the raw payload
   - Verify the payload format matches what the handler expects
   - Review application logs for any processing errors

## Security Best Practices

1. **Always use HTTPS** for webhook endpoints
2. **Enable signature validation** in production environments
3. **Rotate webhook secrets** regularly
4. **Monitor webhook events** for suspicious activity
5. **Implement rate limiting** (already configured in the API)
6. **Log all webhook events** for audit trails

## Next Steps

After configuring webhooks:

1. Run end-to-end tests to verify the complete pipeline
2. Set up monitoring alerts for webhook failures
3. Document the webhook payload formats for each service
4. Create runbooks for common webhook issues
