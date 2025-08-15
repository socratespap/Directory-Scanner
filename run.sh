#!/bin/bash

echo "================================================"
echo "Directory Scanner - Rust + Python Hybrid"
echo "================================================"
echo

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python is not installed or not in PATH"
        echo "Please install Python 3.8+ from your package manager or https://python.org"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "Python found: "
$PYTHON_CMD --version
echo

# Navigate to python frontend
cd "python_frontend"

# Check if requirements are installed
echo "Checking Python dependencies..."
$PYTHON_CMD -c "import PyQt6" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Installing Python dependencies..."
    $PYTHON_CMD -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        echo "You may need to install pip or use a virtual environment"
        exit 1
    fi
else
    echo "Dependencies already installed."
fi

echo
echo "Checking for Rust backend..."

# Check if Rust is available and try to build
if command -v cargo &> /dev/null; then
    echo "Rust found: "
    cargo --version
    echo
    echo "Building Rust backend for maximum performance..."
    $PYTHON_CMD build_rust.py
else
    echo "Rust not found. Using Python fallback implementation."
    echo "For better performance, install Rust from https://rustup.rs/"
fi

echo
echo "================================================"
echo "Starting Directory Scanner GUI..."
echo "================================================"
echo

# Launch the application
$PYTHON_CMD main.py

if [ $? -ne 0 ]; then
    echo
    echo "ERROR: Application failed to start"
    read -p "Press Enter to continue..."
fi

echo
echo "Application closed."