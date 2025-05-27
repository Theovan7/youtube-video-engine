# 📊 Monitoring and Error Tracking Setup Guide

## Overview
This guide provides comprehensive instructions for setting up monitoring, alerting, and error tracking systems for the YouTube Video Engine production environment.

## 🔍 Monitoring Stack

### Primary Components
1. **Uptime Monitoring**: UptimeRobot or Pingdom
2. **Error Tracking**: Sentry
3. **Application Logging**: Built-in Flask logging
4. **Health Monitoring**: Custom health check endpoints
5. **Performance Metrics**: Built-in timing measurements

## 🌐 Uptime Monitoring Setup

### UptimeRobot Configuration (Recommended)

#### Step 1: Create UptimeRobot Account
1. Visit [UptimeRobot.com](https://uptimerobot.com)
2. Sign up for free account (50 monitors included)
3. Verify email and complete setup

#### Step 2: Configure Monitors

**1. Main Health Check Monitor**
- **Monitor Type**: HTTP(s)
- **URL**: `https://youtube-video-engine.fly.dev/health`
- **Friendly Name**: `YouTube Video Engine - Health Check`
- **Monitoring Interval**: 5 minutes
- **Timeout**: 30 seconds
- **Expected Status Code**: 200
- **Keyword**: `"status":"healthy"`

**2. API Endpoint Monitors**
- **Script Processing**: `https://youtube-video-engine.fly.dev/api/v1/process-script` (POST)
- **Webhook Endpoints**: Monitor webhook accessibility
- **Static Assets**: Monitor static file serving

**3. Monitor Configuration**:
```json
{
  "monitors": [
    {
      "type": "HTTP",
      "url": "https://youtube-video-engine.fly.dev/health",
      "name": "YVE - Health Check",
      "interval": 300,
      "timeout": 30,
      "status_codes": [200],
      "keyword": "healthy"
    },
    {
      "type": "HTTP", 
      "url": "https://youtube-video-engine.fly.dev/webhooks/elevenlabs",
      "name": "YVE - ElevenLabs Webhook",
      "interval": 900,
      "timeout": 30,
      "status_codes": [405],
      "method": "GET"
    },
    {
      "type": "HTTP",
      "url": "https://youtube-video-engine.fly.dev/webhooks/nca",
      "name": "YVE - NCA Webhook", 
      "interval": 900,
      "timeout": 30,
      "status_codes": [405],
      "method": "GET"
    },
    {
      "type": "HTTP",
      "url": "https://youtube-video-engine.fly.dev/webhooks/goapi",
      "name": "YVE - GoAPI Webhook",
      "interval": 900,
      "timeout": 30,
      "status_codes": [405],
      "method": "GET"
    }
  ]
}
```

#### Step 3: Configure Alert Contacts

**Email Notifications**:
- Primary: Development team email
- Secondary: Operations team email
- Escalation: Management team email

**Alert Settings**:
- **Down Alert**: Immediate notification
- **Up Alert**: When service recovers
- **Threshold**: 1 failed check = alert
- **Notification Interval**: Every 10 minutes until resolved

**Webhook Integration** (Optional):
```bash
# Slack webhook for team notifications
curl -X POST YOUR_SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "🚨 YouTube Video Engine Alert",
    "attachments": [{
      "color": "danger",
      "fields": [{
        "title": "Status",
        "value": "Service Down",
        "short": true
      }]
    }]
  }'
```

### Alternative: Pingdom Setup

#### Step 1: Create Pingdom Account
1. Visit [Pingdom.com](https://www.pingdom.com)
2. Sign up for account
3. Choose appropriate plan

#### Step 2: Configure Checks
- **Check Type**: HTTP Check
- **URL**: `https://youtube-video-engine.fly.dev/health`
- **Check Interval**: 1 minute
- **Alert Policy**: Immediate alerts

## 🐛 Error Tracking with Sentry

### Step 1: Sentry Setup

#### Create Sentry Project
1. Visit [Sentry.io](https://sentry.io)
2. Create new account or sign in
3. Create new project → Python → Flask
4. Copy the DSN (Data Source Name)

#### Install Sentry SDK
```bash
# Add to requirements.txt
echo "sentry-sdk[flask]==1.40.0" >> requirements.txt

# Install in virtual environment
./venv/bin/pip install sentry-sdk[flask]==1.40.0
```

### Step 2: Configure Sentry in Application

#### Update Flask Configuration
Add to `config.py`:
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

class Config:
    # ... existing config ...
    
    # Sentry Configuration
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    SENTRY_ENVIRONMENT = os.environ.get('SENTRY_ENVIRONMENT', 'production')
    SENTRY_RELEASE = os.environ.get('SENTRY_RELEASE', '1.0.0')
    
    @staticmethod
    def init_sentry():
        if Config.SENTRY_DSN:
            sentry_logging = LoggingIntegration(
                level=logging.INFO,        # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            )
            
            sentry_sdk.init(
                dsn=Config.SENTRY_DSN,
                integrations=[
                    FlaskIntegration(transaction_style='endpoint'),
                    sentry_logging,
                ],
                environment=Config.SENTRY_ENVIRONMENT,
                release=Config.SENTRY_RELEASE,
                traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
                profiles_sample_rate=0.1,  # 10% for profiling
                before_send=filter_sentry_events,
            )
```

#### Initialize Sentry in Application
Update `app.py`:
```python
def create_app(config_name='production'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize Sentry
    from config import Config
    Config.init_sentry()
    
    # ... rest of app initialization
```

#### Environment Variables for Fly.io
```bash
# Set Sentry configuration
fly secrets set SENTRY_DSN="YOUR_SENTRY_DSN_HERE"
fly secrets set SENTRY_ENVIRONMENT="production"
fly secrets set SENTRY_RELEASE="v1.0.0"
```

### Step 3: Custom Error Tracking

#### Enhanced Error Context
Add to service files:
```python
import sentry_sdk
from sentry_sdk import capture_exception, capture_message, set_context, set_tag

def process_video_with_monitoring(video_id, segment_data):
    # Set context for better error tracking
    set_context("video_processing", {
        "video_id": video_id,
        "segment_count": len(segment_data),
        "processing_timestamp": datetime.now().isoformat()
    })
    
    set_tag("operation", "video_processing")
    set_tag("video_id", video_id)
    
    try:
        # Process video
        result = process_video(video_id, segment_data)
        
        # Track successful processing
        capture_message(
            f"Video {video_id} processed successfully",
            level="info"
        )
        
        return result
        
    except Exception as e:
        # Capture exception with context
        capture_exception(e)
        
        # Log additional context
        logger.error(f"Video processing failed for {video_id}: {str(e)}")
        
        raise
```

#### Custom Performance Monitoring
```python
import sentry_sdk
from sentry_sdk import start_transaction

def monitor_api_endpoint(endpoint_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            with start_transaction(
                op="http.server",
                name=endpoint_name,
                sampled=True
            ) as transaction:
                transaction.set_tag("endpoint", endpoint_name)
                
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    
                    # Track successful completion
                    transaction.set_status("ok")
                    
                    return result
                    
                except Exception as e:
                    # Track error
                    transaction.set_status("internal_error")
                    capture_exception(e)
                    raise
                    
                finally:
                    # Track timing
                    duration = time.time() - start_time
                    transaction.set_measurement("duration", duration, "second")
                    
        return wrapper
    return decorator

# Usage
@monitor_api_endpoint("process_script")
def process_script():
    # ... endpoint logic
    pass
```

## 📈 Application Metrics and Logging

### Enhanced Logging Configuration

#### Update Logging Setup
Add to `app.py`:
```python
import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

def setup_enhanced_logging(app):
    if not app.debug:
        # File handler with rotation
        file_handler = RotatingFileHandler(
            'logs/youtube_video_engine.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        # JSON formatter for structured logging
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_obj = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': record.levelname,
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno,
                    'message': record.getMessage(),
                }
                
                if hasattr(record, 'user_id'):
                    log_obj['user_id'] = record.user_id
                if hasattr(record, 'video_id'):
                    log_obj['video_id'] = record.video_id
                if hasattr(record, 'job_id'):
                    log_obj['job_id'] = record.job_id
                    
                return json.dumps(log_obj)
        
        file_handler.setFormatter(JSONFormatter())
        file_handler.setLevel(logging.INFO)
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        
        app.logger.info('YouTube Video Engine startup')
```

#### Performance Metrics Collection
```python
import time
from functools import wraps

class MetricsCollector:
    def __init__(self):
        self.metrics = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_error': 0,
            'response_times': [],
            'active_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0
        }
    
    def record_request(self, success=True, response_time=None):
        self.metrics['requests_total'] += 1
        
        if success:
            self.metrics['requests_success'] += 1
        else:
            self.metrics['requests_error'] += 1
            
        if response_time:
            self.metrics['response_times'].append(response_time)
            
        # Keep only last 1000 response times
        if len(self.metrics['response_times']) > 1000:
            self.metrics['response_times'] = self.metrics['response_times'][-1000:]
    
    def get_metrics_summary(self):
        response_times = self.metrics['response_times']
        
        return {
            'requests': {
                'total': self.metrics['requests_total'],
                'success': self.metrics['requests_success'],
                'error': self.metrics['requests_error'],
                'error_rate': (
                    self.metrics['requests_error'] / max(self.metrics['requests_total'], 1)
                )
            },
            'performance': {
                'avg_response_time': (
                    sum(response_times) / len(response_times) if response_times else 0
                ),
                'min_response_time': min(response_times) if response_times else 0,
                'max_response_time': max(response_times) if response_times else 0,
                'response_time_p95': (
                    sorted(response_times)[int(len(response_times) * 0.95)]
                    if response_times else 0
                )
            },
            'jobs': {
                'active': self.metrics['active_jobs'],
                'completed': self.metrics['completed_jobs'],
                'failed': self.metrics['failed_jobs']
            }
        }

# Global metrics collector
metrics_collector = MetricsCollector()
```

### Metrics Endpoint
Add to API routes:
```python
@app.route('/metrics')
def metrics():
    """Prometheus-style metrics endpoint."""
    return jsonify(metrics_collector.get_metrics_summary())
```

## 🚨 Alerting and Notifications

### Slack Integration

#### Webhook Setup
```python
import requests
import json

class SlackNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
    
    def send_alert(self, title, message, color="danger", fields=None):
        payload = {
            "text": title,
            "attachments": [{
                "color": color,
                "text": message,
                "fields": fields or [],
                "ts": int(time.time())
            }]
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    def send_error_alert(self, error_message, context=None):
        fields = []
        if context:
            for key, value in context.items():
                fields.append({
                    "title": key,
                    "value": str(value),
                    "short": True
                })
        
        self.send_alert(
            "🚨 YouTube Video Engine Error",
            error_message,
            color="danger",
            fields=fields
        )
    
    def send_recovery_alert(self, service_name):
        self.send_alert(
            "✅ YouTube Video Engine Recovery",
            f"{service_name} has recovered and is functioning normally",
            color="good"
        )

# Initialize notifier
slack_notifier = SlackNotifier(os.environ.get('SLACK_WEBHOOK_URL'))
```

### Email Alerts
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailNotifier:
    def __init__(self, smtp_server, smtp_port, username, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    def send_alert(self, to_emails, subject, body):
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = ", ".join(to_emails)
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            
            text = msg.as_string()
            server.sendmail(self.username, to_emails, text)
            server.quit()
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
```

### Health Check Alerts
```python
def check_service_health_with_alerts():
    """Enhanced health check with alerting."""
    health_status = check_service_health()
    
    unhealthy_services = [
        service for service, status in health_status.items()
        if status.get('status') != 'healthy'
    ]
    
    if unhealthy_services:
        # Send alert for unhealthy services
        context = {
            'unhealthy_services': ', '.join(unhealthy_services),
            'timestamp': datetime.now().isoformat(),
            'health_check_url': 'https://youtube-video-engine.fly.dev/health'
        }
        
        slack_notifier.send_error_alert(
            f"Services are unhealthy: {', '.join(unhealthy_services)}",
            context
        )
        
        # Log to Sentry
        sentry_sdk.capture_message(
            f"Health check failed for services: {unhealthy_services}",
            level="error"
        )
    
    return health_status
```

## 📊 Dashboard and Visualization

### Custom Health Dashboard
Create `templates/dashboard.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Video Engine Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .metric-card {
            background: #f5f5f5;
            padding: 20px;
            margin: 10px;
            border-radius: 8px;
            display: inline-block;
            min-width: 200px;
        }
        .healthy { border-left: 5px solid #28a745; }
        .unhealthy { border-left: 5px solid #dc3545; }
        .degraded { border-left: 5px solid #ffc107; }
    </style>
</head>
<body>
    <h1>YouTube Video Engine Dashboard</h1>
    
    <div id="metrics">
        <!-- Metrics will be loaded here -->
    </div>
    
    <div id="charts">
        <canvas id="responseTimeChart"></canvas>
        <canvas id="errorRateChart"></canvas>
    </div>
    
    <script>
        // Auto-refresh dashboard every 30 seconds
        setInterval(loadMetrics, 30000);
        loadMetrics();
        
        function loadMetrics() {
            fetch('/metrics')
                .then(response => response.json())
                .then(data => updateDashboard(data));
        }
        
        function updateDashboard(metrics) {
            // Update metric cards
            document.getElementById('metrics').innerHTML = `
                <div class="metric-card">
                    <h3>Total Requests</h3>
                    <p>${metrics.requests.total}</p>
                </div>
                <div class="metric-card">
                    <h3>Success Rate</h3>
                    <p>${(100 - metrics.requests.error_rate * 100).toFixed(2)}%</p>
                </div>
                <div class="metric-card">
                    <h3>Avg Response Time</h3>
                    <p>${metrics.performance.avg_response_time.toFixed(2)}s</p>
                </div>
                <div class="metric-card">
                    <h3>Active Jobs</h3>
                    <p>${metrics.jobs.active}</p>
                </div>
            `;
        }
    </script>
</body>
</html>
```

## 🔧 Implementation Checklist

### Uptime Monitoring
- [ ] Create UptimeRobot/Pingdom account
- [ ] Configure health check monitor (5-minute intervals)
- [ ] Set up webhook endpoint monitors
- [ ] Configure alert contacts (email, Slack)
- [ ] Test alert notifications
- [ ] Document escalation procedures

### Error Tracking
- [ ] Create Sentry project
- [ ] Install Sentry SDK
- [ ] Configure Sentry in application
- [ ] Set environment variables in Fly.io
- [ ] Add custom error context
- [ ] Test error capture and reporting
- [ ] Set up error alert rules

### Application Metrics
- [ ] Implement structured logging
- [ ] Add performance metrics collection
- [ ] Create metrics endpoint
- [ ] Set up log rotation
- [ ] Configure log aggregation
- [ ] Test metrics collection

### Alerting
- [ ] Set up Slack webhook
- [ ] Configure email notifications
- [ ] Implement health check alerts
- [ ] Test alert delivery
- [ ] Document alert response procedures
- [ ] Create runbook for common issues

### Dashboard
- [ ] Create health dashboard
- [ ] Add metrics visualization
- [ ] Set up auto-refresh
- [ ] Configure access controls
- [ ] Test dashboard functionality
- [ ] Document dashboard usage

## 📞 Maintenance and Support

### Regular Maintenance Tasks
- **Daily**: Review error logs and metrics
- **Weekly**: Analyze performance trends
- **Monthly**: Review and update alert thresholds
- **Quarterly**: Evaluate monitoring stack performance

### Alert Response Procedures
1. **Immediate Response** (< 5 minutes)
   - Acknowledge alert
   - Check system health dashboard
   - Verify service status

2. **Investigation** (5-15 minutes)
   - Review recent deployments
   - Check error logs and metrics
   - Identify root cause

3. **Resolution** (15-60 minutes)
   - Implement fix or workaround
   - Monitor recovery
   - Update stakeholders

4. **Post-Incident** (Within 24 hours)
   - Document incident details
   - Identify improvement opportunities
   - Update monitoring/alerting as needed

### Support Contacts
- **Primary On-Call**: Development team lead
- **Secondary**: Operations team member
- **Escalation**: Technical management
- **Critical Issues**: 24/7 support channel

---
*This monitoring setup ensures comprehensive visibility into the YouTube Video Engine's health, performance, and reliability in production.*
