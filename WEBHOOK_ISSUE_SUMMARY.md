# Webhook Delivery Issue Investigation Summary

## Current Findings

### 1. **Application Status**
- ✅ Application is running on Fly.io (`youtube-video-engine.fly.dev`)
- ✅ Health check endpoint is working
- ✅ All services (Airtable, ElevenLabs, GoAPI, NCA) show as connected
- ✅ DNS resolution is working correctly

### 2. **Webhook Endpoint Issues**
- ❌ Webhook endpoint `/webhooks/nca-toolkit` returns 500 error
- The error occurs even with a valid test payload
- This suggests an issue in the webhook handler code

### 3. **Potential Root Causes**

#### A. **Authentication/Validation Issue**
Looking at `api/webhooks.py`, the webhook handler has a decorator:
```python
@webhook_validation_required('nca-toolkit')
```
This validation might be failing and causing the 500 error.

#### B. **Missing Job ID in Airtable**
The webhook handler expects to find the job ID in Airtable:
```python
airtable_job_record = airtable.get_job(airtable_job_id)
if not airtable_job_record:
    logger.error(f"Airtable Job record {airtable_job_id} not found.")
```
Since our test job doesn't exist in Airtable, this could cause the error.

#### C. **Webhook Event Creation Failure**
The handler tries to create a webhook event record:
```python
webhook_event_id = airtable.create_webhook_event(
    service="NCA", 
    endpoint=payload.get('endpoint', 'N/A'),
    payload=payload,
    related_job_id=airtable_job_id
)
```
This might fail if the table structure doesn't match expectations.

### 4. **Why Webhooks Might Not Be Arriving**

Based on the investigation, here are the most likely reasons:

1. **NCA is not sending webhooks at all**
   - The webhook URL might not be properly registered with NCA
   - NCA might have issues with their webhook delivery system

2. **Webhooks are being sent but rejected**
   - The 500 error we see suggests webhooks might be arriving but failing to process
   - The webhook validation might be rejecting legitimate NCA callbacks

3. **Network/Firewall Issues**
   - Less likely since we can access the endpoint externally
   - But NCA might be blocked or rate-limited

### 5. **Evidence from Code Analysis**

From the webhook handler code:
- There's extensive error handling for missing/inconsistent NCA payloads
- Multiple fallback mechanisms for extracting job IDs and status
- Comments indicate NCA doesn't always return the custom_id properly
- Hardcoded fix for specific job suggests previous webhook issues

## Immediate Actions Needed

### 1. **Check Application Logs**
```bash
fly logs --app youtube-video-engine | grep -E "(webhook|error|500)" | tail -50
```

### 2. **Disable Webhook Validation Temporarily**
To test if validation is the issue, temporarily modify the webhook handler to bypass validation.

### 3. **Add Debug Logging**
Add a simple debug endpoint that logs all incoming requests without any processing:
```python
@webhooks_bp.route('/debug', methods=['POST'])
def debug_webhook():
    logger.info(f"Debug webhook: {request.get_json()}")
    return jsonify({"status": "ok"}), 200
```

### 4. **Test with External Service**
Use webhook.site to verify if NCA is actually sending webhooks:
1. Get a unique URL from webhook.site
2. Use it in an NCA request
3. Check if webhook.site receives anything

### 5. **Implement Polling as Backup**
Since webhooks are unreliable, implement a polling mechanism:
```python
def check_stuck_jobs():
    # Get jobs older than 5 minutes still in processing
    stuck_jobs = get_processing_jobs_older_than(minutes=5)
    
    for job in stuck_jobs:
        if job.external_id:
            # Check DO Spaces for output file
            expected_url = f"https://phi-bucket.nyc3.digitaloceanspaces.com/phi-bucket/{job.external_id}_output_0.mp4"
            if file_exists(expected_url):
                # Process as completed
                process_job_completion(job, expected_url)
```

## Recommended Solution Architecture

### Phase 1: Immediate Fix (Today)
1. Add comprehensive logging to webhook endpoint
2. Create a polling job that runs every 2-5 minutes
3. Check DO Spaces directly for completed files

### Phase 2: Robust Solution (This Week)
1. Implement proper webhook retry mechanism
2. Add webhook health monitoring
3. Create fallback to polling when webhooks fail
4. Store job state in Redis for faster lookups

### Phase 3: Long-term (Next Week)
1. Consider switching to a more reliable processing service
2. Implement proper event sourcing for job state
3. Add comprehensive monitoring and alerting

## Next Steps

1. **Check Fly.io logs** to see actual webhook errors
2. **Test with webhook.site** to verify NCA sends webhooks
3. **Implement basic polling** as immediate workaround
4. **Add debug logging** to understand webhook failures

The most likely scenario is that NCA is either:
- Not sending webhooks at all
- Sending them in a format that causes our handler to error
- Sending them but with significant delays

Given the 500 error we're seeing, it's possible webhooks ARE arriving but failing to process due to validation or data format issues.