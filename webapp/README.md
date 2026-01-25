# Hall Ticket Generator Web Application

A React web application with Flask backend for generating hall tickets.

## Project Structure

```
webapp/
├── frontend/          # React application (Vite)
├── backend/           # Flask API server
└── README.md         # This file
```

## Setup

### Backend Setup

1. Install Python dependencies:
```bash
cd backend
python3 -m pip install -r backend/requirements.txt
```

2. Run the Flask server:
```bash
python3 app.py
```

The backend will run on `http://localhost:5001` (5000 is often used by AirPlay on macOS)

### Frontend Setup

1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

2. Run the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:3000`

## Usage

1. Start the backend server (port 5001)
2. Start the frontend development server (port 3000)
3. Open `http://localhost:3000` in your browser
4. Fill in the form:
   - School name and address
   - Upload student details Excel file
   - Upload timetable Excel file
   - Upload photos ZIP file (with class folders)
   - Optionally upload logo and signature images
5. Click "Generate Hall Tickets"
6. The generated PDFs will be downloaded as a ZIP file

## Production Build

### Frontend

```bash
cd frontend
npm run build
```

The built files will be in `frontend/dist/`

### Backend

**For Development:**
```bash
cd backend
python3 app.py
```

**For Production (using Gunicorn):**
```bash
cd backend
python3 -m pip install gunicorn
python3 -m gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Note: If `gunicorn` command is not found, use `python3 -m gunicorn` instead.

## Deployment

### Option 1: Separate Frontend and Backend

- Deploy frontend (static files) to a CDN or static hosting (Netlify, Vercel, etc.)
- Deploy backend to a cloud service (Heroku, AWS, DigitalOcean, etc.)

### Option 2: Combined Deployment

- Serve frontend static files from Flask
- Deploy as a single application

See `Dockerfile` for containerized deployment.
