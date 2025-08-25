@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Training Manager
color 0A

:: 训练管理器主菜单
:main_menu
cls
echo ==========================================
echo   Unified AI Project - Training Manager
echo ==========================================
echo.
echo 请选择操作:
echo.
echo 1. 生成训练数据 (Generate training data)
echo 2. 下载训练数据 (Download training data)
echo 3. 设置生成与下载 (Setup generation and download)
echo 4. 列出统计 (List statistics)
echo 5. 设置训练 (Setup training)
echo 6. 开始训练 (Start training)
echo 7. 查看训练状态 (View training status)
echo 8. 退出 (Exit)
echo.
set /p choice="请输入选项 (1-8): "

if "%choice%"=="1" goto generate_data
if "%choice%"=="2" goto download_data
if "%choice%"=="3" goto setup_generation_download
if "%choice%"=="4" goto list_statistics
if "%choice%"=="5" goto setup_training
if "%choice%"=="6" goto start_training
if "%choice%"=="7" goto view_training_status
if "%choice%"=="8" goto exit_script
echo.
echo 无效选项，请重新选择。
pause
goto main_menu

:: 生成训练数据
:generate_data
cls
echo ==========================================
echo   生成训练数据 (Generate Training Data)
echo ==========================================
echo.
echo 选择要生成的数据类型:
echo.
echo 1. 全部模拟数据 (All mock data)
echo 2. 视觉数据 (Vision data)
echo 3. 音频数据 (Audio data)
echo 4. 推理数据 (Reasoning data)
echo 5. 多模态数据 (Multimodal data)
echo 6. 返回主菜单 (Back to main menu)
echo.
set /p data_choice="请输入选项 (1-6): "

if "%data_choice%"=="1" (
    echo.
    echo 生成全部模拟训练数据...
    python scripts\generate_mock_data.py
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] 生成训练数据失败
        pause
        goto main_menu
    )
    echo.
    echo [SUCCESS] 全部模拟训练数据生成完成
    pause
    goto main_menu
)

if "%data_choice%"=="2" (
    echo.
    echo 生成视觉训练数据...
    python -c "from scripts.generate_mock_data import MockDataGenerator; g = MockDataGenerator(); g.generate_vision_data()"
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] 生成视觉数据失败
        pause
        goto main_menu
    )
    echo.
    echo [SUCCESS] 视觉训练数据生成完成
    pause
    goto main_menu
)

if "%data_choice%"=="3" (
    echo.
    echo 生成音频训练数据...
    python -c "from scripts.generate_mock_data import MockDataGenerator; g = MockDataGenerator(); g.generate_audio_data()"
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] 生成音频数据失败
        pause
        goto main_menu
    )
    echo.
    echo [SUCCESS] 音频训练数据生成完成
    pause
    goto main_menu
)

if "%data_choice%"=="4" (
    echo.
    echo 生成推理训练数据...
    python -c "from scripts.generate_mock_data import MockDataGenerator; g = MockDataGenerator(); g.generate_reasoning_data()"
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] 生成推理数据失败
        pause
        goto main_menu
    )
    echo.
    echo [SUCCESS] 推理训练数据生成完成
    pause
    goto main_menu
)

if "%data_choice%"=="5" (
    echo.
    echo 生成多模态训练数据...
    python -c "from scripts.generate_mock_data import MockDataGenerator; g = MockDataGenerator(); g.generate_multimodal_data()"
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] 生成多模态数据失败
        pause
        goto main_menu
    )
    echo.
    echo [SUCCESS] 多模态训练数据生成完成
    pause
    goto main_menu
)

if "%data_choice%"=="6" goto main_menu
echo.
echo 无效选项，请重新选择。
pause
goto generate_data

:: 下载训练数据
:download_data
cls
echo ==========================================
echo   下载训练数据 (Download Training Data)
echo ==========================================
echo.
echo 注意: 下载训练数据需要网络连接和足够的磁盘空间
echo.
echo 1. 开始下载训练数据 (Start downloading training data)
echo 2. 查看下载状态 (View download status)
echo 3. 返回主菜单 (Back to main menu)
echo.
set /p download_choice="请输入选项 (1-3): "

if "%download_choice%"=="1" (
    echo.
    echo 开始下载训练数据...
    python scripts\download_training_data.py
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] 下载训练数据失败
        pause
        goto main_menu
    )
    echo.
    echo [SUCCESS] 训练数据下载完成
    pause
    goto main_menu
)

if "%download_choice%"=="2" (
    echo.
    echo 查看训练数据下载状态...
    python -c "from scripts.download_training_data import DatasetDownloader; d = DatasetDownloader(); status = d.get_download_status(); print('训练数据下载状态:'); [print(f'{k}: {v}') for k, v in status.items()]"
    pause
    goto main_menu
)

if "%download_choice%"=="3" goto main_menu
echo.
echo 无效选项，请重新选择。
pause
goto download_data

:: 设置生成与下载
:setup_generation_download
cls
echo ==========================================
echo   设置生成与下载 (Setup Generation and Download)
echo ==========================================
echo.
echo 1. 检查环境 (Check environment)
echo 2. 配置数据路径 (Configure data paths)
echo 3. 设置磁盘空间检查 (Setup disk space check)
echo 4. 返回主菜单 (Back to main menu)
echo.
set /p setup_choice="请输入选项 (1-4): "

if "%setup_choice%"=="1" (
    echo.
    echo 检查环境...
    where python >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python 未安装
        echo 请从 https://python.org/ 下载并安装 Python
        pause
        goto main_menu
    )
    echo [OK] Python 环境正常
    pause
    goto setup_generation_download
)

if "%setup_choice%"=="2" (
    echo.
    echo 配置数据路径...
    echo 当前工作目录: %cd%
    echo 数据目录: data\
    echo 训练配置目录: training\configs\
    echo.
    echo [INFO] 路径配置检查完成
    pause
    goto setup_generation_download
)

if "%setup_choice%"=="3" (
    echo.
    echo 设置磁盘空间检查...
    python -c "import shutil; total, used, free = shutil.disk_usage('.'); print(f'磁盘空间: 总计 {total//(1024**3)}GB, 已用 {used//(1024**3)}GB, 可用 {free//(1024**3)}GB')"
    pause
    goto setup_generation_download
)

if "%setup_choice%"=="4" goto main_menu
echo.
echo 无效选项，请重新选择。
pause
goto setup_generation_download

:: 列出统计
:list_statistics
cls
echo ==========================================
echo   列出统计 (List Statistics)
echo ==========================================
echo.

:: 统计模拟数据
echo 模拟数据统计:
echo ====================
set vision_count=0
set audio_count=0
set reasoning_count=0
set multimodal_count=0

if exist "data\vision_samples\annotations.json" (
    for /f "delims=" %%i in ('find /c "{" ^< "data\vision_samples\annotations.json"') do set vision_count=%%i
    set vision_count=!vision_count:*:=!
)

if exist "data\audio_samples\transcripts.json" (
    for /f "delims=" %%i in ('find /c "{" ^< "data\audio_samples\transcripts.json"') do set audio_count=%%i
    set audio_count=!audio_count:*:=!
)

if exist "data\reasoning_samples\causal_relations.json" (
    for /f "delims=" %%i in ('find /c "{" ^< "data\reasoning_samples\causal_relations.json"') do set reasoning_count=%%i
    set reasoning_count=!reasoning_count:*:=!
)

if exist "data\multimodal_samples\multimodal_pairs.json" (
    for /f "delims=" %%i in ('find /c "{" ^< "data\multimodal_samples\multimodal_pairs.json"') do set multimodal_count=%%i
    set multimodal_count=!multimodal_count:*:=!
)

echo 视觉数据样本: !vision_count! 个
echo 音频数据样本: !audio_count! 个
echo 推理数据样本: !reasoning_count! 个
echo 多模态数据样本: !multimodal_count! 个
echo.

:: 统计下载数据
echo 下载数据统计:
echo ====================
set flickr_count=0
set common_voice_count=0
set coco_count=0
set visual_genome_count=0

if exist "data\flickr30k_sample" (
    for /f "delims=" %%i in ('dir "data\flickr30k_sample" /b /s ^| find /c "."') do set flickr_count=%%i
    set flickr_count=!flickr_count:*:=!
)

if exist "data\common_voice_zh" (
    for /f "delims=" %%i in ('dir "data\common_voice_zh" /b /s ^| find /c "."') do set common_voice_count=%%i
    set common_voice_count=!common_voice_count:*:=!
)

if exist "data\coco_captions" (
    for /f "delims=" %%i in ('dir "data\coco_captions" /b /s ^| find /c "."') do set coco_count=%%i
    set coco_count=!coco_count:*:=!
)

if exist "data\visual_genome_sample" (
    for /f "delims=" %%i in ('dir "data\visual_genome_sample" /b /s ^| find /c "."') do set visual_genome_count=%%i
    set visual_genome_count=!visual_genome_count:*:=!
)

echo Flickr30K 数据集文件数: !flickr_count! 个
echo Common Voice 中文数据集文件数: !common_voice_count! 个
echo COCO Captions 数据集文件数: !coco_count! 个
echo Visual Genome 数据集文件数: !visual_genome_count! 个
echo.

:: 显示数据来源统计
echo 数据来源统计:
echo ====================
echo 模拟数据来源:
echo   - 视觉数据 (vision_samples): !vision_count! 个样本
echo   - 音频数据 (audio_samples): !audio_count! 个样本
echo   - 推理数据 (reasoning_samples): !reasoning_count! 个样本
echo   - 多模态数据 (multimodal_samples): !multimodal_count! 个样本
echo.
echo 下载数据来源:
echo   - Flickr30K 数据集 (flickr30k_sample): !flickr_count! 个文件
echo   - Common Voice 中文数据集 (common_voice_zh): !common_voice_count! 个文件
echo   - COCO Captions 数据集 (coco_captions): !coco_count! 个文件
echo   - Visual Genome 数据集 (visual_genome_sample): !visual_genome_count! 个文件
echo.

:: 显示总统计
set /a total_mock_data=!vision_count! + !audio_count! + !reasoning_count! + !multimodal_count!
set /a total_downloaded_files=!flickr_count! + !common_voice_count! + !coco_count! + !visual_genome_count!
echo 总计:
echo ====================
echo 模拟数据样本总数: !total_mock_data! 个
echo 下载数据文件总数: !total_downloaded_files! 个
echo.

pause
goto main_menu

:: 设置训练
:setup_training
cls
echo ==========================================
echo   设置训练 (Setup Training)
echo ==========================================
echo.
echo 1. 检查训练环境 (Check training environment)
echo 2. 安装训练依赖 (Install training dependencies)
echo 3. 配置训练参数 (Configure training parameters)
echo 4. 返回主菜单 (Back to main menu)
echo.
set /p train_setup_choice="请输入选项 (1-4): "

if "%train_setup_choice%"=="1" (
    echo.
    echo 检查训练环境...
    where python >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python 未安装
        pause
        goto main_menu
    )
    
    echo [OK] Python 环境正常
    
    where pnpm >nul 2>&1
    if %errorlevel% neq 0 (
        echo [INFO] 安装 pnpm...
        npm install -g pnpm
        if %errorlevel% neq 0 (
            echo [ERROR] 安装 pnpm 失败
            pause
            goto main_menu
        )
    )
    echo [OK] pnpm 环境正常
    
    echo.
    echo [SUCCESS] 训练环境检查完成
    pause
    goto setup_training
)

if "%train_setup_choice%"=="2" (
    echo.
    echo 安装训练依赖...
    pnpm install
    if %errorlevel% neq 0 (
        echo [ERROR] 安装依赖失败
        pause
        goto main_menu
    )
    
    cd apps\backend
    if not exist "venv" (
        echo [INFO] 创建 Python 虚拟环境...
        python -m venv venv
        if %errorlevel% neq 0 (
            echo [ERROR] 创建虚拟环境失败
            cd ..\..
            pause
            goto main_menu
        )
    )
    
    echo [INFO] 安装 Python 包...
    call venv\Scripts\activate.bat
    pip install --upgrade pip >nul 2>&1
    pip install -r requirements.txt >nul 2>&1
    pip install -r requirements-dev.txt >nul 2>&1
    cd ..\..
    
    echo.
    echo [SUCCESS] 训练依赖安装完成
    pause
    goto setup_training
)

if "%train_setup_choice%"=="3" (
    echo.
    echo 配置训练参数...
    if exist "training\configs\training_config.json" (
        echo 当前训练配置:
        type training\configs\training_config.json
        echo.
        echo [INFO] 训练配置文件存在
    ) else (
        echo [WARN] 训练配置文件不存在，将使用默认配置
    )
    pause
    goto setup_training
)

if "%train_setup_choice%"=="4" goto main_menu
echo.
echo 无效选项，请重新选择。
pause
goto setup_training

:: 开始训练
:start_training
cls
echo ==========================================
echo   开始训练 (Start Training)
echo ==========================================
echo.
echo 1. 使用默认配置开始训练 (Start training with default config)
echo 2. 使用预设配置开始训练 (Start training with preset config)
echo 3. 自定义训练参数 (Customize training parameters)
echo 4. 运行训练集成测试 (Run training integration tests)
echo 5. 返回主菜单 (Back to main menu)
echo.
set /p start_choice="请输入选项 (1-5): "

if "%start_choice%"=="1" (
    echo.
    echo 使用默认配置开始训练...
    echo [INFO] 此功能需要根据具体模型实现
    echo [INFO] 请参考 apps/backend/training/ 目录中的训练脚本
    echo.
    echo 示例命令:
    echo   cd apps\backend
    echo   call venv\Scripts\activate.bat
    echo   python training\train_model.py
    echo.
    echo 请根据具体需求运行相应的训练脚本
    pause
    goto main_menu
)

if "%start_choice%"=="2" (
    echo.
    echo 使用预设配置开始训练...
    if exist "training\configs\training_preset.json" (
        echo [INFO] 找到预设配置文件
        echo [INFO] 预设配置包含多种训练场景:
        echo.
        echo   1. 快速开始 (Quick Start) - 使用模拟数据快速训练测试
        echo      适用场景: 快速验证训练流程，测试模型基本功能
        echo      数据集: vision_samples, audio_samples, reasoning_samples
        echo      训练轮数: 3
        echo.
        echo   2. 全面训练 (Comprehensive Training) - 使用所有可用数据完整训练
        echo      适用场景: 完整训练所有模型，获得最佳性能
        echo      数据集: 所有可用数据集
        echo      训练轮数: 50
        echo.
        echo   3. 视觉专注 (Vision Focus) - 专注训练视觉相关模型
        echo      适用场景: 专门训练视觉服务模型
        echo      数据集: 视觉相关数据集
        echo      训练轮数: 30
        echo.
        echo   4. 音频专注 (Audio Focus) - 专注训练音频相关模型
        echo      适用场景: 专门训练音频服务模型
        echo      数据集: 音频相关数据集
        echo      训练轮数: 20
        echo.
        set /p preset_choice="请选择训练场景 (1-4): "
        
        if "%preset_choice%"=="1" (
            echo.
            echo [INFO] 启动快速开始训练场景...
            echo [INFO] 使用模拟数据进行快速训练测试
            echo.
            echo 正在启动训练...
            cd apps\backend
            call venv\Scripts\activate.bat
            python ..\..\training\train_model.py --preset quick_start
            cd ..\..
        ) else if "%preset_choice%"=="2" (
            echo.
            echo [INFO] 启动全面训练场景...
            echo [INFO] 使用所有可用数据进行完整训练
            echo.
            echo 正在启动训练...
            cd apps\backend
            call venv\Scripts\activate.bat
            python ..\..\training\train_model.py --preset comprehensive_training
            cd ..\..
        ) else if "%preset_choice%"=="3" (
            echo.
            echo [INFO] 启动视觉专注训练场景...
            echo.
            echo 正在启动训练...
            cd apps\backend
            call venv\Scripts\activate.bat
            python ..\..\training\train_model.py --preset vision_focus
            cd ..\..
        ) else if "%preset_choice%"=="4" (
            echo.
            echo [INFO] 启动音频专注训练场景...
            echo.
            echo 正在启动训练...
            cd apps\backend
            call venv\Scripts\activate.bat
            python ..\..\training\train_model.py --preset audio_focus
            cd ..\..
        ) else (
            echo.
            echo [WARN] 无效选项，返回主菜单
        )
    ) else (
        echo [WARN] 预设配置文件不存在，将使用默认配置
        echo.
        echo 正在启动训练...
        cd apps\backend
        call venv\Scripts\activate.bat
        python ..\..\training\train_model.py
        cd ..\..
    )
    echo.
    pause
    goto main_menu
)

if "%start_choice%"=="3" (
    echo.
    echo 自定义训练参数...
    echo [INFO] 此功能需要交互式参数设置
    echo [INFO] 请手动编辑 training\configs\training_config.json 文件
    echo.
    echo 当前配置:
    if exist "training\configs\training_config.json" (
        type training\configs\training_config.json
    ) else (
        echo [WARN] 配置文件不存在
    )
    echo.
    echo 编辑完成后按任意键继续...
    pause
    goto main_menu
)

if "%start_choice%"=="4" (
    echo.
    echo 运行训练集成测试...
    cd apps\backend
    call venv\Scripts\activate.bat
    python ..\..\scripts\training_integration.py
    if %errorlevel% neq 0 (
        echo [ERROR] 训练集成测试失败
        cd ..\..
        pause
        goto main_menu
    )
    cd ..\..
    echo.
    echo [SUCCESS] 训练集成测试完成
    pause
    goto main_menu
)

if "%start_choice%"=="5" goto main_menu
echo.
echo 无效选项，请重新选择。
pause
goto start_training

:: 查看训练状态
:view_training_status
cls
echo ==========================================
echo   查看训练状态 (View Training Status)
echo ==========================================
echo.
echo 训练配置检查:
echo.
if exist "training\configs\training_config.json" (
    echo [OK] 训练配置文件存在
    echo.
    echo 配置内容:
    type training\configs\training_config.json
) else (
    echo [WARN] 训练配置文件不存在
)

echo.
echo 检查点目录:
echo.
if exist "training\checkpoints" (
    echo [OK] 检查点目录存在
    dir training\checkpoints /b
) else (
    echo [INFO] 检查点目录不存在
)

echo.
echo 日志目录:
echo.
if exist "training\logs" (
    echo [OK] 日志目录存在
    dir training\logs /b
) else (
    echo [INFO] 日志目录不存在
)

echo.
echo 模型目录:
echo.
if exist "training\models" (
    echo [OK] 模型目录存在
    dir training\models /b
) else (
    echo [INFO] 模型目录不存在
)

echo.
pause
goto main_menu

:: 退出脚本
:exit_script
cls
echo.
echo 感谢使用 Unified AI Project 训练管理器!
echo.
echo 按任意键退出...
pause >nul
exit /b 0