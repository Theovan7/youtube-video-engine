"""
Proposed fix for combine-segment-media endpoint

Current behavior:
- Requires base_video_url parameter
- Writes URL to segment
- Then combines

Correct behavior:
- No base_video_url parameter needed
- Reads existing video from segment's 'Video' field
- Combines with voiceover

Changes needed in api/routes.py:

1. Update schema:
```python
class CombineSegmentMediaSchema(Schema):
    segment_id = fields.String(required=True)
    # Remove: base_video_url = fields.String(required=True, validate=validate.URL())
```

2. Update endpoint logic:
```python
def combine_segment_media():
    # Get segment
    segment = airtable.get_segment(data['segment_id'])
    
    # Check if background video exists (in 'Video' field, not 'Base Video')
    if 'Video' not in segment['fields'] or not segment['fields']['Video']:
        return jsonify({'error': 'Background video not ready for this segment. Please upload a video to the segment in Airtable first.'}), 400
    
    # Check if voiceover is ready
    if 'Voiceover' not in segment['fields'] or not segment['fields']['Voiceover']:
        return jsonify({'error': 'Voiceover not ready for this segment'}), 400
    
    # Get URLs from existing fields
    video_url = segment['fields']['Video'][0]['url']
    voiceover_url = segment['fields']['Voiceover'][0]['url']
    
    # No need to update segment - video is already there!
    # Just create job and combine...
```

This reflects the "user in the loop" process where someone manually adds videos to segments before calling the combine endpoint.
"""