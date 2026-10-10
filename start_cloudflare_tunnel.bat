@echo off
setlocal EnableDelayedExpansion
title Cloudflare Tunnel - AI Interview Evaluation System

echo ================================================================
echo      AI Interview Evaluation System - Cloudflare Tunnel
echo ================================================================
echo.

set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "CLOUDFLARED_EXE=%PROJECT_ROOT%cloudflared.exe"

:: 1. Check if cloudflared.exe exists
if not exist "%CLOUDFLARED_EXE%" (
    echo [ERROR] cloudflared.exe not found at:
    echo "%CLOUDFLARED_EXE%"
    echo Please ensure cloudflared.exe is in the project root directory.
    pause
    exit /b 1
)

:: 2. Ensure standard Windows utilities and Python are available in PATH
set "PATH=%SystemRoot%\System32;%SystemRoot%;%SystemRoot%\System32\Wbem;%SystemRoot%\System32\WindowsPowerShell\v1.0;%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"

:: 3. Check if backend is running on 127.0.0.1:8000
echo [1/2] Checking if local backend is online...
python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).getcode() == 200 else 1)" >nul 2>&1

if !errorlevel! neq 0 (
    echo Local backend is not running. Starting backend server...
    start "AI Interview Backend" "%ComSpec%" /k "cd /d ""%BACKEND_DIR%"" && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"
    
    echo Waiting for backend server to initialize...
    set /a RETRIES=0
    set /a MAX_RETRIES=30
    
    :CHECK_BACKEND_LOOP
    python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).getcode() == 200 else 1)" >nul 2>&1
    if !errorlevel! equ 0 goto BACKEND_ONLINE
    set /a RETRIES+=1
    if !RETRIES! geq !MAX_RETRIES! (
        echo.
        echo [ERROR] Backend did not respond within 30 seconds.
        pause
        exit /b 1
    )
    <nul set /p =.
    python -c "import time; time.sleep(1)" >nul 2>&1
    goto CHECK_BACKEND_LOOP
)

:BACKEND_ONLINE
echo [OK] Local backend is active on http://127.0.0.1:8000
echo.
echo [2/2] Launching Cloudflare Tunnel...
echo.
echo ================================================================
echo  Look below for your public HTTPS link (e.g. https://xxx.trycloudflare.com)
echo  Candidate Login URL: https://xxx.trycloudflare.com/app/login.html
echo  To STOP the public tunnel anytime, press Ctrl+C in this window.
echo ================================================================
echo.

"%CLOUDFLARED_EXE%" tunnel --url http://127.0.0.1:8000

endlocal
