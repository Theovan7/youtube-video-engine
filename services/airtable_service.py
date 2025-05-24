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
    
    def __init__(self):
        """Initialize Airtable service."""
        self.config = get_config()()
        self.api = Api(self.config.AIRTABLE_API_KEY)
        self.base = self.api.base(self.config.AIRTABLE_BASE_ID)
        
        # Table references
        self.videos_table = self.base.table(self.config.VIDEOS_TABLE)
        self.segments_table = self.base.table(self.config.SEGMENTS_TABLE)
        self.jobs_table = self.base.table(self.config.JOBS_TABLE)
        self.webhook_events_table = self.base.table(self.config.WEBHOOK_EVENTS_TABLE)
    
    # Video operations
    def create_video(self, name: str, script: str, music_prompt: Optional[str] = None) -> Dict:
        """Create a new video record."""
        try:
            fields = {
                'Name': name,
                'Script': script,
                'Status': self.config.STATUS_PENDING
            }
            if music_prompt:
                fields['Music Prompt'] = music_prompt
            
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
            record = self.videos_table.update(video_id, fields)
            api_logger.log_api_response('airtable', 'update_video', 200, record)
            return record
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'update_video', 'video_id': video_id})
            raise
    
    def update_video_status(self, video_id: str, status: str, error_details: Optional[str] = None) -> Dict:
        """Update video status."""
        fields = {'Status': status}
        if error_details:
            fields['Error Details'] = error_details
        return self.update_video(video_id, fields)
    
    # Segment operations
    def create_segments(self, video_id: str, segments: List[Dict]) -> List[Dict]:
        """Create multiple segment records."""
        try:
            records = []
            for i, segment in enumerate(segments):
                fields = {
                    'Name': f"Segment {i + 1}",
                    'Video': [video_id],
                    'Text': segment['text'],
                    'Order': i + 1,
                    'Start Time': segment.get('start_time', i * self.config.DEFAULT_SEGMENT_DURATION),
                    'End Time': segment.get('end_time', (i + 1) * self.config.DEFAULT_SEGMENT_DURATION),
                    'Status': self.config.STATUS_PENDING
                }
                if segment.get('voice_id'):
                    fields['Voice ID'] = segment['voice_id']
                if segment.get('base_video'):
                    fields['Base Video'] = segment['base_video']
                
                records.append(fields)
            
            # Batch create segments
            created = self.segments_table.batch_create(records)
            api_logger.log_api_response('airtable', 'create_segments', 200, 
                                      {'count': len(created)})
            return created
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'create_segments'})
            raise
    
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
            formula = match({'Video': video_id})
            segments = self.segments_table.all(formula=formula, sort=['Order'])
            return segments
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'get_video_segments', 'video_id': video_id})
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
            
            if video_id:
                fields['Related Video'] = [video_id]
            if segment_id:
                fields['Related Segment'] = [segment_id]
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
                'Processed': False,
                'Success': False
            }
            
            if related_job_id:
                fields['Related Job'] = [related_job_id]
            
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
                'Processed': True,
                'Success': success
            }
            record = self.webhook_events_table.update(event_id, fields)
            return record
        except Exception as e:
            api_logger.log_error('airtable', e, {'operation': 'mark_webhook_processed', 
                                               'event_id': event_id})
            raise
    
    # Utility methods
    def add_attachment(self, table_name: str, record_id: str, field_name: str, 
                      url: str, filename: Optional[str] = None) -> Dict:
        """Add an attachment to a record."""
        try:
            # Get the appropriate table
            table = getattr(self, f"{table_name.lower()}_table")
            
            # Create attachment object
            attachment = {'url': url}
            if filename:
                attachment['filename'] = filename
            
            # Update the record
            record = table.update(record_id, {field_name: [attachment]})
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