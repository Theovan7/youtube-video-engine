"""Fix for background video field mapping issue"""

# The problem:
# - Code expects 'Base Video' field in segments
# - Actual Airtable has 'Video' field (singular) for background videos
# - Current mapping has 'Videos' (plural) which is the parent video link

# Changes needed in api/routes.py:

# FROM:
# 'Base Video': [{'url': data['base_video_url']}]
# TO:
# 'Video': [{'url': data['base_video_url']}]

# FROM:
# if 'Base Video' in fields and fields['Base Video']:
#     segment_data['base_video_url'] = fields['Base Video'][0]['url']
# TO:
# if 'Video' in fields and fields['Video']:
#     segment_data['base_video_url'] = fields['Video'][0]['url']

# Also need to update the airtable_service.py field mapping to include:
# 'base_video': 'Video',  # The background video field (not the parent link)
