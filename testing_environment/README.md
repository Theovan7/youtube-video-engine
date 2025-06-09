# YouTube Video Engine Testing Framework

A comprehensive testing environment for the YouTube Video Engine API, providing local testing capabilities with automatic file validation and backup inspection.

## Structure

```
testing_environment/
├── test_framework.py      # Core testing utilities
├── sample_payloads.py     # Legacy payload templates
├── run_tests.py          # General test runner
├── test_function.py      # Function-specific test runner
├── test_pipeline.py      # Pipeline orchestrator
├── file_inspector.py     # Local backup file analyzer
├── upload_test_file.py   # S3 upload utility
└── test_inputs/          # Test data organized by function
    ├── process-script/
    ├── generate-voiceover/
    ├── generate-ai-image/
    ├── generate-video/
    ├── combine-segment-media/
    ├── combine-all-segments/
    ├── generate-and-add-music/
    └── webhook-simulations/
```

## Quick Start

### 1. Setup Environment

```bash
# Install dependencies
pip install watchdog requests python-dotenv apscheduler

# Start the Flask application
PORT=5001 python app.py

# Configure environment variables (if not already done)
cp .env.example .env
# Edit .env with your API keys and settings
```

### 2. Test Individual Functions

```bash
# List available functions
python testing_environment/test_function.py --list

# Test script processing
python testing_environment/test_function.py --function process-script

# Test voiceover generation
python testing_environment/test_function.py --function generate-voiceover

# Test with custom payload
python testing_environment/test_function.py \
  --function combine-segment-media \
  --payload test_inputs/combine-segment-media/payloads/basic_combine.json
```

### 3. Run Pipeline Tests

```bash
# Run default pipeline (script → voiceover → combine → final)
python testing_environment/test_pipeline.py

# Run against production
python testing_environment/test_pipeline.py --url https://youtube-video-engine.fly.dev
```

### 4. Monitor Files

```bash
# Watch for new files in local backups
python testing_environment/file_inspector.py --watch

# Inspect existing files
python testing_environment/file_inspector.py

# Find files by Airtable record ID
python testing_environment/file_inspector.py --find recABC123

# Export detailed report
python testing_environment/file_inspector.py --export
```

## Function-Specific Testing

### Process Script
```bash
# Add test scripts to:
test_inputs/process-script/scripts/

# Test with:
python testing_environment/test_function.py --function process-script
```

### Generate Voiceover
```bash
# Requires segment ID from process-script
# Auto-uses saved segment IDs or specify in payload:
test_inputs/generate-voiceover/payloads/custom.json

# Test with:
python testing_environment/test_function.py --function generate-voiceover
```

### Combine Segment Media
```bash
# Add test videos and audio to:
test_inputs/combine-segment-media/test_videos/
test_inputs/combine-segment-media/test_audio/

# Files are auto-uploaded to S3 before testing
python testing_environment/test_function.py --function combine-segment-media
```

## Working with Test Files

### Upload Files to S3
```bash
# Upload single file
python testing_environment/upload_test_file.py \
  test_inputs/combine-segment-media/test_videos/sample.mp4

# Upload with specific type
python testing_environment/upload_test_file.py \
  test_inputs/images/landscape.png --type images

# Upload entire directory
python testing_environment/upload_test_file.py \
  test_inputs/generate-video/source_images --dir --type images
```

### File Organization

Each function has its own folder in `test_inputs/`:

- **Scripts**: Plain text files for script processing
- **Payloads**: JSON files with API request payloads
- **Test Files**: Media files (images, videos, audio) for testing
- **Configs**: Function-specific configurations
- **Expected Outputs**: Reference outputs for validation

## Testing Workflows

### 1. Basic Function Test
1. Add test files to function folder
2. Create/modify payload JSON
3. Run function test
4. Check local backups for output

### 2. End-to-End Pipeline
1. Prepare script in `process-script/scripts/`
2. Run pipeline test
3. Monitor progress with file inspector
4. Review final output in local backups

### 3. Webhook Testing
1. Use webhook simulator for async operations
2. Check `webhook-simulations/` for callback templates
3. Verify webhook processing in logs

## Validation

The testing framework validates:

1. **API Responses**
   - Status codes
   - Response structure
   - Job IDs for async operations

2. **File Generation**
   - Files appear in local backups
   - Correct file types and locations
   - Valid media properties (duration, resolution)

3. **Content Validation**
   - Media files are playable
   - Correct durations
   - Proper encoding

## Troubleshooting

### Common Issues

1. **"No segment ID found"**
   - Run process-script test first to generate segments
   - Check `generated_segment_ids.json` in process-script folder

2. **"Files not appearing in local backups"**
   - Ensure `LOCAL_BACKUP_PATH` is set in .env
   - Check folder permissions
   - Verify API is configured for local backups

3. **"Upload failed"**
   - Check S3 credentials in .env
   - Verify internet connection
   - Check file size limits

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python testing_environment/test_function.py --function generate-voiceover
```

## Best Practices

1. **Organize Test Data**: Keep test files in appropriate function folders
2. **Version Payloads**: Save different payload variations for testing
3. **Monitor Outputs**: Use file inspector during tests
4. **Clean Up**: Periodically clean old test files from local backups
5. **Document Tests**: Add comments to payload files explaining test scenarios

## Example Test Session

```bash
# 1. Start file monitor in one terminal
python testing_environment/file_inspector.py --watch

# 2. Run pipeline test in another terminal
python testing_environment/test_pipeline.py

# 3. Check specific outputs
python testing_environment/file_inspector.py --find recABC123

# 4. Generate report
python testing_environment/file_inspector.py --export
```

## Local Backup Location

Files are automatically backed up to:
```
./local_backups/youtube-video-engine/
├── voiceovers/   # MP3 files and AI-generated images  
├── videos/       # Video files
├── music/        # Music files
└── images/       # Image files
```

Example from a successful test:
- File: `./local_backups/youtube-video-engine/voiceovers/20250609_104914_1564c767_voiceover_recmXnXCm5tFVAlFo.mp3`
- Size: 379,551 bytes (370 KB)
- Duration: 23.7 seconds