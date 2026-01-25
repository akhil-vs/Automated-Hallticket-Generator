# Multi-stage build for production
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code (includes all Python modules)
COPY backend/ ./backend/

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Update Flask app to serve static files
RUN echo 'from flask import send_from_directory\nfrom app import app\n\n@app.route("/")\ndef index():\n    return send_from_directory("frontend/dist", "index.html")\n\n@app.route("/<path:path>")\ndef serve_static(path):\n    return send_from_directory("frontend/dist", path)\n' >> backend/app.py

EXPOSE 5000

CMD ["python", "backend/app.py"]
