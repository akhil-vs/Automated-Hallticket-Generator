"""
Gunicorn configuration for production deployment.
"""
import multiprocessing
import os

# Server socket
bind = os.getenv('BIND', '0.0.0.0:5000')
backlog = 2048

# Worker processes
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.getenv('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'hallticket-backend'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Hall Ticket Generator Backend")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Hall Ticket Generator Backend")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Hall Ticket Generator Backend is ready. Spawning workers")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    server.log.info("Shutting down Hall Ticket Generator Backend")
