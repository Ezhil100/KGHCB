@echo off
echo ========================================
echo Hospital Chatbot - Mobile Access Setup
echo ========================================
echo.

echo Your IP Address:
ipconfig | findstr /i "IPv4"
echo.

echo ========================================
echo Starting Backend Server...
echo ========================================
cd /d "%~dp0Hospital_chat_bot-main\Backend"
start "Hospital Chatbot Backend" cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo Starting Frontend Server...
echo ========================================
cd /d "%~dp0Hospital_chat_bot-main\frontend"
start "Hospital Chatbot Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo Servers Starting...
echo ========================================
echo.
echo Backend will be available at:
echo   - Computer: http://localhost:8000
echo   - Mobile:   http://172.20.10.5:8000
echo.
echo Frontend will be available at:
echo   - Computer: http://localhost:5173
echo   - Mobile:   http://172.20.10.5:5173
echo.
echo Make sure your mobile device is on the same WiFi!
echo.
echo Press any key to exit this window...
pause >nul
