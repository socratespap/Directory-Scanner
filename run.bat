@echo off
echo ================================================
echo Directory Scanner - Rust + Python Hybrid
echo ================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found: 
python --version
echo.

:: Navigate to python frontend
cd /d "%~dp0python_frontend"

:: Check if requirements are installed
echo Checking Python dependencies...
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo Installing Python dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo Dependencies already installed.
)

echo.
echo Checking for Rust backend...

:: Check if Rust is available and try to build
cargo --version >nul 2>&1
if not errorlevel 1 (
    echo Rust found: 
    cargo --version
    echo.
    echo Building Rust backend for maximum performance...
    python build_rust.py
) else (
    echo Rust not found. Using Python fallback implementation.
    echo For better performance, install Rust from https://rustup.rs/
)

echo.
echo ================================================
echo Starting Directory Scanner GUI...
echo ================================================
echo.

:: Launch the application
python main.py

if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start
    pause
)

echo.
echo Application closed.
pause