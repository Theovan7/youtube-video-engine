# Test Input Files - Organized by Function

This folder contains test input files organized by API endpoint/function for testing the YouTube Video Engine.

## Folder Structure by Function

```
test_inputs/
├── process-script/           # Script processing endpoint inputs
├── generate-voiceover/       # Voiceover generation test data
├── generate-ai-image/        # AI image generation inputs
├── generate-video/           # Video generation from images
├── combine-segment-media/    # Combining voiceover + video
├── combine-all-segments/     # Concatenating multiple videos
├── generate-and-add-music/   # Music generation and mixing
└── webhook-simulations/      # Webhook callback test payloads
```

## Function-Specific Test Files

### 1. process-script/
**Endpoint**: `/api/v1/process-script` and `/api/v2/process-script`

```
process-script/
├── scripts/
│   ├── short_demo.txt          # 30-second demo script
│   ├── product_launch.txt      # Product announcement
│   ├── tutorial.txt            # How-to video script
│   └── story_narrative.txt     # Story-based content
├── payloads/
│   ├── basic_script.json       # Basic script processing payload
│   ├── with_segments.json      # Script with custom segmentation
│   └── with_markup.json        # Script with timing markup
└── expected_outputs/
    └── segment_structure.json   # Expected segment output format
```

### 2. generate-voiceover/
**Endpoint**: `/api/v2/generate-voiceover`

```
generate-voiceover/
├── text_samples/
│   ├── short_segment.txt       # Single segment text
│   ├── long_segment.txt        # Longer voiceover text
│   └── multilingual.txt        # Text with special characters
├── voice_configs/
│   ├── rachel_config.json      # Rachel voice settings
│   ├── josh_config.json        # Josh voice settings
│   └── custom_voice.json       # Custom voice parameters
└── payloads/
    ├── basic_voiceover.json    # Standard voiceover request
    └── with_settings.json      # Advanced voice settings
```

### 3. generate-ai-image/
**Endpoint**: `/api/v2/generate-ai-image`

```
generate-ai-image/
├── prompts/
│   ├── landscape_prompt.txt    # Nature/landscape prompt
│   ├── product_prompt.txt      # Product visualization
│   └── abstract_prompt.txt     # Abstract art prompt
├── styles/
│   ├── photorealistic.json     # Photorealistic style config
│   ├── artistic.json           # Artistic style config
│   └── cartoon.json            # Cartoon style config
└── payloads/
    └── image_generation.json   # Image generation payload
```

### 4. generate-video/
**Endpoint**: `/api/v2/generate-video`

```
generate-video/
├── source_images/
│   ├── landscape.png           # For zoom effect testing
│   ├── product.jpg             # Product showcase
│   └── portrait.png            # Portrait orientation
├── video_configs/
│   ├── zoom_effect.json        # Zoom video settings
│   ├── kling_settings.json     # Kling AI settings
│   └── camera_controls.json    # Camera movement configs
└── payloads/
    ├── zoom_video.json         # Zoom style generation
    └── kling_video.json        # Kling style generation
```

### 5. combine-segment-media/
**Endpoint**: `/api/v2/combine-segment-media`

```
combine-segment-media/
├── test_videos/
│   ├── silent_5s.mp4           # 5-second silent video
│   ├── silent_30s.mp4          # 30-second silent video
│   └── with_audio.mp4          # Video with existing audio
├── test_audio/
│   ├── voiceover_5s.mp3        # 5-second voiceover
│   ├── voiceover_30s.mp3       # 30-second voiceover
│   └── voiceover_60s.mp3       # 60-second voiceover
└── payloads/
    ├── basic_combine.json      # Basic combination
    └── with_transitions.json   # With transition effects
```

### 6. combine-all-segments/
**Endpoint**: `/api/v2/combine-all-segments`

```
combine-all-segments/
├── segment_videos/
│   ├── segment_1.mp4           # First segment
│   ├── segment_2.mp4           # Second segment
│   └── segment_3.mp4           # Third segment
├── concatenation_configs/
│   └── transition_settings.json # Transition configurations
└── payloads/
    └── concatenate_all.json    # Concatenation payload
```

### 7. generate-and-add-music/
**Endpoint**: `/api/v2/generate-and-add-music`

```
generate-and-add-music/
├── test_videos/
│   └── final_video.mp4         # Video to add music to
├── music_samples/
│   ├── background_music.mp3    # Pre-existing music
│   └── ambient_track.mp3       # Ambient background
├── music_prompts/
│   ├── upbeat_corporate.txt    # Corporate music prompt
│   ├── cinematic.txt           # Cinematic music prompt
│   └── relaxing.txt            # Relaxing music prompt
└── payloads/
    ├── generate_music.json     # Music generation payload
    └── add_existing_music.json # Add pre-existing music
```

### 8. webhook-simulations/
**For testing webhook callbacks**

```
webhook-simulations/
├── nca_callbacks/
│   ├── success_combine.json    # Successful combination
│   ├── success_concat.json     # Successful concatenation
│   ├── failed_processing.json  # Failed job callback
│   └── timeout_error.json      # Timeout error callback
├── goapi_callbacks/
│   ├── music_completed.json    # Music generation done
│   ├── video_completed.json    # Video generation done
│   └── task_failed.json        # Task failure callback
└── test_scenarios/
    ├── retry_scenario.json     # Retry after failure
    └── polling_test.json       # Polling fallback test
```

## Usage Instructions

### 1. Preparing Test Files

For each function you want to test:

1. **Add input files** to the appropriate function folder
2. **Create payload JSON files** with test configurations
3. **Upload files to S3** if testing with real URLs:
   ```bash
   python testing_environment/upload_test_file.py \
     test_inputs/combine-segment-media/test_videos/silent_5s.mp4
   ```

### 2. Running Function-Specific Tests

```bash
# Test specific function with prepared files
python testing_environment/test_function.py --function process-script

# Test with custom payload
python testing_environment/test_function.py \
  --function generate-voiceover \
  --payload test_inputs/generate-voiceover/payloads/basic_voiceover.json
```

### 3. File Naming Conventions

- **Scripts**: `{purpose}_script.txt` (e.g., `tutorial_script.txt`)
- **Images**: `{subject}_{resolution}.{ext}` (e.g., `landscape_1920x1080.png`)
- **Videos**: `{content}_{duration}.mp4` (e.g., `silent_30s.mp4`)
- **Audio**: `{type}_{duration}.mp3` (e.g., `voiceover_60s.mp3`)
- **Payloads**: `{test_case}.json` (e.g., `with_transitions.json`)

### 4. Expected Output Locations

After running tests, check for outputs in:
- `local_backups/youtube-video-engine/voiceovers/` - Generated voiceovers
- `local_backups/youtube-video-engine/videos/` - Processed videos
- `local_backups/youtube-video-engine/music/` - Generated music
- `local_backups/youtube-video-engine/images/` - AI-generated images

## Test Data Requirements

### Video Files
- **Format**: MP4 (H.264 codec preferred)
- **Resolution**: 1920x1080 or higher
- **Frame Rate**: 24-30 fps
- **Duration**: Various (5s, 30s, 60s for testing different scenarios)

### Audio Files
- **Format**: MP3 or WAV
- **Sample Rate**: 44.1 kHz or 48 kHz
- **Bitrate**: 128 kbps or higher
- **Channels**: Mono or Stereo

### Image Files
- **Format**: PNG or JPG
- **Resolution**: Minimum 1920x1080
- **Aspect Ratio**: 16:9 for standard videos
- **Color Space**: sRGB

### Script Files
- **Format**: Plain text (UTF-8)
- **Line Breaks**: Use double line breaks for segment separation
- **Length**: Vary from 30 seconds to 5 minutes of content