<#
.SYNOPSIS
    DevLens AI - Unified Startup Script
    
.DESCRIPTION
    Starts the entire DevLens stack with one click:
    - Docker infrastructure (Acontext, Redis)
    - Backend (FastAPI)
    - Frontend (React/Vite)

.NOTES
    Author: DevLens AI
    Run from project root: .\start_devlens.ps1
#>

param(
    [switch]$SkipDocker,
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

# Colors for output
$colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error   = "Red"
    Info    = "Cyan"
}

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Banner {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                                                           ║" -ForegroundColor Cyan
    Write-Host "║              DevLens AI - Startup Script                  ║" -ForegroundColor Cyan
    Write-Host "║                                                           ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Test-DockerRunning {
    try {
        $null = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
    }
    catch {
        return $false
    }
    return $false
}

function Start-DockerDesktop {
    Write-ColorOutput "Attempting to start Docker Desktop..." $colors.Warning
    
    $dockerPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerPath) {
        Start-Process $dockerPath
        Write-ColorOutput "Docker Desktop starting... Please wait 30 seconds." $colors.Info
        Start-Sleep -Seconds 30
        
        # Check if it's running now
        if (Test-DockerRunning) {
            Write-ColorOutput "✓ Docker Desktop is now running!" $colors.Success
            return $true
        }
        else {
            Write-ColorOutput "✗ Docker Desktop didn't start in time. Please start it manually." $colors.Error
            return $false
        }
    }
    else {
        Write-ColorOutput "✗ Docker Desktop not found at expected path." $colors.Error
        Write-ColorOutput "  Please install Docker Desktop or start it manually." $colors.Warning
        return $false
    }
}

function Start-Infrastructure {
    Write-ColorOutput "`n[1/3] Starting Docker Infrastructure..." $colors.Info
    Write-ColorOutput "      Running: docker-compose up -d" $colors.Info
    
    docker-compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✓ Infrastructure started successfully!" $colors.Success
        return $true
    }
    else {
        Write-ColorOutput "✗ Failed to start infrastructure" $colors.Error
        return $false
    }
}

function Start-Backend {
    Write-ColorOutput "`n[2/3] Starting Backend Server..." $colors.Info
    Write-ColorOutput "      Running: uvicorn app.main:app --reload" $colors.Info
    
    $backendPath = Join-Path $PSScriptRoot "backend"
    
    # Check if backend directory exists
    if (-not (Test-Path $backendPath)) {
        Write-ColorOutput "✗ Backend directory not found: $backendPath" $colors.Error
        return $false
    }
    
    # Start backend in new terminal
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$backendPath'; Write-Host 'DevLens Backend Server' -ForegroundColor Cyan; Write-Host '━━━━━━━━━━━━━━━━━━━━━━━' -ForegroundColor Cyan; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    )
    
    Write-ColorOutput "✓ Backend server starting in new window..." $colors.Success
    return $true
}

function Start-Frontend {
    Write-ColorOutput "`n[3/3] Starting Frontend Server..." $colors.Info
    Write-ColorOutput "      Running: npm run dev" $colors.Info
    
    $frontendPath = Join-Path $PSScriptRoot "frontend"
    
    # Check if frontend directory exists
    if (-not (Test-Path $frontendPath)) {
        Write-ColorOutput "✗ Frontend directory not found: $frontendPath" $colors.Error
        return $false
    }
    
    # Check if node_modules exists
    $nodeModules = Join-Path $frontendPath "node_modules"
    if (-not (Test-Path $nodeModules)) {
        Write-ColorOutput "  Installing npm dependencies first..." $colors.Warning
        Push-Location $frontendPath
        npm install
        Pop-Location
    }
    
    # Start frontend in new terminal
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$frontendPath'; Write-Host 'DevLens Frontend Server' -ForegroundColor Magenta; Write-Host '━━━━━━━━━━━━━━━━━━━━━━━━' -ForegroundColor Magenta; npm run dev"
    )
    
    Write-ColorOutput "✓ Frontend server starting in new window..." $colors.Success
    return $true
}

function Write-Summary {
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host ""
    Write-Host "  🎉 DevLens AI Stack Started Successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  📍 Local URLs:" -ForegroundColor White
    Write-Host "     ├─ Frontend:          http://localhost:5173" -ForegroundColor Cyan
    Write-Host "     ├─ Backend API:       http://localhost:8000" -ForegroundColor Cyan
    Write-Host "     ├─ API Docs:          http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "     └─ Acontext Dashboard: http://localhost:8001" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  💡 Tips:" -ForegroundColor White
    Write-Host "     • Backend and Frontend logs are in separate terminal windows" -ForegroundColor Gray
    Write-Host "     • Close terminal windows to stop servers" -ForegroundColor Gray
    Write-Host "     • Run 'docker-compose down' to stop infrastructure" -ForegroundColor Gray
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host ""
}

# ============================================================================
# Main Script
# ============================================================================

Write-Banner

# Check Docker (unless skipped)
if (-not $SkipDocker) {
    Write-ColorOutput "Checking Docker Desktop status..." $colors.Info
    
    if (-not (Test-DockerRunning)) {
        Write-ColorOutput "✗ Docker Desktop is not running." $colors.Warning
        
        $response = Read-Host "Would you like to start Docker Desktop? (y/n)"
        if ($response -eq 'y' -or $response -eq 'Y') {
            if (-not (Start-DockerDesktop)) {
                Write-ColorOutput "Cannot continue without Docker. Exiting." $colors.Error
                exit 1
            }
        }
        else {
            Write-ColorOutput "Skipping Docker infrastructure. Only starting app servers." $colors.Warning
            $SkipDocker = $true
        }
    }
    else {
        Write-ColorOutput "✓ Docker Desktop is running!" $colors.Success
    }
}

# Start Infrastructure
if (-not $SkipDocker -and -not $FrontendOnly) {
    if (-not (Start-Infrastructure)) {
        Write-ColorOutput "Warning: Infrastructure failed to start. Continuing anyway..." $colors.Warning
    }
    # Give containers time to initialize
    Start-Sleep -Seconds 3
}

# Start Backend
if (-not $FrontendOnly) {
    if (-not (Start-Backend)) {
        Write-ColorOutput "Failed to start backend server." $colors.Error
    }
    # Give backend time to start
    Start-Sleep -Seconds 2
}

# Start Frontend
if (-not $BackendOnly) {
    if (-not (Start-Frontend)) {
        Write-ColorOutput "Failed to start frontend server." $colors.Error
    }
}

# Print Summary
Start-Sleep -Seconds 1
Write-Summary
