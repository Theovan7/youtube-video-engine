# Remote Backup Setup - Production to Local Machine

This guide explains how to set up automatic file backup from production to your local machine.

## Overview

When configured, the production server will automatically send copies of all generated files to your local machine as they're created. Files are organized by type:
- `voiceovers/` - AI-generated voiceovers
- `videos/` - Combined and processed videos  
- `music/` - Background music
- `images/` - AI-generated images

## Setup Instructions

### Step 1: Configure Your Local Machine

1. **Find your local IP address:**
   ```bash
   # On Mac:
   ifconfig | grep "inet " | grep -v 127.0.0.1
   
   # On Windows:
   ipconfig
   ```
   Look for your local network IP (usually starts with 192.168.x.x or 10.x.x.x)

2. **Update your local .env file:**
   ```bash
   # Remote Backup Configuration
   LOCAL_RECEIVER_URL=http://YOUR_IP:8181  # Don't use this line locally
   LOCAL_UPLOAD_SECRET=your_secure_secret_key_here_123
   LOCAL_RECEIVER_PORT=8181
   ```

3. **Start the local receiver service:**
   ```bash
   python local_file_receiver.py
   ```
   
   You should see:
   ```
   Local File Receiver Service
   ===========================
   Listening on: http://0.0.0.0:8181
   ```

### Step 2: Configure Production

1. **Set production environment variables on Fly.io:**
   ```bash
   # Set your local machine's IP and the shared secret
   fly secrets set LOCAL_RECEIVER_URL="http://YOUR_IP:8181" LOCAL_UPLOAD_SECRET="your_secure_secret_key_here_123"
   ```

2. **Deploy the updated code:**
   ```bash
   fly deploy
   ```

### Step 3: Network Configuration

**Important:** For production to reach your local machine, you need one of these options:

#### Option A: Port Forwarding (Home Network)
1. Access your router's admin panel
2. Forward port 8181 to your local machine's IP
3. Use your public IP in LOCAL_RECEIVER_URL

#### Option B: Ngrok Tunnel (Easier, Temporary)
1. Install ngrok: `brew install ngrok` (Mac) or download from ngrok.com
2. Run: `ngrok http 8181`
3. Use the ngrok URL (e.g., `https://abc123.ngrok.io`) as LOCAL_RECEIVER_URL

#### Option C: VPN/Tailscale (Most Secure)
1. Set up Tailscale on both machines
2. Use your Tailscale IP address

## Testing

1. With the local receiver running, test from another terminal:
   ```bash
   curl -X GET http://localhost:8181/health
   ```

2. Generate a voiceover in production and watch the local receiver logs

## File Organization

Files are automatically organized by type:
```
./local_backups/
└── youtube-video-engine/
    ├── voiceovers/     # ElevenLabs voiceovers
    ├── videos/         # Combined videos from NCA
    ├── music/          # AI-generated music
    └── images/         # AI-generated images
```

## Security Notes

1. **Always use a strong LOCAL_UPLOAD_SECRET** - This prevents unauthorized uploads
2. **Consider IP whitelisting** in your firewall
3. **Use HTTPS with ngrok** for encrypted transfer
4. **Monitor the receiver logs** for any suspicious activity

## Troubleshooting

1. **"Connection refused" error:**
   - Check firewall settings
   - Verify the IP address is correct
   - Ensure local receiver is running

2. **"Unauthorized" error:**
   - Verify LOCAL_UPLOAD_SECRET matches on both sides

3. **Files not appearing:**
   - Check the local receiver console for errors
   - Verify LOCAL_RECEIVER_URL is set in production
   - Check production logs: `fly logs`

## API Changes

The `upload_file` method now accepts a `file_type` parameter:
```python
nca.upload_file(
    file_data=audio_data,
    filename="voiceover.mp3",
    content_type="audio/mpeg",
    file_type="voiceovers"  # Optional, auto-detected if not provided
)
```

Supported file types:
- `voiceovers` - Audio files
- `videos` - Video files
- `music` - Background music
- `images` - Image files