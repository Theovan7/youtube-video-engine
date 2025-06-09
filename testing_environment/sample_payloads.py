"""
Sample payloads for testing different API endpoints
"""

# Sample Airtable record IDs (you'll need to replace with real ones)
SAMPLE_VIDEO_ID = "recXXXXXXXXXXXXXX"  # Replace with actual Video record ID
SAMPLE_SEGMENT_ID = "recYYYYYYYYYYYYYY"  # Replace with actual Segment record ID
SAMPLE_JOB_ID = "recZZZZZZZZZZZZZZ"  # Replace with actual Job record ID

# Voice IDs from ElevenLabs
VOICE_IDS = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",
    "domi": "AZnzlk1XvdvUeBnXmlld",
    "bella": "EXAVITQu4vr4xnSDxMaL",
    "antoni": "ErXwobaYiN019PkySvjV",
    "josh": "TxGEqnHWrfWFTfGW9XjX"
}

# Sample Scripts
SAMPLE_SCRIPTS = {
    "short": """Welcome to our test video.
This is a simple test of the video engine.
Thank you for watching.""",
    
    "medium": """Welcome to our comprehensive demonstration of automated video production.

In this first segment, we'll explore the basics of AI-powered content creation.

Moving to segment two, we dive deeper into the technical aspects of voice synthesis.

In our third segment, we examine how visual elements are generated and combined.

Finally, we'll conclude with a look at the future of automated video production.

Thank you for joining us on this journey through modern content creation.""",
    
    "dramatic": """In a world where content is king...

One platform dares to revolutionize video creation.

Artificial intelligence meets creative expression.

The future of storytelling begins now.

This is the YouTube Video Engine."""
}

# API Endpoint Payloads
PAYLOADS = {
    # Script Processing (V1)
    "process_script_v1": {
        "script_text": SAMPLE_SCRIPTS["medium"],
        "video_name": "Test Video - {timestamp}",
        "target_segment_duration": 30
    },
    
    # Script Processing (V2) - with Airtable record
    "process_script_v2": {
        "record_id": SAMPLE_VIDEO_ID  # Requires existing Video record in Airtable
    },
    
    # Voiceover Generation (V1)
    "generate_voiceover_v1": {
        "segment_id": SAMPLE_SEGMENT_ID,
        "voice_id": VOICE_IDS["rachel"],
        "stability": 0.5,
        "similarity_boost": 0.5,
        "style": 0.0,
        "use_speaker_boost": True
    },
    
    # Voiceover Generation (V2) - Direct from segment record
    "generate_voiceover_v2": {
        "record_id": SAMPLE_SEGMENT_ID  # Segment must have voice_id set
    },
    
    # AI Image Generation
    "generate_ai_image": {
        "record_id": SAMPLE_SEGMENT_ID,
        "style": "photorealistic",  # or "artistic", "cartoon", "abstract"
        "aspect_ratio": "16:9",
        "quality": "high"
    },
    
    # Video Generation from Image
    "generate_video": {
        "record_id": SAMPLE_SEGMENT_ID,
        "video_style": "zoom",  # or "kling" for different providers
        "duration": 5,  # seconds
        "zoom_speed": 0.5,  # For zoom style
        "camera_control": {  # For kling style
            "type": "zoom",
            "value": "in"
        }
    },
    
    # Combine Segment Media (voiceover + video)
    "combine_segment_media": {
        "segment_id": SAMPLE_SEGMENT_ID,
        "transition_type": "fade",
        "transition_duration": 0.5
    },
    
    # Combine All Segments
    "combine_all_segments": {
        "video_id": SAMPLE_VIDEO_ID,
        "include_transitions": True,
        "transition_duration": 0.5
    },
    
    # Generate and Add Music
    "generate_and_add_music": {
        "video_id": SAMPLE_VIDEO_ID,
        "music_prompt": "upbeat corporate background music",
        "music_duration": 120,  # seconds
        "music_volume": 0.3  # 30% volume
    },
    
    # Job Status Check
    "check_job_status": {
        "job_id": SAMPLE_JOB_ID
    }
}

# Webhook Callback Payloads (for testing)
WEBHOOK_PAYLOADS = {
    # NCA Toolkit Success Callback
    "nca_success": {
        "id": SAMPLE_JOB_ID,
        "job_id": "nca-1234567890",
        "code": 200,
        "response": {
            "url": "https://phi-bucket.nyc3.digitaloceanspaces.com/youtube-video-engine/videos/test_output.mp4",
            "duration": 30.5,
            "size": 5242880
        }
    },
    
    # NCA Toolkit Failure Callback
    "nca_failure": {
        "id": SAMPLE_JOB_ID,
        "job_id": "nca-1234567890",
        "code": 500,
        "response": {
            "error": "FFmpeg processing failed: Invalid input format"
        }
    },
    
    # GoAPI Music Generation Success
    "goapi_music_success": {
        "data": {
            "id": SAMPLE_JOB_ID,
            "task": "musicgen",
            "status": "completed",
            "music_result": {
                "audio_url": "https://example.com/generated_music.mp3",
                "duration": 120
            }
        }
    },
    
    # GoAPI Video Generation Success
    "goapi_video_success": {
        "data": {
            "id": SAMPLE_JOB_ID,
            "task": "kling",
            "status": "completed",
            "video_result": {
                "video_url": "https://example.com/generated_video.mp4",
                "duration": 5,
                "resolution": "1920x1080"
            }
        }
    }
}

# Test Scenarios
TEST_SCENARIOS = {
    "basic_voiceover": {
        "name": "Basic Voiceover Generation",
        "steps": [
            {
                "endpoint": "/api/v2/generate-voiceover",
                "payload": PAYLOADS["generate_voiceover_v2"],
                "expected_files": [("voiceover", "voiceovers")]
            }
        ]
    },
    
    "full_pipeline": {
        "name": "Full Video Production Pipeline",
        "steps": [
            {
                "name": "Process Script",
                "endpoint": "/api/v2/process-script",
                "payload": PAYLOADS["process_script_v2"],
                "expected_response": ["segments"]
            },
            {
                "name": "Generate Voiceovers",
                "endpoint": "/api/v2/generate-voiceover",
                "payload": "dynamic",  # Will be filled with segment IDs
                "expected_files": [("voiceover", "voiceovers")],
                "repeat_for": "segments"
            },
            {
                "name": "Generate AI Images",
                "endpoint": "/api/v2/generate-ai-image",
                "payload": "dynamic",
                "expected_files": [("image", "images")],
                "repeat_for": "segments"
            },
            {
                "name": "Generate Videos",
                "endpoint": "/api/v2/generate-video",
                "payload": "dynamic",
                "async": True,
                "webhook": "nca",
                "expected_files": [("video", "videos")],
                "repeat_for": "segments"
            },
            {
                "name": "Combine Segments",
                "endpoint": "/api/v2/combine-segment-media",
                "payload": "dynamic",
                "async": True,
                "webhook": "nca",
                "expected_files": [("combined", "videos")],
                "repeat_for": "segments"
            },
            {
                "name": "Concatenate All",
                "endpoint": "/api/v2/combine-all-segments",
                "payload": "dynamic",
                "async": True,
                "webhook": "nca",
                "expected_files": [("final", "videos")]
            },
            {
                "name": "Add Music",
                "endpoint": "/api/v2/generate-and-add-music",
                "payload": "dynamic",
                "async": True,
                "webhook": "goapi",
                "expected_files": [("music", "music"), ("final_with_music", "videos")]
            }
        ]
    }
}

def get_payload_with_timestamp(payload_key: str) -> dict:
    """Get a payload with timestamp inserted where needed"""
    import copy
    from datetime import datetime
    
    payload = copy.deepcopy(PAYLOADS[payload_key])
    
    # Replace timestamp placeholders
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if "video_name" in payload:
        payload["video_name"] = payload["video_name"].format(timestamp=timestamp)
        
    return payload