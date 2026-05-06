@echo off
setlocal

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"
cd /d "%ROOT_DIR%"

if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=%ROOT_DIR%\venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo Starting SpeechWell backend and frontend...
echo.

start "SpeechWell Backend" cmd /k "title SpeechWell Backend && cd /d ""%ROOT_DIR%\backend"" && ""%PYTHON_EXE%"" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
start "SpeechWell Frontend" cmd /k "title SpeechWell Frontend && cd /d ""%ROOT_DIR%\speechwell-frontend"" && npm run dev"

echo Backend window: http://localhost:8000
echo Frontend window: http://localhost:5173
