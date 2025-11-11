# Tunnel client and test execution

Write-Host "=" * 60
Write-Host "Tunnel Integration Test"
Write-Host "=" * 60

# 1. Start tunnel client in background
Write-Host "`n[1/3] Starting tunnel client..."
$clientJob = Start-Job -ScriptBlock {
    Set-Location "D:\git\frps\tunnel-client"
    & ".\venv\Scripts\python.exe" "tunnel_client.py"
}

# 2. Wait for client initialization
Write-Host "[2/3] Waiting for client initialization (5 seconds)..."
Start-Sleep -Seconds 5

# 3. Send HTTP request
Write-Host "[3/3] Sending HTTP request..."
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri "http://192.168.50.196:8091/v1/chat/completions" `
        -Method POST `
        -ContentType "application/json" `
        -Body (@{
            model = "qwen3-coder:30b"
            messages = @(
                @{
                    role = "user"
                    content = "Hello! This is a tunnel test."
                }
            )
            max_tokens = 50
        } | ConvertTo-Json) `
        -TimeoutSec 60

    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "Status: $($response.StatusCode)"
    
    $data = $response.Content | ConvertFrom-Json
    Write-Host "`nResponse:"
    Write-Host "  Model: $($data.model)"
    Write-Host "  Message: $($data.choices[0].message.content)"
    
} catch {
    Write-Host "FAILED!" -ForegroundColor Red
    Write-Host "Error: $_"
} finally {
    # Stop client
    Write-Host "`nStopping client..."
    Stop-Job -Job $clientJob
    Remove-Job -Job $clientJob
}

Write-Host "`nTest completed!"
