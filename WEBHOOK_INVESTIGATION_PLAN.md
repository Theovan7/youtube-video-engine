# Webhook Delivery Investigation & Solution Plan

## Current Situation Analysis

### What We Know:
1. **Files are processed quickly** - NCA completes video combination in seconds/minutes
2. **Files are stored permanently** - Already on DigitalOcean Spaces at `phi-bucket`
3. **Webhooks are not arriving** - Or arriving after hours of delay
4. **Airtable never gets updated** - Because webhook never triggers the update
5. **Files appear "deleted"** - Because Airtable never downloaded them from DO Spaces

### Architecture Flow:
```
1. Upload files to Airtable → Airtable stores permanently ✅
2. Send URLs to NCA → NCA downloads and processes ✅
3. NCA saves to DO Spaces → Files stored at phi-bucket ✅
4. NCA sends webhook → FAILS or DELAYED ❌
5. Webhook updates Airtable → Never happens ❌
6. Airtable downloads from DO → Never happens ❌
```

## Investigation Steps

### 1. Check Webhook Configuration

#### A. Verify Webhook URL Format
```python
# Current webhook URL format:
webhook_url = f"{config.WEBHOOK_BASE_URL}/webhooks/nca-toolkit?job_id={job_id}&operation=combine"

# Should be:
# https://youtube-video-engine.fly.dev/webhooks/nca-toolkit?job_id=xxx&operation=xxx
```

**Things to check:**
- Is the URL publicly accessible?
- SSL certificate valid?
- No authentication blocking webhooks?

#### B. Test Webhook Endpoint Directly
```bash
# Test from outside
curl -X POST https://youtube-video-engine.fly.dev/webhooks/nca-toolkit \
  -H "Content-Type: application/json" \
  -d '{"test": true, "job_id": "test123"}'

# Check if it reaches the app
fly logs --app youtube-video-engine | grep webhook
```

### 2. Analyze NCA Webhook Behavior

#### A. NCA Webhook Retry Policy
- Does NCA retry failed webhooks?
- What's the timeout for webhook delivery?
- Does NCA queue webhooks?

#### B. Common Issues:
1. **Timeout Issues**
   - NCA might timeout if webhook endpoint is slow
   - Default timeout might be too short

2. **SSL/TLS Issues**
   - Certificate validation failures
   - TLS version mismatch

3. **Network Issues**
   - Firewall blocking outbound from NCA
   - DNS resolution problems

4. **Queue Backlog**
   - NCA might have a webhook queue that's backed up
   - Rate limiting on webhook delivery

### 3. Fly.io Configuration Check

#### A. Inbound Traffic
```bash
# Check if app is receiving ANY webhook attempts
fly logs --app youtube-video-engine | grep POST | grep -v health

# Check machine status
fly status --app youtube-video-engine

# Check if there are any proxy/firewall rules
fly ips list --app youtube-video-engine
```

#### B. Response Time
- Is the webhook endpoint responding quickly?
- Any timeouts in processing?

### 4. Debug Webhook Content

Create a webhook debugging endpoint:
```python
@webhooks_bp.route('/debug-webhook', methods=['POST'])
def debug_webhook():
    """Log everything about incoming webhook"""
    logger.info("="*60)
    logger.info("DEBUG WEBHOOK RECEIVED")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Args: {dict(request.args)}")
    logger.info(f"Form: {dict(request.form)}")
    logger.info(f"JSON: {request.get_json(silent=True)}")
    logger.info(f"Data: {request.data}")
    logger.info("="*60)
    return jsonify({"status": "logged"}), 200
```

## Potential Root Causes

### 1. **NCA Webhook Queue Overload**
- If NCA has many customers, webhook delivery might be queued
- Solution: Implement polling as primary method

### 2. **Network Connectivity**
- NCA → Fly.io connection issues
- Solution: Use webhook.site to test NCA delivery

### 3. **Webhook Format Mismatch**
- NCA might be sending webhooks in unexpected format
- Solution: Log raw webhook data

### 4. **Rate Limiting**
- Either NCA or Fly.io might be rate limiting
- Solution: Check rate limit headers

## Comprehensive Solution Design

### Phase 1: Immediate Fixes

#### 1. Add Webhook Logging
```python
# In api/webhooks.py
@webhooks_bp.before_request
def log_webhook_attempt():
    """Log all webhook attempts"""
    logger.info(f"Webhook attempt: {request.method} {request.path}")
    logger.info(f"From IP: {request.remote_addr}")
    logger.info(f"User-Agent: {request.headers.get('User-Agent')}")
```

#### 2. Implement Basic Polling
```python
# New file: services/job_monitor.py
import time
from datetime import datetime, timedelta

class JobMonitor:
    def __init__(self):
        self.nca_service = NCAService()
        self.airtable = AirtableService()
    
    def check_stuck_jobs(self):
        """Check for jobs stuck in processing"""
        # Get jobs older than 5 minutes still processing
        stuck_jobs = self.airtable.get_jobs_by_status(
            status='processing',
            older_than_minutes=5
        )
        
        for job in stuck_jobs:
            external_id = job['fields'].get('External Job ID')
            if not external_id:
                continue
                
            # Check if file exists on DO Spaces
            file_url = self.construct_output_url(external_id)
            if self.check_file_exists(file_url):
                # File exists, process as completed
                self.process_completed_job(job, file_url)
    
    def construct_output_url(self, external_id):
        """Construct the likely output URL"""
        return f"https://phi-bucket.nyc3.digitaloceanspaces.com/phi-bucket/{external_id}_output_0.mp4"
    
    def check_file_exists(self, url):
        """Check if file exists at URL"""
        try:
            response = requests.head(url, timeout=5)
            return response.status_code == 200
        except:
            return False
```

### Phase 2: Robust Polling System

#### 1. Scheduled Job Checker
```python
# Add to app.py
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('interval', minutes=2)
def monitor_jobs():
    """Check for stuck jobs every 2 minutes"""
    try:
        monitor = JobMonitor()
        monitor.check_stuck_jobs()
    except Exception as e:
        logger.error(f"Job monitoring error: {e}")

scheduler.start()
```

#### 2. Smart Polling Strategy
```python
def get_polling_interval(job_age_minutes):
    """Dynamic polling interval based on job age"""
    if job_age_minutes < 5:
        return None  # Don't poll yet
    elif job_age_minutes < 15:
        return 2  # Poll every 2 minutes
    elif job_age_minutes < 60:
        return 5  # Poll every 5 minutes
    else:
        return 15  # Poll every 15 minutes for old jobs
```

### Phase 3: Enhanced Webhook Handling

#### 1. Webhook Retry Queue
```python
class WebhookQueue:
    def __init__(self):
        self.redis = redis.Redis()
    
    def add_expected_webhook(self, job_id, operation):
        """Track that we expect a webhook"""
        key = f"webhook:expected:{job_id}"
        data = {
            'operation': operation,
            'created_at': datetime.utcnow().isoformat(),
            'attempts': 0
        }
        self.redis.setex(key, timedelta(hours=24), json.dumps(data))
    
    def check_missing_webhooks(self):
        """Find webhooks that never arrived"""
        pattern = "webhook:expected:*"
        for key in self.redis.scan_iter(match=pattern):
            data = json.loads(self.redis.get(key))
            created = datetime.fromisoformat(data['created_at'])
            age = datetime.utcnow() - created
            
            if age > timedelta(minutes=5):
                # Webhook is overdue
                job_id = key.split(':')[-1]
                self.attempt_recovery(job_id, data['operation'])
```

#### 2. Webhook Health Monitoring
```python
class WebhookHealthMonitor:
    def __init__(self):
        self.metrics = {
            'received': 0,
            'processed': 0,
            'failed': 0,
            'last_received': None
        }
    
    def record_webhook(self, success=True):
        """Track webhook metrics"""
        self.metrics['received'] += 1
        if success:
            self.metrics['processed'] += 1
        else:
            self.metrics['failed'] += 1
        self.metrics['last_received'] = datetime.utcnow()
    
    def get_health_status(self):
        """Get webhook health status"""
        if not self.metrics['last_received']:
            return 'No webhooks received'
        
        time_since_last = datetime.utcnow() - self.metrics['last_received']
        if time_since_last > timedelta(hours=1):
            return 'WARNING: No webhooks in last hour'
        
        success_rate = self.metrics['processed'] / self.metrics['received']
        if success_rate < 0.9:
            return f'WARNING: Success rate {success_rate:.1%}'
        
        return 'Healthy'
```

## Implementation Priority

### Week 1: Immediate Fixes
1. **Day 1-2**: Add comprehensive webhook logging
2. **Day 3-4**: Implement basic file existence checking
3. **Day 5**: Deploy and monitor

### Week 2: Polling System
1. **Day 1-2**: Build job monitoring service
2. **Day 3-4**: Add scheduled polling
3. **Day 5**: Test with stuck jobs

### Week 3: Enhanced Monitoring
1. **Day 1-2**: Add webhook queue tracking
2. **Day 3-4**: Implement health monitoring
3. **Day 5**: Create monitoring dashboard

## Testing Plan

### 1. Webhook Testing
```bash
# Test webhook delivery
python test_webhook_delivery.py

# Monitor logs
fly logs --app youtube-video-engine | grep webhook

# Check file existence
python check_do_spaces_files.py
```

### 2. Polling Testing
```python
# Create test job
job_id = create_test_job()

# Wait for processing
time.sleep(60)

# Trigger manual poll
monitor = JobMonitor()
monitor.check_specific_job(job_id)
```

### 3. Load Testing
```python
# Create multiple jobs
for i in range(10):
    create_combination_job(f"test_segment_{i}")

# Monitor completion rate
monitor_completion_rate()
```

## Metrics to Track

1. **Webhook Metrics**
   - Webhooks received per hour
   - Average delay from job creation
   - Success/failure rate

2. **Job Metrics**
   - Jobs created per hour
   - Average processing time
   - Stuck job rate

3. **Recovery Metrics**
   - Jobs recovered by polling
   - Average recovery time
   - False positive rate

## Fallback Strategies

1. **If webhooks completely fail**: Use polling as primary method
2. **If DO Spaces is slow**: Add caching layer
3. **If Airtable updates fail**: Queue updates for retry

## Configuration Changes

```env
# Add to .env
ENABLE_JOB_POLLING=true
POLLING_INTERVAL_MINUTES=2
WEBHOOK_TIMEOUT_MINUTES=5
MAX_POLLING_AGE_HOURS=24

# Redis for job tracking
REDIS_URL=redis://localhost:6379

# Monitoring
ENABLE_WEBHOOK_MONITORING=true
ALERT_EMAIL=your-email@example.com
```

This comprehensive plan should help us identify why webhooks are delayed and implement a robust solution with polling as backup.