@echo off
echo ========================================
echo Hospital Chatbot - Firewall Setup
echo ========================================
echo.
echo This script will add firewall rules to allow
echo mobile access to your chatbot application.
echo.
echo You need to run this as Administrator!
echo.
pause

echo.
echo Adding firewall rule for Backend (Port 8000)...
netsh advfirewall firewall add rule name="Hospital Chatbot Backend" dir=in action=allow protocol=TCP localport=8000

echo.
echo Adding firewall rule for Frontend (Port 5173)...
netsh advfirewall firewall add rule name="Hospital Chatbot Frontend" dir=in action=allow protocol=TCP localport=5173

echo.
echo ========================================
echo Firewall Rules Added Successfully!
echo ========================================
echo.
echo You can now access the application from your mobile device.
echo.
pause
