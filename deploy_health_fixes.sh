#!/bin/bash
# YouTube Video Engine - FIXED Health Check Deployment Script
# This script contains all the fixes for the intermittent health check failures

set -e  # Exit on any error

echo "🚀 YouTube Video Engine - HEALTH CHECK FIXES DEPLOYMENT"
echo "========================================================="

echo "🔧 FIXES APPLIED:"
echo "✅ Added fast /health/basic endpoint for Fly.io health checks"
echo "✅ Increased memory allocation from 512MB to 1024MB"
echo "✅ Reduced gunicorn workers from 4 to 2 (better for 1GB memory)"
echo "✅ Fixed configuration mismatches between Dockerfile and fly.toml"
echo "✅ Increased health check timeouts from 2s to 10s"
echo "✅ Increased connection limits for better performance"
echo "✅ Changed health check interval from 10s to 30s"
echo "✅ Removed conflicting Dockerfile HEALTHCHECK"
echo ""

# Check if fly CLI is available
if ! command -v fly &> /dev/null; then
    echo "❌ Fly CLI not found. Please install: https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

# Check authentication with timeout
echo "🔐 Checking Fly.io authentication..."
if timeout 10s fly auth whoami &> /dev/null; then
    echo "✅ Authentication confirmed"
else
    echo "❌ Authentication failed or timed out. Please run: fly auth login"
    echo "   If this persists, there may be network connectivity issues."
    echo "   Try again later or from a different network."
    exit 1
fi

# Show current app status with timeout
echo "📊 Checking current app status..."
if timeout 15s fly status --app youtube-video-engine; then
    echo "✅ App status retrieved"
else
    echo "⚠️  Could not retrieve app status (likely network issue)"
    echo "   Proceeding with deployment anyway..."
fi

echo ""
echo "🔍 Pre-deployment validation..."

# Validate that the health check fixes are in place
if grep -q "/health/basic" app.py; then
    echo "✅ Basic health check endpoint confirmed"
else
    echo "❌ Basic health check endpoint not found in app.py"
    exit 1
fi

if grep -q "memory_mb = 1024" fly.toml; then
    echo "✅ Memory increase to 1024MB confirmed"
else
    echo "❌ Memory increase not found in fly.toml"
    exit 1
fi

if grep -q "workers 2" fly.toml; then
    echo "✅ Worker count reduction to 2 confirmed"
else
    echo "❌ Worker count reduction not found in fly.toml"
    exit 1
fi

echo ""
echo "🚀 Deploying health check fixes to production..."

# Deploy with timeout and better error handling
if timeout 300s fly deploy --app youtube-video-engine --strategy rolling; then
    echo ""
    echo "🎉 Deployment completed successfully!"
    
    # Wait for deployment to settle
    echo "⏳ Waiting for deployment to settle..."
    sleep 20
    
    # Test the new basic health endpoint
    echo "🏥 Testing new basic health endpoint..."
    if curl -s -f https://youtube-video-engine.fly.dev/health/basic > /dev/null; then
        echo "✅ Basic health check endpoint responding"
    else
        echo "⚠️  Basic health check endpoint not yet responding"
        echo "   This may be normal during deployment transition"
    fi
    
    # Test the comprehensive health endpoint
    echo "🔍 Testing comprehensive health endpoint..."
    if curl -s -f https://youtube-video-engine.fly.dev/health > /dev/null; then
        echo "✅ Comprehensive health check endpoint responding"
    else
        echo "⚠️  Comprehensive health check endpoint issues"
        echo "   Check logs: fly logs --app youtube-video-engine"
    fi
    
    # Show recent logs
    echo ""
    echo "📋 Recent deployment logs:"
    if timeout 10s fly logs --app youtube-video-engine --lines 10; then
        echo "✅ Logs retrieved"
    else
        echo "⚠️  Could not retrieve logs (network timeout)"
    fi
    
    echo ""
    echo "🎉 HEALTH CHECK FIXES DEPLOYED SUCCESSFULLY!"
    echo "================================================"
    echo "✅ Fast basic health endpoint: /health/basic"
    echo "✅ Increased memory allocation: 1024MB"
    echo "✅ Optimized worker configuration: 2 workers"
    echo "✅ Improved health check timing: 30s interval, 10s timeout"
    echo "✅ Fixed configuration mismatches"
    echo ""
    echo "📋 Monitoring commands:"
    echo "• Health check: curl https://youtube-video-engine.fly.dev/health/basic"
    echo "• Full health: curl https://youtube-video-engine.fly.dev/health"
    echo "• App status: fly status --app youtube-video-engine"
    echo "• Watch logs: fly logs --app youtube-video-engine -f"
    
else
    echo ""
    echo "❌ DEPLOYMENT FAILED"
    echo "==================="
    echo "This could be due to:"
    echo "1. Network connectivity issues with Fly.io"
    echo "2. Authentication problems"
    echo "3. Resource constraints"
    echo ""
    echo "🔧 Troubleshooting steps:"
    echo "1. Check network connectivity: ping api.fly.io"
    echo "2. Re-authenticate: fly auth logout && fly auth login"
    echo "3. Try from different network/location"
    echo "4. Check Fly.io status: https://status.fly.io"
    echo ""
    echo "🚀 Manual deployment option:"
    echo "1. Copy fixed files to a machine with better connectivity"
    echo "2. Run this script from there"
    echo "3. Or use Fly.io dashboard for deployment"
    
    exit 1
fi
