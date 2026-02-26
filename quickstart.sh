#!/bin/bash
# File Logic Summary: Shell bootstrap helper that automates environment setup and service startup for local development.
# SpeechWell Quick Start Script

echo "================================"
echo "SpeechWell - Quick Start Setup"
echo "================================"
echo ""

# Check Python installation
echo "✓ Checking Python..."
if ! command -v python &> /dev/null; then
    echo "✗ Python not found. Please install Python 3.9+"
    exit 1
fi

# Install backend dependencies
echo "✓ Installing backend dependencies..."
cd backend
pip install -r requirements.txt --quiet
if [ $? -eq 0 ]; then
    echo "✓ Backend dependencies installed"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

# Check if ML models exist
echo "✓ Checking ML models..."
if [ ! -f "ml/models/dysarthria_model_v1.pkl" ]; then
    echo "⚠ ML models not found. Running training..."
    python ml/training/train_dysarthria_model.py
fi

# Install frontend dependencies
echo "✓ Installing frontend dependencies..."
cd ../speechwell-frontend
npm install --quiet
if [ $? -eq 0 ]; then
    echo "✓ Frontend dependencies installed"
else
    echo "✗ Failed to install frontend dependencies"
    exit 1
fi

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "To start the application:"
echo ""
echo "1. Start Backend (Terminal 1):"
echo "   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2. Start Frontend (Terminal 2):"
echo "   cd speechwell-frontend"
echo "   npm run dev"
echo ""
echo "3. Open browser to: http://localhost:5173"
echo ""
echo "Backend API: http://localhost:8000"
echo ""
echo "For detailed documentation, see: INTEGRATION_GUIDE.md"

