# YouTube Video Engine Testing Environment

This testing environment allows you to test the YouTube Video Engine API endpoints and validate that files are being properly uploaded to external services and saved to local backups.

## Components

### 1. Test Framework (`test_framework.py`)
Core testing utilities:
- `VideoEngineTestFramework`: Main testing class
  - Sends requests to API endpoints
  - Waits for files to appear in local backups
  - Validates file content (size, duration, format)
  - Generates test reports

- `WebhookSimulator`: Simulates webhook callbacks
  - NCA Toolkit callbacks
  - GoAPI callbacks

### 2. Sample Payloads (`sample_payloads.py`)
Pre-configured test payloads for all endpoints:
- Script processing
- Voiceover generation
- AI image generation
- Video generation
- Media combination
- Music generation

### 3. Test Runner (`run_tests.py`)
Main test execution script:
- Individual endpoint tests
- Full pipeline tests
- Health checks
- Comprehensive test suite

### 4. File Inspector (`file_inspector.py`)
Monitors and analyzes files in local backups:
- Real-time file monitoring
- Media metadata extraction (duration, resolution, codec)
- File statistics
- Search by Airtable record ID
- Export detailed reports

## Setup

1. **Install Dependencies**:
```bash
pip install watchdog  # For file monitoring
```

2. **Configure Environment**:
```bash
# .env file
LOCAL_BACKUP_PATH=./local_backups
TEST_BASE_URL=http://localhost:5000  # or your API URL

# Required API keys
AIRTABLE_API_KEY=your_key
AIRTABLE_BASE_ID=your_base_id
NCA_API_KEY=your_key
ELEVENLABS_API_KEY=your_key
GOAPI_API_KEY=your_key
OPENAI_API_KEY=your_key
```

3. **Update Sample IDs**:
Edit `sample_payloads.py` and replace the sample Airtable record IDs with real ones:
```python
SAMPLE_VIDEO_ID = "recXXXXXXXXXXXXXX"  # Real Video record
SAMPLE_SEGMENT_ID = "recYYYYYYYYYYYYYY"  # Real Segment record
```

## Usage

### Running Tests

1. **Run All Tests**:
```bash
python testing_environment/run_tests.py
```

2. **Run Specific Test**:
```bash
# Test only voiceover generation
python testing_environment/run_tests.py --test voiceover

# Test with specific segment ID
python testing_environment/run_tests.py --test voiceover --segment-id recABC123

# Test against production
python testing_environment/run_tests.py --url https://youtube-video-engine.fly.dev
```

3. **Available Tests**:
- `health`: Health check only
- `voiceover`: Voiceover generation
- `image`: AI image generation
- `combine`: Video combination
- `pipeline`: Full production pipeline
- `all`: Run all tests

### Inspecting Files

1. **Scan Existing Files**:
```bash
python testing_environment/file_inspector.py
```

2. **Watch for New Files** (real-time monitoring):
```bash
python testing_environment/file_inspector.py --watch
```

3. **Find Files by Record ID**:
```bash
python testing_environment/file_inspector.py --find recABC123
```

4. **Export Detailed Report**:
```bash
python testing_environment/file_inspector.py --export
```

## Testing Workflow

### 1. Basic Endpoint Test
```python
# Test voiceover generation
python testing_environment/run_tests.py --test voiceover --segment-id recYourSegmentID
```

The test will:
1. Send request to `/api/v2/generate-voiceover`
2. Wait for voiceover file in `local_backups/youtube-video-engine/voiceovers/`
3. Validate file exists and has valid MP3 format
4. Show file size and duration

### 2. Monitor Files in Real-Time
In a separate terminal:
```bash
python testing_environment/file_inspector.py --watch
```

This will show:
- New files as they're created
- File metadata (size, duration, resolution)
- Extracted Airtable record IDs
- Running statistics

### 3. Full Pipeline Test
```python
# Test complete video production
python testing_environment/run_tests.py --test pipeline
```

This tests:
1. Script processing → Creates segments
2. Voiceover generation → MP3 files
3. AI image generation → PNG files
4. Video combination → MP4 files

### 4. Async Webhook Testing
For endpoints that use webhooks (NCA, GoAPI):

```python
# The test framework automatically simulates webhooks
# You'll see output like:
# ✅ Combination job started
#   Job ID: recJobID123
#   Simulating webhook callback...
#   ✅ Webhook processed successfully
#   📁 Combined video saved: segment_combined.mp4
```

## Validation

The testing environment validates:

1. **API Response**:
   - Correct status codes (200, 201, 202)
   - Expected response structure
   - Job IDs for async operations

2. **File Presence**:
   - Files appear in correct subdirectories
   - Filenames contain expected IDs
   - Files created within timeout period

3. **File Content**:
   - Valid file format (MP3, MP4, PNG)
   - Non-zero file size
   - Media duration (for audio/video)
   - Video resolution
   - MD5 checksum

4. **Airtable Updates**:
   - Records updated with file URLs
   - Status fields set correctly
   - Job completion tracking

## Troubleshooting

1. **Files Not Appearing**:
   - Check `LOCAL_BACKUP_PATH` is configured
   - Ensure write permissions on backup directory
   - Verify API is running and accessible

2. **Validation Failures**:
   - Install `ffprobe` for media validation: `brew install ffmpeg`
   - Check file permissions
   - Verify external services are configured

3. **Webhook Issues**:
   - For local testing, webhooks are simulated
   - For production testing, ensure webhook URLs are accessible
   - Check job polling is enabled as fallback

## Example Output

```
🏥 Testing Health Check...
✅ API is healthy
  ✅ airtable: connected
  ✅ elevenlabs: connected
  ✅ nca_toolkit: connected

🎤 Testing Voiceover Generation...
✅ Voiceover generated successfully
  📁 File: recABC123_voiceover.mp3
  📏 Size: 245,832 bytes
  ⏱️  Duration: 15.3 seconds

Test Summary
============
✅ PASS - Health Check
✅ PASS - Voiceover Generation
✅ PASS - AI Image Generation
✅ PASS - Video Combination

Overall: 4/4 tests passed
```