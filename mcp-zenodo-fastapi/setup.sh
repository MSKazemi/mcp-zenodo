#!/bin/bash

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from .env.example. Please update it with your Zenodo API token."
fi

# Create necessary directories
mkdir -p logs

echo "Setup complete! Please update your .env file with your Zenodo API token."
echo "To start the server, run: source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000" 