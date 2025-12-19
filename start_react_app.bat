@echo off
echo ====================================
echo Clinical Trial Query Chatbot (React)
echo ====================================
echo.

echo Starting Backend API...
start "Chatbot Backend" cmd /k "cd backend && python app.py"

echo Waiting for backend...
timeout /t 5 /nobreak > nul

echo Starting React Frontend...
cd frontend
start "Chatbot Frontend" cmd /k "npm run dev"

echo.
echo ====================================
echo Application Started!
echo Backend: http://localhost:8001
echo Frontend: http://localhost:5173
echo ====================================
echo.

start http://localhost:5173
