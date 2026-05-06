#!/bin/bash
# File Logic Summary: Shell bootstrap helper that automates environment setup and service startup for local development.

echo "================================"
echo "SpeechWell - Quick Start Setup"
echo "================================"
echo ""

echo "Checking Python..."
if ! command -v python &> /dev/null; then
    echo "Python not found. Please install Python 3.9+"
    exit 1
fi

echo "Installing backend dependencies..."
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "Failed to install backend dependencies"
    exit 1
fi

echo "Checking ML models..."
if [ ! -f "ml/models/dysarthria_model_v2_rf_svc_ensemble.pkl" ]; then
    echo "Latest ensemble model not found."
    echo "Train it with: python ml/training/train_dysarthria_rf_svc_ensemble.py --group-aware"
else
    echo "Latest ensemble model found"
fi

echo "Installing frontend dependencies..."
cd speechwell-frontend || exit 1
npm install --quiet
if [ $? -ne 0 ]; then
    echo "Failed to install frontend dependencies"
    exit 1
fi

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Start the backend:"
echo "python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Start the frontend:"
echo "cd speechwell-frontend && npm run dev"
