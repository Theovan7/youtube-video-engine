#!/usr/bin/env python3
"""
Local file receiver service that accepts file uploads from production.
Run this on your local machine to receive files from the production server.
"""

from flask import Flask, request, jsonify
import os
import hashlib
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
LOCAL_BACKUP_PATH = os.getenv('LOCAL_BACKUP_PATH', './local_backups')
UPLOAD_SECRET = os.getenv('LOCAL_UPLOAD_SECRET', 'change_this_secret_key')
PORT = int(os.getenv('LOCAL_RECEIVER_PORT', '8181'))

def verify_auth(request):
    """Verify the upload is authorized."""
    auth_header = request.headers.get('X-Upload-Secret')
    return auth_header == UPLOAD_SECRET

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    """Receive file upload from production."""
    # Verify authentication
    if not verify_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get file data
    file_data = request.files.get('file')
    if not file_data:
        return jsonify({'error': 'No file provided'}), 400
    
    # Get metadata
    file_type = request.form.get('file_type', 'unknown')  # voiceovers, videos, music, images
    original_path = request.form.get('original_path', '')
    filename = request.form.get('filename', file_data.filename)
    
    # Construct local path maintaining structure
    if file_type == 'unknown' and original_path:
        # Extract type from original path if not provided
        if 'voiceover' in original_path.lower():
            file_type = 'voiceovers'
        elif 'video' in original_path.lower():
            file_type = 'videos'
        elif 'music' in original_path.lower():
            file_type = 'music'
        elif 'image' in original_path.lower() or '.png' in original_path.lower():
            file_type = 'images'
    
    # Create directory structure
    local_dir = os.path.join(LOCAL_BACKUP_PATH, 'youtube-video-engine', file_type)
    os.makedirs(local_dir, exist_ok=True)
    
    # Save file
    local_path = os.path.join(local_dir, filename)
    file_data.save(local_path)
    
    # Calculate checksum
    with open(local_path, 'rb') as f:
        checksum = hashlib.md5(f.read()).hexdigest()
    
    print(f"✓ Received {file_type}: {filename} ({os.path.getsize(local_path):,} bytes)")
    
    return jsonify({
        'status': 'success',
        'local_path': local_path,
        'checksum': checksum,
        'size': os.path.getsize(local_path)
    })

@app.route('/upload/batch', methods=['POST'])
def upload_batch():
    """Receive multiple files in one request."""
    if not verify_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    
    results = []
    for key in request.files:
        file_data = request.files[key]
        file_type = request.form.get(f'{key}_type', 'unknown')
        filename = request.form.get(f'{key}_filename', file_data.filename)
        
        # Save file
        local_dir = os.path.join(LOCAL_BACKUP_PATH, 'youtube-video-engine', file_type)
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, filename)
        file_data.save(local_path)
        
        results.append({
            'filename': filename,
            'type': file_type,
            'size': os.path.getsize(local_path)
        })
        
        print(f"✓ Received {file_type}: {filename}")
    
    return jsonify({
        'status': 'success',
        'files': results
    })

if __name__ == '__main__':
    print(f"""
Local File Receiver Service
===========================
Listening on: http://localhost:{PORT}
Backup path: {LOCAL_BACKUP_PATH}

Make sure to:
1. Set LOCAL_UPLOAD_SECRET in .env (same on both local and production)
2. Configure your router/firewall to allow incoming connections
3. Set LOCAL_RECEIVER_URL in production .env (e.g., http://your-ip:8181)

Press Ctrl+C to stop
""")
    app.run(host='0.0.0.0', port=PORT, debug=True)