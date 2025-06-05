# Voiceover API Update - Synchronous Processing

## Overview
ElevenLabs Text-to-Speech API does not support webhooks. All voiceover generation is now synchronous and returns audio data immediately.

## API Endpoint

### Generate Voiceover (Synchronous)
- **URL:** `/api/v2/generate-voiceover`
- **Method:** POST
- **Content-Type:** application/json

### Request Body
```json
{
  "record_id": "segment_record_id"
}
```

### Response (Success - 200)
```json
{
  "segment_id": "recdRdKs6y9dyf609",
  "voice_id": "kcx1H2eb9RYJRyCtQLxY",
  "voice_name": "Gravitas - The deep narrator voice",
  "stability": 0.5,
  "similarity_boost": 0.5,
  "voiceover_url": "https://...",
  "status": "completed"
}
```

### Response (Error - 400/500)
```json
{
  "error": "Error description",
  "details": "Detailed error message"
}
```

## Process Flow

1. **Request Received** - API receives segment ID
2. **Fetch Segment** - Get segment text and voice settings from Airtable
3. **Generate Audio** - Call ElevenLabs TTS API (synchronous)
4. **Upload Audio** - Store audio file in NCA cloud storage
5. **Update Airtable** - Save voiceover URL to segment record
6. **Return Response** - Send success response with audio URL

## Status Updates

The segment status in Airtable will be updated as follows:
- `Generating Voiceover` - Set when processing starts
- `Voiceover Ready` - Set when audio is successfully generated
- `Voiceover Failed` - Set if any error occurs

## Migration Notes

### Old Webhook-Based Flow (DEPRECATED)
- Created job records
- Sent webhook URL to ElevenLabs
- Waited for callback that never came
- Jobs stuck in "processing" forever

### New Synchronous Flow
- No job records for voiceover
- Immediate audio generation
- Direct upload to storage
- Instant status updates

## Error Handling

Common errors and their resolutions:
- **Voice not linked:** Ensure a voice is selected in the Voices field
- **Empty segment text:** Verify SRT Text field has content
- **ElevenLabs API error:** Check API key and quota
- **Upload failure:** Verify NCA service is accessible

## Example Usage

```bash
# Generate voiceover for a segment
curl -X POST https://youtube-video-engine.fly.dev/api/v2/generate-voiceover \
  -H "Content-Type: application/json" \
  -d '{"record_id": "recdRdKs6y9dyf609"}'
```
