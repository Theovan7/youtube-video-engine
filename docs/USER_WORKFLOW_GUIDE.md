# 🎥 User Workflow Guide: Background Video Upload

## Overview
The YouTube Video Engine uses a **user-in-the-loop** process for background videos, where users manually select and upload appropriate videos for each segment. This ensures high-quality, contextually relevant visual content for each part of your script.

## 📋 Step-by-Step Workflow

### 1. Generate Your Video Segments
- Submit your script via API to `/api/v1/process-script`
- The system will automatically create segments in Airtable
- Each segment will appear in the **Segments** table

### 2. Review Generated Segments
- Open your Airtable base for the project
- Navigate to the **Segments** table
- Review each segment's text content
- Note the estimated duration for each segment

### 3. Upload Background Videos
**For each segment:**
1. **Select Appropriate Video**: Choose a video that matches the segment content
   - Video should be relevant to the text being narrated
   - Consider the tone and style (professional, casual, educational, etc.)
   - Ensure video is longer than the segment duration

2. **Upload to Airtable**:
   - Click on the **Video** field for the segment
   - Upload your selected background video file
   - Airtable will automatically store and provide a URL

### 4. Video Requirements
- **Format**: MP4 preferred (MOV, AVI also supported)
- **Resolution**: 1920x1080 (1080p) recommended
- **Duration**: Should be at least as long as the segment duration
- **Quality**: High quality preferred for professional results
- **File Size**: Airtable supports files up to 20GB

### 5. Continue Processing
Once all segments have background videos uploaded:
- The system can proceed with voiceover generation
- Videos will be automatically combined with voiceovers
- Final video assembly will concatenate all segments

## 💡 Best Practices

### Video Selection Guidelines
- **Educational Content**: Use clean, professional footage related to the topic
- **Product Demos**: Show the actual product or related visuals
- **Storytelling**: Choose videos that support the narrative
- **Branding**: Maintain consistent visual style across segments

### Quality Standards
- **Visual Quality**: Use HD or higher resolution videos
- **Audio**: Background video audio will be replaced by generated voiceover
- **Lighting**: Well-lit, clear footage works best
- **Motion**: Avoid excessive camera shake or rapid movements

### Organization Tips
- **Naming Convention**: Use descriptive names for your videos
- **Backup Copies**: Keep original videos in your own storage
- **Version Control**: Note which video version was used for each segment
- **Review Process**: Preview segments before final processing

## 🔧 Technical Details

### Supported Formats
- **Video**: MP4, MOV, AVI, MKV, WMV
- **Codecs**: H.264, H.265 (HEVC), VP9
- **Frame Rates**: 24fps, 30fps, 60fps

### Airtable Integration
- Videos are stored as **Attachment** fields in Airtable
- Each segment has a dedicated **Video** field
- URLs are automatically generated and accessible via API
- Files are securely stored and backed up by Airtable

### API Integration
- The `/api/v1/combine-segment-media` endpoint automatically reads from the Video field
- No additional parameters needed - just provide the segment_id
- System validates that videos are uploaded before processing
- Clear error messages if videos are missing

## ❗ Troubleshooting

### Common Issues
1. **"Video not found" error**
   - Ensure video is uploaded to the correct segment's Video field
   - Verify file was fully uploaded (check for upload completion)
   - Refresh Airtable view to confirm upload

2. **Processing failures**
   - Check video format compatibility
   - Ensure video file isn't corrupted
   - Verify adequate file size (not too large for processing)

3. **Quality issues**
   - Use higher resolution source videos
   - Ensure good lighting in original footage
   - Check video compression settings

### Getting Help
- Check the error logs in the system dashboard
- Review job status via `/api/v1/jobs/{job_id}` endpoint
- Contact support with specific error messages and job IDs

## 🎯 Quick Reference

**Essential Steps:**
1. ✅ Process script → Segments created
2. ✅ Upload videos to each segment's Video field in Airtable
3. ✅ Generate voiceovers via API
4. ✅ System combines videos with voiceovers automatically
5. ✅ Final video assembly and music addition

**Key URLs:**
- Health Check: `https://youtube-video-engine.fly.dev/health`
- Process Script: `POST /api/v1/process-script`
- Generate Voiceover: `POST /api/v1/generate-voiceover`
- Combine Media: `POST /api/v1/combine-segment-media`

---
*This workflow ensures high-quality, contextually appropriate video content while maintaining full user control over visual elements.*
