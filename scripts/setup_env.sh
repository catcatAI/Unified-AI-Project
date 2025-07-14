#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Check if venv directory exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment. Make sure python3 is installed and in your PATH."
        exit 1
    fi
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies."
    exit 1
fi

echo "Virtual environment setup complete."
echo "To activate it in the future, run: source ./venv/bin/activate"
