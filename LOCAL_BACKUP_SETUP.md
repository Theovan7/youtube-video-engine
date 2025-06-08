# Local Backup Configuration

This document explains how to enable local backup of files that are uploaded to DigitalOcean Spaces.

## Overview

When enabled, the system will save a copy of every file uploaded to DigitalOcean Spaces to a local directory on the server. This provides:
- Local backup of all uploaded files
- Faster access for debugging
- Redundancy in case of cloud storage issues

## Configuration

### Enable Local Backup

Add the following environment variable to your `.env` file:

```bash
LOCAL_BACKUP_PATH=/path/to/your/backup/folder
```

For example:
```bash
LOCAL_BACKUP_PATH=/home/user/youtube-video-backups
```

If not set, it defaults to `./local_backups` in the project directory.

### Directory Structure

Files are saved with the same structure as in DigitalOcean Spaces:

```
LOCAL_BACKUP_PATH/
└── youtube-video-engine/
    ├── voiceovers/      # AI-generated voiceovers
    ├── videos/          # Combined videos (if implemented)
    └── music/           # Background music (if implemented)
```

## How It Works

1. When a file is uploaded via `NCAService.upload_file()`, it:
   - Uploads to DigitalOcean Spaces as usual
   - If `LOCAL_BACKUP_PATH` is configured, saves a copy locally
   - Returns both the remote URL and local path (if saved)

2. File naming remains consistent:
   - Format: `{timestamp}_{unique_id}_{original_filename}`
   - Example: `20250607_160620_f58e76b1_voiceover_recXYZ.mp3`

## Testing

Run the test script to verify the functionality:

```bash
python test_local_backup.py
```

This will:
- Upload a test file to DigitalOcean Spaces
- Save a local copy if configured
- Verify the local file matches the uploaded content

## Important Notes

1. **Disk Space**: Monitor available disk space when enabling local backups
2. **Permissions**: Ensure the application has write permissions to the backup directory
3. **Cleanup**: Implement a cleanup strategy for old files to prevent disk usage issues

## Example Response

When uploading with local backup enabled:

```python
{
    'url': 'https://phi-bucket.nyc3.digitaloceanspaces.com/youtube-video-engine/voiceovers/...',
    'key': 'youtube-video-engine/voiceovers/20250607_160620_f58e76b1_test.mp3',
    'bucket': 'phi-bucket',
    'local_path': '/home/user/backups/youtube-video-engine/voiceovers/20250607_160620_f58e76b1_test.mp3'
}
```