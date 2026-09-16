@echo off
chcp 65001 >nul
title GökAI V1 — Autonomous AI Software Engineering Platform
color 0B

echo.
echo  ========================================================================
echo    GÖKAI V1 — AUTONOMOUS MULTI-AGENT AI SOFTWARE ENGINEERING PLATFORM
echo    GÖK SYSTEMS TECH — Enterprise Release
echo  ========================================================================
echo.

set "GOKAI_DIR=%~dp0"
if "%GOKAI_DIR:~-1%"=="\" set "GOKAI_DIR=%GOKAI_DIR:~0,-1%"

:: Locate Python
set "PYTHON_EXE=python"
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    where py >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set "PYTHON_EXE=py"
    ) else if exist "%USERPROFILE%\miniconda3\python.exe" (
        set "PYTHON_EXE=%USERPROFILE%\miniconda3\python.exe"
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    ) else (
        echo [ERROR] Python 3.10+ was not found in PATH or standard installation directories.
        echo Please install Python from https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

echo [✓] Found Python: %PYTHON_EXE%

:: Locate Node.js & npm
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is required but was not found in PATH.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

where npm >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] npm is required but was not found in PATH.
    pause
    exit /b 1
)

echo [✓] Found Node.js and npm

:: Ensure .env exists
if not exist "%GOKAI_DIR%\.env" (
    echo [*] Creating .env from .env.example...
    copy "%GOKAI_DIR%\.env.example" "%GOKAI_DIR%\.env" >nul
)

:: Install frontend dependencies if needed
if not exist "%GOKAI_DIR%\apps\frontend\node_modules" (
    echo [*] Installing frontend dependencies...
    cd /d "%GOKAI_DIR%\apps\frontend"
    call npm install
    cd /d "%GOKAI_DIR%"
)

:: Launch Backend API Gateway
echo [*] Launching FastAPI Backend on http://localhost:8000 ...
start "GökAI Backend (Port 8000)" cmd /c "cd /d "%GOKAI_DIR%\.." && "%PYTHON_EXE%" -m uvicorn gokai.apps.backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Launch Frontend Vite Server
echo [*] Launching React 19 Frontend on http://localhost:3000 ...
start "GökAI Frontend (Port 3000)" cmd /c "cd /d "%GOKAI_DIR%\apps\frontend" && npm run dev -- --port 3000 --host"

:: Wait and launch browser
echo [*] Waiting for services to initialize...
timeout /t 3 >nul

start http://localhost:3000

echo.
echo  ========================================================================
echo    GÖKAI V1 IS NOW RUNNING:
echo    • Web Interface:    http://localhost:3000
echo    • API Gateway:      http://localhost:8000
echo    • Swagger Docs:     http://localhost:8000/docs
echo  ========================================================================
echo.
pause
