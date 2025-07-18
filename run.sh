#!/bin/bash

set -e

# Backend setup
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

cd ../frontend

# Install Node.js dependencies
npm install

cd ..

echo "Setup complete. To run the app:"
echo "  1. Start the backend: source backend/venv/bin/activate && python backend/local_chess.py"
echo "  2. Start the frontend: cd frontend && npm run dev" 