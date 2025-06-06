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
        self.logger = logging.getLogger(__name__) # Initialize logger for the service instance
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
    
    def safe_update_video_status(self, video_id: str, status: str, error_details: Optional[str] = None, 
                                additional_fields: Optional[Dict] = None) -> Dict:
        """Safely update video status with fallback handling.
        Note: The existing Videos table doesn't have a Status field, so this logs the intent but may not update.
        """
        fields = additional_fields.copy() if additional_fields else {}
        
        # Try to add Status field if it exists, otherwise just log
        try:
            fields['Status'] = status
            record = self.videos_table.update(video_id, fields)
            api_logger.log_api_response('airtable', 'safe_update_video_status', 200, 
                                      {'video_id': video_id, 'status': status, 'success': True})
            return record
        except Exception as e:
            # Log the original error and try without Status field
            logger.warning(f"Failed to set video {video_id} status to '{status}' (field may not exist): {e}")
            api_logger.log_error('airtable', e, {
                'operation': 'safe_update_video_status', 
                'video_id': video_id, 
                'intended_status': status
            })
            
            # Try without Status field and with error details if provided
            try:
                fields_without_status = additional_fields.copy() if additional_fields else {}
                if error_details:
                    fields_without_status['Error Details'] = error_details
                
                if fields_without_status:
                    record = self.videos_table.update(video_id, fields_without_status)
                else:
                    record = self.get_video(video_id)
                
                logger.info(f"Updated video {video_id} without Status field (status '{status}' intended)")
                api_logger.log_api_response('airtable', 'safe_update_video_status', 200, 
                                          {'video_id': video_id, 'status': status, 'no_status_field': True})
                return record
            except Exception as fallback_error:
                # If even the fallback fails, log and re-raise original error
                logger.error(f"Failed to update video {video_id} even without Status field: {fallback_error}")
                api_logger.log_error('airtable', fallback_error, {
                    'operation': 'safe_update_video_status_fallback', 
                    'video_id': video_id
                })
                raise e  # Re-raise original error
    
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
                
                # Add Original SRT Text field if provided
                if 'original_text' in segment:
                    fields['Original SRT Text'] = segment['original_text']
                
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
    
    def safe_update_segment_status(self, segment_id: str, status: str, additional_fields: Optional[Dict] = None) -> Dict:
        """Safely update segment status with fallback to 'Undefined'."""
        fields = additional_fields.copy() if additional_fields else {}
        fields['Status'] = status
        
        try:
            # Try to update with the intended status
            record = self.segments_table.update(segment_id, fields)
            api_logger.log_api_response('airtable', 'safe_update_segment_status', 200, 
                                      {'segment_id': segment_id, 'status': status, 'success': True})
            return record
        except Exception as e:
            # Log the original error
            logger.warning(f"Failed to set segment {segment_id} status to '{status}': {e}")
            api_logger.log_error('airtable', e, {
                'operation': 'safe_update_segment_status', 
                'segment_id': segment_id, 
                'intended_status': status
            })
            
            # Try fallback to 'Undefined' status
            try:
                fields['Status'] = 'Undefined'
                record = self.segments_table.update(segment_id, fields)
                logger.info(f"Successfully set segment {segment_id} status to 'Undefined' as fallback")
                api_logger.log_api_response('airtable', 'safe_update_segment_status', 200, 
                                          {'segment_id': segment_id, 'status': 'Undefined', 'fallback': True})
                return record
            except Exception as fallback_error:
                # If even 'Undefined' fails, log and re-raise original error
                logger.error(f"Even 'Undefined' status failed for segment {segment_id}: {fallback_error}")
                api_logger.log_error('airtable', fallback_error, {
                    'operation': 'safe_update_segment_status_fallback',
                    'segment_id': segment_id
                })
                raise e  # Re-raise original error

    def get_video_segments(self, video_id: str) -> List[Dict]:
        """Get all segments for a video by retrieving the video record and its linked segment IDs."""
        try:
            self.logger.info(f"Fetching video record {video_id} to get linked segments.")
            video_record = self.videos_table.get(video_id)

            if not video_record or 'fields' not in video_record or 'Segments' not in video_record['fields']:
                self.logger.warning(f"Video record {video_id} not found or has no 'Segments' field.", extra={'operation': 'get_video_segments', 'video_id': video_id})
                return []

            segment_ids = video_record['fields'].get('Segments', []) # Ensure 'Segments' field exists
            if not segment_ids:
                self.logger.info(f"No segment IDs linked in 'Segments' field for video {video_id}.", extra={'operation': 'get_video_segments', 'video_id': video_id})
                return []

            self.logger.info(f"Found {len(segment_ids)} segment IDs linked to video {video_id}: {segment_ids}")

            segments_data = []
            for segment_id in segment_ids:
                segment_record = self.segments_table.get(segment_id)
                if segment_record:
                    segments_data.append(segment_record)
                else:
                    self.logger.warning(f"Segment record {segment_id} linked from video {video_id} not found in Segments table.", extra={'operation': 'get_video_segments', 'video_id': video_id, 'segment_id': segment_id})
            
            # Sort segments by 'SRT Segment ID'
            # This key attempts to sort numerically if 'SRT Segment ID' is an int or a string representing an int,
            # otherwise sorts as string. Handles missing values by pushing them to the end.
            def get_sort_key(segment_record):
                fields = segment_record.get('fields', {})
                srt_id_value = fields.get('SRT Segment ID')
                if srt_id_value is None:
                    return (float('inf'), '') # Sort Nones last
                if isinstance(srt_id_value, (int, float)):
                    return (0, srt_id_value)
                if isinstance(srt_id_value, str):
                    try:
                        return (0, int(srt_id_value)) # Try to convert string to int
                    except ValueError:
                        return (1, srt_id_value) # Sort as string if not convertible
                return (2, srt_id_value) # Fallback for other types

            segments_data.sort(key=get_sort_key)
            self.logger.info(f"Returning {len(segments_data)} segments for video {video_id} after fetching and sorting.")
            return segments_data

        except Exception as e:
            self.logger.error(f"Error in get_video_segments for video_id {video_id}: {str(e)}", extra={'operation': 'get_video_segments', 'video_id': video_id}, exc_info=True)
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
    
    # Generic table operations
    def get_record(self, table_name: str, record_id: str) -> Dict:
        """Get a record from any table by ID."""
        try:
            table = self.base.table(table_name)
            record = table.get(record_id)
            return record
        except Exception as e:
            api_logger.log_error('airtable', e, {
                'operation': 'get_record', 
                'table_name': table_name, 
                'record_id': record_id
            })
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
    
    def safe_update_job_status(self, job_id: str, status: str, additional_fields: Optional[Dict] = None) -> Dict:
        """Safely update job status with fallback to 'Undefined'."""
        fields = additional_fields.copy() if additional_fields else {}
        fields['Status'] = status
        
        try:
            # Try to update with the intended status
            record = self.jobs_table.update(job_id, fields)
            
            # Log status changes
            api_logger.log_job_status(job_id, status, fields)
            api_logger.log_api_response('airtable', 'safe_update_job_status', 200, 
                                      {'job_id': job_id, 'status': status, 'success': True})
            return record
        except Exception as e:
            # Log the original error
            logger.warning(f"Failed to set job {job_id} status to '{status}': {e}")
            api_logger.log_error('airtable', e, {
                'operation': 'safe_update_job_status', 
                'job_id': job_id, 
                'intended_status': status
            })
            
            # Try fallback to 'Undefined' status
            try:
                fields['Status'] = 'Undefined'
                record = self.jobs_table.update(job_id, fields)
                logger.info(f"Successfully set job {job_id} status to 'Undefined' as fallback")
                api_logger.log_job_status(job_id, 'Undefined', fields)
                api_logger.log_api_response('airtable', 'safe_update_job_status', 200, 
                                          {'job_id': job_id, 'status': 'Undefined', 'fallback': True})
                return record
            except Exception as fallback_error:
                # If even 'Undefined' fails, log and re-raise original error
                logger.error(f"Even 'Undefined' status failed for job {job_id}: {fallback_error}")
                api_logger.log_error('airtable', fallback_error, {
                    'operation': 'safe_update_job_status_fallback', 
                    'job_id': job_id
                })
                raise e  # Re-raise original error
    
    def safe_update_job_type(self, job_id: str, job_type: str, additional_fields: Optional[Dict] = None) -> Dict:
        """Safely update job type with fallback to 'Undefined'."""
        fields = additional_fields.copy() if additional_fields else {}
        fields['Type'] = job_type
        
        try:
            # Try to update with the intended type
            record = self.jobs_table.update(job_id, fields)
            api_logger.log_api_response('airtable', 'safe_update_job_type', 200, 
                                      {'job_id': job_id, 'type': job_type, 'success': True})
            return record
        except Exception as e:
            # Log the original error
            logger.warning(f"Failed to set job {job_id} type to '{job_type}': {e}")
            api_logger.log_error('airtable', e, {
                'operation': 'safe_update_job_type', 
                'job_id': job_id, 
                'intended_type': job_type
            })
            
            # Try fallback to 'Undefined' type
            try:
                fields['Type'] = 'Undefined'
                record = self.jobs_table.update(job_id, fields)
                logger.info(f"Successfully set job {job_id} type to 'Undefined' as fallback")
                api_logger.log_api_response('airtable', 'safe_update_job_type', 200, 
                                          {'job_id': job_id, 'type': 'Undefined', 'fallback': True})
                return record
            except Exception as fallback_error:
                # If even 'Undefined' fails, log and re-raise original error
                logger.error(f"Even 'Undefined' type failed for job {job_id}: {fallback_error}")
                api_logger.log_error('airtable', fallback_error, {
                    'operation': 'safe_update_job_type_fallback', 
                    'job_id': job_id
                })
                raise e  # Re-raise original error
    
    def complete_job(self, job_id: str, response_payload: Optional[Dict] = None, notes: Optional[str] = None) -> Dict:
        """Mark a job as completed."""
        additional_fields = {}
        if response_payload:
            additional_fields['Response Payload'] = str(response_payload)
        if notes:
            additional_fields['Notes'] = notes
        return self.safe_update_job_status(job_id, self.config.STATUS_COMPLETED, additional_fields)
    
    def fail_job(self, job_id: str, error_details: str, notes: Optional[str] = None) -> Dict:
        """Mark a job as failed."""
        additional_fields = {'Error Details': error_details}
        if notes:
            additional_fields['Notes'] = notes
        return self.safe_update_job_status(job_id, self.config.STATUS_FAILED, additional_fields)
    
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
    
    def mark_webhook_processed(self, event_id: str, success: bool = True, notes: Optional[str] = None) -> Dict:
        """Mark a webhook event as processed and optionally add notes."""
        try:
            fields = {
                'Processed': 'Yes',  # Using Yes/No instead of boolean
                'Success': 'Yes' if success else 'No'
            }
            if notes is not None:
                fields['Notes'] = notes
            
            record = self.webhook_events_table.update(event_id, fields)
            # Log the main action; detailed params can be inferred from context or added if APILogger is extended
            api_logger.log_api_response('airtable', 'mark_webhook_processed', 200, record)
            return record
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'mark_webhook_processed', 
                                               'event_id': event_id,
                                               'success': success,
                                               'notes_provided': notes is not None})
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