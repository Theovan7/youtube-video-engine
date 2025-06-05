# DigitalOcean Spaces Setup for YouTube Video Engine

## 🚨 URGENT: Create Isolated Bucket

### Step 1: Create the Bucket

1. **Log in to DigitalOcean**: https://cloud.digitalocean.com/

2. **Navigate to Spaces**: Click on "Spaces" in the left sidebar

3. **Create a New Space**:
   - Click "Create Space"
   - **Choose Region**: Select `NYC3` (New York 3) to match existing configuration
   - **Enable CDN**: Optional but recommended for better performance
   - **Space Name**: `youtube-video-engine`
   - **Project**: Select appropriate project or create new one
   - Click "Create a Space"

4. **Configure Space Settings**:
   - Go to Settings tab
   - **File Listing**: Set to "Restricted" (optional, for security)
   - **CORS Configuration**: Add if needed for web access

### Step 2: Update Environment Variables

Add these to your Fly.io secrets:

```bash
# YouTube-specific bucket configuration
fly secrets set YOUTUBE_S3_BUCKET_NAME="youtube-video-engine"
fly secrets set YOUTUBE_S3_VOICEOVER_PATH="voiceovers"
fly secrets set YOUTUBE_S3_VIDEO_PATH="videos"
fly secrets set YOUTUBE_S3_MUSIC_PATH="music"

# Keep existing S3 credentials (they work across all spaces)
# NCA_S3_ACCESS_KEY and NCA_S3_SECRET_KEY remain the same
```

### Step 3: Deploy the Updated Code

Once the bucket is created:

```bash
cd /Users/theovandermerwe/Dropbox/CODING2/ClaudeDesktop/ProjectHI/youtube_video_engine
fly deploy --verbose
```

### Step 4: Verify Bucket Structure

After deployment, your bucket will have this structure:
```
youtube-video-engine/
├── voiceovers/     # AI-generated voiceovers
├── videos/         # Combined and processed videos
└── music/          # AI-generated background music
```

## File URL Format

Files will be accessible at:
```
https://youtube-video-engine.nyc3.digitaloceanspaces.com/voiceovers/[timestamp]_[uuid]_[filename]
```

## Benefits of Isolated Bucket

1. **Separation of Concerns**: YouTube Video Engine files are isolated from other projects
2. **Better Organization**: Clear folder structure for different media types
3. **Access Control**: Can implement bucket-specific policies if needed
4. **Cost Tracking**: Easier to monitor storage and bandwidth costs per project
5. **Backup/Migration**: Simpler to backup or migrate a single project

## Testing After Setup

Test the voiceover generation with the new bucket:

```bash
curl -X POST https://youtube-video-engine.fly.dev/api/v2/generate-voiceover \
  -H "Content-Type: application/json" \
  -d '{"record_id": "recdRdKs6y9dyf609"}'
```

Success response should include a URL like:
```json
{
  "voiceover_url": "https://youtube-video-engine.nyc3.digitaloceanspaces.com/voiceovers/20250527_210000_a1b2c3d4_voiceover_recdRdKs6y9dyf609.mp3"
}
```

## Important Notes

- The same S3 access keys work across all DigitalOcean Spaces in your account
- The bucket must be created before deployment
- Files are set to `public-read` by default - adjust if needed
- Consider setting up lifecycle rules for old files to manage costs
