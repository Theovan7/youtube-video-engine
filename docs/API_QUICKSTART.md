# API Quick Start Guide

Welcome to the YouTube Video Engine API! This guide will help you get started quickly.

## Base URL

```
Development: http://localhost:5000
Production: https://your-app.fly.dev
```

## Authentication

Currently, the API uses rate limiting but no authentication. In production, you should implement API key authentication.

## Quick Start Examples

### 1. Check API Health

```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "airtable": "connected",
    "elevenlabs": "connected",
    "nca_toolkit": "connected",
    "goapi": "connected"
  }
}
```

### 2. Process a Script

```bash
curl -X POST http://localhost:5000/api/v1/process-script \
  -H "Content-Type: application/json" \
  -d '{
    "script_text": "Welcome to our video. Today we will learn about automation. This powerful technology can save you hours of work.",
    "video_id": "recXXXXXXXXXXXXXX",
    "target_segment_duration": 30
  }'
```

Response:
```json
{
  "video_id": "recXXXXXXXXXXXXXX",
  "segments_created": 1,
  "segments": [
    {
      "id": "recYYYYYYYYYYYYYY",
      "order": 1,
      "text": "Welcome to our video. Today we will learn about automation. This powerful technology can save you hours of work.",
      "estimated_duration": 10.5
    }
  ]
}
```

### 3. Generate Voiceover

```bash
curl -X POST http://localhost:5000/api/v1/generate-voiceover \
  -H "Content-Type: application/json" \
  -d '{
    "segment_id": "recYYYYYYYYYYYYYY",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "stability": 0.5,
    "similarity_boost": 0.5
  }'
```

Response:
```json
{
  "job_id": "job_123456789",
  "status": "processing",
  "message": "Voiceover generation started"
}
```

### 4. Check Job Status

```bash
curl http://localhost:5000/api/v1/jobs/job_123456789
```

Response:
```json
{
  "job_id": "job_123456789",
  "type": "voiceover",
  "status": "completed",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:05:00Z",
  "result": {
    "voiceover_url": "https://storage.example.com/voiceover.mp3",
    "duration": 10.5
  }
}
```

### 5. Complete Video Production Pipeline

Here's a complete example of producing a video from start to finish:

```python
import requests
import time

BASE_URL = "http://localhost:5000"

# Step 1: Process the script
script_response = requests.post(
    f"{BASE_URL}/api/v1/process-script",
    json={
        "script_text": "Your amazing script here...",
        "video_id": "recXXXXXXXXXXXXXX",
        "target_segment_duration": 30
    }
)
segments = script_response.json()["segments"]

# Step 2: Generate voiceovers for each segment
for segment in segments:
    voiceover_response = requests.post(
        f"{BASE_URL}/api/v1/generate-voiceover",
        json={
            "segment_id": segment["id"],
            "voice_id": "21m00Tcm4TlvDq8ikWAM"
        }
    )
    job_id = voiceover_response.json()["job_id"]
    
    # Wait for completion
    while True:
        status = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}").json()
        if status["status"] in ["completed", "failed"]:
            break
        time.sleep(2)

# Step 3: Upload background videos to Airtable
# MANUAL STEP: Users must upload appropriate background videos 
# to the 'Video' field in each segment record in Airtable
print("Please upload background videos to each segment in Airtable before proceeding...")
input("Press Enter when all videos have been uploaded...")

# Step 4: Combine media for each segment
for segment in segments:
    combine_response = requests.post(
        f"{BASE_URL}/api/v1/combine-segment-media",
        json={"segment_id": segment["id"]}
    )
    # Wait for completion...

# Step 5: Combine all segments
combine_all_response = requests.post(
    f"{BASE_URL}/api/v1/combine-all-segments",
    json={"video_id": "recXXXXXXXXXXXXXX"}
)
# Wait for completion...

# Step 6: Add background music
music_response = requests.post(
    f"{BASE_URL}/api/v1/generate-and-add-music",
    json={
        "video_id": "recXXXXXXXXXXXXXX",
        "music_prompt": "upbeat corporate background music",
        "duration": 180
    }
)
# Wait for completion...

print("Video production complete!")
```

## API Documentation

For complete API documentation with all endpoints, request/response schemas, and interactive testing:

Visit: `http://localhost:5000/api/docs`

## Error Handling

All errors follow this format:

```json
{
  "error": "Error type",
  "message": "Detailed error message",
  "details": {
    "field": "Additional context"
  }
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid input)
- `404`: Not Found
- `429`: Rate Limit Exceeded
- `500`: Internal Server Error

## Rate Limiting

Default rate limit: 100 requests per hour per IP address

Rate limit headers in response:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time when limit resets

## Webhooks

The API uses webhooks for asynchronous operations. When you start a long-running operation (voiceover, video processing, music generation), you'll receive a job ID. The external service will call our webhook when complete, updating the job status.

## Next Steps

1. Set up your Airtable base with the required schema
2. Configure your environment variables
3. Test the health endpoint
4. Try processing a simple script
5. Explore the full API documentation at `/api/docs`

## Need Help?

- Check the [Architecture Documentation](./ARCHITECTURE.md)
- Review the [Configuration Guide](./CONFIGURATION.md)
- Explore the integration tests in `/scripts/test_integrations.py`
