# Backend Deployment Guide

This guide covers deploying the backend API separately from the frontend.

**For separate frontend and backend deployment, see [SEPARATE_DEPLOYMENT.md](./SEPARATE_DEPLOYMENT.md)**

## Current Structure

The project has a mixed structure:
- **Root level**: Python modules (`excel_reader.py`, `pdf_generator.py`, etc.)
- **webapp/backend/**: Flask API application (`app.py`)
- **webapp/frontend/**: React frontend (optional for backend-only deployment)

## Backend-Only Deployment Options

### Option 1: Docker Deployment (Recommended)

#### Using the Backend Dockerfile

```bash
# From project root
cd webapp
docker build -f Dockerfile.backend -t hallticket-backend ..
docker run -p 5000:5000 hallticket-backend
```

#### Using Docker Compose

```bash
# From webapp directory
docker-compose -f docker-compose.backend.yml up -d
```

### Option 2: Direct Python Deployment

#### Requirements
- Python 3.9+
- All dependencies from `webapp/backend/requirements.txt`

#### Setup

```bash
# Install dependencies
pip install -r webapp/backend/requirements.txt

# Set PYTHONPATH to include root directory
export PYTHONPATH=/path/to/AutomatedHallticketGenerator:$PYTHONPATH

# Run the application
cd webapp/backend
python app.py
```

### Option 3: Production Server (Gunicorn)

#### Install Gunicorn
```bash
pip install gunicorn
```

#### Run with Gunicorn
```bash
# From project root
export PYTHONPATH=/path/to/AutomatedHallticketGenerator:$PYTHONPATH
cd webapp/backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### With systemd service (Linux)

Create `/etc/systemd/system/hallticket-backend.service`:

```ini
[Unit]
Description=Hall Ticket Generator Backend
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/AutomatedHallticketGenerator/webapp/backend
Environment="PYTHONPATH=/path/to/AutomatedHallticketGenerator"
ExecStart=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

## Environment Variables

- `FLASK_ENV`: Set to `production` for production deployment
- `PYTHONPATH`: Should include the project root directory
- `PORT`: Optional, defaults to 5000

## API Endpoints

- `GET /api/health`: Health check endpoint
- `POST /api/generate`: Generate hall tickets (main endpoint)

## Notes

1. **Module Imports**: The backend imports modules from the root directory using `sys.path`. Ensure `PYTHONPATH` is set correctly.

2. **File Uploads**: Temporary files are stored in `/tmp/hallticket_uploads` by default. Configure volumes or storage as needed.

3. **CORS**: Currently configured to allow all origins. Restrict in production:
   ```python
   CORS(app, resources={r"/api/*": {"origins": ["https://yourdomain.com"]}})
   ```

4. **Security**: 
   - Use environment variables for sensitive data
   - Enable HTTPS in production
   - Set proper CORS origins
   - Consider rate limiting

## Recommended Improvements

For better deployment structure, consider:

1. **Create a Python package**: Move modules into a package structure
2. **Separate config**: Use environment-based configuration
3. **Add logging**: Configure proper logging for production
4. **Add monitoring**: Integrate with monitoring tools (Prometheus, etc.)
