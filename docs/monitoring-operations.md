# Monitoring & Operations Guide

This guide covers setting up monitoring, alerts, and operational procedures for the YouTube Video Engine.

## Uptime Monitoring

### Option 1: UptimeRobot (Free Tier Available)

1. **Create Account**: Sign up at https://uptimerobot.com
2. **Add Monitor**:
   - Monitor Type: HTTP(s)
   - Friendly Name: YouTube Video Engine
   - URL: https://youtube-video-engine.fly.dev/health
   - Monitoring Interval: 5 minutes
   - Monitor Timeout: 30 seconds

3. **Configure Alerts**:
   - Add email notifications
   - Add SMS alerts (paid feature)
   - Configure webhook alerts to Slack/Discord

4. **Advanced Settings**:
   - HTTP Method: GET
   - Alert after X occurrences: 2 (to avoid false positives)
   - SSL check: Enabled

### Option 2: Pingdom

1. **Create Account**: Sign up at https://www.pingdom.com
2. **Add Uptime Check**:
   - Name: YouTube Video Engine Health
   - URL: https://youtube-video-engine.fly.dev/health
   - Check interval: 1 minute
   - Expected response: Contains "healthy"

3. **Alert Settings**:
   - Alert policy: High priority
   - Alert delay: 2 minutes
   - Notification channels: Email, SMS, Slack

### Option 3: Fly.io Built-in Monitoring

Fly.io provides basic monitoring out of the box:

```bash
# View app status
fly status -a youtube-video-engine

# View metrics dashboard
fly dashboard -a youtube-video-engine
```

## Application Logs

### Real-time Log Monitoring

```bash
# Stream logs in real-time
fly logs -a youtube-video-engine

# Stream logs with filtering
fly logs -a youtube-video-engine | grep ERROR
fly logs -a youtube-video-engine | grep webhook
```

### Log Analysis

```bash
# Export logs for analysis
fly logs -a youtube-video-engine --since 1h > logs.txt

# Search for specific patterns
grep "Failed to" logs.txt
grep "500" logs.txt
grep "timeout" logs.txt
```

## Error Alerts

### Email Alerts with Sentry

1. **Install Sentry SDK**:
   ```bash
   pip install sentry-sdk[flask]
   ```

2. **Configure in app.py**:
   ```python
   import sentry_sdk
   from sentry_sdk.integrations.flask import FlaskIntegration
   
   sentry_sdk.init(
       dsn="YOUR_SENTRY_DSN",
       integrations=[FlaskIntegration()],
       traces_sample_rate=0.1,
       environment="production"
   )
   ```

3. **Deploy with Sentry**:
   ```bash
   fly secrets set SENTRY_DSN=your-sentry-dsn
   fly deploy
   ```

### Slack Alerts

Create a simple alert script:

```python
# scripts/monitor_health.py
import requests
import json
import os
from datetime import datetime

SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK_URL')
APP_URL = "https://youtube-video-engine.fly.dev/health"

def check_health():
    try:
        response = requests.get(APP_URL, timeout=10)
        data = response.json()
        
        if response.status_code != 200 or data.get('status') != 'healthy':
            send_slack_alert(f"⚠️ Health check failed: {data}")
            return False
            
        # Check individual services
        services = data.get('services', {})
        failed_services = [s for s, status in services.items() if status != 'connected']
        
        if failed_services:
            send_slack_alert(f"⚠️ Services disconnected: {', '.join(failed_services)}")
            return False
            
    except Exception as e:
        send_slack_alert(f"🚨 Health check error: {str(e)}")
        return False
    
    return True

def send_slack_alert(message):
    if not SLACK_WEBHOOK:
        print(f"Alert: {message}")
        return
        
    payload = {
        "text": f"YouTube Video Engine Alert",
        "attachments": [{
            "color": "danger",
            "text": message,
            "ts": datetime.now().timestamp()
        }]
    }
    
    requests.post(SLACK_WEBHOOK, json=payload)

if __name__ == "__main__":
    check_health()
```

## Operational Procedures

### Daily Operations Checklist

1. **Morning Check (9 AM)**:
   - [ ] Review overnight alerts
   - [ ] Check Airtable for failed jobs
   - [ ] Verify all services are connected
   - [ ] Review error logs from past 24h

2. **Midday Check (2 PM)**:
   - [ ] Monitor API usage metrics
   - [ ] Check external service quotas
   - [ ] Review any customer complaints

3. **End of Day (6 PM)**:
   - [ ] Clear completed jobs older than 7 days
   - [ ] Archive processed webhook events
   - [ ] Check disk usage on Fly.io

### Weekly Maintenance

1. **Monday**: Review API performance metrics
2. **Wednesday**: Check and rotate API keys if needed
3. **Friday**: Backup Airtable data
4. **Sunday**: Run full system health check

### Incident Response

#### Level 1: Service Degradation
- One or more external services showing intermittent failures
- Response time > 5 seconds
- Actions:
  1. Check external service status pages
  2. Review recent deployments
  3. Monitor for 30 minutes

#### Level 2: Partial Outage
- One or more endpoints returning errors
- External services disconnected
- Actions:
  1. Check Fly.io status
  2. Verify API keys are valid
  3. Restart app if necessary: `fly apps restart -a youtube-video-engine`
  4. Notify stakeholders

#### Level 3: Complete Outage
- Health check failing
- App not responding
- Actions:
  1. Check Fly.io platform status
  2. Review recent deployments: `fly releases -a youtube-video-engine`
  3. Rollback if needed: `fly releases rollback -a youtube-video-engine`
  4. Escalate to senior team
  5. Post incident report

## Performance Monitoring

### API Response Times

Monitor key endpoints:

```python
# scripts/performance_check.py
import requests
import time

endpoints = [
    "/health",
    "/api/v1/status",
]

for endpoint in endpoints:
    start = time.time()
    response = requests.get(f"https://youtube-video-engine.fly.dev{endpoint}")
    duration = time.time() - start
    
    print(f"{endpoint}: {duration:.2f}s - Status: {response.status_code}")
```

### Resource Usage

```bash
# Check app metrics
fly scale show -a youtube-video-engine

# View resource usage
fly dashboard metrics -a youtube-video-engine
```

## Backup & Recovery

### Airtable Backup

1. **Manual Backup**:
   - Export each table as CSV monthly
   - Store in secure cloud storage

2. **Automated Backup Script**:
   ```python
   # scripts/backup_airtable.py
   from services.airtable_service import AirtableService
   import json
   from datetime import datetime
   
   airtable = AirtableService()
   backup_date = datetime.now().strftime("%Y%m%d")
   
   # Backup each table
   tables = ['Videos', 'Segments', 'Jobs', 'Webhook Events']
   for table in tables:
       records = airtable.table(table).all()
       with open(f'backup_{table}_{backup_date}.json', 'w') as f:
           json.dump(records, f, indent=2)
   ```

### Disaster Recovery Plan

1. **Data Loss**:
   - Restore from latest Airtable backup
   - Replay webhook events if needed
   - Notify affected users

2. **Service Outage**:
   - Deploy to backup region
   - Update DNS if needed
   - Monitor service restoration

3. **Security Breach**:
   - Rotate all API keys immediately
   - Review access logs
   - Notify security team
   - Document incident

## Maintenance Windows

### Scheduled Maintenance

- **Time**: Sundays 2-4 AM UTC
- **Frequency**: Monthly
- **Duration**: Max 2 hours
- **Activities**:
  - Dependency updates
  - Database optimization
  - Security patches
  - Performance tuning

### Maintenance Procedure

1. **Pre-maintenance** (T-24h):
   - Notify users via email/banner
   - Prepare rollback plan
   - Test changes in staging

2. **During Maintenance**:
   - Enable maintenance mode: `fly ssh console -C "touch maintenance.flag"`
   - Perform updates
   - Run health checks
   - Disable maintenance mode: `fly ssh console -C "rm maintenance.flag"`

3. **Post-maintenance**:
   - Verify all services
   - Run integration tests
   - Monitor for 1 hour
   - Send completion notice

## Key Metrics to Track

1. **Availability**: Target 99.9% uptime
2. **Response Time**: < 2s for all endpoints
3. **Error Rate**: < 0.1% of requests
4. **Job Success Rate**: > 95%
5. **Webhook Delivery**: > 99%

## Contact Information

### Escalation Path

1. **Level 1**: On-call engineer
2. **Level 2**: Team lead
3. **Level 3**: Platform team
4. **Level 4**: CTO

### External Services Support

- **Airtable**: support@airtable.com
- **ElevenLabs**: support@elevenlabs.io
- **GoAPI**: support@goapi.ai
- **NCA Toolkit**: support@nocodedevs.com
- **Fly.io**: support@fly.io
