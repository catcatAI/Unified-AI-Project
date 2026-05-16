@echo off
cd /d "D:\Projects\Unified-AI-Project\apps\backend\src"
echo Starting Angela Backend + Terminal Chat REPL...
echo Type messages below and press Enter to chat.
echo Exit/quit to stop.
echo ========================================
python -m services.main_api_server --repl
pause