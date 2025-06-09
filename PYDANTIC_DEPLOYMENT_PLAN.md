# Pydantic Migration Deployment Plan

## Deployment Strategy: Gradual Migration

We'll deploy the Pydantic migration in phases to ensure zero downtime and easy rollback if needed.

## Phase 1: Foundation Deployment (Immediate)

### 1.1 Add Pydantic Dependencies
✅ Already added to requirements.txt:
- `pydantic==2.10.4`
- `pydantic-settings==2.7.0`

### 1.2 Deploy Model Definitions
✅ All models created and tested:
- `models/webhooks/` - Phase 1 webhook models
- `models/api/` - Phase 2 API models  
- `models/services/` - Phase 3 service models
- `models/airtable_models.py` - Airtable record models
- `config_pydantic.py` - Pydantic configuration

### 1.3 Update Main Application Entry Points

#### Update app.py to use Pydantic config:
```python
# Add at top of app.py
from config_pydantic import get_settings
settings = get_settings()

# Replace config imports
# OLD: from config import get_config
# NEW: config = settings  # For backwards compatibility
```

#### Update API routes to use Pydantic (gradual):
- Keep existing routes working
- Add new Pydantic routes alongside
- Gradually migrate endpoints

## Phase 2: Webhook Integration (Day 1)

### 2.1 Update Webhook Handlers
Replace webhook validation with Pydantic models:

```python
# api/webhooks.py
from models.webhooks.nca_models import NCAWebhookPayload
from models.webhooks.goapi_models import GoAPIWebhookPayload
from models.webhooks.elevenlabs_models import ElevenLabsWebhookPayload

@app.route('/webhooks/nca-toolkit', methods=['POST'])
def nca_webhook():
    try:
        payload = NCAWebhookPayload(**request.json)
        # Existing logic continues...
    except ValidationError as e:
        return {"error": "Invalid webhook payload", "details": e.errors()}, 400
```

### 2.2 Benefits Immediate
- ✅ Better webhook validation
- ✅ Clear error messages for debugging
- ✅ Type safety in webhook processing

## Phase 3: Service Integration (Day 2-3)

### 3.1 Update Service Classes
Gradually update services to use Pydantic models:

```python
# services/elevenlabs_service.py
from models.services.elevenlabs_models import ElevenLabsTTSRequest, ElevenLabsTTSResponse

def generate_speech(self, text: str, voice_id: str) -> ElevenLabsTTSResponse:
    # Create validated request
    request = ElevenLabsTTSRequest(text=text, voice_id=voice_id)
    # Make API call and return validated response
```

### 3.2 Service Migration Order
1. **ElevenLabs** (most used, well-defined API)
2. **OpenAI** (script processing)
3. **GoAPI** (video generation)
4. **NCA** (media operations)

## Phase 4: API Endpoints (Day 4-5)

### 4.1 Update API Routes
Replace Marshmallow with Pydantic validation:

```python
# api/routes.py
from models.api.requests import ProcessScriptRequest
from models.api.responses import ProcessScriptResponse

@app.route('/api/v2/process-script', methods=['POST'])
def process_script():
    try:
        request = ProcessScriptRequest(**request.json)
        # Process with validated data
        response = ProcessScriptResponse(...)
        return response.dict()
    except ValidationError as e:
        return ErrorResponse(error="Validation failed", details=e.errors()).dict(), 400
```

### 4.2 Backwards Compatibility
- Keep existing v1 endpoints unchanged
- Add new v2 endpoints with Pydantic
- Gradually migrate clients to v2

## Phase 5: Configuration (Day 6)

### 5.1 Switch to Pydantic Configuration
```python
# Replace in all files:
# OLD: from config import Config; config = Config()
# NEW: from config_pydantic import get_settings; settings = get_settings()
```

### 5.2 Environment Validation
- Automatic validation on startup
- Clear error messages for missing env vars
- Type checking for all config values

## Deployment Commands

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Update Main App
```bash
# Backup current config import
cp app.py app.py.backup

# Update app.py to use Pydantic config
# (Manual edit or script)
```

### Step 3: Deploy Gradually
```bash
# Deploy webhook updates
git add models/ api/webhooks.py
git commit -m "Add Pydantic webhook models

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# Test webhooks in production
# Monitor for errors

# Deploy service updates (next day)
git add services/
git commit -m "Update services to use Pydantic models"

# Deploy API updates (next day)
git add api/routes_pydantic.py
git commit -m "Add Pydantic API endpoints"
```

## Rollback Plan

### If Issues Arise:
1. **Webhook issues**: Revert webhook handlers to original
2. **Service issues**: Services have backwards compatibility
3. **API issues**: v1 endpoints still work
4. **Config issues**: Fall back to original config.py

### Rollback Commands:
```bash
# Quick rollback
git revert <commit-hash>

# Or restore backup
cp app.py.backup app.py
```

## Monitoring During Deployment

### Key Metrics to Watch:
1. **Error rates** in webhook endpoints
2. **API response times** (should improve)
3. **Validation errors** in logs
4. **Memory usage** (should be similar or better)

### Success Indicators:
- ✅ No increase in error rates
- ✅ Better error messages in logs
- ✅ Webhook validation working
- ✅ API responses more consistent

## Testing in Production

### Post-Deployment Tests:
1. **Webhook delivery** from all services
2. **API endpoint validation** with real requests
3. **Service integration** with external APIs
4. **Configuration loading** in all environments

## Benefits Realized Immediately

### Day 1 (Webhooks):
- Better webhook debugging
- Clearer validation errors
- More robust webhook processing

### Day 2-3 (Services):
- Type-safe service calls
- Earlier error detection
- Better IDE support for development

### Day 4-5 (APIs):
- Consistent API responses
- Better client error handling
- Automatic API documentation

### Day 6 (Configuration):
- Environment validation on startup
- Type-safe configuration access
- Clear config error messages

## Final Validation

After full deployment:
1. Run comprehensive test suite
2. Verify all endpoints working
3. Check error logs for validation issues
4. Confirm performance metrics
5. Test rollback procedures

## Success Criteria

✅ **Zero downtime** during migration  
✅ **No functionality regression**  
✅ **Improved error handling**  
✅ **Better development experience**  
✅ **Robust type safety throughout**

The migration is designed to be **incremental, safe, and reversible** at each step.