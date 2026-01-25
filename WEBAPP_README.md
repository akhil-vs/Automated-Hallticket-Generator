# Hall Ticket Generator - Web Application

A modern React web application with Flask backend for generating hall tickets through a user-friendly interface.

## Quick Start

### Option 1: Using the Start Script (Easiest)

```bash
cd webapp
./start.sh
```

This will:
- Install dependencies (if needed)
- Start the backend server on port 5000
- Start the frontend server on port 3000
- Open http://localhost:3000 in your browser

### Option 2: Manual Setup

#### Backend Setup

```bash
cd webapp/backend
python3 -m pip install -r requirements.txt
python3 app.py
```

Backend runs on: http://localhost:5000

#### Frontend Setup

```bash
cd webapp/frontend
npm install
npm run dev
```

Frontend runs on: http://localhost:3000

## Features

- **Modern UI**: Beautiful, responsive React interface
- **File Upload**: Easy drag-and-drop file uploads
- **Real-time Validation**: Validates files before processing
- **Progress Indicators**: Shows generation progress
- **Automatic Download**: Downloads generated PDFs as ZIP file
- **Error Handling**: Clear error messages for troubleshooting

## Usage

1. Fill in school information (name and address)
2. Upload student details Excel file (multiple sheets, one per class)
3. Upload timetable Excel file
4. Upload student photos as a ZIP file (with class folders inside)
5. Optionally upload school logo and principal signature
6. Click "Generate Hall Tickets"
7. Download the generated ZIP file containing all PDFs

## Production Deployment

### Using Docker

```bash
cd webapp
docker-compose up -d
```

### Manual Deployment

1. **Build Frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy Backend**:
   - For development, use Flask's built-in server:
     ```bash
     cd backend
     python3 app.py
     ```
   - For production, use Gunicorn:
     ```bash
     cd backend
     python3 -m pip install gunicorn
     python3 -m gunicorn -w 4 -b 0.0.0.0:5000 app:app
     ```
   Note: If `gunicorn` command is not found, use `python3 -m gunicorn` instead.
   - Or use any WSGI server (uWSGI, Waitress, etc.)

3. **Serve Static Files**:
   - The Flask app is configured to serve the React build files
   - Or deploy frontend separately to a CDN/static host

### Hosting Options

- **Heroku**: Deploy both frontend and backend
- **AWS**: Use Elastic Beanstalk or EC2
- **DigitalOcean**: App Platform or Droplet
- **Vercel/Netlify**: Frontend + Serverless functions
- **Railway/Render**: Full-stack deployment

## File Structure

```
webapp/
├── frontend/              # React application
│   ├── src/
│   │   ├── App.jsx       # Main application component
│   │   └── App.css       # Styles
│   ├── package.json
│   └── vite.config.js    # Vite configuration
├── backend/               # Flask API
│   ├── app.py            # Main Flask application
│   └── requirements.txt  # Python dependencies
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Docker Compose setup
└── start.sh             # Quick start script
```

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/generate` - Generate hall tickets
- `DELETE /api/cleanup/<request_id>` - Clean up temporary files

## Environment Variables

You can set these environment variables:

- `FLASK_ENV` - Set to `production` for production mode
- `UPLOAD_FOLDER` - Custom upload directory (default: system temp)

## Troubleshooting

### CORS Errors
- Make sure backend is running on port 5000
- Check that CORS is enabled in `app.py`

### File Upload Issues
- Check file size limits (default: 500MB)
- Ensure files are in correct format (.xlsx, .zip, .png, .jpg)

### Import Errors
- Make sure you're running from the project root
- Check that all Python modules are in the correct location

## Support

For issues or questions, check the main README.md or open an issue.
