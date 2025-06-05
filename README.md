# YouTube Video Engine

Production-ready automation system that transforms written scripts into fully produced videos with AI-generated voiceovers and background music.

## Overview

The YouTube Video Engine is a Flask-based API service that automates the entire video production pipeline from script to final video with voiceover and background music.

## Features

- **Script Processing**: Parse scripts into timed segments
- **AI Voiceover Generation**: Generate professional voiceovers using ElevenLabs
- **AI Image Generation**: Generate images from text prompts using OpenAI's DALL-E 3
- **Video Assembly**: Combine voiceovers with background videos
- **Music Integration**: Add AI-generated background music
- **Complete Automation**: End-to-end video production pipeline
- **Webhook Support**: Async processing with comprehensive webhook handling
- **Airtable Integration**: All data stored in Airtable for easy management

## Tech Stack

- **Backend**: Python 3.11+ with Flask
- **Database**: Airtable (no SQL database needed)
- **Media Processing**: NCA Toolkit (FREE)
- **Voice Generation**: ElevenLabs API
- **Image Generation**: OpenAI DALL-E 3 API
- **Music Generation**: GoAPI (Suno)
- **File Storage**: Digital Ocean Spaces (via NCA)
- **Deployment**: Fly.io with Docker

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Theovan7/youtube-video-engine.git
cd youtube-video-engine
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment variables:
```bash
cp .env.example .env
```

5. Configure your API keys in `.env`:
- `AIRTABLE_API_KEY`
- `AIRTABLE_BASE_ID`
- `NCA_API_KEY`
- `ELEVENLABS_API_KEY`
- `GOAPI_API_KEY`
- `OPENAI_API_KEY`
- `WEBHOOK_BASE_URL`

## Usage

### Development

```bash
python app.py
```

The API will be available at `http://localhost:5000`

### API Endpoints

#### Process Script
```http
POST /api/v1/process-script
Content-Type: application/json

{
  "script_text": "Your script here...",
  "video_id": "airtable_record_id",
  "target_segment_duration": 30
}
```

#### Generate Voiceover
```http
POST /api/v1/generate-voiceover
Content-Type: application/json

{
  "segment_id": "airtable_record_id",
  "voice_id": "elevenlabs_voice_id",
  "stability": 0.5,
  "similarity_boost": 0.5
}
```

#### Combine Media
```http
POST /api/v1/combine-segment-media
Content-Type: application/json

{
  "segment_id": "airtable_record_id"
}
```

**Note**: Before calling this endpoint, users must manually upload a background video to the `Video` field in the segment record in Airtable. This is a "user in the loop" process where human judgment is used to select appropriate videos for each segment.

#### Combine All Segments
```http
POST /api/v1/combine-all-segments
Content-Type: application/json

{
  "video_id": "airtable_record_id"
}
```

#### Generate and Add Music
```http
POST /api/v1/generate-and-add-music
Content-Type: application/json

{
  "video_id": "airtable_record_id",
  "music_prompt": "upbeat corporate background music",
  "duration": 180
}
```

#### Generate AI Image (v2 API)
```http
POST /api/v2/generate-ai-image
Content-Type: application/json

{
  "segment_id": "airtable_record_id",
  "size": "1792x1008",  // optional: 1920x1080, 1792x1008, 1024x576, auto
  // Note: quality parameter removed - gpt-image-1 produces high-fidelity output by default
}
```

**Note**: This endpoint requires the segment to have an 'AI Image Prompt' field populated in Airtable. The generated image will be uploaded to the 'Image' attachment field. Generates 4 images in YouTube-friendly 16:9 aspect ratios using OpenAI's gpt-image-1 model.

#### Generate Video (v2 API)
```http
POST /api/v2/generate-video
Content-Type: application/json

{
  "segment_id": "airtable_record_id",
  "duration_override": 5,    // optional: 5 or 10 seconds, auto-calculated if not provided
  "aspect_ratio": "16:9",    // optional: "1:1", "16:9", "auto"
  "quality": "standard"      // optional: "standard", "high"
}
```

**Note**: This endpoint requires the segment to have an 'Upscale Image' field with an image. Uses Kling AI v1.6 via GoAPI to generate videos from images. Duration is automatically determined from the segment's 'Duration' field (<5 seconds = 5 second video, ≥5 seconds = 10 second video). The generated video will be uploaded to the 'Video' attachment field.

#### Check Job Status
```http
GET /api/v1/jobs/{job_id}
```

#### Health Check
```http
GET /health
```

## Deployment

### Deploy to Fly.io

1. Install Fly CLI:
```bash
curl -L https://fly.io/install.sh | sh
```

2. Launch the app:
```bash
fly launch
```

3. Set secrets:
```bash
fly secrets set AIRTABLE_API_KEY=your_key
fly secrets set AIRTABLE_BASE_ID=your_base_id
fly secrets set NCA_API_KEY=your_key
fly secrets set ELEVENLABS_API_KEY=your_key
fly secrets set GOAPI_API_KEY=your_key
fly secrets set OPENAI_API_KEY=your_key
```

4. Deploy:
```bash
fly deploy
```

## Airtable Schema

### Videos Table
- Name (Single line text)
- Script (Long text)
- Status (Single select: pending, processing, completed, failed)
- Segments (Link to Segments)
- Combined Segments Video (Attachment)
- Music Prompt (Long text)
- Music (Attachment)
- Final Video (Attachment)
- Error Details (Long text)

### Segments Table
- Name (Formula/Auto)
- Video (Link to Videos)
- Text (Long text)
- Order (Number)
- Start Time (Number)
- End Time (Number)
- Duration (Formula) - Used for video generation duration logic
- Voice ID (Single line)
- AI Image Prompt (Long text) - Text prompt for AI image generation
- Image (Attachment) - AI-generated images (4 images in 16:9 aspect ratio)
- Upscale Image (Attachment) - Source image for video generation
- Video (Attachment) - AI-generated videos OR user uploads background videos here
- Voiceover (Attachment)
- Combined (Attachment)
- Status (Single select)

### Jobs Table
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

### Webhook Events Table
- Event ID (Autonumber)
- Service (Single select: nca, elevenlabs, goapi)
- Endpoint (Single line)
- Raw Payload (Long text)
- Processed (Checkbox)
- Related Job (Link to Jobs)
- Success (Checkbox)

## Testing

Run tests:
```bash
pytest
```

Run integration tests:
```bash
python scripts/test_integrations.py
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Webhook Security

### Webhook Signature Validation

The API supports optional webhook signature validation to ensure webhook requests are authentic and haven't been tampered with. This feature can be enabled independently for each service.

#### Configuration

Set the following environment variables to enable webhook validation:

```bash
# Enable validation for each service (default: False)
WEBHOOK_VALIDATION_ELEVENLABS_ENABLED=True
WEBHOOK_VALIDATION_NCA_ENABLED=True
WEBHOOK_VALIDATION_GOAPI_ENABLED=True

# Webhook secrets (required if validation is enabled)
WEBHOOK_SECRET_ELEVENLABS=your-elevenlabs-webhook-secret
WEBHOOK_SECRET_NCA=your-nca-webhook-secret
WEBHOOK_SECRET_GOAPI=your-goapi-webhook-secret
```

#### How It Works

1. Each service sends a signature header with webhook requests:
   - ElevenLabs: `X-ElevenLabs-Signature`
   - NCA Toolkit: `X-NCA-Signature`
   - GoAPI: `X-GoAPI-Signature`

2. The signature is calculated using HMAC-SHA256:
   ```python
   signature = hmac.new(
       secret.encode('utf-8'),
       request_body,
       hashlib.sha256
   ).hexdigest()
   ```

3. The API validates the signature before processing the webhook

4. Invalid signatures return a 401 Unauthorized response

#### Testing Webhook Validation

You can test webhook validation using curl:

```bash
# Calculate signature
PAYLOAD='{"status": "completed", "output": {"url": "https://example.com/result.mp3"}}'
SECRET="your-webhook-secret"
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/^.*= //')

# Send webhook with signature
curl -X POST http://localhost:5000/webhooks/elevenlabs?job_id=test-job \
  -H "Content-Type: application/json" \
  -H "X-ElevenLabs-Signature: $SIGNATURE" \
  -d "$PAYLOAD"
```

## Support

For issues and questions, please open an issue on GitHub.

## Acknowledgments

- NCA Toolkit for free media processing
- ElevenLabs for AI voice generation
- GoAPI for AI music generation
- Airtable for flexible data storage