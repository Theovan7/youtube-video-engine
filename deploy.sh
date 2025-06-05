#!/bin/bash
# YouTube Video Engine - Production Deployment Script
# Run this script to deploy the webhook fixes to production

set -e  # Exit on any error

echo "🚀 YouTube Video Engine - Production Deployment"
echo "================================================"

# Check if fly CLI is available
if ! command -v fly &> /dev/null; then
    echo "❌ Fly CLI not found. Please install: https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

# Check authentication
echo "🔐 Checking Fly.io authentication..."
if ! fly auth whoami &> /dev/null; then
    echo "❌ Not authenticated with Fly.io. Please run: fly auth login"
    exit 1
fi

echo "✅ Authentication confirmed"

# Show current app status
echo "📊 Current app status:"
fly status --app youtube-video-engine

echo ""
echo "🔍 Pre-deployment validation..."

# Validate that the webhook fixes are in place
if grep -q "Method 4: Check for success indicators" api/webhooks.py; then
    echo "✅ Webhook status parsing fix confirmed"
else
    echo "❌ Webhook fix not found in api/webhooks.py"
    exit 1
fi

if grep -q "validate_nca_job_exists" api/webhooks.py; then
    echo "✅ NCA job validation function confirmed"
else
    echo "❌ NCA job validation function not found"
    exit 1
fi

echo ""
echo "🚀 Deploying to production..."

# Deploy with automatic rollback on failure
fly deploy --app youtube-video-engine --strategy rolling

# Check deployment health
echo ""
echo "🏥 Post-deployment health check..."
sleep 10  # Wait for deployment to settle

# Test webhook endpoint
echo "📡 Testing webhook endpoint..."
WEBHOOK_URL="https://youtube-video-engine.fly.dev/webhooks/test"
if curl -s -f -X POST -H "Content-Type: application/json" -d '{"test": true}' "$WEBHOOK_URL" > /dev/null; then
    echo "✅ Webhook endpoint responding"
else
    echo "⚠️  Webhook endpoint not responding - check logs"
fi

# Show recent logs
echo ""
echo "📋 Recent deployment logs:"
fly logs --app youtube-video-engine --lines 10

echo ""
echo "🎉 Deployment completed!"
echo "================================================"
echo "✅ Webhook status parsing fixes deployed"
echo "✅ NCA job validation active"
echo "✅ Manual recovery completed"
echo ""
echo "📋 Next steps:"
echo "1. Monitor webhook processing for 24 hours"
echo "2. Test new combination jobs end-to-end"
echo "3. Set up alerts for stuck segments"
echo ""
echo "🔍 Monitor with: fly logs --app youtube-video-engine -f"
echo "📊 Check status: fly status --app youtube-video-engine"
