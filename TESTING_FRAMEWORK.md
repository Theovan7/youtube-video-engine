# YouTube Video Engine Testing Framework

## Overview

The YouTube Video Engine Testing Framework is a comprehensive local testing environment designed to validate API endpoints, test external service integrations, and verify file processing through local backup inspection.

## Key Features

- **Function-based Organization**: Test inputs and outputs organized by API endpoints
- **Local Backup Verification**: Automatic inspection of files saved to `./local_backups/`
- **Real-time File Monitoring**: Watch for new files as they're processed
- **Media Validation**: FFprobe integration for validating audio/video files
- **Webhook Simulation**: Test asynchronous operations locally
- **Pipeline Orchestration**: Run complete video generation workflows

## Testing Framework Components

### 1. Core Framework (`testing_environment/test_framework.py`)
- `VideoEngineTestFramework`: Main testing class with endpoint testing, file validation, and response verification
- `WebhookSimulator`: Simulates webhook callbacks for async operations
- Built-in retry logic and timeout handling
- Automatic file type detection and validation

### 2. Function Testing (`testing_environment/test_function.py`)
- Test individual API endpoints
- Load custom payloads from JSON files
- Automatic file upload to S3 for media tests
- Response validation and error reporting

### 3. Pipeline Testing (`testing_environment/test_pipeline.py`)
- Orchestrates complete video generation workflows
- Manages dependencies between API calls
- Tracks job statuses across multiple services
- Generates comprehensive test reports

### 4. File Inspector (`testing_environment/file_inspector.py`)
- Real-time monitoring of local backup directory
- File metadata extraction (size, duration, format)
- Search by Airtable record ID
- Export detailed inspection reports

## Quick Start Guide

### 1. Start the API Server
```bash
# Use port 5001 to avoid macOS AirPlay conflicts
PORT=5001 python app.py
```

### 2. Test a Single Function
```bash
# Test voiceover generation
python testing_environment/test_function.py generate-voiceover

# Test with specific segment
python test_voiceover_segment.py --segment-id recmXnXCm5tFVAlFo
```

### 3. Monitor File Backups
```bash
# Start real-time monitoring
python testing_environment/file_inspector.py --watch

# Find files for a specific record
python testing_environment/file_inspector.py --find recmXnXCm5tFVAlFo
```

## Local Backup Structure

Files are automatically saved to:
```
./local_backups/youtube-video-engine/
├── voiceovers/   # MP3 files and voiceover-related images
├── videos/       # Generated video files
├── music/        # Background music files
└── images/       # AI-generated images
```

File naming convention:
`{timestamp}_{unique_id}_{type}_{record_id}.{extension}`

Example:
`20250609_104914_1564c767_voiceover_recmXnXCm5tFVAlFo.mp3`

## API Endpoints Covered

### Synchronous Endpoints
- `/api/v2/process-script` - Parse script into segments
- `/api/v2/generate-voiceover` - Generate audio via ElevenLabs

### Asynchronous Endpoints (webhook-based)
- `/api/v2/generate-ai-image` - Generate images via OpenAI
- `/api/v2/generate-video` - Generate videos via GoAPI
- `/api/v2/combine-segment-media` - Combine audio/video via NCA
- `/api/v2/combine-all-segments` - Concatenate videos via NCA
- `/api/v2/generate-and-add-music` - Add background music

## Test Input Organization

```
testing_environment/test_inputs/
├── process-script/
│   ├── scripts/           # Raw script text files
│   └── payloads/          # JSON request payloads
├── generate-voiceover/
│   └── payloads/          # Segment ID payloads
├── generate-ai-image/
│   └── payloads/          # Image generation requests
├── generate-video/
│   ├── source_images/     # Input images for video
│   └── payloads/          # Video generation configs
├── combine-segment-media/
│   ├── test_videos/       # Sample video files
│   ├── test_audio/        # Sample audio files
│   └── payloads/          # Combination requests
└── webhook-simulations/
    └── callbacks/         # Webhook response templates
```

## Example Test Session

```bash
# Terminal 1: Start the API
PORT=5001 python app.py

# Terminal 2: Monitor files
python testing_environment/file_inspector.py --watch

# Terminal 3: Run tests
python testing_environment/test_function.py generate-voiceover

# View results
ls -la ./local_backups/youtube-video-engine/voiceovers/
```

## Troubleshooting

### Common Issues

1. **Port 5000 Already in Use**
   - macOS AirPlay Receiver uses port 5000
   - Solution: Use `PORT=5001 python app.py`

2. **ModuleNotFoundError: apscheduler**
   - Missing job scheduling dependency
   - Solution: `pip install apscheduler`

3. **403 Forbidden on API Calls**
   - Flask app not running
   - Solution: Start the app first

4. **Files Not in Local Backup**
   - Check `LOCAL_BACKUP_PATH` in config
   - Verify write permissions
   - Check S3 upload succeeded first

## Environment Requirements

```bash
# Required Python packages
pip install flask requests python-dotenv boto3 watchdog apscheduler

# Required environment variables
AIRTABLE_API_KEY=your_key
ELEVENLABS_API_KEY=your_key
GOAPI_API_KEY=your_key
OPENAI_API_KEY=your_key
NCA_API_KEY=your_key
NCA_S3_ACCESS_KEY=your_key
NCA_S3_SECRET_KEY=your_key
LOCAL_BACKUP_PATH=./local_backups
```

## Integration with Main Application

The testing framework integrates seamlessly with the main application:

1. **Uses Same Config**: Reads from `config.py` and `.env`
2. **Same Service Classes**: Tests actual service implementations
3. **Real API Endpoints**: No mocking - tests real functionality
4. **Production-Ready**: Can test against local or production URLs

## Best Practices

1. **Always Start Fresh**: Clear test outputs before major test runs
2. **Monitor Logs**: Keep app.log open to catch errors
3. **Use File Inspector**: Verify files are created correctly
4. **Test Incrementally**: Test individual functions before pipelines
5. **Document Payloads**: Add comments to JSON files explaining test cases

## Next Steps

1. Add more test cases to `test_inputs/` folders
2. Create automated test suites for CI/CD
3. Add performance benchmarking
4. Implement test result comparison
5. Add visual regression testing for generated videos

## Related Documentation

- [Testing Environment README](testing_environment/README.md)
- [API Quickstart Guide](docs/API_QUICKSTART.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Video Processing Guide](docs/VIDEO_PROCESSING.md)