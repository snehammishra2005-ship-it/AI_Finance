@echo off
REM Always run from the project folder, even when double-clicked elsewhere.
cd /d "%~dp0"

echo Starting AI in Finance Project...

REM Use the project's virtual environment, not the global Python.
if not exist "venv\Scripts\python.exe" (
    echo ERROR: venv not found at venv\Scripts\python.exe
    echo Create it first:
    echo     python -m venv venv
    echo     venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Start Backend in its own window (port 8000 - the frontend expects this).
start "Backend API" venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
timeout /t 5 >nul

REM Start Frontend in its own window (port 8501).
start "Frontend UI" venv\Scripts\python.exe -m streamlit run ui/app.py --server.port 8501

echo Services started.
echo Backend:  http://127.0.0.1:8000/docs
echo Frontend: http://localhost:8501
echo Close the two spawned windows to stop the servers.
