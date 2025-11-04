"""
Gunicorn configuration for AstroSurge WebApp
"""
import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.getenv('FLASK_PORT', '5000')}"
backlog = 2048

# Worker processes
# Default to 2 workers, can be overridden via GUNICORN_WORKERS env var
workers = int(os.getenv('GUNICORN_WORKERS', '2'))
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'astrosurge-webapp'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

