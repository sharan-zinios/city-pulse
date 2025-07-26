#!/usr/bin/env pwsh
# Simple City Pulse Startup (No Docker)
# This script runs everything locally without Docker dependencies

param(
    [int]$IncidentCount = 10000,
    [string]$DatasetFile = "historical_incidents.json",
    [switch]$Help
)

function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

if ($Help) {
    Write-Info "🚀 City Pulse Simple Startup"
    Write-Info "============================"
    Write-Output ""
    Write-Output "This script runs City Pulse locally without Docker:"
    Write-Output "• Generates realistic incident dataset"
    Write-Output "• Starts local incident simulator"
    Write-Output "• Launches web dashboard with real-time updates"
    Write-Output ""
    Write-Output "USAGE:"
    Write-Output "  .\start_simple.ps1 [OPTIONS]"
    Write-Output ""
    Write-Output "OPTIONS:"
    Write-Output "  -IncidentCount <number>     Number of incidents (default: 10000)"
    Write-Output "  -DatasetFile <filename>     Dataset file (default: historical_incidents.json)"
    Write-Output "  -Help                       Show this help"
    Write-Output ""
    Write-Output "SERVICES:"
    Write-Output "  📊 Dashboard: http://localhost:3001"
    Write-Output "  🤖 Simulator: Background Python process"
    Write-Output ""
    exit 0
}

Write-Info "🏙️  CITY PULSE - SIMPLE LOCAL STARTUP"
Write-Info "====================================="
Write-Output ""

# Check prerequisites
Write-Info "🔍 Checking prerequisites..."

try {
    $pythonVersion = python --version 2>&1
    Write-Success "✅ Python: $pythonVersion"
} catch {
    Write-Error "❌ Python not found. Please install Python 3.8+"
    exit 1
}

try {
    $nodeVersion = node --version 2>&1
    Write-Success "✅ Node.js: $nodeVersion"
} catch {
    Write-Error "❌ Node.js not found. Please install Node.js 14+"
    exit 1
}

if (-not (Test-Path "local_dev")) {
    Write-Error "❌ Run from city-pulse root directory"
    exit 1
}

Write-Success "✅ Prerequisites OK"
Write-Output ""

# Step 1: Generate dataset
Write-Info "📊 STEP 1: Dataset Generation"
Write-Info "-----------------------------"

if (-not (Test-Path $DatasetFile)) {
    Write-Info "🏗️  Generating $IncidentCount incidents..."
    python local_dev/generate_dataset.py --count $IncidentCount --output $DatasetFile
    
    if (Test-Path $DatasetFile) {
        $fileSize = (Get-Item $DatasetFile).Length / 1MB
        Write-Success "✅ Generated: $([math]::Round($fileSize, 2)) MB"
    } else {
        Write-Error "❌ Dataset generation failed"
        exit 1
    }
} else {
    Write-Success "✅ Using existing dataset: $DatasetFile"
}

Write-Output ""

# Step 2: Install client dependencies
Write-Info "📦 STEP 2: Client Dependencies"
Write-Info "------------------------------"

if (-not (Test-Path "client\node_modules")) {
    Write-Info "📥 Installing Node.js dependencies..."
    Set-Location "client"
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ npm install failed"
        exit 1
    }
    Set-Location ".."
    Write-Success "✅ Dependencies installed"
} else {
    Write-Success "✅ Dependencies already installed"
}

Write-Output ""

# Step 3: Start services
Write-Info "🚀 STEP 3: Starting Services"
Write-Info "----------------------------"

# Start dashboard in background
Write-Info "🌐 Starting dashboard server..."
$dashboardJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Set-Location "client"
    npm start
}

Write-Success "✅ Dashboard started (Job: $($dashboardJob.Id))"

# Wait for dashboard
Write-Info "⏳ Waiting for dashboard..."
Start-Sleep -Seconds 8

# Check dashboard health
try {
    $health = Invoke-RestMethod -Uri "http://localhost:3001/health" -TimeoutSec 5
    Write-Success "✅ Dashboard healthy: $($health.status)"
} catch {
    Write-Warning "⚠️  Dashboard still starting..."
}

# Start simulator in background  
Write-Info "🤖 Starting incident simulator..."
$simulatorJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    python local_dev/realtime_simulator.py --dataset $using:DatasetFile
}

Write-Success "✅ Simulator started (Job: $($simulatorJob.Id))"

Write-Output ""

# Step 4: Service information
Write-Info "🎯 STEP 4: Your Services"
Write-Info "------------------------"

Write-Success "🌐 Dashboard:    http://localhost:3001"
Write-Success "📊 Health Check: http://localhost:3001/health"
Write-Success "🔌 WebSocket:    ws://localhost:3001"
Write-Success "📡 API:          http://localhost:3001/api/incidents/recent"

Write-Output ""

Write-Info "🎪 What You'll See:"
Write-Info "• Real-time incident feed with animations"
Write-Info "• Live notifications for high-priority incidents"
Write-Info "• AI agent activity monitoring"
Write-Info "• Statistics and area distribution"
Write-Info "• Beautiful dark theme with responsive design"

Write-Output ""

Write-Success "🎉 CITY PULSE IS RUNNING!"
Write-Success "========================="
Write-Output ""
Write-Warning "🌟 Open your browser: http://localhost:3001"
Write-Warning "🔄 Watch real-time incidents stream in!"
Write-Warning "📱 Try it on mobile - it's fully responsive!"
Write-Output ""

Write-Info "💡 Control Commands:"
Write-Info "   Get-Job                    # View running services"
Write-Info "   Stop-Job -Id <JobId>       # Stop a service"
Write-Info "   Receive-Job -Id <JobId>    # View service logs"
Write-Output ""

Write-Info "🔄 Monitoring services... (Press Ctrl+C to stop all)"

try {
    while ($true) {
        Start-Sleep -Seconds 30
        
        $jobs = Get-Job
        $running = $jobs | Where-Object { $_.State -eq "Running" }
        
        if ($running.Count -eq 0) {
            Write-Warning "⚠️  All services stopped"
            break
        }
        
        Write-Info "✅ Services active: $($running.Count) running"
        
        # Quick health check
        try {
            $health = Invoke-RestMethod -Uri "http://localhost:3001/health" -TimeoutSec 2
            Write-Info "   📊 Dashboard: Connected clients = $($health.connectedClients)"
        } catch {
            Write-Warning "   ⚠️  Dashboard not responding"
        }
    }
} catch {
    Write-Info "🛑 Stopping all services..."
    
    Get-Job | Stop-Job
    Get-Job | Remove-Job -Force
    
    Write-Success "✅ All services stopped"
}
