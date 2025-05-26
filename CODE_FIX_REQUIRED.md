# YouTube Video Engine - Code Fix Required

## Issue: Field Name Mismatch for Background Videos

### Current Problem:
- The API code expects a `Base Video` field in the segments table
- The actual Airtable has a `Video` field where users upload background videos
- The API requires a `base_video_url` parameter instead of reading existing videos from Airtable

### How It Should Work (User in the Loop):
1. Script processing creates segments
2. **Users manually upload background videos** to the `Video` field in each segment in Airtable
3. When ready, the API combines the user-uploaded video with the AI-generated voiceover
4. No need to pass URLs - videos are already in Airtable

### Code Changes Needed:

#### 1. In `api/routes.py` - Update field references:
```python
# Change all references from:
'Base Video'
# To:
'Video'
```

#### 2. In `api/routes.py` - Update combine_segment_media endpoint:
```python
# Remove the base_video_url requirement from schema
class CombineSegmentMediaSchema(Schema):
    segment_id = fields.String(required=True)
    # Remove: base_video_url = fields.String(required=True, validate=validate.URL())

# Update the endpoint to read existing video
def combine_segment_media():
    # Check if background video exists in segment
    if 'Video' not in segment['fields'] or not segment['fields']['Video']:
        return jsonify({'error': 'Background video not uploaded. Please upload a video to this segment in Airtable first.'}), 400
    
    # Get video URL from segment (no need to update segment)
    video_url = segment['fields']['Video'][0]['url']
```

#### 3. In `services/airtable_service.py` - Add field mapping:
```python
SEGMENT_FIELD_MAP = {
    # ... existing mappings ...
    'base_video': 'Video',  # The background video field (not 'Videos' which is the parent link)
}
```

### Important Notes:
- `Video` field = Where background videos are stored (singular)
- `Videos` field = Link to parent video record (plural) - don't confuse these!
- This is a semi-automated process requiring human intervention to select appropriate videos

### Testing After Fix:
1. Create segments from a script
2. Manually upload videos to the `Video` field in Airtable
3. Call the combine endpoint with just the segment_id
4. Verify it uses the existing video without requiring a URL parameter
