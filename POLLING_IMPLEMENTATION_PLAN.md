# Polling Implementation Plan

## Overview
Since webhooks are unreliable (taking hours or not arriving at all), we need to implement a polling mechanism as a backup to ensure jobs are processed even when webhooks fail.

## Key Insights from Investigation

1. **Files are already on DO Spaces** - NCA uploads results to DigitalOcean Spaces immediately
2. **Predictable URLs** - Output files follow pattern: `https://phi-bucket.nyc3.digitaloceanspaces.com/phi-bucket/{external_job_id}_output_0.mp4`
3. **Webhook issues are systemic** - The webhook handler has extensive fallback logic, suggesting ongoing reliability issues
4. **Jobs get stuck in "processing"** - Without webhooks, jobs never transition to completed state

## Polling System Design

### 1. Job Monitor Service

```python
# services/job_monitor.py
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class JobMonitor:
    def __init__(self):
        self.airtable = AirtableService()
        self.nca = NCAService()
        self.logger = logging.getLogger(__name__)
        
    def check_stuck_jobs(self, older_than_minutes: int = 5) -> List[Dict]:
        """Find jobs that have been processing for too long."""
        try:
            # Get all jobs in processing state
            processing_jobs = self.airtable.jobs_table.all(
                formula="AND(Status='processing', DATETIME_DIFF(NOW(), {Created Time}, 'minutes') > {})".format(older_than_minutes)
            )
            return processing_jobs
        except Exception as e:
            self.logger.error(f"Error getting stuck jobs: {e}")
            return []
    
    def check_file_exists(self, url: str) -> bool:
        """Check if a file exists at the given URL."""
        try:
            response = requests.head(url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def construct_output_url(self, external_job_id: str, operation: str) -> str:
        """Construct the expected output URL based on job type."""
        base_url = "https://phi-bucket.nyc3.digitaloceanspaces.com/phi-bucket"
        
        # NCA typically appends _output_0 to the job ID
        return f"{base_url}/{external_job_id}_output_0.mp4"
    
    def process_completed_job(self, job: Dict, output_url: str) -> None:
        """Process a job that we've determined is complete."""
        job_id = job['id']
        fields = job['fields']
        
        # Simulate webhook payload
        webhook_payload = {
            'id': job_id,
            'job_id': fields.get('External Job ID'),
            'code': 200,
            'response': {
                'url': output_url
            }
        }
        
        # Get operation from job data
        request_payload = fields.get('Request Payload', '{}')
        try:
            import ast
            payload_data = ast.literal_eval(request_payload)
            operation = payload_data.get('operation', 'unknown')
        except:
            operation = 'unknown'
        
        # Process based on operation type
        self.handle_job_completion(job_id, operation, output_url, fields)
    
    def handle_job_completion(self, job_id: str, operation: str, output_url: str, job_fields: Dict):
        """Handle different types of job completions."""
        
        if operation == 'combine':
            # Update segment with combined video
            segment_id = self.extract_segment_id(job_fields)
            if segment_id:
                self.airtable.safe_update_segment_status(
                    segment_id, 
                    'combined', 
                    {'Voiceover + Video': [{'url': output_url}]}
                )
                
        elif operation == 'concatenate':
            # Update video with concatenated result
            video_id = self.extract_video_id(job_fields)
            if video_id:
                self.airtable.update_video(
                    video_id,
                    {'Combined Segments Video': [{'url': output_url}]}
                )
                
        elif operation == 'add_music':
            # Update video with final result
            video_id = self.extract_video_id(job_fields)
            if video_id:
                self.airtable.update_video(
                    video_id,
                    {'Video + Music': [{'url': output_url}]}
                )
        
        # Update job status
        self.airtable.complete_job(
            job_id, 
            response_payload={'output_url': output_url},
            notes=f'Completed via polling. Output: {output_url}'
        )
    
    def run_check_cycle(self):
        """Run a single check cycle for stuck jobs."""
        stuck_jobs = self.check_stuck_jobs(older_than_minutes=5)
        
        self.logger.info(f"Found {len(stuck_jobs)} potentially stuck jobs")
        
        for job in stuck_jobs:
            try:
                external_id = job['fields'].get('External Job ID')
                if not external_id:
                    continue
                
                # Check if output file exists
                output_url = self.construct_output_url(external_id, 'default')
                
                if self.check_file_exists(output_url):
                    self.logger.info(f"Found completed file for job {job['id']}: {output_url}")
                    self.process_completed_job(job, output_url)
                else:
                    # Try to get status from NCA
                    try:
                        nca_status = self.nca.get_job_status(external_id)
                        if nca_status.get('status') == 'failed':
                            error_msg = nca_status.get('error', 'Unknown error')
                            self.airtable.fail_job(job['id'], error_msg)
                    except:
                        pass
                        
            except Exception as e:
                self.logger.error(f"Error processing job {job['id']}: {e}")
```

### 2. Scheduled Polling

```python
# Add to app.py or create scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from services.job_monitor import JobMonitor

# Initialize scheduler
scheduler = BackgroundScheduler()
job_monitor = JobMonitor()

# Schedule job checks every 2 minutes
@scheduler.scheduled_job('interval', minutes=2)
def check_stuck_jobs():
    """Check for stuck jobs periodically."""
    try:
        job_monitor.run_check_cycle()
    except Exception as e:
        logger.error(f"Error in scheduled job check: {e}")

# Start scheduler
scheduler.start()
```

### 3. Manual Trigger Endpoint

```python
# Add to api/routes_v2.py
@api_bp.route('/check-stuck-jobs', methods=['POST'])
def trigger_job_check():
    """Manually trigger a check for stuck jobs."""
    try:
        monitor = JobMonitor()
        monitor.run_check_cycle()
        return jsonify({'status': 'success', 'message': 'Job check completed'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
```

## Implementation Steps

### Phase 1: Basic Polling (Immediate)

1. **Create job_monitor.py** with basic stuck job detection
2. **Add DO Spaces file checking** to verify job completion
3. **Process completed jobs** by updating Airtable records
4. **Deploy and test** with existing stuck jobs

### Phase 2: Enhanced Polling (This Week)

1. **Add intelligent polling intervals**
   - Check new jobs every 2 minutes
   - Check older jobs every 5-10 minutes
   - Stop checking after 24 hours

2. **Implement retry logic**
   - Retry file checks if network errors occur
   - Exponential backoff for repeated failures

3. **Add metrics and monitoring**
   - Track polling success rate
   - Alert on high failure rates
   - Log processing times

### Phase 3: Production Ready (Next Week)

1. **Add Redis caching**
   - Cache job states to reduce Airtable API calls
   - Track polling attempts per job
   - Implement distributed locking for multi-instance deployments

2. **Create admin dashboard**
   - Show stuck jobs
   - Manual retry capabilities
   - Webhook vs polling statistics

3. **Optimize performance**
   - Batch Airtable updates
   - Parallel file existence checks
   - Smart scheduling based on job age

## Configuration

```python
# Add to config.py
POLLING_ENABLED = os.getenv('POLLING_ENABLED', 'true').lower() == 'true'
POLLING_INTERVAL_MINUTES = int(os.getenv('POLLING_INTERVAL_MINUTES', '2'))
POLLING_MAX_AGE_HOURS = int(os.getenv('POLLING_MAX_AGE_HOURS', '24'))
POLLING_BATCH_SIZE = int(os.getenv('POLLING_BATCH_SIZE', '10'))
```

## Testing Plan

1. **Unit Tests**
   - Test file existence checking
   - Test URL construction
   - Test job processing logic

2. **Integration Tests**
   - Create test job without webhook
   - Verify polling picks it up
   - Confirm Airtable updates correctly

3. **Load Tests**
   - Test with 100+ stuck jobs
   - Measure processing time
   - Verify no rate limit issues

## Monitoring

1. **Metrics to Track**
   - Jobs processed via webhook vs polling
   - Average time to detect completion
   - File check success rate
   - Airtable API usage

2. **Alerts to Set**
   - High number of stuck jobs
   - Polling failures
   - File not found after expected time

## Deployment

1. **Add dependencies**
   ```txt
   APScheduler==3.10.4
   redis==5.0.1
   ```

2. **Update Fly.io config**
   ```toml
   [env]
     POLLING_ENABLED = "true"
     POLLING_INTERVAL_MINUTES = "2"
   ```

3. **Deploy**
   ```bash
   fly deploy --verbose
   ```

## Expected Outcomes

1. **Immediate Impact**
   - Stuck jobs will be processed within 2-5 minutes
   - No more "lost" jobs
   - Better visibility into job status

2. **Long-term Benefits**
   - Resilient to webhook failures
   - Faster issue detection
   - Improved user experience

This polling system will act as a safety net, ensuring that even if webhooks fail completely, jobs will still be processed in a timely manner.