@echo off
REM Neuronix Quick Start Script for Windows
REM ========================================

setlocal enabledelayedexpansion

echo.
echo ================================================================================
echo 🧠 NEURONIX - CLINICAL PSYCHOLOGY AI ASSISTANT
echo ================================================================================
echo.

REM Check if in correct directory
if not exist "scripts\neuronix_ingest.py" (
    echo ❌ Error: Must run from project root directory (c:\Users\admin\Desktop\desktop\NEURO_MENTAL)
    echo.
    pause
    exit /b 1
)

REM Check for virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo ⚠️  Virtual environment not found. Creating...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements
echo.
echo 📦 Installing/updating packages...
pip install -q -r requirements.txt
if !errorlevel! neq 0 (
    echo ❌ Failed to install requirements
    pause
    exit /b 1
)
echo ✅ Packages ready

REM Check Google API key
if "!GOOGLE_API_KEY!"=="" (
    echo.
    echo ⚠️  GOOGLE_API_KEY not set!
    echo.
    echo To set it, run in PowerShell:
    echo   $env:GOOGLE_API_KEY = "your-api-key-here"
    echo.
    set /p GOOGLE_API_KEY="Enter your GOOGLE_API_KEY (or press Enter to skip): "
)

REM Menu
:menu
echo.
echo ================================================================================
echo 📋 NEURONIX MENU
echo ================================================================================
echo.
echo 1. Run Ingestion Pipeline (import PDFs from docs/)
echo 2. Run Query System (interactive query mode)
echo 3. Check Database Status
echo 4. View Monitoring Logs
echo 5. Exit
echo.
set /p choice="Enter choice (1-5): "

if "!choice!"=="1" (
    echo.
    echo ✅ Starting Neuronix Ingestion...
    echo.
    cd scripts
    python neuronix_ingest.py
    cd ..
    pause
    cls
    goto menu
)

if "!choice!"=="2" (
    echo.
    echo ✅ Starting Neuronix Query System...
    echo.
    cd scripts
    python neuronix_query.py
    cd ..
    pause
    cls
    goto menu
)

if "!choice!"=="3" (
    echo.
    echo ✅ Checking database status...
    echo.
    cd scripts
    python -c "from neuronix_query import NeuronixQuerySystem; q = NeuronixQuerySystem(verbose=False); status = q.get_db_status(); import json; print('\n' + json.dumps(status, indent=2))"
    cd ..
    pause
    cls
    goto menu
)

if "!choice!"=="4" (
    echo.
    if exist "scripts\neuronix_monitoring.log" (
        echo 📊 Monitoring Log (last 50 lines):
        echo.
        powershell -Command "Get-Content scripts\neuronix_monitoring.log -Tail 50"
    ) else (
        echo ⚠️  No monitoring log found. Run ingestion first.
    )
    echo.
    pause
    cls
    goto menu
)

if "!choice!"=="5" (
    echo.
    echo 👋 Goodbye!
    echo.
    exit /b 0
)

echo ❌ Invalid choice
goto menu
