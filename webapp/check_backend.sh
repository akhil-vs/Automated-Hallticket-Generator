#!/bin/bash
# Check if backend is running

echo "Checking backend server status..."

if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✓ Backend is running on http://localhost:5000"
    curl -s http://localhost:5000/api/health | python3 -m json.tool
else
    echo "✗ Backend is NOT running"
    echo ""
    echo "To start the backend:"
    echo "  cd webapp/backend"
    echo "  python3 app.py"
    echo ""
    echo "Or check if port 5000 is in use:"
    echo "  lsof -ti:5000"
fi
