@echo off
setlocal EnableDelayedExpansion
title AI Interview Evaluation System

echo ====================================================
echo        AI Interview Evaluation System
echo ====================================================
echo.

:: Ensure standard Windows utilities and Python are available in PATH
set "PATH=%SystemRoot%\System32;%SystemRoot%;%SystemRoot%\System32\Wbem;%SystemRoot%\System32\WindowsPowerShell\v1.0;%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"

set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"

if not exist "%BACKEND_DIR%\main.py" (
    echo [ERROR] Backend folder or main.py not found at:
    echo "%BACKEND_DIR%"
    echo.
    pause
    exit /b 1
)

cd /d "%BACKEND_DIR%"

echo [1/3] Checking backend server status...

:: Check if server is already responding on port 8000
python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).getcode() == 200 else 1)" >nul 2>&1

if !errorlevel! equ 0 (
    echo [OK] Backend server is already running on http://127.0.0.1:8000.
    goto LAUNCH_BROWSER
)

echo [2/3] Starting backend server in a dedicated window...
start "AI Interview Backend" "%ComSpec%" /k "cd /d ""%BACKEND_DIR%"" && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"

echo Waiting for backend server to initialize (loading AI models)...
set /a RETRIES=0
set /a MAX_RETRIES=30

:CHECK_LOOP
python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).getcode() == 200 else 1)" >nul 2>&1
if !errorlevel! equ 0 goto SERVER_READY

set /a RETRIES+=1
if !RETRIES! geq !MAX_RETRIES! goto SERVER_TIMEOUT

<nul set /p =.
python -c "import time; time.sleep(1)" >nul 2>&1
goto CHECK_LOOP

:SERVER_TIMEOUT
echo.
echo.
echo [ERROR] Backend did not respond within 30 seconds.
echo Please check the "AI Interview Backend" console window for details.
echo.
pause
exit /b 1

:SERVER_READY
echo.
echo [OK] Backend server is online and healthy.

:LAUNCH_BROWSER
echo [3/3] Opening login page in default browser...
start "" "http://127.0.0.1:8000/app/login.html"

echo.
echo ====================================================
echo  System is running at: http://127.0.0.1:8000
echo  Login URL: http://127.0.0.1:8000/app/login.html
echo ====================================================
echo.
python -c "import time; time.sleep(3)" >nul 2>&1

endlocal
exit /b 0