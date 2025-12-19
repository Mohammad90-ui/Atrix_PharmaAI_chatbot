@echo off
echo ====================================
echo Clinical Trial Query Chatbot
echo ====================================
echo.

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install -r backend\requirements.txt --quiet

echo.
echo ====================================
echo Starting Backend API Server...
echo ====================================
echo.

start "Chatbot Backend" cmd /k "call venv\Scripts\activate.bat && cd backend && python app.py"

timeout /t 5 /nobreak > nul

echo.
echo ====================================
echo Starting React Frontend...
echo ====================================
echo.

start "Chatbot Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ====================================
echo Chatbot is starting!
echo ====================================
echo.
echo Backend API: http://localhost:8001
echo Frontend UI: http://localhost:5173
echo.
echo Press any key to open UI in browser...
pause > nul

start http://localhost:5173
