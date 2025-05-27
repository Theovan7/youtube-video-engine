"""Airtable service for YouTube Video Engine."""

import logging
from typing import Dict, List, Optional, Any
from pyairtable import Api
from pyairtable.formulas import match
from config import get_config
from utils.logger import APILogger

logger = logging.getLogger(__name__)
api_logger = APILogger()


class AirtableService:
    """Service for interacting with Airtable."""
    
    # Field mappings for existing tables
    VIDEO_FIELD_MAP = {
        'name': 'Description',
        'script': 'Video Script',
        'video_id': 'Video ID',
        'ai_video': 'AI Video',
        'video_srt': 'Video SRT',
        'transcript_url': 'Transcript URL',
        'video_broll': 'Video + B-Roll',
        'width': 'Width',
        'height': 'Height',
        'segments_count': '# Segments',
        'music': 'Music',
        'music_task_id': 'AI Music Task ID',
        'video_captions': 'Video + Captions',
        'video_music': 'Video + Music'
    }
    
    SEGMENT_FIELD_MAP = {
        'segment_id': 'Segment ID',
        'srt_id': 'SRT Segment ID',
        'srt_segment': 'SRT Segment',
        'video': 'Videos',
        'timestamps': 'Timestamps',
        'text': 'SRT Text',
        'start_time': 'Start Time',
        'end_time': 'End Time',
        'duration': 'Duration'
    }
    
    def __init__(self):
        """Initialize Airtable service."""
        self.config = get_config()()
        self.api = Api(self.config.AIRTABLE_API_KEY)
        self.base = self.api.base(self.config.AIRTABLE_BASE_ID)
        
        # Table references
        self.videos_table = self.base.table(self.config.VIDEOS_TABLE)
        self.segments_table = self.base.table(self.config.SEGMENTS_TABLE)
        self.voices_table = self.base.table(self.config.VOICES_TABLE)
        self.jobs_table = self.base.table(self.config.JOBS_TABLE)
        self.webhook_events_table = self.base.table(self.config.WEBHOOK_EVENTS_TABLE)
    
    # Video operations
    def create_video(self, name: str, script: str, music_prompt: Optional[str] = None) -> Dict:
        """Create a new video record."""
        try:
            fields = {
                'Description': name,  # Using Description instead of Name
                'Video Script': script,  # Using Video Script instead of Script
                # Note: Videos table doesn't have a Status field in the existing schema
            }
            # Store music prompt in a different way if needed
            
            record = self.videos_table.create(fields)
            api_logger.log_api_response('airtable', 'create_video', 200, record)
            return record
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'create_video'})
            raise
    
    def get_video(self, video_id: str) -> Dict:
        """Get a video record by ID."""
        try:
            record = self.videos_table.get(video_id)
            return record
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'get_video', 'video_id': video_id})
            raise
    
    def update_video(self, video_id: str, fields: Dict) -> Dict:
        """Update a video record."""
        try:
            # Map field names to actual Airtable field names
            mapped_fields = {}
            for key, value in fields.items():
                # Check if we have a mapping for this field
                if key in ['name', 'script']:
                    mapped_key = self.VIDEO_FIELD_MAP.get(key, key)
                    mapped_fields[mapped_key] = value
                else:
                    # Pass through unmapped fields as-is (for direct field names)
                    mapped_fields[key] = value
            
            record = self.videos_table.update(video_id, mapped_fields)
            api_logger.log_api_response('airtable', 'update_video', 200, record)
            return record
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'update_video', 'video_id': video_id})
            raise
    
    def update_video_status(self, video_id: str, status: str, error_details: Optional[str] = None) -> Dict:
        """Update video status.
        Note: The existing Videos table doesn't have a Status field.
        This method will store status information in a different way or should be modified.
        """
        # Since there's no Status field, we might need to track this in the Jobs table
        # or add a Status field to the Videos table
        fields = {}
        if error_details:
            # We can store error details somewhere
            fields['Error Details'] = error_details
        return self.update_video(video_id, fields) if fields else self.get_video(video_id)
    
    # Segment operations
    def create_segments(self, video_id: str, segments: List[Dict]) -> List[Dict]:
        """Create multiple segment records."""
        try:
            records = []
            for i, segment in enumerate(segments):
                fields = {
                    'SRT Segment ID': str(i + 1),  # Using SRT Segment ID
                    'Videos': [video_id],  # Using Videos instead of Video
                    'SRT Text': segment['text'],  # Using SRT Text instead of Text
                    'Start Time': segment.get('start_time', i * self.config.DEFAULT_SEGMENT_DURATION),
                    'End Time': segment.get('end_time', (i + 1) * self.config.DEFAULT_SEGMENT_DURATION),
                    # Note: Segments table doesn't have Order, Status, or Voice ID fields
                    # Video field is where users upload background videos
                }
                
                # Calculate timestamps in format "00:00:00.000 --> 00:00:00.000"
                start_time = segment.get('start_time', i * self.config.DEFAULT_SEGMENT_DURATION)
                end_time = segment.get('end_time', (i + 1) * self.config.DEFAULT_SEGMENT_DURATION)
                fields['Timestamps'] = f"{self._format_timestamp(start_time)} --> {self._format_timestamp(end_time)}"
                
                records.append(fields)
            
            # Batch create segments
            created = self.segments_table.batch_create(records)
            api_logger.log_api_response('airtable', 'create_segments', 200, 
                                      {'count': len(created)})
            return created
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'create_segments'})
            raise
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to SRT timestamp format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def get_segment(self, segment_id: str) -> Dict:
        """Get a segment record by ID."""
        try:
            record = self.segments_table.get(segment_id)
            return record
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'get_segment', 'segment_id': segment_id})
            raise
    
    def update_segment(self, segment_id: str, fields: Dict) -> Dict:
        """Update a segment record."""
        try:
            record = self.segments_table.update(segment_id, fields)
            api_logger.log_api_response('airtable', 'update_segment', 200, record)
            return record
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'update_segment', 'segment_id': segment_id})
            raise
    
    def get_video_segments(self, video_id: str) -> List[Dict]:
        """Get all segments for a video."""
        try:
            # Use FIND function for linked record search
            formula = f"FIND('{video_id}', {{Videos}}) > 0"
            segments = self.segments_table.all(formula=formula, sort=['SRT Segment ID'])  # Sort by SRT Segment ID
            return segments
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'get_video_segments', 'video_id': video_id})
            raise
    
    # Voice operations
    def get_voice(self, voice_id: str) -> Dict:
        """Get a voice record by ID."""
        try:
            record = self.voices_table.get(voice_id)
            return record
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'get_voice', 'voice_id': voice_id})
            raise
    
    # Job operations
    def create_job(self, job_type: str, video_id: Optional[str] = None, 
                   segment_id: Optional[str] = None, external_job_id: Optional[str] = None,
                   webhook_url: Optional[str] = None, request_payload: Optional[Dict] = None) -> Dict:
        """Create a job record."""
        try:
            fields = {
                'Type': job_type,
                'Status': self.config.STATUS_PENDING
            }
            
            # Note: Related Video and Related Segment fields don't exist in current schema
            # These would need to be added to the Jobs table in Airtable
            # For now, storing as plain text in Request Payload
            if video_id:
                if not request_payload:
                    request_payload = {}
                request_payload['video_id'] = video_id
            if segment_id:
                if not request_payload:
                    request_payload = {}
                request_payload['segment_id'] = segment_id
            if external_job_id:
                fields['External Job ID'] = external_job_id
            if webhook_url:
                fields['Webhook URL'] = webhook_url
            if request_payload:
                fields['Request Payload'] = str(request_payload)
            
            record = self.jobs_table.create(fields)
            api_logger.log_job_status(record['id'], self.config.STATUS_PENDING, 
                                    {'type': job_type})
            return record
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'create_job'})
            raise
    
    def get_job(self, job_id: str) -> Dict:
        """Get a job record by ID."""
        try:
            record = self.jobs_table.get(job_id)
            return record
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'get_job', 'job_id': job_id})
            raise
    
    def get_job_by_external_id(self, external_job_id: str) -> Optional[Dict]:
        """Get a job record by external job ID."""
        try:
            formula = match({'External Job ID': external_job_id})
            records = self.jobs_table.all(formula=formula)
            return records[0] if records else None
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'get_job_by_external_id', 
                                               'external_job_id': external_job_id})
            raise
    
    def update_job(self, job_id: str, fields: Dict) -> Dict:
        """Update a job record."""
        try:
            record = self.jobs_table.update(job_id, fields)
            
            # Log status changes
            if 'Status' in fields:
                api_logger.log_job_status(job_id, fields['Status'], fields)
            
            return record
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'update_job', 'job_id': job_id})
            raise
    
    def complete_job(self, job_id: str, response_payload: Optional[Dict] = None) -> Dict:
        """Mark a job as completed."""
        fields = {'Status': self.config.STATUS_COMPLETED}
        if response_payload:
            fields['Response Payload'] = str(response_payload)
        return self.update_job(job_id, fields)
    
    def fail_job(self, job_id: str, error_details: str) -> Dict:
        """Mark a job as failed."""
        fields = {
            'Status': self.config.STATUS_FAILED,
            'Error Details': error_details
        }
        return self.update_job(job_id, fields)
    
    # Webhook event operations
    def create_webhook_event(self, service: str, endpoint: str, payload: Dict,
                           related_job_id: Optional[str] = None) -> Dict:
        """Create a webhook event record."""
        try:
            fields = {
                'Service': service,
                'Endpoint': endpoint,
                'Raw Payload': str(payload),
                'Processed': 'No',  # Using Yes/No instead of boolean
                'Success': 'No'     # Using Yes/No instead of boolean
            }
            
            # Note: Related Job field might not exist in current schema
            # Storing job ID in Raw Payload for now
            if related_job_id:
                payload['_related_job_id'] = related_job_id
            
            record = self.webhook_events_table.create(fields)
            api_logger.log_webhook(service, payload)
            return record
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'create_webhook_event'})
            raise
    
    def mark_webhook_processed(self, event_id: str, success: bool = True) -> Dict:
        """Mark a webhook event as processed."""
        try:
            fields = {
                'Processed': 'Yes',  # Using Yes/No instead of boolean
                'Success': 'Yes' if success else 'No'
            }
            record = self.webhook_events_table.update(event_id, fields)
            return record
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'mark_webhook_processed', 
                                               'event_id': event_id})
            raise
    
    # Helper methods for existing video table structure
    def add_video_attachment(self, video_id: str, attachment_type: str, url: str, 
                           filename: Optional[str] = None) -> Dict:
        """Add an attachment to a video record.
        
        attachment_type can be: 'AI Video', 'Video + B-Roll', 'Music', 
                               'Video + Captions', 'Video + Music'
        """
        return self.add_attachment('videos', video_id, attachment_type, url, filename)
    
    def update_video_urls(self, video_id: str, srt_url: Optional[str] = None,
                         transcript_url: Optional[str] = None, 
                         music_task_id: Optional[str] = None) -> Dict:
        """Update URL fields in a video record."""
        fields = {}
        if srt_url:
            fields['Video SRT'] = srt_url
        if transcript_url:
            fields['Transcript URL'] = transcript_url
        if music_task_id:
            fields['AI Music Task ID'] = music_task_id
        
        return self.update_video(video_id, fields) if fields else self.get_video(video_id)
    
    def update_video_dimensions(self, video_id: str, width: int, height: int) -> Dict:
        """Update video dimensions."""
        fields = {
            'Width': width,
            'Height': height
        }
        return self.update_video(video_id, fields)
    def add_attachment(self, table_name: str, record_id: str, field_name: str, 
                      url: str, filename: Optional[str] = None) -> Dict:
        """Add an attachment to a record."""
        try:
            # Get the appropriate table
            table = getattr(self, f"{table_name.lower()}_table")
            
            # Get existing record to preserve existing attachments
            record = table.get(record_id)
            existing_attachments = record['fields'].get(field_name, [])
            
            # Create attachment object
            attachment = {'url': url}
            if filename:
                attachment['filename'] = filename
            
            # Append to existing attachments
            attachments = existing_attachments + [attachment]
            
            # Update the record
            record = table.update(record_id, {field_name: attachments})
            return record
        except Exception as e:
            api_logger.log_error('airtable', e, {
                'operation': 'add_attachment',
                'table': table_name,
                'record_id': record_id,
                'field': field_name
            })
            raise
    
    def find_records(self, table_name: str, formula: str) -> List[Dict]:
        """Find records in a table using a formula."""
        try:
            table = getattr(self, f"{table_name.lower()}_table")
            records = table.all(formula=formula)
            return records
        except Exception as e:
            api_logger.log_error('airtable', e, {
                'operation': 'find_records',
                'table': table_name,
                'formula': formula
            })
            raise