# YouTube Video Engine - Architecture Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [API Design](#api-design)
6. [Security Considerations](#security-considerations)
7. [Deployment Architecture](#deployment-architecture)
8. [Monitoring and Logging](#monitoring-and-logging)

## System Overview

The YouTube Video Engine is a microservices-based application that automates video production from scripts. It orchestrates multiple external services to create professional videos with AI-generated voiceovers and background music.

### Key Features

- **Script Processing**: Intelligent parsing of scripts into timed segments
- **AI Voice Generation**: Professional voiceovers using ElevenLabs
- **Video Assembly**: Automated combination of voice and video segments
- **Music Integration**: AI-generated background music via GoAPI (Suno)
- **Asynchronous Processing**: Webhook-based job handling
- **Scalable Architecture**: Containerized deployment on Fly.io

## Architecture Diagram

```
┌─────────────────┐
│   Client Apps   │
│  (Web/Mobile)   │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐     ┌──────────────────┐
│   Fly.io Edge   │────▶│  Rate Limiter    │
│   (CDN/Proxy)   │     │  (Flask-Limiter) │
└─────────────────┘     └──────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│          Flask Application              │
│  ┌────────────┐  ┌─────────────────┐  │
│  │   API      │  │    Webhook      │  │
│  │  Routes    │  │   Handlers      │  │
│  └──────┬─────┘  └────────┬────────┘  │
│         │                  │           │
│         ▼                  ▼           │
│  ┌─────────────────────────────────┐  │
│  │      Service Layer              │  │
│  │  ┌──────────┐ ┌──────────────┐ │  │
│  │  │ Script   │ │  Media       │ │  │
│  │  │ Service  │ │  Service     │ │  │
│  │  └──────────┘ └──────────────┘ │  │
│  └─────────────────────────────────┘  │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│           External Services             │
├─────────────────┬───────────────────────┤
│   Airtable      │     NCA Toolkit       │
│   (Database)    │   (Media Processing)  │
├─────────────────┼───────────────────────┤
│   ElevenLabs    │      GoAPI            │
│ (Voice Gen)     │   (Music Gen)         │
└─────────────────┴───────────────────────┘
```

## Component Details

### 1. Flask Application Layer

The core application built with Flask handles:

- **Request Routing**: RESTful API endpoints
- **Request Validation**: Input sanitization and validation
- **Rate Limiting**: Protection against abuse
- **CORS Handling**: Cross-origin resource sharing

### 2. Service Layer

Encapsulates business logic and external service integrations:

#### Script Processing Service
- Parses scripts into segments
- Calculates timing and duration
- Manages segment ordering

#### Airtable Service
- Database operations (CRUD)
- Schema management
- Relationship handling

#### NCA Toolkit Service
- Video processing via FFmpeg
- File storage on Digital Ocean Spaces
- Media combination operations

#### ElevenLabs Service
- Text-to-speech conversion
- Voice customization
- Asynchronous job management

#### GoAPI Service
- AI music generation
- Style and duration control
- Background music integration

### 3. Webhook System

Handles asynchronous callbacks from external services:

- **Signature Validation**: Ensures webhook authenticity
- **Job Status Updates**: Updates Airtable records
- **Error Handling**: Manages failed operations
- **Event Logging**: Tracks all webhook events

## Data Flow

### 1. Script Processing Flow

```
Client → POST /api/v1/process-script
  ↓
Parse Script → Create Segments → Store in Airtable
  ↓
Return Segment IDs → Client
```

### 2. Voice Generation Flow

```
Client → POST /api/v1/generate-voiceover
  ↓
Create Job → Call ElevenLabs API → Return Job ID
  ↓
ElevenLabs → Webhook → Update Segment → Store Audio URL
```

### 3. Video Assembly Flow

```
Client → POST /api/v1/combine-segment-media
  ↓
Fetch Segment Data → Call NCA Toolkit → Create Combination Job
  ↓
NCA → Webhook → Update Segment → Store Combined Video URL
```

### 4. Final Production Flow

```
Client → POST /api/v1/combine-all-segments
  ↓
Fetch All Segments → Concatenate Videos → Store Result
  ↓
Client → POST /api/v1/generate-and-add-music
  ↓
Generate Music → Add to Video → Store Final Video
```

## API Design

### RESTful Principles

- **Resource-Based URLs**: `/api/v1/resource`
- **HTTP Methods**: GET, POST, PUT, DELETE
- **Status Codes**: Semantic HTTP status codes
- **JSON Payloads**: Consistent request/response format

### Endpoint Categories

1. **Script Processing**
   - `POST /api/v1/process-script`

2. **Voice Generation**
   - `POST /api/v1/generate-voiceover`

3. **Media Processing**
   - `POST /api/v1/combine-segment-media`
   - `POST /api/v1/combine-all-segments`

4. **Music Generation**
   - `POST /api/v1/generate-and-add-music`

5. **Job Management**
   - `GET /api/v1/jobs/{job_id}`

6. **System Health**
   - `GET /health`

### API Documentation

Interactive API documentation available at `/api/docs` using Swagger UI.

## Security Considerations

### 1. Authentication & Authorization

- **API Keys**: Service-level authentication
- **Rate Limiting**: Request throttling per IP
- **CORS Policy**: Controlled cross-origin access

### 2. Webhook Security

- **Signature Validation**: HMAC-SHA256 verification
- **Timestamp Validation**: Prevent replay attacks
- **IP Whitelisting**: Optional service IP restrictions

### 3. Data Security

- **HTTPS Only**: Encrypted communications
- **Input Validation**: Prevent injection attacks
- **Error Handling**: No sensitive data in errors

### 4. Environment Variables

```bash
# Core Configuration
FLASK_ENV=production
SECRET_KEY=<strong-random-key>

# Service API Keys
AIRTABLE_API_KEY=<key>
NCA_API_KEY=<key>
ELEVENLABS_API_KEY=<key>
GOAPI_API_KEY=<key>

# Webhook Secrets
WEBHOOK_SECRET_NCA=<secret>
WEBHOOK_SECRET_ELEVENLABS=<secret>
WEBHOOK_SECRET_GOAPI=<secret>

# Webhook Validation
WEBHOOK_VALIDATION_NCA_ENABLED=true
WEBHOOK_VALIDATION_ELEVENLABS_ENABLED=true
WEBHOOK_VALIDATION_GOAPI_ENABLED=true
```

## Deployment Architecture

### Container Configuration

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "app:app"]
```

### Fly.io Configuration

```toml
app = "youtube-video-engine"
primary_region = "ord"

[build]
  dockerfile = "Dockerfile"

[env]
  FLASK_ENV = "production"
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

[[services]]
  protocol = "tcp"
  internal_port = 8080

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [services.concurrency]
    type = "connections"
    hard_limit = 25
    soft_limit = 20

  [[services.tcp_checks]]
    interval = "10s"
    timeout = "2s"
    grace_period = "5s"
```

### Scaling Strategy

1. **Horizontal Scaling**: Multiple app instances
2. **Auto-scaling**: Based on request load
3. **Geographic Distribution**: Multi-region deployment
4. **Database Scaling**: Airtable handles scaling

## Monitoring and Logging

### 1. Application Logging

```python
# Structured JSON logging
{
    "timestamp": "2024-01-01T12:00:00Z",
    "level": "INFO",
    "service": "youtube-video-engine",
    "message": "Request processed",
    "metadata": {
        "endpoint": "/api/v1/process-script",
        "duration_ms": 234,
        "status_code": 200
    }
}
```

### 2. Health Monitoring

- **Endpoint**: `/health`
- **Checks**: All external service connections
- **Frequency**: Every 10 seconds
- **Alerts**: On service degradation

### 3. Performance Metrics

- **Request Duration**: Track API response times
- **Error Rates**: Monitor failure patterns
- **Service Health**: External API availability
- **Job Success Rate**: Async operation completion

### 4. Error Tracking

- **Centralized Logging**: All errors logged with context
- **Error Classification**: By service and severity
- **Alert Thresholds**: Automated notifications
- **Debug Information**: Request IDs for tracing

## Best Practices

### 1. Code Organization

```
youtube_video_engine/
├── api/              # API routes and endpoints
├── services/         # Business logic and integrations
├── utils/            # Shared utilities
├── tests/            # Test suite
└── docs/             # Documentation
```

### 2. Error Handling

- **Graceful Degradation**: Continue with partial functionality
- **Retry Logic**: Exponential backoff for transient failures
- **Circuit Breaker**: Prevent cascading failures
- **User-Friendly Messages**: Clear error communication

### 3. Testing Strategy

- **Unit Tests**: Service-level logic
- **Integration Tests**: API endpoint testing
- **End-to-End Tests**: Full workflow validation
- **Load Testing**: Performance benchmarks

### 4. Development Workflow

1. **Local Development**: Docker Compose setup
2. **Code Review**: PR-based workflow
3. **CI/CD Pipeline**: Automated testing and deployment
4. **Staging Environment**: Pre-production testing
5. **Production Deployment**: Blue-green deployment

## Future Enhancements

1. **Caching Layer**: Redis for performance
2. **Queue System**: Celery for job processing
3. **Analytics**: Usage tracking and insights
4. **Multi-language Support**: Voice and UI
5. **Advanced Features**: Video effects, transitions
6. **Machine Learning**: Script optimization
