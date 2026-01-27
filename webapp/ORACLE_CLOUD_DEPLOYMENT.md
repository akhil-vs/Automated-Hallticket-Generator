# Oracle Cloud Deployment Troubleshooting

## Common Issues and Solutions

### Issue: 404 Not Found on `/api/health`

This is usually caused by reverse proxy (nginx) configuration on Oracle Cloud.

## Solution 1: Check if App is Running

```bash
# SSH into your Oracle Cloud instance
ssh user@your-oracle-instance

# Check if the app is running
ps aux | grep gunicorn
# or
ps aux | grep python

# Check if port 5000 is listening
netstat -tlnp | grep 5000
# or
ss -tlnp | grep 5000
```

## Solution 2: Test Direct Port Access

Try accessing the app directly on port 5000:

```bash
# From your local machine
curl http://your-domain:5000/api/health

# Or if you have SSH access, test locally on the server
curl http://localhost:5000/api/health
```

If this works, the issue is with nginx/reverse proxy configuration.

## Solution 3: Configure Nginx (Most Common Fix)

Oracle Cloud often uses nginx as a reverse proxy. Create/update nginx configuration:

**Note**: If you don't have a domain name yet, use `server_name _;` to accept all server names (works with IP address).

### Create Nginx Config

```bash
sudo nano /etc/nginx/sites-available/hallticket-backend
```

**Option 1: If you have a domain name**, use `webapp/nginx-oracle-cloud.conf`

**Option 2: If you only have an IP address** (no domain), use `webapp/nginx-oracle-cloud-ip.conf` or add this configuration:

```nginx
server {
    listen 80 default_server;
    server_name _;  # Accepts all server names (works with IP address)

    # API endpoints - proxy to Flask
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Increase timeouts for file uploads
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }

    # Health check endpoint (alternative)
    location /health {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Root endpoint
    location = / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
    }
}
```

### Enable the Site

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/hallticket-backend /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## Solution 4: Check Gunicorn Configuration

Make sure Gunicorn is binding to the correct interface:

In `gunicorn_config.py`, ensure:
```python
bind = os.getenv('BIND', '0.0.0.0:5000')  # Should be 0.0.0.0, not 127.0.0.1
```

## Solution 5: Check Firewall/Security Rules

Oracle Cloud has security rules that might block port 5000.

1. **Check Oracle Cloud Console**:
   - Go to Networking → Security Lists
   - Ensure port 5000 (or 80/443) is open

2. **Check iptables** (if configured):
   ```bash
   sudo iptables -L -n
   ```

## Solution 6: Use Alternative Endpoints

The app now has multiple endpoints you can test:

```bash
# Try these endpoints
curl http://your-domain/api/health
curl http://your-domain/health
curl http://your-domain/
```

## Solution 7: Check Application Logs

```bash
# Check Gunicorn logs
journalctl -u your-service-name -f

# Or if running manually, check output
# Check where your logs are (configured in gunicorn_config.py)
tail -f /var/log/hallticket-backend/error.log
```

## Solution 8: Verify Deployment

### Check if Docker Container is Running

```bash
docker ps
docker logs <container-id>
```

### Check if Systemd Service is Running

```bash
sudo systemctl status hallticket-backend
sudo systemctl logs hallticket-backend -f
```

## Solution 9: Test with Different Paths

The app now supports:
- `/api/health` - Full path
- `/health` - Short path (no /api prefix)
- `/` - Root endpoint (for debugging)

Try all three to see which works.

## Quick Diagnostic Script

Create a test script:

```bash
#!/bin/bash
# test-backend.sh

DOMAIN="your-domain.com"

echo "Testing backend endpoints..."
echo ""

echo "1. Testing /api/health:"
curl -v http://$DOMAIN/api/health
echo ""
echo ""

echo "2. Testing /health:"
curl -v http://$DOMAIN/health
echo ""
echo ""

echo "3. Testing / (root):"
curl -v http://$DOMAIN/
echo ""
echo ""

echo "4. Testing direct port (if accessible):"
curl -v http://$DOMAIN:5000/api/health
```

Run it:
```bash
chmod +x test-backend.sh
./test-backend.sh
```

## Common Oracle Cloud Specific Issues

### 1. Oracle Cloud Load Balancer

If using Oracle Cloud Load Balancer:
- Check listener configuration
- Ensure backend set includes your instance
- Verify health check path is correct

### 2. Oracle Cloud Network Security

- Check Security Lists
- Check Network Security Groups
- Verify ingress rules allow HTTP/HTTPS traffic

### 3. Oracle Cloud Instance Firewall

```bash
# Check UFW (if enabled)
sudo ufw status

# Allow port 5000 (if needed)
sudo ufw allow 5000/tcp

# Or allow nginx
sudo ufw allow 'Nginx Full'
```

## Recommended Setup for Oracle Cloud

1. **Use Nginx as Reverse Proxy** (port 80/443)
2. **Run Flask on localhost:5000** (not exposed externally)
3. **Use systemd** to manage the service
4. **Set up SSL** with Let's Encrypt

### Example systemd Service

Create `/etc/systemd/system/hallticket-backend.service`:

```ini
[Unit]
Description=Hall Ticket Generator Backend
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/webapp/backend
Environment="PYTHONPATH=/path/to/webapp/backend"
Environment="FLASK_ENV=production"
ExecStart=/usr/local/bin/gunicorn -c gunicorn_config.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable hallticket-backend
sudo systemctl start hallticket-backend
sudo systemctl status hallticket-backend
```

## Still Getting 404?

1. **Check nginx error logs**:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

2. **Check nginx access logs**:
   ```bash
   sudo tail -f /var/log/nginx/access.log
   ```

3. **Verify the route exists**:
   ```bash
   # SSH into server
   curl http://localhost:5000/api/health
   ```

4. **Check if app is actually running**:
   ```bash
   ps aux | grep gunicorn
   netstat -tlnp | grep 5000
   ```

## Need More Help?

1. Check application logs
2. Check nginx logs
3. Verify firewall rules
4. Test direct port access
5. Review nginx configuration

The most common issue is nginx not properly proxying `/api/` requests to the Flask app on port 5000.
