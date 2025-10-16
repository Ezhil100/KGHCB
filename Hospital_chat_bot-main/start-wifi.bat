@echo off
echo ================================================
echo  Hospital AI Assistant - WiFi Network Setup
echo ================================================
echo.
echo Your WiFi IP: 192.168.137.173
echo.
echo Starting Backend Server (FastAPI)...
echo Backend will be available at: http://192.168.137.173:8000
echo.

cd Backend
start "Backend Server" cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak > nul

echo.
echo Starting Frontend Server (Vite)...
echo Frontend will be available at: http://192.168.137.173:5173
echo.

cd ..\frontend
start "Frontend Server" cmd /k "npm run dev"

echo.
echo ================================================
echo  Servers Starting...
echo ================================================
echo.
echo Backend API: http://192.168.137.173:8000
echo Frontend App: http://192.168.137.173:5173
echo.
echo On your mobile device or other computer, open:
echo http://192.168.137.173:5173
echo.
echo Press Ctrl+C in each window to stop the servers
echo ================================================
