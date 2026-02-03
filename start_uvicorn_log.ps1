$log_file_name = "uvicorn_log_$(Get-Date -Format "yyyyMMdd_HHmmss").log"
$log_path = "C:\Users\catai\.gemini\tmp\a122009cd5fd3579faefff628130b3cc10b6e589f71b86a76ed8974a24383d84\$log_file_name"
Set-Content -Path $log_path -Value "" # Ensure file exists and is empty

# Start uvicorn, redirecting all output to the log file
# The `Start-Job` cmdlet is better for true background processes and output redirection
Start-Job -ScriptBlock {
    param($LogFile, $WorkingDir)
    Set-Location $WorkingDir
    Invoke-Expression "python -m uvicorn apps.backend.main:app --reload *>$LogFile"
} -ArgumentList $log_path, "D:\Projects\Unified-AI-Project" -Name "UvicornServer"

Write-Host "Uvicorn server started in background. Logs are being written to $log_path"
Write-Host "To stop the server: Get-Job -Name UvicornServer | Stop-Job -PassThru | Remove-Job"
Write-Host "To view logs: Get-Content $log_path"
