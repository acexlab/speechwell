<#
File Logic Summary: PowerShell bootstrap helper that automates environment setup and service startup on Windows.
#>

# SpeechWell Quick Start Script (Windows PowerShell)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "SpeechWell - Quick Start Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host ">> Checking Python..." -ForegroundColor Yellow
$pythonCheck = python --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Python $pythonCheck" -ForegroundColor Green

# Navigate to workspace
$workspacePath = "c:\Users\franc\Documents\SpeechWell"
Set-Location $workspacePath

# Install backend dependencies
Write-Host ">> Installing backend dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: Backend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Check if ML models exist
Write-Host ">> Checking ML models..." -ForegroundColor Yellow
if (-Not (Test-Path "ml/models/dysarthria_model_v1.pkl")) {
    Write-Host "WARN: ML models not found. Please train them manually." -ForegroundColor Yellow
    Write-Host "Run: python ml/training/train_dysarthria_model.py" -ForegroundColor Yellow
} else {
    Write-Host "OK: ML models found" -ForegroundColor Green
}

# Install frontend dependencies
Write-Host ">> Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location speechwell-frontend
npm install --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to install frontend dependencies" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the application:" -ForegroundColor Green
Write-Host ""
Write-Host "1. Start Backend (Terminal 1):" -ForegroundColor Yellow
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start Frontend (Terminal 2):" -ForegroundColor Yellow
Write-Host "   cd speechwell-frontend" -ForegroundColor Gray
Write-Host "   npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Open browser to: http://localhost:5173" -ForegroundColor Yellow
Write-Host ""
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "For detailed documentation, see: INTEGRATION_GUIDE.md" -ForegroundColor Green

