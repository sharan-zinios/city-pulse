#!/usr/bin/env pwsh
# City Pulse Local Microservices Startup Script
# This script sets up and runs the complete local development environment

param(
    [int]$IncidentCount = 10000,
    [string]$DatasetFile = "historical_incidents.json",
    [switch]$UseDocker,
    [switch]$SkipDatasetGeneration,
    [switch]$SkipDashboard,
    [switch]$CleanStart,
    [switch]$Help
)

# Color functions
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) { Write-Output $args }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success { Write-ColorOutput Green $args }
function Write-Info { Write-ColorOutput Cyan $args }
function Write-Warning { Write-ColorOutput Yellow $args }
function Write-Error { Write-ColorOutput Red $args }

function Show-Help {
    Write-Info "🚀 City Pulse Local Microservices Startup"
    Write-Info "========================================="
    Write-Output ""
    Write-Output "This script sets up and runs the complete City Pulse system locally with:"
    Write-Output "• Real-time incident simulator"
    Write-Output "• Beautiful web dashboard"
    Write-Output "• WebSocket streaming"
    Write-Output "• Microservices architecture"
    Write-Output ""
    Write-Output "USAGE:"
    Write-Output "  .\start_local.ps1 [OPTIONS]"
    Write-Output ""
    Write-Output "OPTIONS:"
    Write-Output "  -IncidentCount <number>     Number of incidents to generate (default: 10000)"
    Write-Output "  -DatasetFile <filename>     Dataset filename (default: historical_incidents.json)"
    Write-Output "  -UseDocker                  Use Docker containers for microservices"
    Write-Output "  -SkipDatasetGeneration      Skip dataset generation if file exists"
    Write-Output "  -SkipDashboard              Skip dashboard startup (simulator only)"
    Write-Output "  -CleanStart                 Clean all previous data and start fresh"
    Write-Output "  -Help                       Show this help message"
    Write-Output ""
    Write-Output "EXAMPLES:"
    Write-Output "  .\start_local.ps1                           # Standard local setup"
    Write-Output "  .\start_local.ps1 -UseDocker                # Docker microservices"
    Write-Output "  .\start_local.ps1 -CleanStart               # Fresh start with cleanup"
    Write-Output "  .\start_local.ps1 -IncidentCount 5000       # Custom dataset size"
    Write-Output ""
    Write-Output "SERVICES:"
    Write-Output "  📊 Dashboard:     http://localhost:3001"
    Write-Output "  🔌 WebSocket:     ws://localhost:3001"
    Write-Output "  🏃 Simulator:     Background process"
    Write-Output ""
}

if ($Help) {
    Show-Help
    exit 0
}

# Header
Write-Info "🏙️  CITY PULSE - LOCAL MICROSERVICES STARTUP"
Write-Info "============================================="
Write-Output ""

# Check prerequisites
Write-Info "🔍 Checking prerequisites..."

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Success "✅ Python found: $pythonVersion"
} catch {
    Write-Error "❌ Python not found. Please install Python 3.8+ and add it to PATH."
    exit 1
}

# Check Node.js if not using Docker
if (-not $UseDocker) {
    try {
        $nodeVersion = node --version 2>&1
        Write-Success "✅ Node.js found: $nodeVersion"
    } catch {
        Write-Error "❌ Node.js not found. Please install Node.js 14+ or use -UseDocker flag."
        exit 1
    }
}

# Check Docker if using Docker
if ($UseDocker) {
    try {
        $dockerVersion = docker --version 2>&1
        Write-Success "✅ Docker found: $dockerVersion"
        
        $composeVersion = docker-compose --version 2>&1
        Write-Success "✅ Docker Compose found: $composeVersion"
    } catch {
        Write-Error "❌ Docker or Docker Compose not found. Please install Docker Desktop."
        exit 1
    }
}

# Check directory structure
if (-not (Test-Path "local_dev")) {
    Write-Error "❌ Please run this script from the city-pulse root directory."
    exit 1
}

Write-Success "✅ Prerequisites check passed"
Write-Output ""

# Clean start if requested
if ($CleanStart) {
    Write-Info "🧹 Cleaning previous data..."
    
    # Remove databases
    if (Test-Path "local_dev\local_incidents.db") {
        Remove-Item "local_dev\local_incidents.db" -Force
        Write-Info "   Removed incidents database"
    }
    
    if (Test-Path "local_dev\agent_activity.db") {
        Remove-Item "local_dev\agent_activity.db" -Force
        Write-Info "   Removed agent activity database"
    }
    
    # Remove dataset if exists
    if (Test-Path $DatasetFile) {
        Remove-Item $DatasetFile -Force
        Write-Info "   Removed existing dataset"
    }
    
    # Docker cleanup
    if ($UseDocker) {
        Write-Info "   Cleaning Docker containers and volumes..."
        docker-compose down -v 2>$null
        docker system prune -f 2>$null
    }
    
    Write-Success "✅ Cleanup completed"
    Write-Output ""
}

# Step 1: Generate dataset
if (-not $SkipDatasetGeneration -or -not (Test-Path $DatasetFile)) {
    Write-Info "📊 STEP 1: Generating incident dataset..."
    Write-Info "----------------------------------------"
    
    if (Test-Path $DatasetFile -and -not $CleanStart) {
        Write-Warning "⚠️  Dataset file '$DatasetFile' already exists."
        $overwrite = Read-Host "Do you want to overwrite it? (y/N)"
        if ($overwrite -ne "y" -and $overwrite -ne "Y") {
            Write-Info "📁 Using existing dataset: $DatasetFile"
        } else {
            Remove-Item $DatasetFile -Force
        }
    }
    
    if (-not (Test-Path $DatasetFile)) {
        Write-Info "🏗️  Generating $IncidentCount realistic Bengaluru incidents..."
        
        try {
            $generateCmd = "python local_dev/generate_dataset.py --count $IncidentCount --output $DatasetFile"
            Invoke-Expression $generateCmd
            
            if (Test-Path $DatasetFile) {
                $fileSize = (Get-Item $DatasetFile).Length / 1MB
                Write-Success "✅ Dataset generated: $([math]::Round($fileSize, 2)) MB"
            } else {
                Write-Error "❌ Dataset generation failed"
                exit 1
            }
        } catch {
            Write-Error "❌ Dataset generation failed: $_"
            exit 1
        }
    }
} else {
    Write-Info "📊 STEP 1: Using existing dataset..."
    Write-Success "✅ Found dataset: $DatasetFile"
}

Write-Output ""

# Step 2: Setup and start services
if ($UseDocker) {
    Write-Info "🐳 STEP 2: Starting Docker microservices..."
    Write-Info "-------------------------------------------"
    
    # Build and start containers
    Write-Info "🔨 Building Docker images..."
    docker-compose build
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Docker build failed"
        exit 1
    }
    
    Write-Info "🚀 Starting microservices..."
    docker-compose up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Docker startup failed"
        exit 1
    }
    
    Write-Success "✅ Docker services started"
    
    # Wait for services to be ready
    Write-Info "⏳ Waiting for services to be ready..."
    Start-Sleep -Seconds 10
    
    # Check service health
    Write-Info "🔍 Checking service health..."
    
    try {
        $dashboardHealth = Invoke-RestMethod -Uri "http://localhost:3001/health" -TimeoutSec 10
        Write-Success "✅ Dashboard: $($dashboardHealth.status)"
    } catch {
        Write-Warning "⚠️  Dashboard health check failed (may still be starting)"
    }
    
} else {
    Write-Info "🖥️  STEP 2: Starting local services..."
    Write-Info "-------------------------------------"
    
    # Install client dependencies
    if (-not (Test-Path "client\node_modules")) {
        Write-Info "📦 Installing client dependencies..."
        Set-Location "client"
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Error "❌ Client dependency installation failed"
            exit 1
        }
        Set-Location ".."
        Write-Success "✅ Client dependencies installed"
    }
    
    # Start dashboard server in background
    if (-not $SkipDashboard) {
        Write-Info "🌐 Starting dashboard server..."
        
        $dashboardJob = Start-Job -ScriptBlock {
            Set-Location $using:PWD
            Set-Location "client"
            npm start
        }
        
        Write-Success "✅ Dashboard server started (Job ID: $($dashboardJob.Id))"
        
        # Wait for dashboard to start
        Write-Info "⏳ Waiting for dashboard to start..."
        Start-Sleep -Seconds 5
        
        # Check if dashboard is running
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:3001/health" -TimeoutSec 5
            Write-Success "✅ Dashboard health check passed"
        } catch {
            Write-Warning "⚠️  Dashboard may still be starting..."
        }
    }
    
    # Start simulator in background
    Write-Info "🤖 Starting incident simulator..."
    
    $simulatorJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        python local_dev/realtime_simulator.py --dataset $using:DatasetFile
    }
    
    Write-Success "✅ Simulator started (Job ID: $($simulatorJob.Id))"
}

Write-Output ""

# Step 3: Show service information
Write-Info "🎯 STEP 3: Service Information"
Write-Info "------------------------------"

Write-Success "🌐 Dashboard URL:     http://localhost:3001"
Write-Success "🔌 WebSocket URL:     ws://localhost:3001"
Write-Success "📊 Health Check:      http://localhost:3001/health"
Write-Success "📡 API Endpoint:      http://localhost:3001/api/incidents/recent"

if ($UseDocker) {
    Write-Success "🐳 Docker Services:"
    Write-Success "   • city-pulse-dashboard"
    Write-Success "   • city-pulse-simulator"
    Write-Success "   • city-pulse-redis (optional)"
    Write-Success "   • city-pulse-postgres (optional)"
}

Write-Output ""

# Step 4: Usage instructions
Write-Info "📋 STEP 4: What's Running"
Write-Info "-------------------------"

Write-Info "🏃 Real-Time Simulator:"
Write-Info "   • Loading incidents from $DatasetFile"
Write-Info "   • Processing 7 incidents every 20 seconds"
Write-Info "   • Running 4 AI agents (notification, trend, resource, news)"
Write-Info "   • Storing data in SQLite databases"

Write-Info "🌐 Web Dashboard:"
Write-Info "   • Real-time incident feed"
Write-Info "   • Live notifications and alerts"
Write-Info "   • AI agent activity monitoring"
Write-Info "   • Statistics and area distribution"

Write-Info "🔌 WebSocket Streaming:"
Write-Info "   • Live incident updates"
Write-Info "   • Real-time notifications"
Write-Info "   • Statistics broadcasting"

Write-Output ""

# Step 5: Monitoring and control
Write-Info "🎮 STEP 5: Control Commands"
Write-Info "---------------------------"

if ($UseDocker) {
    Write-Info "Docker Commands:"
    Write-Info "   docker-compose logs -f           # View all logs"
    Write-Info "   docker-compose logs dashboard    # Dashboard logs only"
    Write-Info "   docker-compose logs simulator    # Simulator logs only"
    Write-Info "   docker-compose down              # Stop all services"
    Write-Info "   docker-compose restart           # Restart services"
} else {
    Write-Info "Local Commands:"
    Write-Info "   Get-Job                          # View running jobs"
    Write-Info "   Receive-Job -Id <JobId>          # View job output"
    Write-Info "   Stop-Job -Id <JobId>             # Stop a job"
    Write-Info "   Remove-Job -Id <JobId>           # Remove completed job"
}

Write-Output ""

# Final instructions
Write-Success "🎉 CITY PULSE LOCAL ENVIRONMENT IS READY!"
Write-Success "=========================================="
Write-Output ""
Write-Info "🌟 Open your browser and visit: http://localhost:3001"
Write-Info "📱 You'll see real-time incidents, notifications, and AI agent activity"
Write-Info "🔄 The system will continuously process incidents and update the dashboard"
Write-Output ""

if ($UseDocker) {
    Write-Warning "💡 To stop all services: docker-compose down"
} else {
    Write-Warning "💡 To stop services: Stop-Job -Name * (then Remove-Job -Name *)"
}

Write-Warning "💡 Press Ctrl+C in simulator terminal to stop gracefully"
Write-Output ""

# Keep script running if not using Docker
if (-not $UseDocker -and -not $SkipDashboard) {
    Write-Info "🔄 Monitoring services... (Press Ctrl+C to stop)"
    
    try {
        while ($true) {
            Start-Sleep -Seconds 30
            
            # Check job status
            $jobs = Get-Job
            $runningJobs = $jobs | Where-Object { $_.State -eq "Running" }
            
            if ($runningJobs.Count -eq 0) {
                Write-Warning "⚠️  All background jobs have stopped"
                break
            }
            
            Write-Info "✅ Services running: $($runningJobs.Count) jobs active"
        }
    } catch {
        Write-Info "🛑 Stopping services..."
        
        # Stop all jobs
        Get-Job | Stop-Job
        Get-Job | Remove-Job -Force
        
        Write-Success "✅ All services stopped"
    }
}
