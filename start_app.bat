@echo off
echo ================================================
echo    UPSC News Aggregator - Windows Launcher
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    echo Download from: https://python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if we're in the right directory
if not exist "main.py" (
    echo ❌ main.py not found
    echo Please run this script from the UPSC News Aggregator directory
    pause
    exit /b 1
)

echo ✅ Application files found
echo.

REM Try to install dependencies if requirements.txt exists
if exist "requirements.txt" (
    echo 📦 Installing/checking dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ Failed to install dependencies
        echo Please check your internet connection and try again
        pause
        exit /b 1
    )
    echo ✅ Dependencies ready
    echo.
)

REM Start the application
echo 🚀 Starting UPSC News Aggregator...
echo Press Ctrl+C to stop the application
echo.

python run_app.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Application failed to start
    echo.
    echo 🔧 Try these solutions:
    echo 1. Run: pip install -r requirements.txt
    echo 2. Make sure you have Python 3.7+ installed
    echo 3. Check the error messages above
    echo.
)

pause 