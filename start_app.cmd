
@echo off
echo Starting AI in Finance Project...

@REM Start Backend in background
start "Backend API" /B python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
timeout /t 5 >nul

@REM Start Frontend
start "Frontend UI" python -m streamlit run ui/app.py

echo Services started. 
echo Backend: http://127.0.0.1:8000/docs
echo Frontend: http://localhost:8501
