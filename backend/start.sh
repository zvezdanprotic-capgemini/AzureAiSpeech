#!/bin/bash

echo "Starting Image Analysis API Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists and has required variables
if [ ! -f ".env" ]; then
    echo "❌ .env file not found! Please create it with your Azure Vision credentials."
    exit 1
fi

# Start the server
echo "Starting FastAPI server..."
python main.py
