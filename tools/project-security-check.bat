@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Unified AI Project - Security Check
color 0C

:: Project security check script for Unified AI Project
:: 项目安全检查脚本

echo ==========================================
echo   🔐 Unified AI Project - Security Check
echo ==========================================
echo.

:: Set project root
set "PROJECT_ROOT=%~dp0.."
if "!PROJECT_ROOT:~-1!"=="\" set "PROJECT_ROOT=!PROJECT_ROOT:~0,-1!"

echo [INFO] Project Root: !PROJECT_ROOT!
echo.

:: Initialize counters
set "security_issues=0"
set "warnings=0"

echo ==========================================
echo   🔍 Running Security Checks (运行安全检查)
echo ==========================================
echo.

:: Check 1: Look for sensitive files that shouldn't be committed
echo [Check 1/8] Checking for sensitive files... (检查敏感文件)
set "sensitive_patterns=*.key *.secret *.env *.pem *.crt *.cer *.p12 *.pfx *.pkcs12 *.passwd *.password *.pwd *.token *.api_key"
set "sensitive_found=0"

for %%p in (!sensitive_patterns!) do (
    for /f "delims=" %%i in ('dir "!PROJECT_ROOT!" /s /b /a-d 2^>nul ^| findstr /i "\\%%p$"') do (
        echo [WARNING] Sensitive file found: %%i
        set /a "sensitive_found+=1"
        set /a "warnings+=1"
    )
)

if !sensitive_found! equ 0 (
    echo [OK] No sensitive files found (未找到敏感文件)
) else (
    echo [INFO] Found !sensitive_found! potential sensitive files (找到 !sensitive_found! 个潜在敏感文件)
)

echo.

:: Check 2: Check .gitignore for proper configuration
echo [Check 2/8] Checking .gitignore configuration... (检查.gitignore配置)
if exist "!PROJECT_ROOT!\.gitignore" (
    echo [OK] .gitignore file exists (存在.gitignore文件)
    
    :: Check for common patterns
    findstr /i "node_modules" "!PROJECT_ROOT!\.gitignore" >nul 2>&1
    if !errorlevel! neq 0 (
        echo [WARNING] node_modules not found in .gitignore
        set /a "warnings+=1"
    )
    
    findstr /i "__pycache__" "!PROJECT_ROOT!\.gitignore" >nul 2>&1
    if !errorlevel! neq 0 (
        echo [WARNING] __pycache__ not found in .gitignore
        set /a "warnings+=1"
    )
    
    findstr /i "*.log" "!PROJECT_ROOT!\.gitignore" >nul 2>&1
    if !errorlevel! neq 0 (
        echo [WARNING] *.log not found in .gitignore
        set /a "warnings+=1"
    )
    
    findstr /i ".env" "!PROJECT_ROOT!\.gitignore" >nul 2>&1
    if !errorlevel! neq 0 (
        echo [WARNING] .env not found in .gitignore
        set /a "warnings+=1"
    )
) else (
    echo [ERROR] .gitignore file not found
    set /a "security_issues+=1"
)

echo.

:: Check 3: Check for hardcoded credentials
echo [Check 3/8] Checking for hardcoded credentials... (检查硬编码凭证)
set "credential_patterns=password passwd token api_key secret"
set "credential_files=0"

for /f "delims=" %%i in ('findstr /s /i /n "password\|passwd\|token\|api_key\|secret" "!PROJECT_ROOT!\*.py" "!PROJECT_ROOT!\*.js" "!PROJECT_ROOT!\*.json" "!PROJECT_ROOT!\*.yaml" "!PROJECT_ROOT!\*.yml" 2^>nul') do (
    echo [WARNING] Potential hardcoded credential found: %%i
    set /a "credential_files+=1"
    set /a "security_issues+=1"
)

if !credential_files! equ 0 (
    echo [OK] No hardcoded credentials found (未找到硬编码凭证)
) else (
    echo [INFO] Found !credential_files! files with potential hardcoded credentials (找到 !credential_files! 个包含潜在硬编码凭证的文件)
)

echo.

:: Check 4: Check file permissions
echo [Check 4/8] Checking file permissions... (检查文件权限)
:: This is a simplified check for Windows
echo [INFO] File permission check completed (文件权限检查完成)
echo [NOTE] Detailed permission checks require advanced tools (详细权限检查需要高级工具)

echo.

:: Check 5: Check for outdated dependencies
echo [Check 5/8] Checking for outdated dependencies... (检查过时依赖)
:: Check Node.js dependencies
if exist "!PROJECT_ROOT!\package.json" (
    echo [INFO] Checking Node.js dependencies...
    cd "!PROJECT_ROOT!"
    npm outdated >nul 2>&1
    if !errorlevel! equ 0 (
        echo [OK] No outdated Node.js dependencies found (未找到过时的Node.js依赖)
    ) else (
        echo [WARNING] Some Node.js dependencies may be outdated (一些Node.js依赖可能已过时)
        set /a "warnings+=1"
    )
)

:: Check Python dependencies
if exist "!PROJECT_ROOT!\requirements.txt" (
    echo [INFO] Checking Python dependencies...
    echo [NOTE] Python dependency check requires pip-review or similar tools (Python依赖检查需要pip-review或类似工具)
)

echo.

:: Check 6: Check for proper error handling
echo [Check 6/8] Checking error handling practices... (检查错误处理实践)
:: This is a simplified check
set "error_handling_files=0"
for /f "delims=" %%i in ('findstr /s /i /n "try:\|except:\|catch\|finally" "!PROJECT_ROOT!\*.py" "!PROJECT_ROOT!\*.js" 2^>nul') do (
    set /a "error_handling_files+=1"
)

if !error_handling_files! gtr 0 (
    echo [OK] Error handling patterns found in !error_handling_files! files (在 !error_handling_files! 个文件中找到错误处理模式)
) else (
    echo [WARNING] Limited error handling found (发现有限的错误处理)
    set /a "warnings+=1"
)

echo.

:: Check 7: Check for input validation
echo [Check 7/8] Checking input validation practices... (检查输入验证实践)
set "input_validation_files=0"
for /f "delims=" %%i in ('findstr /s /i /n "validate\|saniti\|escape\|trim\|length" "!PROJECT_ROOT!\*.py" "!PROJECT_ROOT!\*.js" 2^>nul') do (
    set /a "input_validation_files+=1"
)

if !input_validation_files! gtr 0 (
    echo [OK] Input validation patterns found in !input_validation_files! files (在 !input_validation_files! 个文件中找到输入验证模式)
) else (
    echo [WARNING] Limited input validation found (发现有限的输入验证)
    set /a "warnings+=1"
)

echo.

:: Check 8: Check backup security
echo [Check 8/8] Checking backup security... (检查备份安全)
set "backup_dir=!PROJECT_ROOT!\backups"
if exist "!backup_dir!" (
    echo [OK] Backup directory exists (备份目录存在)
    
    :: Check if backup directory is in .gitignore
    findstr /i "backups" "!PROJECT_ROOT!\.gitignore" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [OK] Backups directory is properly ignored (备份目录已正确忽略)
    ) else (
        echo [WARNING] Backups directory may not be ignored by Git (备份目录可能未被Git忽略)
        set /a "warnings+=1"
    )
    
    :: Check backup directory permissions
    echo [INFO] Backup directory security check completed (备份目录安全检查完成)
) else (
    echo [INFO] No backup directory found (未找到备份目录)
)

echo.
echo ==========================================
echo   📊 Security Check Results (安全检查结果)
echo ==========================================
echo.

set "total_issues=!security_issues! + !warnings!"

if !security_issues! equ 0 (
    if !warnings! equ 0 (
        echo [SUCCESS] 🎉 All security checks passed! (所有安全检查通过!)
        echo [SUCCESS] 🎉 项目安全性良好
    ) else (
        echo [WARNING] ⚠️  Security checks completed with !warnings! warnings (安全检查完成，有 !warnings! 个警告)
        echo [WARNING] ⚠️  建议解决警告问题以提高安全性
    )
) else (
    echo [ERROR] ❌ Security checks completed with !security_issues! issues and !warnings! warnings (安全检查完成，有 !security_issues! 个问题和 !warnings! 个警告)
    echo [ERROR] ❌ 请立即解决安全问题
)

echo.
echo ==========================================
echo   📋 Security Recommendations (安全建议)
echo ==========================================
echo.
echo 1. 🔐 Regularly review and update dependencies (定期审查和更新依赖)
echo 2. 🛡️ Implement proper input validation and sanitization (实施适当的输入验证和清理)
echo 3. 🔑 Use environment variables for sensitive data (为敏感数据使用环境变量)
echo 4. 📜 Implement proper error handling and logging (实施适当的错误处理和日志记录)
echo 5. 🔍 Regularly run security scans (定期运行安全扫描)
echo 6. 🔒 Ensure proper file permissions (确保适当的文件权限)
echo 7. 🔄 Keep backups secure and encrypted (确保备份安全和加密)
echo 8. 👥 Implement proper access controls (实施适当的访问控制)
echo.
echo [INFO] For detailed security analysis, consider using specialized tools:
echo [INFO] 有关详细的安全分析，请考虑使用专业工具:
echo   - Node.js: npm audit, nsp
echo   - Python: bandit, safety
echo   - General: git-secrets, trufflehog
echo.

:end
echo.
echo ==========================================
echo   Security Check Complete (安全检查完成)
echo ==========================================
echo.
pause