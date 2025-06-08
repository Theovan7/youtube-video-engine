# Tailscale Setup for Production → Local Machine File Backup

## Step 1: Set up Tailscale on Your Mac

Run these commands in your terminal:

```bash
# 1. Connect to Tailscale (this will open a browser for authentication)
tailscale up

# 2. Get your Tailscale IP address (save this!)
tailscale ip -4
```

Your Tailscale IP will look like: `100.x.x.x`

## Step 2: Get a Tailscale Auth Key for Production

1. Go to: https://login.tailscale.com/admin/settings/keys
2. Click "Generate auth key"
3. Settings for the key:
   - ✅ Reusable: Yes (so it survives redeploys)
   - ✅ Ephemeral: No
   - Expiration: 90 days (or longer)
   - Tags: Leave empty
4. Copy the key (starts with `tskey-auth-...`)

## Step 3: Set Fly.io Secrets

```bash
# Set the Tailscale auth key
fly secrets set TAILSCALE_AUTHKEY="tskey-auth-YOUR_KEY_HERE"

# Set your local machine's Tailscale IP and upload secret
fly secrets set LOCAL_RECEIVER_URL="http://100.x.x.x:8181" \
                LOCAL_UPLOAD_SECRET="your_secret_key_here_123"
```

Replace `100.x.x.x` with your actual Tailscale IP from Step 1.

## Step 4: Deploy with Tailscale Support

The updated Dockerfile and startup script are ready. Just deploy:

```bash
fly deploy
```

## Step 5: Start Your Local Receiver

On your Mac, start the receiver:

```bash
python local_file_receiver.py
```

## Testing

1. Generate a voiceover in production
2. Watch your local receiver console - you should see:
   ```
   ✓ Received voiceovers: 20250608_xxxxx_voiceover_recXXX.mp3 (91,996 bytes)
   ```

## How It Works

1. Production container starts and connects to Tailscale using the auth key
2. Production gets its own Tailscale IP (e.g., 100.64.1.8)
3. When files are generated, production sends them to your Mac's Tailscale IP
4. Your Mac receives files even though it's behind your home router
5. All traffic is encrypted end-to-end

## Troubleshooting

- **Can't connect to Tailscale on Mac**: Try `brew services restart tailscale`
- **Production can't reach Mac**: Check `fly ssh console -a youtube-video-engine` then `tailscale status`
- **Files not appearing**: Check production logs with `fly logs`

## Network Diagram

```
[Production on Fly.io]          [Your Mac at Home]
    100.64.1.8        <----->      100.64.1.5
         |                              |
         |    Encrypted Tailscale      |
         |         Connection          |
         |                              |
    Sends files -----------------> Receives files
                                   on port 8181
```