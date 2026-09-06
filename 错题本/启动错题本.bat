@echo off
setlocal
set "APP_URL=http://127.0.0.1:8765/%%E9%%94%%99%%E9%%A2%%98%%E6%%9C%%AC/index.html"
set "APP_DIR=%~dp0"

rem 1) If the service is already running, just open the page.
netstat -ano | findstr /r /c:":8765 .*LISTENING" >nul
if %ERRORLEVEL% EQU 0 goto open_page

rem 2) server.py lives in this same folder.
if not exist "%APP_DIR%server.py" (
  echo.
  echo server.py was not found in "%APP_DIR%".
  pause
  exit /b 1
)

rem 3) Start the service in a minimized background window.
echo Starting error-book service on http://127.0.0.1:8765 ...
if exist "D:\python\python.exe" (
  start "errorbook-service" /min "D:\python\python.exe" "%APP_DIR%server.py"
) else (
  start "errorbook-service" /min py -3 "%APP_DIR%server.py"
)

rem 4) Wait until the port is listening (max ~8 seconds), then open the page.
for /l %%i in (1,1,16) do (
  timeout /t 1 /nobreak >nul
  netstat -ano | findstr /r /c:":8765 .*LISTENING" >nul
  if not errorlevel 1 goto open_page
)

echo.
echo The service did not start in time. Keep this window open and send me a screenshot.
pause
exit /b 1

:open_page
start "" "%APP_URL%"
echo.
echo ============================================
echo  Error-book started (opened on PC)
echo ============================================
echo  Phone access (same WiFi):
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  for /f "tokens=* delims= " %%b in ("%%a") do (
    echo    http://%%b:8765/%%E9%%94%%99%%E9%%A2%%98%%E6%%9C%%AC/index.html
  )
)
echo.
echo  On phone: browser menu -^> Add to Home Screen
echo  Close this window, service keeps running
echo ============================================
timeout /t 8 >nul
exit /b 0
