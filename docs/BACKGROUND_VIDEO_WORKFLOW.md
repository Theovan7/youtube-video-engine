# Background Video Workflow - User in the Loop Process

## Overview

The YouTube Video Engine uses a **semi-automated** approach for background videos. This is a deliberate design choice that requires human judgment to select appropriate video content for each segment.

## How It Works

### 1. Script Processing (Automated)
- User submits a script via the API
- System automatically parses the script into segments
- Each segment is created as a record in Airtable

### 2. Voiceover Generation (Automated)
- API generates AI voiceovers for each segment using ElevenLabs
- Voiceovers are automatically attached to segment records

### 3. Background Video Selection (Manual - User in the Loop)
- **Users manually review each segment in Airtable**
- **Users select and upload appropriate background videos**
- **Videos are uploaded to the `Video` field in each segment record**

### 4. Video Combination (Automated)
- Once videos are uploaded, the API combines them with voiceovers
- System reads the existing video from the segment's `Video` field
- No need to pass video URLs - they're already in Airtable

## Why This Approach?

1. **Quality Control**: Humans can ensure videos match the content appropriately
2. **Creative Direction**: Allows for artistic choices that align with brand/message
3. **Context Sensitivity**: Humans understand nuance and can avoid inappropriate combinations
4. **Flexibility**: Different videos can be tried without re-running the entire pipeline

## Field Names in Airtable

⚠️ **Important**: Don't confuse these fields:

- `Video` (singular) - Where users upload background videos
- `Videos` (plural) - Link to the parent video record

## API Usage

### Correct Usage
```javascript
// After user has uploaded videos to segments in Airtable
const response = await fetch('/api/v1/combine-segment-media', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    segment_id: 'recXXXXXXXXXXXXXX'
    // Note: No base_video_url needed!
  })
});
```

### Common Mistakes
```javascript
// ❌ WRONG - Don't pass video URLs
{
  segment_id: 'recXXXXXXXXXXXXXX',
  base_video_url: 'https://example.com/video.mp4'  // Not needed!
}
```

## Step-by-Step Workflow

1. **Process Script**
   ```bash
   POST /api/v1/process-script
   ```

2. **Generate Voiceovers**
   ```bash
   POST /api/v1/generate-voiceover
   ```

3. **Manual Step**
   - Open Airtable
   - Navigate to Segments table
   - For each segment:
     - Review the text content
     - Select an appropriate background video
     - Upload to the `Video` field

4. **Combine Media**
   ```bash
   POST /api/v1/combine-segment-media
   ```
   - API reads video from Airtable
   - Combines with voiceover
   - Stores result

5. **Continue with Pipeline**
   - Combine all segments
   - Add background music
   - Final video ready!

## Best Practices

1. **Video Selection Guidelines**
   - Match video mood to content tone
   - Ensure video length covers the voiceover duration
   - Consider visual continuity between segments
   - Avoid distracting or conflicting imagery

2. **File Requirements**
   - Supported formats: MP4, MOV, AVI
   - Recommended resolution: 1920x1080 (1080p)
   - Maximum file size: Set by Airtable limits

3. **Quality Checks**
   - Preview videos before uploading
   - Ensure no copyright issues
   - Check for appropriate content
   - Verify technical quality (no corruption, proper encoding)

## Troubleshooting

### "Background video not uploaded" Error
- **Cause**: No video in the `Video` field for the segment
- **Solution**: Upload a video to the segment in Airtable before calling combine

### "Video field not found" Error
- **Cause**: Code looking for wrong field name
- **Solution**: Ensure code uses `Video` not `Base Video`

### Video Not Processing
- **Check**: Is the video in a supported format?
- **Check**: Is the file size within limits?
- **Check**: Can you play the video locally?

## Future Enhancements

While the current system requires manual video uploads, potential future features could include:

- Video library management system
- AI-powered video suggestions (still requiring human approval)
- Bulk upload tools
- Video preview in the API response

However, the core principle of human oversight for video selection should remain to ensure quality and appropriateness.
