@echo off
cd /d %~dp0..
python -u tests\refactor\test_phase1.py > test_phase1_out.txt 2>&1
echo Done