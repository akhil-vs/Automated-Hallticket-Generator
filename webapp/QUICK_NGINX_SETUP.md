# Quick Nginx Setup for Oracle Cloud (No Domain Name)

If you only have an IP address and no domain name, follow these steps:

## Step 1: Get Your Public IP Address

```bash
# On your Oracle Cloud instance
curl ifconfig.me
# or
hostname -I
```

Note your public IP address (e.g., `123.45.67.89`)

## Step 2: Install Nginx (if not already installed)

```bash
sudo apt update
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
```

## Step 3: Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/hallticket-backend
```

Copy and paste this configuration:

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    # Accept all server names (works with IP address)
    server_name _;

    # Increase client body size for file uploads (500MB)
    client_max_body_size 500M;

    # API endpoints - proxy to Flask backend
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
        proxy_send_timeout 300s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Root endpoint for debugging
    location = / {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Logging
    access_log /var/log/nginx/hallticket-backend-access.log;
    error_log /var/log/nginx/hallticket-backend-error.log;
}
```

Save and exit (Ctrl+X, then Y, then Enter)

## Step 4: Enable the Site

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/hallticket-backend /etc/nginx/sites-enabled/

# Remove default nginx site (optional, to avoid conflicts)
sudo rm /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t
```

If test is successful, you'll see:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

## Step 5: Reload Nginx

```bash
sudo systemctl reload nginx
# or
sudo systemctl restart nginx
```

## Step 6: Test Your Backend

From your local machine (replace with your actual IP):

```bash
# Test health endpoint
curl http://YOUR_PUBLIC_IP/api/health

# Test alternative endpoints
curl http://YOUR_PUBLIC_IP/health
curl http://YOUR_PUBLIC_IP/
```

You should get JSON responses like:
```json
{"status": "ok", "message": "Hall Ticket Generator API is running", "version": "1.0.0"}
```

## Step 7: Verify Backend is Running

Make sure your Flask backend is running on port 5000:

```bash
# Check if port 5000 is listening
sudo netstat -tlnp | grep 5000
# or
sudo ss -tlnp | grep 5000

# Check if your app process is running
ps aux | grep gunicorn
# or
ps aux | grep python
```

## Troubleshooting

### If you get "502 Bad Gateway"

This means nginx can't reach your Flask app. Check:

1. **Is Flask running?**
   ```bash
   ps aux | grep gunicorn
   ```

2. **Is it listening on port 5000?**
   ```bash
   sudo netstat -tlnp | grep 5000
   ```

3. **Test locally on the server:**
   ```bash
   curl http://localhost:5000/api/health
   ```

### If you get "Connection refused"

Check firewall:
```bash
# Check if port 80 is open
sudo ufw status

# Allow HTTP if needed
sudo ufw allow 80/tcp
sudo ufw allow 'Nginx Full'
```

Also check Oracle Cloud Security Lists in the console.

### Check Nginx Logs

```bash
# Error logs
sudo tail -f /var/log/nginx/error.log

# Access logs
sudo tail -f /var/log/nginx/access.log
```

## Using Your IP Address

Once nginx is configured, you can access your API using:

- `http://YOUR_PUBLIC_IP/api/health`
- `http://YOUR_PUBLIC_IP/api/generate`
- `http://YOUR_PUBLIC_IP/health`

## Later: Adding a Domain Name

When you get a domain name:

1. Point your domain's A record to your Oracle Cloud IP
2. Update nginx config:
   ```nginx
   server_name your-domain.com;
   ```
3. Reload nginx
4. Access via: `http://your-domain.com/api/health`

## Quick Reference

```bash
# Edit nginx config
sudo nano /etc/nginx/sites-available/hallticket-backend

# Test config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Check nginx status
sudo systemctl status nginx

# View logs
sudo tail -f /var/log/nginx/error.log
```
