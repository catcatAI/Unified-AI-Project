@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Training Manager
color 0A

:: Add error handling and logging (添加錯誤處理和日志記錄)
set "LOG_FILE=%~dp0train-manager-errors.log"
set "SCRIPT_NAME=train-manager.bat"

:: Log script start (記錄腳本啟動)
echo [%date% %time%] Script started: %SCRIPT_NAME% >> "%LOG_FILE%" 2>nul

:: Use absolute paths derived from script location (使用從腳本位置派生的絕對路徑)
set "PROJECT_ROOT=%~dp0.."
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
:: 保存原始目錄路徑
set "ORIGINAL_DIR=%CD%"

:main_menu
cls
echo ==========================================
echo   🧠 Unified AI Project - Training Manager
echo ==========================================
echo.
echo Manage your AI model training processes. (管理您的AI模型訓練過程)
echo.
echo Please select an option: (請選擇一個選項)
echo.
echo   1. 🚀 Start Training (開始訓練)
echo   2. 📊 View Training Progress (查看訓練進度)
echo   3. ⏸️  Pause Training (暫停訓練)
echo   4. ▶️  Resume Training (繼續訓練)
echo   5. 🛑 Stop Training (停止訓練)
echo   6. 📈 View Training Results (查看訓練結果)
echo   7. 🧪 Run Training Tests (運行訓練測試)
echo   8. 📂 Manage Training Data (管理訓練數據)
echo   9. ⚙️  Training Configuration (訓練配置)
echo   10. 🤝 Collaborative Training (協作式訓練)
echo   11. ❌ Exit (退出)
echo.
echo ==========================================
echo.

:: Get user choice with validation (獲取用戶選擇並驗證)
:get_user_choice
set "main_choice="
set /p "main_choice=Enter your choice (1-11): "
if not defined main_choice (
    echo [ERROR] No input provided
    echo [%date% %time%] No input provided >> "%LOG_FILE%" 2>nul
    timeout /t 2 >nul
    goto get_user_choice
)

:: Validate numeric input for menu choices (驗證菜單選擇的數字輸入)
set "main_choice=%main_choice: =%"
for %%i in (1 2 3 4 5 6 7 8 9 10 11) do (
    if "%main_choice%"=="%%i" (
        goto choice_%%i
    )
)

echo [ERROR] Invalid choice '%main_choice%'. Please enter a valid option.
echo [%date% %time%] Invalid choice: %main_choice% >> "%LOG_FILE%" 2>nul
timeout /t 2 >nul
goto get_user_choice

:choice_1
goto start_training
:choice_2
goto view_progress
:choice_3
goto pause_training
:choice_4
goto resume_training
:choice_5
goto stop_training
:choice_6
goto view_results
:choice_7
goto run_training_tests
:choice_8
goto manage_data
:choice_9
goto training_config
:choice_10
goto collaborative_training
:choice_11
goto exit_script

:: Start Training (開始訓練)
:start_training
echo.
echo [INFO] Starting training process... (開始訓練過程)
echo [%date% %time%] Starting training >> "%LOG_FILE%" 2>nul

:: Check if training environment is set up (檢查訓練環境是否已設置)
if not exist "%PROJECT_ROOT%\training\" (
    echo [WARNING] Training directory not found (訓練目錄未找到)
    echo [INFO] Setting up training environment... (設置訓練環境)
    :: 修正路徑引用錯誤，從 tools\setup-training.bat 更正為 setup-training.bat
    if exist "%PROJECT_ROOT%\tools\setup-training.bat" (
        call "%PROJECT_ROOT%\tools\setup-training.bat"
    ) else (
        echo [ERROR] setup-training.bat not found
        echo [%date% %time%] setup-training.bat not found >> "%LOG_FILE%" 2>nul
        echo Press any key to continue...
        pause >nul
        goto main_menu
    )
)

:: Run training script with preset options (使用預設選項運行訓練腳本)
:: 修正路徑引用錯誤，確保使用正確的絕對路徑
set "TRAINING_SCRIPT=%PROJECT_ROOT%\training\train_model.py"
if exist "%TRAINING_SCRIPT%" (
    echo [INFO] Launching training script... (啟動訓練腳本)
    echo.
    echo Available training presets: (可用的訓練預設)
    echo   1. quick_start - Quick training with mock data for testing (使用模擬數據進行快速訓練以進行測試)
    echo   2. comprehensive_training - Full training with all available data (使用所有可用數據進行完整訓練)
    echo   3. vision_focus - Focus on vision-related models (專注於視覺相關模型)
    echo   4. audio_focus - Focus on audio-related models (專注於音頻相關模型)
    echo   5. full_dataset_training - Full dataset training with auto-pause/resume (完整數據集訓練，支持自動暫停/繼續)
    echo   6. math_model_training - Train mathematical calculation model (訓練數學計算模型)
    echo   7. logic_model_training - Train logical reasoning model (訓練邏輯推理模型)
    echo   8. real_math_model_training - Real mathematical model training with TensorFlow (使用TensorFlow進行真實數學模型訓練)
    echo   9. real_logic_model_training - Real logical reasoning model training with TensorFlow (使用TensorFlow進行真實邏輯推理模型訓練)
    echo   10. concept_models_training - Train all concept models (訓練所有概念模型)
    echo   11. collaborative_training - Full model collaborative training (全模型協作式訓練)
    echo   12. Custom training (自定義訓練)
    echo.
    
    set "preset_choice="
    set /p "preset_choice=Enter your choice (1-12, or press Enter for quick_start): "
    
    :: 保存當前目錄並切換到訓練目錄
    set "SAVED_DIR=%CD%"
    cd /d "%PROJECT_ROOT%\training"
    
    if not defined preset_choice (
        echo [INFO] Using default preset: quick_start
        python train_model.py --preset quick_start
    ) else if "%preset_choice%"=="1" (
        echo [INFO] Using preset: quick_start
        python train_model.py --preset quick_start
    ) else if "%preset_choice%"=="2" (
        echo [INFO] Using preset: comprehensive_training
        python train_model.py --preset comprehensive_training
    ) else if "%preset_choice%"=="3" (
        echo [INFO] Using preset: vision_focus
        python train_model.py --preset vision_focus
    ) else if "%preset_choice%"=="4" (
        echo [INFO] Using preset: audio_focus
        python train_model.py --preset audio_focus
    ) else if "%preset_choice%"=="5" (
        echo [INFO] Using preset: full_dataset_training
        python train_model.py --preset full_dataset_training
    ) else if "%preset_choice%"=="6" (
        echo [INFO] Using preset: math_model_training
        python train_model.py --preset math_model_training
    ) else if "%preset_choice%"=="7" (
        echo [INFO] Using preset: logic_model_training
        python train_model.py --preset logic_model_training
    ) else if "%preset_choice%"=="8" (
        echo [INFO] Using preset: real_math_model_training
        python train_model.py --preset real_math_model_training
    ) else if "%preset_choice%"=="9" (
        echo [INFO] Using preset: real_logic_model_training
        python train_model.py --preset real_logic_model_training
    ) else if "%preset_choice%"=="10" (
        echo [INFO] Using preset: concept_models_training
        python train_model.py --preset concept_models_training
    ) else if "%preset_choice%"=="11" (
        echo [INFO] Using preset: collaborative_training
        python train_model.py --preset collaborative_training
    ) else (
        echo [INFO] Using custom training
        python train_model.py
    )
    
    :: 檢查訓練腳本執行結果
    if errorlevel 1 (
        echo [WARNING] Training script execution paused or interrupted
        echo [%date% %time%] Training script execution paused or interrupted >> "%LOG_FILE%" 2>nul
    ) else (
        echo [INFO] Training completed successfully
        echo [%date% %time%] Training completed successfully >> "%LOG_FILE%" 2>nul
    )
    
    :: 返回到保存的目錄
    cd /d "%SAVED_DIR%"
) else (
    echo [ERROR] Training script (train_model.py) not found
    echo [%date% %time%] Training script not found: %TRAINING_SCRIPT% >> "%LOG_FILE%" 2>nul
    echo Looking for: %TRAINING_SCRIPT%
)

echo.
echo Press any key to continue...
pause >nul
goto main_menu

:: Resume Training (繼續訓練)
:resume_training
echo.
echo [INFO] Resuming training process... (繼續訓練過程)
echo [%date% %time%] Resuming training >> "%LOG_FILE%" 2>nul

:: Run training script with resume option (使用繼續選項運行訓練腳本)
set "TRAINING_SCRIPT=%PROJECT_ROOT%\training\train_model.py"
if exist "%TRAINING_SCRIPT%" (
    echo [INFO] Launching training script with resume option... (啟動帶繼續選項的訓練腳本)
    echo.
    echo Available training presets: (可用的訓練預設)
    echo   1. quick_start - Quick training with mock data for testing (使用模擬數據進行快速訓練以進行測試)
    echo   2. comprehensive_training - Full training with all available data (使用所有可用數據進行完整訓練)
    echo   3. vision_focus - Focus on vision-related models (專注於視覺相關模型)
    echo   4. audio_focus - Focus on audio-related models (專注於音頻相關模型)
    echo   5. full_dataset_training - Full dataset training with auto-pause/resume (完整數據集訓練，支持自動暫停/繼續)
    echo   6. math_model_training - Train mathematical calculation model (訓練數學計算模型)
    echo   7. logic_model_training - Train logical reasoning model (訓練邏輯推理模型)
    echo   8. real_math_model_training - Real mathematical model training with TensorFlow (使用TensorFlow進行真實數學模型訓練)
    echo   9. real_logic_model_training - Real logical reasoning model training with TensorFlow (使用TensorFlow進行真實邏輯推理模型訓練)
    echo   10. concept_models_training - Train all concept models (訓練所有概念模型)
    echo   11. collaborative_training - Full model collaborative training (全模型協作式訓練)
    echo.
    
    set "preset_choice="
    set /p "preset_choice=Enter your choice (1-11, or press Enter for quick_start): "
    
    :: 保存當前目錄並切換到訓練目錄
    set "SAVED_DIR=%CD%"
    cd /d "%PROJECT_ROOT%\training"
    
    if not defined preset_choice (
        echo [INFO] Using default preset: quick_start
        python train_model.py --preset quick_start --resume
    ) else if "%preset_choice%"=="1" (
        echo [INFO] Using preset: quick_start
        python train_model.py --preset quick_start --resume
    ) else if "%preset_choice%"=="2" (
        echo [INFO] Using preset: comprehensive_training
        python train_model.py --preset comprehensive_training --resume
    ) else if "%preset_choice%"=="3" (
        echo [INFO] Using preset: vision_focus
        python train_model.py --preset vision_focus --resume
    ) else if "%preset_choice%"=="4" (
        echo [INFO] Using preset: audio_focus
        python train_model.py --preset audio_focus --resume
    ) else if "%preset_choice%"=="5" (
        echo [INFO] Using preset: full_dataset_training
        python train_model.py --preset full_dataset_training --resume
    ) else if "%preset_choice%"=="6" (
        echo [INFO] Using preset: math_model_training
        python train_model.py --preset math_model_training --resume
    ) else if "%preset_choice%"=="7" (
        echo [INFO] Using preset: logic_model_training
        python train_model.py --preset logic_model_training --resume
    ) else if "%preset_choice%"=="8" (
        echo [INFO] Using preset: real_math_model_training
        python train_model.py --preset real_math_model_training --resume
    ) else if "%preset_choice%"=="9" (
        echo [INFO] Using preset: real_logic_model_training
        python train_model.py --preset real_logic_model_training --resume
    ) else if "%preset_choice%"=="10" (
        echo [INFO] Using preset: concept_models_training
        python train_model.py --preset concept_models_training --resume
    ) else if "%preset_choice%"=="11" (
        echo [INFO] Using preset: collaborative_training
        python train_model.py --preset collaborative_training --resume
    ) else (
        echo [INFO] Using custom training
        python train_model.py --resume
    )
    
    :: 檢查訓練腳本執行結果
    if errorlevel 1 (
        echo [WARNING] Training script execution paused or interrupted
        echo [%date% %time%] Training script execution paused or interrupted >> "%LOG_FILE%" 2>nul
    ) else (
        echo [INFO] Training completed successfully
        echo [%date% %time%] Training completed successfully >> "%LOG_FILE%" 2>nul
    )
    
    :: 返回到保存的目錄
    cd /d "%SAVED_DIR%"
) else (
    echo [ERROR] Training script (train_model.py) not found
    echo [%date% %time%] Training script not found: %TRAINING_SCRIPT% >> "%LOG_FILE%" 2>nul
    echo Looking for: %TRAINING_SCRIPT%
)

echo.
echo Press any key to continue...
pause >nul
goto main_menu

:: Collaborative Training (協作式訓練)
:collaborative_training
echo.
echo [INFO] Starting collaborative training... (開始協作式訓練)
echo [%date% %time%] Starting collaborative training >> "%LOG_FILE%" 2>nul

:: Run collaborative training with the new preset
set "TRAINING_SCRIPT=%PROJECT_ROOT%\training\train_model.py"
if exist "%TRAINING_SCRIPT%" (
    echo [INFO] Launching collaborative training... (啟動協作式訓練)
    echo.
    echo This will start full model collaborative training using all available data.
    echo 這將開始使用所有可用數據的全模型協作式訓練。
    echo.
    
    set /p "confirm=Do you want to continue? (y/N): "
    if /i "%confirm%"=="y" (
        :: 保存當前目錄並切換到訓練目錄
        set "SAVED_DIR=%CD%"
        cd /d "%PROJECT_ROOT%\training"
        
        echo [INFO] Starting collaborative training with preset: collaborative_training
        python train_model.py --preset collaborative_training
        
        :: 檢查訓練腳本執行結果
        if errorlevel 1 (
            echo [WARNING] Collaborative training script execution paused or interrupted
            echo [%date% %time%] Collaborative training script execution paused or interrupted >> "%LOG_FILE%" 2>nul
        ) else (
            echo [INFO] Collaborative training completed successfully
            echo [%date% %time%] Collaborative training completed successfully >> "%LOG_FILE%" 2>nul
        )
        
        :: 返回到保存的目錄
        cd /d "%SAVED_DIR%" 2>nul
        if errorlevel 1 (
            echo [ERROR] Failed to return to original directory
            echo [%date% %time%] Failed to return to original directory >> "%LOG_FILE%" 2>nul
        )
    ) else (
        echo [INFO] Collaborative training cancelled by user
        echo [%date% %time%] Collaborative training cancelled by user >> "%LOG_FILE%" 2>nul
    )
) else (
    echo [ERROR] Training script (train_model.py) not found
    echo [%date% %time%] Training script not found: %TRAINING_SCRIPT% >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to continue...
pause >nul
goto main_menu

:: Pause Training (暫停訓練)
:pause_training
echo.
echo [INFO] Pausing training... (暫停訓練)
echo [%date% %time%] Pausing training >> "%LOG_FILE%" 2>nul
echo [INFO] Training pause functionality requires manual intervention
echo [INFO] Please use Ctrl+C in the training console to pause training
echo.
echo Press any key to continue...
pause >nul
goto main_menu

:: Stop Training (停止訓練)
:stop_training
echo.
echo [INFO] Stopping training... (停止訓練)
echo [%date% %time%] Stopping training >> "%LOG_FILE%" 2>nul
echo [INFO] Training stop functionality requires manual intervention
echo [INFO] Please close the training console to stop training
echo.
echo Press any key to continue...
pause >nul
goto main_menu

:: View Training Progress (查看訓練進度)
:view_progress
echo.
echo [INFO] Viewing training progress... (查看訓練進度)
echo [%date% %time%] Viewing training progress >> "%LOG_FILE%" 2>nul

:: Check for progress files (檢查進度文件)
:: 修正路徑引用，確保使用正確的絕對路徑
if exist "%PROJECT_ROOT%\training\progress.log" (
    echo === Training Progress === (訓練進度)
    type "%PROJECT_ROOT%\training\progress.log"
) else (
    echo [INFO] No progress log found (未找到進度日志)
)

echo.
echo Press any key to continue...
pause >nul
goto main_menu

:: View Training Results (查看訓練結果)
:view_results
echo.
echo [INFO] Viewing training results... (查看訓練結果)
echo [%date% %time%] Viewing training results >> "%LOG_FILE%" 2>nul

:: Check for results files (檢查結果文件)
:: 修正路徑引用，確保使用正確的絕對路徑並檢查 models 目錄
if exist "%PROJECT_ROOT%\training\models\" (
    echo === Training Results Directory === (訓練結果目錄)
    dir "%PROJECT_ROOT%\training\models\" /b
    echo.
    echo [INFO] Found training results in models directory (在models目錄中找到訓練結果)
) else (
    echo [WARNING] No models directory found (未找到models目錄)
)

echo.
echo Press any key to continue...
pause >nul
goto main_menu

:: Run Training Tests (運行訓練測試)
:run_training_tests
echo.
echo [INFO] Running training tests... (運行訓練測試)
echo [%date% %time%] Running training tests >> "%LOG_FILE%" 2>nul

:: Run training integration tests (運行訓練集成測試)
:: 修正路徑引用，確保使用正確的絕對路徑
if exist "%PROJECT_ROOT%\scripts\training_integration.py" (
    echo [INFO] Running training integration tests... (運行訓練集成測試)
    python "%PROJECT_ROOT%\scripts\training_integration.py"
) else (
    echo [ERROR] Training integration script not found
    echo [%date% %time%] Training integration script not found >> "%LOG_FILE%" 2>nul
)

echo.
echo Press any key to continue...
pause >nul
goto main_menu

:: Manage Training Data (管理訓練數據)
:manage_data
echo.
echo [INFO] Managing training data... (管理訓練數據)
echo [%date% %time%] Managing training data >> "%LOG_FILE%" 2>nul

:: Check for data directory (檢查數據目錄)
:: 修正路徑引用，確保使用正確的絕對路徑
if exist "%PROJECT_ROOT%\data\" (
    echo === Data Directory === (數據目錄)
    dir "%PROJECT_ROOT%\data\" /b
    echo.
    echo [INFO] Found data directory (找到數據目錄)
) else (
    echo [WARNING] No data directory found (未找到數據目錄)
)

echo.
echo Press any key to continue...
pause >nul
goto main_menu

:: Training Configuration (訓練配置)
:training_config
echo.
echo [INFO] Training configuration... (訓練配置)
echo [%date% %time%] Training configuration >> "%LOG_FILE%" 2>nul

:: Check for config files (檢查配置文件)
:: 修正路徑引用，確保使用正確的絕對路徑
if exist "%PROJECT_ROOT%\training\configs\" (
    echo === Training Configurations === (訓練配置)
    dir "%PROJECT_ROOT%\training\configs\" /b
    echo.
    echo [INFO] Found configuration files (找到配置文件)
) else (
    echo [WARNING] No configuration directory found (未找到配置目錄)
)

echo.
echo Press any key to continue...
pause >nul
goto main_menu

:: Exit Script (退出腳本)
:exit_script
echo.
echo [INFO] Exiting Training Manager... (退出訓練管理器)
echo [%date% %time%] Exiting Training Manager >> "%LOG_FILE%" 2>nul
echo.
echo Returning to main menu... (返回主菜單)
echo.
:: 確保返回到原始目錄
cd /d "%ORIGINAL_DIR%"
echo Press any key to continue...
pause >nul
goto :eof