#!/bin/bash

echo "===================================="
echo "Clinical Trial Query Chatbot"
echo "===================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Installing dependencies..."
pip install -r backend/requirements.txt --quiet

echo ""
echo "===================================="
echo "Starting Backend API Server..."
echo "===================================="
echo ""

# Start backend in background
(cd backend && python app.py) &
BACKEND_PID=$!

sleep 5

echo ""
echo "===================================="
echo "Starting React Frontend..."
echo "===================================="
echo ""

# Start UI in background
(cd frontend && npm run dev) &
UI_PID=$!

echo ""
echo "===================================="
echo "Chatbot is running!"
echo "===================================="
echo ""
echo "Backend API: http://localhost:8001"
echo "Frontend UI: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for both processes
wait $BACKEND_PID $UI_PID
