@echo off
echo 開始執行項目修復...
cd /d "%~dp0"
python repair_scripts\run_all_repairs.py --fix --backup --verbose
echo 修復完成，請查看 summaries 目錄中的報告
pause