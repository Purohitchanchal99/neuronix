@echo off
REM ================================================================
REM Retry Only Failed PDFs
REM ================================================================
REM Sirf failed PDFs ko dobara ingest karna, sb ko nhi
REM (Only retry failed PDFs, not all)
REM ================================================================

echo.
echo ================================================================
echo NEURONIX: Retry Only Failed PDFs
echo ================================================================
echo.
echo This will retry ONLY the 2 failed PDFs:
echo  1. Abnormal Psychology_Psychology2e_WEB.pdf
echo  2. Applied Statistics_IntroductoryStatistics-OP.pdf
echo.
echo Already-processed PDFs will be SKIPPED.
echo.

cd /d "%~dp0"

REM Run with Python
python retry_failed_pdfs_only.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Retry script failed!
    pause
    exit /b 1
)

echo.
echo ================================================================
echo SUCCESS: Retry complete!
echo ================================================================
pause
