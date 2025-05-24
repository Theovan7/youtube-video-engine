"""Field mapper utility for flexible Airtable field detection."""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class AirtableFieldMapper:
    """Handle multiple field name variations in Airtable."""
    
    # Field name variations for different field types
    VOICEOVER_FIELDS = [
        "Voiceover", "Audio", "Voiceover Audio", "Voice Audio",
        "Generated Audio", "Speech", "TTS Audio", "Voiceover File",
        "Audio File", "Voice Over", "VO Audio", "Narration",
        "Speech Audio", "AI Voice", "Generated Voice"
    ]
    
    VIDEO_FIELDS = [
        "Video", "Video File", "Background Video", "Base Video",
        "Source Video", "Video Background", "Media", "Video Media",
        "Segment Video", "Video Attachment", "MP4 File", "Video Asset",
        "Video Clip", "Raw Video", "Original Video"
    ]
    
    COMBINED_FIELDS = [
        "Combined", "Voiceover + Video", "Combined Video", 
        "Output Video", "Final Video", "Segment Video",
        "Processed Video", "Combined Media", "Video Output",
        "Merged Video", "Complete Video", "Final Output",
        "Video with Audio", "Completed Segment"
    ]
    
    FINAL_VIDEO_FIELDS = [
        "Final Video", "Complete Video", "Output Video",
        "Finished Video", "Master Video", "Published Video",
        "Video Final", "Completed Video", "Export Video"
    ]
    
    MUSIC_FIELDS = [
        "Music", "Background Music", "BGM", "Audio Track",
        "Music Track", "Sound Track", "Background Audio",
        "Music File", "Generated Music", "AI Music"
    ]
    
    STATUS_FIELDS = [
        "Status", "State", "Processing Status", "Current Status",
        "Job Status", "Progress", "Stage"
    ]
    
    ERROR_FIELDS = [
        "Error Details", "Error", "Error Message", "Failure Reason",
        "Error Info", "Problem", "Issue", "Error Description"
    ]
    
    def __init__(self):
        """Initialize the field mapper."""
        self._field_cache = {}
    
    def find_field(self, record: Dict, field_type: str) -> Optional[Any]:
        """Find field value trying multiple variations."""
        # Get the appropriate field list
        field_list = getattr(self, f"{field_type.upper()}_FIELDS", [])
        
        # Check if we have a cached field name for this record type
        record_fields = record.get('fields', {})
        cache_key = f"{field_type}:{','.join(sorted(record_fields.keys()))}"
        
        if cache_key in self._field_cache:
            cached_field = self._field_cache[cache_key]
            if cached_field in record_fields:
                return self.extract_value(record_fields[cached_field])
        
        # Search for the field
        for field_name in field_list:
            if field_name in record_fields:
                value = record_fields[field_name]
                if value:
                    logger.info(f"Found {field_type} in field: {field_name}")
                    # Cache the successful field name
                    self._field_cache[cache_key] = field_name
                    return self.extract_value(value)
        
        # Log debugging info if not found
        logger.warning(f"No {field_type} field found in record {record.get('id', 'unknown')}")
        logger.debug(f"Searched fields: {field_list}")
        logger.debug(f"Available fields: {list(record_fields.keys())}")
        return None
    
    def extract_value(self, value: Any) -> Optional[Any]:
        """Extract the actual value from various Airtable formats."""
        if value is None:
            return None
        
        # Handle attachment fields (they return arrays)
        if isinstance(value, list) and value:
            # If it's a list of attachment objects
            if isinstance(value[0], dict):
                # For attachments with URL
                if 'url' in value[0]:
                    return value[0]['url']
                # For linked records
                elif isinstance(value[0], str):
                    return value[0]
            # If it's just a list of strings (linked record IDs)
            elif isinstance(value[0], str):
                return value[0] if len(value) == 1 else value
        
        # Handle single attachment object
        elif isinstance(value, dict) and 'url' in value:
            return value['url']
        
        # Handle plain string values
        elif isinstance(value, str):
            return value
        
        # Handle numeric or boolean values
        else:
            return value
    
    def extract_url(self, value: Any) -> Optional[str]:
        """Extract URL from various Airtable formats."""
        extracted = self.extract_value(value)
        
        # Ensure we return a string URL
        if isinstance(extracted, str):
            return extracted
        elif isinstance(extracted, list) and extracted and isinstance(extracted[0], str):
            return extracted[0]
        
        return None
    
    def extract_attachment_info(self, value: Any) -> Optional[Dict]:
        """Extract full attachment information including URL and metadata."""
        if value is None:
            return None
        
        # Handle attachment fields
        if isinstance(value, list) and value and isinstance(value[0], dict):
            attachment = value[0]
            return {
                'url': attachment.get('url'),
                'filename': attachment.get('filename'),
                'size': attachment.get('size'),
                'type': attachment.get('type'),
                'id': attachment.get('id')
            }
        
        # Handle single attachment
        elif isinstance(value, dict) and 'url' in value:
            return {
                'url': value.get('url'),
                'filename': value.get('filename'),
                'size': value.get('size'),
                'type': value.get('type'),
                'id': value.get('id')
            }
        
        return None
    
    def find_all_attachments(self, record: Dict) -> Dict[str, List[Dict]]:
        """Find all attachment fields in a record."""
        attachments = {}
        record_fields = record.get('fields', {})
        
        # Check all fields for attachments
        for field_name, value in record_fields.items():
            if isinstance(value, list) and value and isinstance(value[0], dict) and 'url' in value[0]:
                attachments[field_name] = [self.extract_attachment_info(att) for att in value]
        
        return attachments
    
    def map_fields(self, record: Dict, field_mapping: Dict[str, str]) -> Dict:
        """Map fields using a custom mapping."""
        mapped = {}
        record_fields = record.get('fields', {})
        
        for target_field, source_options in field_mapping.items():
            # If source_options is a string, convert to list
            if isinstance(source_options, str):
                source_options = [source_options]
            
            # Try each source option
            for source_field in source_options:
                if source_field in record_fields:
                    mapped[target_field] = self.extract_value(record_fields[source_field])
                    break
        
        return mapped
    
    def get_required_fields(self, record: Dict, field_types: List[str]) -> Dict[str, Any]:
        """Get multiple required fields from a record."""
        result = {}
        
        for field_type in field_types:
            value = self.find_field(record, field_type)
            if value is not None:
                result[field_type.lower()] = value
        
        return result
    
    def validate_required_fields(self, record: Dict, required_types: List[str]) -> tuple[bool, List[str]]:
        """Validate that a record has all required field types."""
        missing = []
        
        for field_type in required_types:
            if self.find_field(record, field_type) is None:
                missing.append(field_type)
        
        return len(missing) == 0, missing