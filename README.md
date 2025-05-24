# YouTube Video Engine

Production-ready automation system that transforms written scripts into fully produced videos with AI-generated voiceovers and background music.

## Overview

The YouTube Video Engine is a Flask-based API service that automates the entire video production pipeline from script to final video with voiceover and background music.

## Features

- **Script Processing**: Parse scripts into timed segments
- **AI Voiceover Generation**: Generate professional voiceovers using ElevenLabs
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
- Duration (Formula)
- Voice ID (Single line)
- Base Video (Attachment)
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

## Support

For issues and questions, please open an issue on GitHub.

## Acknowledgments

- NCA Toolkit for free media processing
- ElevenLabs for AI voice generation
- GoAPI for AI music generation
- Airtable for flexible data storage