#!/bin/bash
# Helper script to free port 5000

echo "Freeing port 5000..."

# Kill processes using port 5000
lsof -ti:5000 | xargs kill -9 2>/dev/null

# Also kill common Flask/Gunicorn processes
pkill -9 -f "gunicorn.*5000" 2>/dev/null
pkill -9 -f "flask.*5000" 2>/dev/null
pkill -9 -f "python.*app.py" 2>/dev/null

sleep 1

if lsof -ti:5000 > /dev/null 2>&1; then
    echo "Warning: Port 5000 is still in use. Try:"
    echo "  lsof -ti:5000 | xargs kill -9"
else
    echo "Port 5000 is now free!"
fi
