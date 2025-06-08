#!/bin/bash
# Startup script for production with Tailscale support

echo "Starting YouTube Video Engine with Tailscale support..."

# Start Tailscale if auth key is provided
if [ ! -z "$TAILSCALE_AUTHKEY" ]; then
    echo "Starting Tailscale daemon..."
    # Start tailscaled in background
    /usr/sbin/tailscaled --tun=userspace-networking --socks5-server=localhost:1055 &
    
    # Wait for tailscaled to start
    sleep 2
    
    echo "Connecting to Tailscale network..."
    # Connect using auth key
    tailscale up --authkey="$TAILSCALE_AUTHKEY" --hostname="youtube-video-engine-prod"
    
    # Show connection status
    echo "Tailscale status:"
    tailscale status
    
    # Get our Tailscale IP
    TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "Not connected")
    echo "Production Tailscale IP: $TAILSCALE_IP"
else
    echo "TAILSCALE_AUTHKEY not set, skipping Tailscale setup"
fi

# Start the main application
echo "Starting Gunicorn..."
exec gunicorn --config gunicorn.conf.py app:app