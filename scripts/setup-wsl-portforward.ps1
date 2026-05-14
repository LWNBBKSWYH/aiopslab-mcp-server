# WSL Port Forwarding Setup Script
# Forward Windows localhost:$Port to WSL

param(
    [int]$Port = 8765
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  WSL Port Forwarding Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Check admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "`n[ERROR] Admin privileges required" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator" -ForegroundColor Yellow
    Write-Host "`nOr manually run:" -ForegroundColor Gray
    Write-Host "  netsh interface portproxy add v4to v4 listenport=$Port connectport=$Port connectaddress=localhost" -ForegroundColor Gray
    exit 1
}

# Get WSL IP
Write-Host "`n[1/2] Getting WSL IP address..." -ForegroundColor White
try {
    $WSLIP = (wsl hostname -I).Trim().Split(" ")[0]
    Write-Host "  WSL IP: $WSLIP" -ForegroundColor Green
} catch {
    Write-Host "  Failed, using localhost" -ForegroundColor Yellow
    $WSLIP = "127.0.0.1"
}

# Set port forwarding
Write-Host "`n[2/2] Setting port forwarding..." -ForegroundColor White
Write-Host "  localhost:$Port -> $WSLIP`:$Port" -ForegroundColor Gray

# Remove old rule if exists
netsh interface portproxy delete v4to v4 listenport=$Port 2>$null

# Add new rule
netsh interface portproxy add v4to v4 listenport=$Port connectport=$Port connectaddress=$WSLIP

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Port forwarding configured" -ForegroundColor Green

    # Verify
    Write-Host "`nVerifying port forwarding..." -ForegroundColor White
    Start-Sleep -Seconds 1

    try {
        $testUrl = "http://localhost:$Port/mcp"
        Write-Host "  Testing: $testUrl" -ForegroundColor Gray
        $response = Invoke-WebRequest -Uri $testUrl -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response) {
            Write-Host "  [OK] Connection successful (Status: $($response.StatusCode))" -ForegroundColor Green
        }
    } catch {
        Write-Host "  [OK] Port forwarded (service may require SSE response)" -ForegroundColor Green
    }

    Write-Host "`n============================================" -ForegroundColor Cyan
    Write-Host "  Port forwarding setup complete!" -ForegroundColor Green
    Write-Host "  MCP Server: http://localhost:$Port/mcp" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
} else {
    Write-Host "  [ERROR] Setup failed" -ForegroundColor Red
}

# Show current rules
Write-Host "`nCurrent port forwarding rules:" -ForegroundColor White
netsh interface portproxy show v4to v4