"""Job monitoring service for detecting and processing stuck jobs."""

import time
import logging
import requests
import ast
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from services.airtable_service import AirtableService
from services.nca_service import NCAService
from config import get_config
from utils.logger import APILogger

logger = logging.getLogger(__name__)
api_logger = APILogger()


class JobMonitor:
    """Monitor and process stuck jobs when webhooks fail."""
    
    def __init__(self):
        """Initialize the job monitor."""
        self.config = get_config()()
        self.airtable = AirtableService()
        self.nca = NCAService()
        self.logger = logger
        
    def check_stuck_jobs(self, older_than_minutes: int = 5) -> List[Dict]:
        """Find jobs that have been processing for too long."""
        try:
            # Get the jobs table
            jobs_table = self.airtable.jobs_table
            
            # Get all jobs
            all_jobs = jobs_table.all()
            
            # Filter for stuck jobs
            stuck_jobs = []
            current_time = datetime.utcnow()
            
            for job in all_jobs:
                fields = job.get('fields', {})
                status = fields.get('Status', '')
                created_time = fields.get('Created Time', '')
                
                # Check if job is in processing state
                if status == self.config.STATUS_PROCESSING:
                    # Parse created time
                    if created_time:
                        try:
                            # Airtable returns ISO format with Z suffix
                            created_dt = datetime.fromisoformat(created_time.replace('Z', '+00:00').replace('+00:00', ''))
                            age_minutes = (current_time - created_dt).total_seconds() / 60
                            
                            if age_minutes > older_than_minutes:
                                stuck_jobs.append({
                                    'id': job['id'],
                                    'fields': fields,
                                    'age_minutes': age_minutes
                                })
                        except Exception as e:
                            self.logger.warning(f"Error parsing created time for job {job['id']}: {e}")
            
            self.logger.info(f"Found {len(stuck_jobs)} stuck jobs older than {older_than_minutes} minutes")
            return stuck_jobs
            
        except Exception as e:
            self.logger.error(f"Error getting stuck jobs: {e}")
            return []
    
    def check_file_exists(self, url: str) -> bool:
        """Check if a file exists at the given URL."""
        try:
            response = requests.head(url, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            self.logger.debug(f"File check failed for {url}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error checking file {url}: {e}")
            return False
    
    def construct_output_url(self, external_job_id: str) -> str:
        """Construct the expected output URL based on NCA's pattern."""
        # NCA stores files in this pattern
        return f"https://phi-bucket.nyc3.digitaloceanspaces.com/phi-bucket/{external_job_id}_output_0.mp4"
    
    def extract_segment_id(self, job_fields: Dict) -> Optional[str]:
        """Extract segment ID from job fields."""
        # First try Related Segment Video field
        segment_id = None
        related_segments = job_fields.get('Related Segment Video', [])
        if related_segments and len(related_segments) > 0:
            segment_id = related_segments[0]
        
        # Fallback to parsing request payload
        if not segment_id:
            request_payload = job_fields.get('Request Payload', '{}')
            try:
                if request_payload and request_payload != '{}':
                    # Try to parse as dict
                    if request_payload.startswith('{'):
                        payload_data = ast.literal_eval(request_payload)
                    else:
                        payload_data = {}
                    
                    segment_id = payload_data.get('segment_id') or payload_data.get('record_id')
            except Exception as e:
                self.logger.debug(f"Could not parse request payload: {e}")
        
        return segment_id
    
    def extract_video_id(self, job_fields: Dict) -> Optional[str]:
        """Extract video ID from job fields."""
        # First try Related Video field
        video_id = None
        related_videos = job_fields.get('Related Video', [])
        if related_videos and len(related_videos) > 0:
            video_id = related_videos[0]
        
        # Fallback to parsing request payload
        if not video_id:
            request_payload = job_fields.get('Request Payload', '{}')
            try:
                if request_payload and request_payload != '{}':
                    # Try to parse as dict
                    if request_payload.startswith('{'):
                        payload_data = ast.literal_eval(request_payload)
                    else:
                        payload_data = {}
                    
                    video_id = payload_data.get('video_id') or payload_data.get('record_id')
            except Exception as e:
                self.logger.debug(f"Could not parse request payload: {e}")
        
        return video_id
    
    def extract_operation(self, job_fields: Dict) -> str:
        """Extract operation type from job fields."""
        # Try to get from request payload
        request_payload = job_fields.get('Request Payload', '{}')
        try:
            if request_payload and request_payload != '{}':
                if request_payload.startswith('{'):
                    payload_data = ast.literal_eval(request_payload)
                else:
                    payload_data = {}
                
                operation = payload_data.get('operation', '')
                if operation:
                    return operation
        except:
            pass
        
        # Fallback based on job type
        job_type = job_fields.get('Job Type', '')
        if job_type == self.config.JOB_TYPE_COMBINATION:
            return 'combine'
        elif job_type == self.config.JOB_TYPE_CONCATENATION:
            return 'concatenate'
        elif job_type == self.config.JOB_TYPE_FINAL:
            return 'add_music'
        
        return 'unknown'
    
    def handle_job_completion(self, job_id: str, operation: str, output_url: str, job_fields: Dict):
        """Handle different types of job completions."""
        try:
            self.logger.info(f"Processing completed job {job_id} with operation '{operation}'")
            
            if operation == 'combine':
                # Update segment with combined video
                segment_id = self.extract_segment_id(job_fields)
                if segment_id:
                    self.logger.info(f"Updating segment {segment_id} with combined video")
                    self.airtable.safe_update_segment_status(
                        segment_id, 
                        'combined', 
                        {'Voiceover + Video': [{'url': output_url}]}
                    )
                else:
                    self.logger.warning(f"Could not find segment ID for combine job {job_id}")
                    
            elif operation == 'concatenate':
                # Update video with concatenated result
                video_id = self.extract_video_id(job_fields)
                if video_id:
                    self.logger.info(f"Updating video {video_id} with concatenated segments")
                    self.airtable.update_video(
                        video_id,
                        {'Combined Segments Video': [{'url': output_url}]}
                    )
                else:
                    self.logger.warning(f"Could not find video ID for concatenate job {job_id}")
                    
            elif operation == 'add_music':
                # Update video with final result
                video_id = self.extract_video_id(job_fields)
                if video_id:
                    self.logger.info(f"Updating video {video_id} with final video + music")
                    self.airtable.update_video(
                        video_id,
                        {'Video + Music': [{'url': output_url}]}
                    )
                else:
                    self.logger.warning(f"Could not find video ID for add_music job {job_id}")
            
            # Update job status to completed
            self.airtable.complete_job(
                job_id, 
                response_payload={'output_url': output_url, 'completed_via': 'polling'},
                notes=f'Completed via polling at {datetime.utcnow().isoformat()}. Output: {output_url}'
            )
            
            # Log successful completion
            api_logger.log_job_status(job_id, self.config.STATUS_COMPLETED, {
                'completed_via': 'polling',
                'operation': operation,
                'output_url': output_url
            })
            
        except Exception as e:
            self.logger.error(f"Error handling job completion for {job_id}: {e}", exc_info=True)
            raise
    
    def process_completed_job(self, job: Dict, output_url: str):
        """Process a job that we've determined is complete."""
        job_id = job['id']
        fields = job['fields']
        
        # Extract operation type
        operation = self.extract_operation(fields)
        
        # Handle the completion
        self.handle_job_completion(job_id, operation, output_url, fields)
    
    def check_nca_job_status(self, external_job_id: str) -> Optional[Dict]:
        """Check job status directly from NCA."""
        try:
            status = self.nca.get_job_status(external_job_id)
            return status
        except Exception as e:
            self.logger.debug(f"Could not get NCA status for job {external_job_id}: {e}")
            return None
    
    def run_check_cycle(self):
        """Run a single check cycle for stuck jobs."""
        try:
            self.logger.info("Starting job monitoring cycle")
            
            # Get stuck jobs
            stuck_jobs = self.check_stuck_jobs(older_than_minutes=5)
            
            if not stuck_jobs:
                self.logger.info("No stuck jobs found")
                return
            
            self.logger.info(f"Processing {len(stuck_jobs)} stuck jobs")
            
            processed_count = 0
            failed_count = 0
            
            for job in stuck_jobs:
                try:
                    job_id = job['id']
                    fields = job['fields']
                    external_id = fields.get('External Job ID')
                    
                    if not external_id:
                        self.logger.debug(f"Job {job_id} has no external ID, skipping")
                        continue
                    
                    self.logger.info(f"Checking job {job_id} with external ID {external_id}")
                    
                    # Check if output file exists on DO Spaces
                    output_url = self.construct_output_url(external_id)
                    
                    if self.check_file_exists(output_url):
                        self.logger.info(f"Found completed file for job {job_id}: {output_url}")
                        self.process_completed_job(job, output_url)
                        processed_count += 1
                    else:
                        # File doesn't exist, try to get status from NCA
                        self.logger.debug(f"No file found at {output_url}, checking NCA status")
                        
                        nca_status = self.check_nca_job_status(external_id)
                        if nca_status:
                            status = nca_status.get('status', '').lower()
                            
                            if status == 'failed':
                                error_msg = nca_status.get('error', 'Job failed in NCA')
                                self.logger.warning(f"Job {job_id} failed in NCA: {error_msg}")
                                self.airtable.fail_job(job_id, error_msg, notes=f"Failed via polling check at {datetime.utcnow().isoformat()}")
                                failed_count += 1
                            elif status == 'completed':
                                # Status says completed but no file found
                                self.logger.warning(f"Job {job_id} marked as completed in NCA but no file found")
                                # Try alternative URL patterns or wait for next cycle
                            else:
                                self.logger.debug(f"Job {job_id} still processing in NCA (status: {status})")
                        else:
                            # If job is very old (>1 hour), consider it failed
                            if job['age_minutes'] > 60:
                                self.logger.warning(f"Job {job_id} is {job['age_minutes']:.0f} minutes old with no output, marking as failed")
                                self.airtable.fail_job(
                                    job_id, 
                                    "Job timed out - no output after 1 hour",
                                    notes=f"Timed out via polling at {datetime.utcnow().isoformat()}"
                                )
                                failed_count += 1
                                
                except Exception as e:
                    self.logger.error(f"Error processing job {job.get('id', 'unknown')}: {e}", exc_info=True)
            
            self.logger.info(f"Job monitoring cycle complete. Processed: {processed_count}, Failed: {failed_count}")
            
        except Exception as e:
            self.logger.error(f"Error in job monitoring cycle: {e}", exc_info=True)
            raise