"""Setup script to create .env file from template."""

import os
import shutil

def setup_env():
    """Setup .env file from template."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    env_example = os.path.join(project_root, '.env.example')
    env_file = os.path.join(project_root, '.env')
    
    # Check if .env already exists
    if os.path.exists(env_file):
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return
    
    # Copy .env.example to .env
    if os.path.exists(env_example):
        shutil.copy(env_example, env_file)
        print(f"Created .env file from template")
        
        print("\nPlease update the following environment variables in .env:")
        print("- AIRTABLE_API_KEY: Your Airtable API key")
        print("- AIRTABLE_BASE_ID: Your Airtable base ID")
        print("- ELEVENLABS_API_KEY: Your ElevenLabs API key")
        print("- GOAPI_API_KEY: Your GoAPI key for music generation")
        print("- WEBHOOK_BASE_URL: Your public URL for webhooks (ngrok for local testing)")
        
        print("\nNote: NCA Toolkit credentials are pre-configured with the free API")
    else:
        print("Error: .env.example not found!")
        print("Creating basic .env file...")
        
        env_content = """# YouTube Video Engine Configuration

# Flask Configuration
SECRET_KEY=your-secret-key-change-in-production
FLASK_ENV=development
FLASK_DEBUG=True

# Airtable Configuration
AIRTABLE_API_KEY=your-airtable-api-key
AIRTABLE_BASE_ID=your-airtable-base-id

# NCA Toolkit Configuration (FREE API)
NCA_API_KEY=K2_JVFN!csh&i1248
NCA_BASE_URL=https://no-code-architect-app-gpxhq.ondigitalocean.app
NCA_S3_BUCKET_NAME=phi-bucket
NCA_S3_ENDPOINT_URL=https://phi-bucket.nyc3.digitaloceanspaces.com
NCA_S3_ACCESS_KEY=DO00BM6DUUHUETVKRM6G
NCA_S3_SECRET_KEY=UpjohyN2x+cl8CAhJfpuwDNsMgxGqCz70CUwNcoD+x4
NCA_S3_REGION=nyc3

# ElevenLabs Configuration
ELEVENLABS_API_KEY=your-elevenlabs-api-key

# GoAPI Configuration
GOAPI_API_KEY=your-goapi-key

# Application Configuration
WEBHOOK_BASE_URL=http://localhost:5000
LOG_LEVEL=INFO

# Rate Limiting
RATELIMIT_STORAGE_URL=memory://
RATELIMIT_DEFAULT=100 per hour
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("Created basic .env file")
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env and add your API keys")
    print("2. Set up Airtable base with required tables")
    print("3. Run 'python app.py' to start the server")
    print("4. Use ngrok for webhook testing: 'ngrok http 5000'")


if __name__ == "__main__":
    setup_env()
