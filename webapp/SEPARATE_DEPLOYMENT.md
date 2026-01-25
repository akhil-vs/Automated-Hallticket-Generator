# Separate Frontend and Backend Deployment Guide

This guide explains how to deploy the frontend and backend separately, which is useful for:
- Scaling frontend and backend independently
- Using different hosting providers
- Better separation of concerns
- CDN for frontend, dedicated server for backend

## Architecture

```
┌─────────────┐         HTTP/HTTPS          ┌─────────────┐
│   Frontend  │ ──────────────────────────> │   Backend   │
│  (Nginx)    │                              │  (Flask)    │
│  Port 80    │                              │  Port 5000  │
└─────────────┘                              └─────────────┘
```

## Prerequisites

- Docker and Docker Compose installed
- Backend API URL (if deploying separately)

## Option 1: Deploy Backend Only

### Using Docker

```bash
# From project root
cd webapp
docker build -f Dockerfile.backend -t hallticket-backend ..
docker run -p 5000:5000 hallticket-backend
```

### Using Docker Compose

```bash
# From webapp directory
docker-compose -f docker-compose.backend.yml up -d
```

### Direct Python Deployment

```bash
# Install dependencies
pip install -r webapp/backend/requirements.txt

# Set environment
export FLASK_ENV=production
export PYTHONPATH=/path/to/AutomatedHallticketGenerator/webapp/backend

# Run with Gunicorn
cd webapp/backend
gunicorn -c gunicorn_config.py app:app
```

### Environment Variables

- `FLASK_ENV`: Set to `production`
- `PYTHONPATH`: Path to backend directory
- `PORT`: Optional, defaults to 5000

### Backend API Endpoints

- `GET /api/health`: Health check
- `POST /api/generate`: Generate hall tickets

## Option 2: Deploy Frontend Only

### Using Docker

```bash
# From project root
cd webapp
docker build -f Dockerfile.frontend -t hallticket-frontend ..
docker run -p 80:80 -e VITE_API_URL=http://your-backend-url:5000 hallticket-frontend
```

### Using Docker Compose

```bash
# From webapp directory
# Set your backend URL
export VITE_API_URL=http://your-backend-url:5000
docker-compose -f docker-compose.frontend.yml up -d
```

### Direct Nginx Deployment

1. Build the frontend:
```bash
cd webapp/frontend
npm install
npm run build
```

2. Copy `dist/` folder to your nginx server

3. Configure nginx (see `webapp/frontend/nginx.conf`)

4. Update API URL in nginx config or use environment variable

### Environment Variables

- `VITE_API_URL`: Backend API URL (e.g., `http://api.example.com:5000`)

**Important**: Environment variables must be set at **build time** for Vite. If you need to change the API URL after building, you'll need to rebuild the frontend.

## Option 3: Deploy Both Separately

### Step 1: Deploy Backend

```bash
# Deploy backend first
cd webapp
docker-compose -f docker-compose.backend.yml up -d

# Note the backend URL (e.g., http://your-server:5000)
```

### Step 2: Deploy Frontend

```bash
# Build frontend with backend URL
export VITE_API_URL=http://your-backend-url:5000
cd webapp
docker-compose -f docker-compose.frontend.yml up -d
```

### Step 3: Configure CORS

Make sure your backend allows requests from your frontend domain:

In `webapp/backend/app.py`, update CORS settings:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://your-frontend-domain.com", "https://your-frontend-domain.com"],
        "methods": ["GET", "POST", "DELETE", "OPTIONS", "PUT"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
}, supports_credentials=True)
```

## Production Considerations

### 1. HTTPS/SSL

- Use reverse proxy (nginx, Traefik) with SSL certificates
- Update `VITE_API_URL` to use `https://`
- Configure backend to accept HTTPS connections

### 2. Domain Configuration

**Frontend**: `https://halltickets.example.com`
**Backend**: `https://api.example.com` or `https://halltickets.example.com/api`

### 3. Nginx Reverse Proxy (Recommended)

If deploying frontend and backend on the same server:

```nginx
# Frontend
server {
    listen 80;
    server_name halltickets.example.com;
    root /usr/share/nginx/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
}

# Backend API
server {
    listen 80;
    server_name api.example.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. Environment-Specific Builds

Create build scripts for different environments:

```bash
# .env.production
VITE_API_URL=https://api.example.com

# Build
vite build --mode production
```

### 5. Health Checks

- Backend: `GET /api/health`
- Frontend: Check if `index.html` is served

## Troubleshooting

### Frontend can't connect to backend

1. Check `VITE_API_URL` is set correctly
2. Verify CORS settings in backend
3. Check network connectivity between frontend and backend
4. Verify backend is running and accessible

### CORS Errors

Update backend CORS configuration to include your frontend domain:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "https://your-domain.com"],
        ...
    }
})
```

### Environment Variables Not Working

Remember: Vite environment variables must be set at **build time**, not runtime. Rebuild the frontend if you change `VITE_API_URL`.

## Quick Start Commands

### Backend Only
```bash
cd webapp
docker-compose -f docker-compose.backend.yml up -d
```

### Frontend Only
```bash
export VITE_API_URL=http://your-backend:5000
cd webapp
docker-compose -f docker-compose.frontend.yml up -d
```

### Both Separately
```bash
# Terminal 1: Backend
cd webapp
docker-compose -f docker-compose.backend.yml up

# Terminal 2: Frontend (after backend is running)
export VITE_API_URL=http://localhost:5000
docker-compose -f docker-compose.frontend.yml up
```

## File Structure

```
webapp/
├── Dockerfile.backend          # Backend-only Dockerfile
├── Dockerfile.frontend         # Frontend-only Dockerfile
├── docker-compose.backend.yml  # Backend compose file
├── docker-compose.frontend.yml # Frontend compose file
└── frontend/
    └── nginx.conf              # Nginx config for frontend
```
