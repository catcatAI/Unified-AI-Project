
$port = 8000
echo "Checking for process on port $port..."
$process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique

if ($process) {
    echo "Found process ID: $process. Killing it..."
    Stop-Process -Id $process -Force
    echo "Process killed."
} else {
    echo "No process found on port $port."
}

echo "Starting new backend instance..."
$env:PYTHONPATH = "d:\Projects\Unified-AI-Project"
Start-Process -FilePath "python" -ArgumentList "apps/backend/main.py" -RedirectStandardOutput "logs/backend_restart.log" -RedirectStandardError "logs/backend_restart_err.log" -PassThru
echo "Backend start command issued."
