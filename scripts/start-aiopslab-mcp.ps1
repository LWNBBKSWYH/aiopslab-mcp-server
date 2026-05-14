# AIOpsLab MCP Server Startup Script
# Start MCP Server and setup port forwarding

param(
    [string]$Mode = "windows",
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AIOpsLab MCP Server Startup Script" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

if ($Mode -eq "wsl") {
    # ============================================
    # Mode 1: WSL Port Forwarding
    # ============================================
    Write-Host "`n[Mode] WSL Port Forwarding" -ForegroundColor Yellow

    # Get WSL IP
    Write-Host "`n[1/3] Getting WSL IP address..." -ForegroundColor White
    try {
        $WSLIP = (wsl hostname -I).Trim().Split(" ")[0]
        Write-Host "  WSL IP: $WSLIP" -ForegroundColor Green
    } catch {
        Write-Host "  Failed, using default localhost" -ForegroundColor Yellow
        $WSLIP = "127.0.0.1"
    }

    # Setup port forwarding
    Write-Host "`n[2/3] Setting port forwarding..." -ForegroundColor White
    Write-Host "  Listen: 0.0.0.0:$Port -> localhost:$Port" -ForegroundColor Gray

    $existingRule = netsh interface portproxy show v4to v4 | Select-String ":$Port"
    if ($existingRule) {
        Write-Host "  Port $Port forwarding already exists, skipping" -ForegroundColor Yellow
    } else {
        try {
            netsh interface portproxy add v4to v4 listenport=$Port connectport=$Port connectaddress=$WSLIP
            Write-Host "  Port forwarding configured" -ForegroundColor Green
        } catch {
            Write-Host "  Admin privileges required for port forwarding" -ForegroundColor Red
            Write-Host "  Please run as Administrator" -ForegroundColor Red
        }
    }

    # Test connection
    Write-Host "`n[3/3] Testing connection..." -ForegroundColor White
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$Port/" -TimeoutSec 5 -UseBasicParsing
        Write-Host "  Connection OK! Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "`nMCP Server: http://localhost:$Port/mcp" -ForegroundColor Cyan
    } catch {
        Write-Host "  Connection failed: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "  Ensure WSL MCP Server is running" -ForegroundColor Yellow
    }

} else {
    # ============================================
    # Mode 2: Windows Local MCP Server
    # ============================================
    Write-Host "`n[Mode] Windows Local MCP Server" -ForegroundColor Yellow

    # Check Python
    Write-Host "`n[1/4] Checking Python..." -ForegroundColor White
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "  $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "  Python not found. Please install Python 3.11+" -ForegroundColor Red
        exit 1
    }

    # Install dependencies
    Write-Host "`n[2/4] Installing dependencies..." -ForegroundColor White
    $MCPPath = "E:\桌面\AiOps\aiopslab-mcp-server"
    if (Test-Path $MCPPath) {
        Set-Location $MCPPath
        Write-Host "  Installing Python dependencies..." -ForegroundColor Gray
        pip install -r requirements.txt -q
    } else {
        Write-Host "  MCP Server not found: $MCPPath" -ForegroundColor Red
        exit 1
    }

    # Start MCP Server
    Write-Host "`n[3/4] Starting MCP Server..." -ForegroundColor White
    Write-Host "  Port: $Port" -ForegroundColor Gray
    Write-Host "  Address: http://0.0.0.0:$Port/mcp" -ForegroundColor Gray
    Write-Host "`n  Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Host ""

    $mcpProcess = Start-Process -FilePath "python" -ArgumentList "mcp_server.py" -PassThru -NoNewWindow
    Start-Sleep -Seconds 3

    # Test
    Write-Host "`n[4/4] Testing service..." -ForegroundColor White
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$Port/mcp" -TimeoutSec 5 -UseBasicParsing
        Write-Host "  MCP Server OK! Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "`nMCP Server: http://localhost:$Port/mcp" -ForegroundColor Cyan
    } catch {
        Write-Host "  Service may still be starting..." -ForegroundColor Yellow
        Write-Host "  Check http://localhost:$Port/mcp" -ForegroundColor Yellow
    }

    Write-Host "`n============================================" -ForegroundColor Cyan
    Write-Host "  MCP Server running. Press any key to stop..." -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan

    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

    if ($mcpProcess -and !$mcpProcess.HasExited) {
        Stop-Process -Id $mcpProcess.Id -Force
        Write-Host "`nMCP Server stopped" -ForegroundColor Green
    }
}

Write-Host "`nDone!" -ForegroundColor Green