@echo off
cd /d "D:\Projects\Unified-AI-Project\apps\backend\src"
echo Starting Angela Backend...
python -m uvicorn services.main_api_server:app --host 127.0.0.1 --port 8000
pause
