# Dockerfile (place this in webapp/backend/Dockerfile)
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend code
COPY . .

# Set Python path
ENV PYTHONPATH=/app
 
# Expose port
EXPOSE 5001

# Run with gunicorn
CMD ["gunicorn", "-c", "gunicorn_config.py", "app:app"]