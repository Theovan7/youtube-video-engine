# 🚀 AI Deployment Agent - GENERIC Deployment Process

## **CRITICAL UPDATE: Mandatory Code Verification Added**

After discovering that health checks can pass while deployed code remains stale, **SSH code verification is now MANDATORY** for all deployments.

---

## **Enhanced 7-Step Deployment Process** (Universal Template)

### Step 1: Pre-Deployment Check & Status Review

**Tools Used:**
- `fly-apps-list` - Verify app exists in organization  
- `fly-status` - Check current version, health, and overall status
- `fly-machine-list` - Get detailed machine configuration
- `read_file` - Review previous deployment log

**Actions:**
```bash
fly-apps-list org=personal                    # Confirm app exists
fly-status app=youtube-video-engine           # Current version & health
fly-machine-list app=youtube-video-engine     # Machine details & env vars
read_file agent_files/deployment_log.md       # Review deployment history
```

**Verification Points:**
- App exists and is accessible
- Current version number
- Health check status (HTTP + TCP)
- Machine state and configuration
- Previous deployment patterns

### Step 2: Project Structure & Configuration Validation

**Tools Used:**
- `list_directory` - Browse project structure
- `read_file` - Validate key configuration files

**Actions:**
```bash
list_directory ${PROJECT_ROOT}                # Verify all files present
read_file fly.toml                           # Check Fly configuration
read_file Dockerfile                         # Verify build instructions  
read_file requirements.txt                   # Check dependencies
read_file app.py                            # Verify main application file
```

**Validation Points:**
- Essential files present (Dockerfile, fly.toml, requirements.txt, app.py)
- Configuration settings are correct
- Build instructions are valid
- No missing critical files

### Step 3: Environment Variables Review & Management

**Tools Used:**
- `fly-machine-list` - View current environment variables
- `fly-machine-update` - Update environment variables if needed

**Actions:**
```bash
fly-machine-list app=youtube-video-engine     # Check current env vars
# If updates needed:
fly-machine-update app=youtube-video-engine   # Update environment variables
  id=${MACHINE_ID}
  env=["VAR_NAME=value", "OTHER_VAR=value"]
```

**Note**: Environment variables are preserved automatically during deployment.

### Step 4: Execute Full Deployment

**Tools Used:**
- `execute_command` - Run deployment command

**Actions:**
```bash
cd ${PROJECT_ROOT} && fly deploy              # Full deployment
```

**Deployment Process:**
- Dockerfile build process (`COPY . .` captures ALL local changes)
- New image creation with unique tag
- Version increment (e.g., N → N+1)
- Rolling update to new image
- Automatic health check validation
- DNS configuration check

**Build Understanding:**
- Layer caching optimizes build time
- `COPY . .` layer rebuilds when local code changes
- If verification fails, may need `fly deploy --force` to rebuild all layers

### Step 5: Post-Deployment Health Check

**Tools Used:**
- `fly-status` - Verify new version deployed
- `fly-machine-list` - Confirm machine configuration
- `fly-logs` - Check for deployment issues (if needed)

**Actions:**
```bash
fly-status app=youtube-video-engine           # Verify new version
fly-machine-list app=youtube-video-engine     # Confirm machine config
# If issues detected:
fly-logs app=youtube-video-engine            # Debug deployment
```

**Verification Points:**
- ✅ Version number incremented
- ✅ New image tag created and deployed
- ✅ New release ID generated
- ✅ New instance ID created
- ✅ Health checks passing (HTTP + TCP)
- ✅ Machine state = "started"
- ✅ All services connected

**⚠️ CRITICAL WARNING**: Health checks passing ≠ Code updated!

### Step 6: 🚨 **MANDATORY Code Verification via SSH**

**Tools Used:**
- `fly-machine-exec` - SSH into running container for code verification

**Actions:**
```bash
# Get current machine ID (DYNAMIC - changes between deployments)
MACHINE_ID=$(fly-machine-list app=youtube-video-engine --json | jq -r '.[0].id')

# ESSENTIAL: Verify deployed code matches local changes
fly-machine-exec app=youtube-video-engine command="grep -n '${VERIFICATION_PATTERN}' ${TARGET_FILE}" id=${MACHINE_ID}

# Template verification commands:
fly-machine-exec app=youtube-video-engine command="grep -n '${YOUR_CODE_PATTERN}' ${TARGET_FILE}" id=${MACHINE_ID}
fly-machine-exec app=youtube-video-engine command="head -50 ${TARGET_FILE}" id=${MACHINE_ID}
fly-machine-exec app=youtube-video-engine command="ls -la ${TARGET_DIRECTORY}" id=${MACHINE_ID}
fly-machine-exec app=youtube-video-engine command="stat ${TARGET_FILE}" id=${MACHINE_ID}
```

**Verification Templates:**
```bash
# Search for specific code changes
fly-machine-exec app=youtube-video-engine command="grep -n '${CODE_PATTERN}' ${FILE_PATH}" id=${MACHINE_ID}

# Check file modification timestamps  
fly-machine-exec app=youtube-video-engine command="stat ${FILE_PATH}" id=${MACHINE_ID}

# View specific line ranges
fly-machine-exec app=youtube-video-engine command="sed -n '${START_LINE},${END_LINE}p' ${FILE_PATH}" id=${MACHINE_ID}

# Verify function definitions
fly-machine-exec app=youtube-video-engine command="grep -n 'def ${FUNCTION_NAME}' ${FILE_PATH}" id=${MACHINE_ID}
```

**Dynamic Machine ID:**
- **Get Machine ID**: `fly-machine-list app=youtube-video-engine` (first result)
- **JSON Parsing**: `fly-machine-list app=youtube-video-engine --json | jq -r '.[0].id'`

**Verification Results:**
- ✅ **SUCCESS**: Code found in deployed container → Deployment complete
- ❌ **FAILURE**: Code missing → Redeploy required with `fly deploy --force`

### Step 7: Documentation & Memory Storage

**Tools Used:**
- `get_current_time` - Get Perth, WA timestamp
- `write_file` - Update deployment log
- `store_memory` - Remember deployment patterns

**Actions:**
```bash
get_current_time timezone=Australia/Perth     # Perth timestamp
write_file agent_files/deployment_log.md      # Update complete log
store_memory deployment_details               # Store deployment pattern
```

**Documentation Updates:**
- New version details
- Image and release information
- Deployment timing
- Health check results
- **Code verification results** (✅ or ❌)
- Any issues encountered
- Process improvements

---

## 🔄 **Universal Deployment Decision Matrix**

### **Full Deployment with Code Verification** (Version Increment):
- **When**: Code changes, configuration updates, dependency changes
- **Command**: `execute_command: cd ${PROJECT_ROOT} && fly deploy`
- **Process**: Build → Deploy → Health Check → **SSH Code Verification**
- **Result**: New version, new image, new instance, **verified code**
- **Time**: ~45-60 seconds + verification time
- **⚠️ CRITICAL**: Must include SSH verification step

### **Force Deployment** (When Code Verification Fails):
- **When**: Standard deployment passes health checks but code verification fails
- **Command**: `execute_command: cd ${PROJECT_ROOT} && fly deploy --force`
- **Result**: Rebuilds all Docker layers, ensures latest code deployment
- **Time**: ~60-90 seconds (rebuilds all layers)

### **Environment Variable Update** (No Version Change):
- **When**: Need to change env vars without code deployment
- **Command**: `fly-machine-update` with env parameter
- **Result**: Same version, updated configuration
- **Time**: ~5-10 seconds

### **Machine Restart** (Same Version):
- **When**: Memory issues, stuck processes, cache clearing
- **Command**: `fly-apps-restart --force-stop`
- **Result**: Same version, fresh process state
- **Time**: ~10-20 seconds

---

## 🚨 **Universal Error Recovery & Critical Lessons**

### **Code Verification Failure (CRITICAL ISSUE):**
**Symptoms:**
- Version increments (N → N+1)
- Health checks pass (HTTP + TCP)
- But deployed code missing latest changes

**Root Cause:**
- Docker layer caching issues
- Build context problems
- Stale `COPY . .` layer

**Solution:**
```bash
# 1. Verify local changes are saved
# 2. Force complete rebuild
execute_command: cd ${PROJECT_ROOT} && fly deploy --force
# 3. Re-verify code via SSH
fly-machine-exec app=youtube-video-engine command="grep -n '${CODE_PATTERN}' ${FILE_PATH}" id=${MACHINE_ID}
# 4. If still failing, check .dockerignore file
```

### **Build Failures:**
- Check Dockerfile syntax
- Verify requirements.txt dependencies
- Review build logs via `fly-logs`
- Force rebuild with `fly deploy --force`

### **Health Check Failures:**
- Verify health endpoint (usually `/health` or `/health/basic`)
- Check application startup via `fly-logs`
- Restart machine via `fly-apps-restart`
- Update environment variables if needed

### **Emergency Procedures:**
- `fly-apps-restart --force-stop` - Emergency restart
- `fly-machine-exec` - Execute debug commands
- `fly-logs` - Real-time debugging
- `execute_command: fly deploy --force` - Force deployment

---

## 🛠️ **Complete Tool Arsenal**

### **Fly.io Management Tools:**
- `fly-apps-list` - List all apps
- `fly-apps-restart` - Restart applications 
- `fly-status` - App status and health
- `fly-logs` - Application logs
- `fly-machine-list` - Machine details & env vars
- `fly-machine-update` - Update machine config & env vars
- `fly-machine-exec` - **SSH into containers (CRITICAL for code verification)**
- `fly-machine-create` - Create new machines
- `fly-machine-run` - Run one-off commands
- `fly-machine-start/stop/restart` - Machine lifecycle
- `fly-machine-status` - Detailed machine status

### **File System & Execution:**
- `read_file` / `write_file` - File operations
- `list_directory` - Browse project structure
- `execute_command` - Run terminal commands (including `fly deploy`)
- `search_files` - Find specific files
- `get_file_info` - File metadata

### **Monitoring & Documentation:**
- `get_current_time` - Perth timezone timestamps
- `store_memory` - Remember patterns and issues
- `retrieve_memory` - Recall previous deployments

---

## 📋 **Generic Commands Reference**

### **Standard Deployment Process:**
```bash
# 1. Check current status
fly-status app=youtube-video-engine

# 2. Execute deployment
execute_command: cd ${PROJECT_ROOT} && fly deploy

# 3. Verify health
fly-status app=youtube-video-engine

# 4. MANDATORY: Verify code deployed
MACHINE_ID=$(fly-machine-list app=youtube-video-engine --json | jq -r '.[0].id')
fly-machine-exec app=youtube-video-engine command="grep -n '${CODE_PATTERN}' ${FILE_PATH}" id=${MACHINE_ID}

# 5. Update log
write_file agent_files/deployment_log.md
```

### **Code Verification Commands (TEMPLATES):**
```bash
# Get current machine ID dynamically
MACHINE_ID=$(fly-machine-list app=youtube-video-engine --json | jq -r '.[0].id')

# Search for specific changes
fly-machine-exec app=youtube-video-engine command="grep -n '${SEARCH_PATTERN}' ${TARGET_FILE}" id=${MACHINE_ID}

# Check file timestamps
fly-machine-exec app=youtube-video-engine command="stat ${TARGET_FILE}" id=${MACHINE_ID}

# View file contents
fly-machine-exec app=youtube-video-engine command="head -${LINE_COUNT} ${TARGET_FILE}" id=${MACHINE_ID}

# List directory with timestamps
fly-machine-exec app=youtube-video-engine command="ls -la ${TARGET_DIRECTORY}" id=${MACHINE_ID}
```

### **Emergency Commands:**
```bash
# Force deployment (if code verification fails)
execute_command: cd ${PROJECT_ROOT} && fly deploy --force

# Emergency restart
fly-apps-restart --force-stop app=youtube-video-engine

# Debug logs
fly-logs app=youtube-video-engine

# Execute commands in container
MACHINE_ID=$(fly-machine-list app=youtube-video-engine --json | jq -r '.[0].id')
fly-machine-exec app=youtube-video-engine command="ps aux" id=${MACHINE_ID}
```

---

## 📊 **Universal Docker Build Process Understanding**

```dockerfile
# Layer-by-layer build understanding:
FROM python:3.11-slim                        # Base (cached)
WORKDIR /app                                 # Working dir (cached)
RUN apt-get update && apt-get install...     # System deps (cached)
COPY requirements.txt .                      # Requirements (cached if unchanged)
RUN pip install --no-cache-dir -r requirements.txt  # Python deps (cached)
COPY . .                                     # ← YOUR CODE (rebuilds when changed)
RUN useradd -m -u 1000 appuser...           # User setup (cached)
CMD ["gunicorn", "--bind"...]                # Startup (cached)
```

**Critical Points:**
- `COPY . .` captures ALL local changes
- Layer caching optimizes build time
- If code verification fails, Docker may have cached a stale layer
- Use `--force` flag to rebuild all layers when verification fails

---

## 🎯 **Universal Success Metrics**

### **Deployment Success Criteria:**
1. ✅ Version number incremented
2. ✅ New image tag created
3. ✅ Health checks passing (HTTP + TCP)
4. ✅ Machine state = "started"
5. ✅ **Code verification passes via SSH** ← **MANDATORY STEP**

### **Performance Benchmarks:**
- **Build Time**: ~15-20 seconds (optimized with layer caching)
- **Image Size**: Consistent (varies by project)
- **Health Check**: Immediate (< 10 seconds)
- **Total Deployment**: ~45-60 seconds + verification

---

## ⚠️ **CRITICAL LESSONS LEARNED**

### **Universal Code Verification Failure Pattern:**
- **Issue**: Health checks passed but deployed code was missing latest changes
- **Discovery**: SSH verification reveals code not found in deployed container
- **Resolution**: Force rebuild with `fly deploy --force`
- **Lesson**: **Health checks passing ≠ Code updated**

### **Mandatory Process Changes:**
1. **SSH code verification is now MANDATORY** for all deployments
2. Always verify specific code changes are deployed
3. If verification fails, use `fly deploy --force` to rebuild all layers
4. Document verification results in deployment log

### **Docker Layer Caching Gotchas:**
- Layer caching can cause stale code deployment
- `COPY . .` layer may not rebuild properly
- Force rebuild resolves caching issues
- Always verify deployed code matches local changes

---

## 🔧 **Variables for Customization**

### **Project-Specific Variables:**
```bash
PROJECT_ROOT="/Users/theovandermerwe/Dropbox/CODING2/ClaudeDesktop/ProjectHI/youtube_video_engine"
APP_NAME="youtube-video-engine"
```

### **Verification Variables (Customize per deployment):**
```bash
VERIFICATION_PATTERN="your_unique_code_change"
TARGET_FILE="/app/path/to/your/file.py"
TARGET_DIRECTORY="/app/your/directory"
FUNCTION_NAME="your_function_name"
START_LINE="100"
END_LINE="110"
LINE_COUNT="50"
```

### **Dynamic Runtime Variables:**
```bash
MACHINE_ID=$(fly-machine-list app=${APP_NAME} --json | jq -r '.[0].id')
```

---

This is the **generic, reusable deployment process** that can be applied to every redeploy by customizing the variables for each specific deployment scenario.