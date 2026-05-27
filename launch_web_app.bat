@echo off
REM Neuronix Day 4 Web App Launcher
REM Run: .\launch_web_app.bat

echo.
echo ========================================
echo    NEURONIX - WEB APP LAUNCHER
echo    Day 4: Memory & Empathy
echo ========================================
echo.

REM Set API Key (if needed)
echo Checking API key...
if "%GOOGLE_API_KEY%"=="" (
    echo.
    echo WARNING: GOOGLE_API_KEY not set!
    echo.
    echo To set it, run:
    echo   $env:GOOGLE_API_KEY = "your-api-key-here"
    echo.
    echo Get your key from: https://makersuite.google.com/app/apikey
    echo.
    echo Continuing anyway (demo mode will be used)...
    pause
)

REM Launch Streamlit
echo.
echo Starting Neuronix Web App...
echo.
echo Access the app at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0"
python -m streamlit run app.py --logger.level=info

pause
