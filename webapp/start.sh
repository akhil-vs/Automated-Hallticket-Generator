#!/bin/bash

# Start script for the web application

echo "Starting Hall Ticket Generator Web Application..."

# Check if backend dependencies are installed
if [ ! -d "backend/venv" ] && [ ! -f "backend/.installed" ]; then
    echo "Installing backend dependencies..."
    cd backend
    python3 -m pip install -r backend/requirements.txt
    touch .installed
    cd ..
else
    echo "Backend dependencies already installed (or using venv)"
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Start backend in background
echo "Starting backend server on port 5000..."
cd backend
python3 app.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Start frontend
echo "Starting frontend server on port 3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "=========================================="
echo "Application is running!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:5001"
echo ""
echo "Note: Using port 5001 (5000 is used by AirPlay on macOS)"
echo "Press Ctrl+C to stop both servers"
echo "=========================================="

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait
