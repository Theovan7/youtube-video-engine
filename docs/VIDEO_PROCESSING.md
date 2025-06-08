# Video Processing Documentation

## Overview

This document describes how the YouTube Video Engine processes videos, particularly focusing on how it handles video/audio duration mismatches when combining voiceovers with background videos.

## FFmpeg Configuration

The system uses FFmpeg through the NCA Toolkit API for all video processing operations. The key implementation is in the `combine_audio_video` method in `services/nca_service.py`.

## Duration Matching Strategy

When combining a background video with a voiceover, the system ensures the output video duration always matches the audio (voiceover) duration.

### Technical Implementation

```python
# FFmpeg filter configuration
ffmpeg_filters_payload = [
    {'filter': '[0:v]tpad=stop_mode=clone:stop_duration=300[v]'}
]

# Output options (no -shortest flag)
ffmpeg_output_options_payload = [
    {'option': '-map', 'argument': '[v]'},
    {'option': '-map', 'argument': '1:a:0'},
    {'option': '-c:v', 'argument': 'libx264'},
    {'option': '-c:a', 'argument': 'copy'}
]
```

### Filter Explanation

- **`tpad=stop_mode=clone:stop_duration=300`**: This filter pads the video temporally
  - `stop_mode=clone`: When the video ends, it holds (clones) the last frame
  - `stop_duration=300`: Maximum padding duration of 300 seconds (5 minutes)

### Behavior Examples

1. **Video shorter than audio** (e.g., 10s video + 25s audio):
   - Output: 25s video
   - First 10s: Normal video playback
   - Last 15s: Last frame held (freeze frame effect)

2. **Video longer than audio** (e.g., 25s video + 19s audio):
   - Output: 19s video
   - Video is naturally cut when audio ends
   - No explicit trimming needed

3. **Video and audio same length**:
   - Output matches input duration
   - No padding or trimming occurs

## Zoom Video Special Handling

For zoom-style videos generated from images, the system adds 20% extra duration to ensure smooth transitions:

```python
# Add 20% to the duration for zoom videos
zoom_duration = actual_segment_duration * 1.2
```

This prevents abrupt cuts during scene transitions.

## Technical Details

### Video Codec
- **Codec**: libx264 (H.264)
- **Reason**: Wide compatibility and good compression

### Audio Handling
- **Codec**: copy (no re-encoding)
- **Reason**: Preserves original audio quality and speeds up processing

### Maximum Extension
- **Limit**: 300 seconds (5 minutes)
- **Reason**: Prevents excessive memory usage while covering most use cases

## Common Issues and Solutions

### Issue: Video stops at original duration
**Cause**: Using `-shortest` flag with tpad filter
**Solution**: Remove `-shortest` flag to allow full audio duration

### Issue: Last frame not holding
**Cause**: Incorrect filter syntax or missing `stop_mode=clone`
**Solution**: Ensure filter is exactly `[0:v]tpad=stop_mode=clone:stop_duration=300[v]`

### Issue: Audio/video sync problems
**Cause**: Re-encoding audio unnecessarily
**Solution**: Use `copy` codec for audio to maintain sync

## API Usage

When calling the combine endpoint:

```bash
POST /api/v2/combine-segment-media
{
  "record_id": "segment_id"
}
```

The system automatically:
1. Retrieves video and voiceover URLs from Airtable
2. Applies the duration matching logic
3. Uploads the processed video back to Airtable

## Future Improvements

Potential enhancements could include:
- Configurable maximum padding duration
- Different padding modes (blur, fade to black, etc.)
- Smart scene detection for better transition points
- Crossfade effects between segments

## References

- [FFmpeg tpad filter documentation](https://ffmpeg.org/ffmpeg-filters.html#tpad)
- [NCA Toolkit API documentation](https://docs.ncatoolkit.com)