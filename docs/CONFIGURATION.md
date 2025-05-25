# Configuration Guide

This guide covers all configuration options for the YouTube Video Engine.

## Environment Variables

### Required Variables

These environment variables must be set for the application to function:

| Variable | Description | Example |
|----------|-------------|---------|
| `AIRTABLE_API_KEY` | Airtable personal access token | `patXXXXXXXXXXXXXX` |
| `AIRTABLE_BASE_ID` | Airtable base identifier | `appXXXXXXXXXXXXXX` |
| `NCA_API_KEY` | NCA Toolkit API key | `nca_XXXXXXXXXXXX` |
| `ELEVENLABS_API_KEY` | ElevenLabs API key | `sk_XXXXXXXXXXXX` |
| `GOAPI_API_KEY` | GoAPI key for music generation | `goapi_XXXXXXXXXX` |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `FLASK_ENV` | Flask environment | `production` | `development` |
| `PORT` | Application port | `5000` | `8080` |
| `DEBUG` | Debug mode | `False` | `True` |
| `SECRET_KEY` | Flask secret key | Auto-generated | `your-secret-key` |
| `WEBHOOK_BASE_URL` | Base URL for webhooks | Derived from request | `https://yourdomain.com` |

### Webhook Configuration

#### Webhook Secrets

| Variable | Description | Required |
|----------|-------------|----------|
| `WEBHOOK_SECRET_NCA` | NCA webhook signature secret | If validation enabled |
| `WEBHOOK_SECRET_ELEVENLABS` | ElevenLabs webhook signature secret | If validation enabled |
| `WEBHOOK_SECRET_GOAPI` | GoAPI webhook signature secret | If validation enabled |

#### Webhook Validation

| Variable | Description | Default |
|----------|-------------|---------|
| `WEBHOOK_VALIDATION_NCA_ENABLED` | Enable NCA webhook validation | `False` |
| `WEBHOOK_VALIDATION_ELEVENLABS_ENABLED` | Enable ElevenLabs webhook validation | `False` |
| `WEBHOOK_VALIDATION_GOAPI_ENABLED` | Enable GoAPI webhook validation | `False` |

### Rate Limiting Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `RATELIMIT_ENABLED` | Enable rate limiting | `True` |
| `RATELIMIT_DEFAULT` | Default rate limit | `100/hour` |
| `RATELIMIT_STORAGE_URL` | Redis URL for rate limit storage | `memory://` |

### Service-Specific Configuration

#### ElevenLabs Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ELEVENLABS_DEFAULT_VOICE_ID` | Default voice ID | None |
| `ELEVENLABS_DEFAULT_STABILITY` | Default voice stability | `0.5` |
| `ELEVENLABS_DEFAULT_SIMILARITY_BOOST` | Default similarity boost | `0.5` |

#### NCA Toolkit Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `NCA_WEBHOOK_TIMEOUT` | Webhook timeout in seconds | `300` |
| `NCA_MAX_FILE_SIZE` | Maximum file size in MB | `500` |

#### GoAPI Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `GOAPI_DEFAULT_DURATION` | Default music duration in seconds | `180` |
| `GOAPI_MAX_DURATION` | Maximum music duration in seconds | `300` |

## Example .env File

```bash
# Core Configuration
FLASK_ENV=production
PORT=8080
SECRET_KEY=your-very-secret-key-here
DEBUG=False

# Airtable Configuration
AIRTABLE_API_KEY=patXXXXXXXXXXXXXX
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX

# External Service APIs
NCA_API_KEY=nca_XXXXXXXXXXXX
ELEVENLABS_API_KEY=sk_XXXXXXXXXXXX
GOAPI_API_KEY=goapi_XXXXXXXXXX

# Webhook Configuration
WEBHOOK_BASE_URL=https://your-app.fly.dev
WEBHOOK_SECRET_NCA=your-nca-webhook-secret
WEBHOOK_SECRET_ELEVENLABS=your-elevenlabs-webhook-secret
WEBHOOK_SECRET_GOAPI=your-goapi-webhook-secret

# Enable Webhook Validation
WEBHOOK_VALIDATION_NCA_ENABLED=True
WEBHOOK_VALIDATION_ELEVENLABS_ENABLED=True
WEBHOOK_VALIDATION_GOAPI_ENABLED=True

# Rate Limiting
RATELIMIT_ENABLED=True
RATELIMIT_DEFAULT=100/hour
RATELIMIT_STORAGE_URL=memory://

# Service Defaults
ELEVENLABS_DEFAULT_STABILITY=0.5
ELEVENLABS_DEFAULT_SIMILARITY_BOOST=0.5
GOAPI_DEFAULT_DURATION=180
```

## Airtable Configuration

### Required Tables

The application requires these tables in your Airtable base:

#### Videos Table

| Field Name | Field Type | Description |
|------------|------------|-------------|
| Name | Single line text | Video title |
| Script | Long text | Full script text |
| Status | Single select | `pending`, `processing`, `completed`, `failed` |
| Segments | Link to Segments | Related segments |
| Combined Segments Video | Attachment | Concatenated video |
| Music Prompt | Long text | Music generation prompt |
| Music | Attachment | Generated music file |
| Final Video | Attachment | Final video with music |
| Error Details | Long text | Error information |

#### Segments Table

| Field Name | Field Type | Description |
|------------|------------|-------------|
| Name | Formula/Auto | Segment identifier |
| Video | Link to Videos | Parent video |
| Text | Long text | Segment text |
| Order | Number | Segment order |
| Start Time | Number | Start time in seconds |
| End Time | Number | End time in seconds |
| Duration | Formula | `{End Time} - {Start Time}` |
| Voice ID | Single line text | ElevenLabs voice ID |
| Base Video | Attachment | Background video |
| Voiceover | Attachment | Generated voiceover |
| Combined | Attachment | Combined video |
| Status | Single select | `pending`, `processing`, `completed`, `failed` |

#### Jobs Table

| Field Name | Field Type | Description |
|------------|------------|-------------|
| Job ID | Formula/Auto | Unique job identifier |
| Type | Single select | `voiceover`, `combine_media`, `combine_segments`, `music_generation` |
| Status | Single select | `pending`, `processing`, `completed`, `failed` |
| Related Video | Link to Videos | Associated video |
| Related Segment | Link to Segments | Associated segment |
| External Job ID | Single line text | External service job ID |
| Webhook URL | URL | Callback URL |
| Request Payload | Long text | JSON request data |
| Response Payload | Long text | JSON response data |
| Error Details | Long text | Error information |
| Created At | Created time | Job creation time |
| Updated At | Last modified time | Last update time |

#### Webhook Events Table

| Field Name | Field Type | Description |
|------------|------------|-------------|
| Event ID | Autonumber | Unique event ID |
| Service | Single select | `nca`, `elevenlabs`, `goapi` |
| Endpoint | Single line text | Webhook endpoint |
| Raw Payload | Long text | Raw webhook data |
| Processed | Checkbox | Processing status |
| Related Job | Link to Jobs | Associated job |
| Success | Checkbox | Success status |
| Created At | Created time | Event time |

## Deployment Configuration

### Fly.io Secrets

Set production secrets using the Fly CLI:

```bash
# Set required secrets
fly secrets set AIRTABLE_API_KEY=patXXXXXXXXXXXXXX
fly secrets set AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
fly secrets set NCA_API_KEY=nca_XXXXXXXXXXXX
fly secrets set ELEVENLABS_API_KEY=sk_XXXXXXXXXXXX
fly secrets set GOAPI_API_KEY=goapi_XXXXXXXXXX

# Set webhook secrets
fly secrets set WEBHOOK_SECRET_NCA=your-nca-secret
fly secrets set WEBHOOK_SECRET_ELEVENLABS=your-elevenlabs-secret
fly secrets set WEBHOOK_SECRET_GOAPI=your-goapi-secret

# Enable webhook validation
fly secrets set WEBHOOK_VALIDATION_NCA_ENABLED=True
fly secrets set WEBHOOK_VALIDATION_ELEVENLABS_ENABLED=True
fly secrets set WEBHOOK_VALIDATION_GOAPI_ENABLED=True
```

### Docker Configuration

The application uses a multi-stage Dockerfile for optimal image size:

```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "app:app"]
```

## Security Best Practices

1. **API Keys**: Never commit API keys to version control
2. **Webhook Secrets**: Use strong, unique secrets for each service
3. **Environment Files**: Add `.env` to `.gitignore`
4. **Production Secrets**: Use Fly.io secrets management
5. **HTTPS Only**: Always use HTTPS in production
6. **Rate Limiting**: Configure appropriate rate limits
7. **Input Validation**: All inputs are validated before processing

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   - Error: `KeyError: 'AIRTABLE_API_KEY'`
   - Solution: Ensure all required environment variables are set

2. **Invalid Airtable Base**
   - Error: `Invalid base ID`
   - Solution: Verify `AIRTABLE_BASE_ID` matches your base

3. **Webhook Signature Validation Failure**
   - Error: `401 Unauthorized`
   - Solution: Check webhook secrets match service configuration

4. **Rate Limit Exceeded**
   - Error: `429 Too Many Requests`
   - Solution: Implement request throttling or increase limits

### Debug Mode

Enable debug mode for detailed error information:

```bash
FLASK_ENV=development
DEBUG=True
```

**Warning**: Never enable debug mode in production!

## Performance Tuning

### Gunicorn Workers

Adjust based on CPU cores:

```bash
# Formula: (2 × CPU cores) + 1
# For 2 cores:
gunicorn --workers 5 app:app
```

### Connection Pooling

For high-traffic applications, implement connection pooling:

```python
# In config.py
AIRTABLE_CONNECTION_POOL_SIZE = 10
NCA_REQUEST_TIMEOUT = 30
ELEVENLABS_REQUEST_TIMEOUT = 60
```

### Caching

Implement caching for frequently accessed data:

```python
# Future enhancement
CACHE_TYPE = 'redis'
CACHE_REDIS_URL = 'redis://localhost:6379/0'
CACHE_DEFAULT_TIMEOUT = 300
```
