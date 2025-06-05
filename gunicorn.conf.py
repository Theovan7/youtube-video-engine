"""Gunicorn configuration for YouTube Video Engine."""

import os
import multiprocessing

# Server socket
bind = "0.0.0.0:8080"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 50

# Restart workers after this many requests to prevent memory leaks
restart_workers = True

# Logging Configuration - CRITICAL for Fly.io
# All logs must go to stdout/stderr for Fly.io to capture them
accesslog = "-"  # stdout
errorlog = "-"   # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Log level - Set to INFO for production debugging
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

# Capture output from stdout/stderr in application code
capture_output = True

# Enable access logging
disable_redirect_access_to_syslog = True

# Process naming
proc_name = 'youtube-video-engine'

# Server mechanics
preload_app = True
daemon = False
raw_env = []

# SSL (not needed for Fly.io as they handle TLS termination)
keyfile = None
certfile = None

# Worker tmp directory
worker_tmp_dir = "/dev/shm"

# Graceful shutdown
graceful_timeout = 30
