# Test Input Files

This folder contains sample input files that can be used for testing the YouTube Video Engine API endpoints.

## File Organization

```
test_inputs/
├── scripts/          # Sample script text files
├── images/           # Sample images for video generation
├── videos/           # Sample video files for testing
├── audio/            # Sample audio/music files
└── configs/          # Configuration files for different test scenarios
```

## Usage

### For Script Processing
Place `.txt` files in `scripts/` folder containing sample video scripts.

### For Image-to-Video Generation
Place image files (PNG, JPG) in `images/` folder to test video generation from static images.

### For Video Processing
Place MP4 files in `videos/` folder to test video combination and concatenation.

### For Audio/Music
Place MP3/WAV files in `audio/` folder to test voiceover combination and background music.

## Example Files to Add

1. **Scripts** (`scripts/`):
   - `short_demo.txt` - 30-second demo script
   - `product_launch.txt` - Product announcement script
   - `tutorial.txt` - How-to video script
   - `story.txt` - Narrative content

2. **Images** (`images/`):
   - `landscape.png` - For zoom effect testing
   - `product.jpg` - For product videos
   - `logo.png` - For intro/outro testing

3. **Videos** (`videos/`):
   - `sample_5s.mp4` - Short test video
   - `sample_30s.mp4` - Medium length video
   - `silent_video.mp4` - Video without audio

4. **Audio** (`audio/`):
   - `background_music.mp3` - For music overlay testing
   - `voiceover_sample.mp3` - Sample voiceover
   - `sound_effect.wav` - Short sound effect

## File Upload Process

When you have files to test:
1. Place them in the appropriate subdirectory
2. Update the test scripts to reference these files
3. Files can be uploaded to S3 first using the upload utility, then referenced by URL

## Test File Requirements

- **Images**: Min 1920x1080 resolution recommended
- **Videos**: H.264 codec, MP4 container preferred
- **Audio**: MP3 or WAV format, 44.1kHz sample rate
- **Scripts**: Plain text files, UTF-8 encoding