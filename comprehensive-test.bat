@echo off
chcp 65001 >nul 2>&1
echo ================================================
echo Unified-AI-Project - Comprehensive Testing Suite
echo ================================================
echo.

cd /d "D:\Projects\Unified-AI-Project"

echo [1/5] Environment Health Check
echo ================================================
echo Checking Python version...
python --version
echo.
echo Checking Node.js version...
node --version
echo.
echo Checking npm/pnpm availability...
npm --version
pnpm --version 2>nul || echo pnpm not available
echo.

echo [2/5] Backend Component Diagnostics  
echo ================================================
cd apps\backend
echo Running component diagnostics...
python diagnose_components.py
echo.

echo [3/5] AGI Integration Testing
echo ================================================
echo Running full AGI integration test...
python test_agi_integration.py
echo.

echo [4/5] Project Structure Validation
echo ================================================
cd ..\..\
echo Checking critical directories...
if exist "apps\backend" echo ✅ Backend directory exists
if exist "apps\frontend-dashboard" echo ✅ Frontend directory exists  
if exist "apps\desktop-app" echo ✅ Desktop app directory exists
if exist "data" echo ✅ Data directory exists
if exist "scripts" echo ✅ Scripts directory exists
if exist "docs" echo ✅ Documentation directory exists
echo.

echo Checking training data...
if exist "data\common_voice_zh" echo ✅ Common Voice data (57GB) available
if exist "data\visual_genome_sample" echo ✅ Visual Genome data (18GB) available
if exist "data\coco_captions" echo ✅ MS COCO data (1GB) available
echo.

echo [5/5] Git Status Check
echo ================================================
echo Checking Git repository status...
git status --porcelain | find /v "" >nul && (
    echo ⚠️ There are uncommitted changes
    git status
) || (
    echo ✅ Git repository is clean
)
echo.

echo ================================================
echo Testing Summary Complete
echo ================================================
echo All tests executed. Check output above for results.
echo.
echo For detailed testing, run individual scripts:
echo - health-check.bat (Environment check)
echo - run-tests.bat (Quick tests)  
echo - test-runner.bat (Complete test suite)
echo.

pause