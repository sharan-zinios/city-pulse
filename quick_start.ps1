#!/usr/bin/env pwsh
# Quick Start Script for City Pulse Local Development
# This script generates the dataset and runs the local simulator

param(
    [int]$IncidentCount = 10000,
    [string]$DatasetFile = "historical_incidents.json",
    [int]$BatchSize = 7,
    [int]$BatchInterval = 20,
    [switch]$SkipDatasetGeneration,
    [switch]$Help
)

# Color functions for better output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success { Write-ColorOutput Green $args }
function Write-Info { Write-ColorOutput Cyan $args }
function Write-Warning { Write-ColorOutput Yellow $args }
function Write-Error { Write-ColorOutput Red $args }

# Help function
function Show-Help {
    Write-Info "🚀 City Pulse Local Development Quick Start"
    Write-Info "=========================================="
    Write-Output ""
    Write-Output "This script helps you quickly set up and run the City Pulse system locally."
    Write-Output ""
    Write-Output "USAGE:"
    Write-Output "  .\quick_start.ps1 [OPTIONS]"
    Write-Output ""
    Write-Output "OPTIONS:"
    Write-Output "  -IncidentCount <number>     Number of incidents to generate (default: 10000)"
    Write-Output "  -DatasetFile <filename>     Dataset filename (default: historical_incidents.json)"
    Write-Output "  -BatchSize <number>         Incidents per batch (default: 7)"
    Write-Output "  -BatchInterval <seconds>    Seconds between batches (default: 20)"
    Write-Output "  -SkipDatasetGeneration      Skip dataset generation if file exists"
    Write-Output "  -Help                       Show this help message"
    Write-Output ""
    Write-Output "EXAMPLES:"
    Write-Output "  .\quick_start.ps1                                    # Generate 10k incidents and run simulator"
    Write-Output "  .\quick_start.ps1 -IncidentCount 5000               # Generate 5k incidents"
    Write-Output "  .\quick_start.ps1 -SkipDatasetGeneration            # Skip generation, use existing dataset"
    Write-Output "  .\quick_start.ps1 -BatchSize 10 -BatchInterval 15   # Custom batch settings"
    Write-Output ""
}

# Show help if requested
if ($Help) {
    Show-Help
    exit 0
}

# Header
Write-Info "🏙️  CITY PULSE - LOCAL DEVELOPMENT QUICK START"
Write-Info "=============================================="
Write-Output ""

# Check if Python is installed
Write-Info "🔍 Checking prerequisites..."
try {
    $pythonVersion = python --version 2>&1
    Write-Success "✅ Python found: $pythonVersion"
} catch {
    Write-Error "❌ Python not found. Please install Python 3.8+ and add it to PATH."
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "local_dev")) {
    Write-Error "❌ Please run this script from the city-pulse root directory."
    Write-Error "   Expected to find 'local_dev' directory."
    exit 1
}

Write-Success "✅ Directory structure looks good"
Write-Output ""

# Step 1: Generate dataset (if needed)
if (-not $SkipDatasetGeneration -or -not (Test-Path $DatasetFile)) {
    Write-Info "📊 STEP 1: Generating incident dataset..."
    Write-Info "----------------------------------------"
    
    if (Test-Path $DatasetFile) {
        Write-Warning "⚠️  Dataset file '$DatasetFile' already exists."
        $overwrite = Read-Host "Do you want to overwrite it? (y/N)"
        if ($overwrite -ne "y" -and $overwrite -ne "Y") {
            Write-Info "📁 Using existing dataset: $DatasetFile"
            Write-Output ""
        } else {
            Write-Info "🗑️  Removing existing dataset..."
            Remove-Item $DatasetFile -Force
        }
    }
    
    if (-not (Test-Path $DatasetFile)) {
        Write-Info "🏗️  Generating $IncidentCount realistic Bengaluru incidents..."
        Write-Info "   This may take a few minutes..."
        
        try {
            $generateCmd = "python local_dev/generate_dataset.py --count $IncidentCount --output $DatasetFile"
            Write-Info "   Running: $generateCmd"
            Invoke-Expression $generateCmd
            
            if (Test-Path $DatasetFile) {
                $fileSize = (Get-Item $DatasetFile).Length / 1MB
                Write-Success "✅ Dataset generated successfully!"
                Write-Success "   File: $DatasetFile"
                Write-Success "   Size: $([math]::Round($fileSize, 2)) MB"
            } else {
                Write-Error "❌ Dataset generation failed - file not created"
                exit 1
            }
        } catch {
            Write-Error "❌ Dataset generation failed: $_"
            exit 1
        }
    }
} else {
    Write-Info "📊 STEP 1: Using existing dataset..."
    Write-Info "-----------------------------------"
    
    if (Test-Path $DatasetFile) {
        $fileSize = (Get-Item $DatasetFile).Length / 1MB
        Write-Success "✅ Found existing dataset: $DatasetFile"
        Write-Success "   Size: $([math]::Round($fileSize, 2)) MB"
    } else {
        Write-Error "❌ Dataset file '$DatasetFile' not found."
        Write-Error "   Run without -SkipDatasetGeneration to generate it."
        exit 1
    }
}

Write-Output ""

# Step 2: Install dependencies (if needed)
Write-Info "📦 STEP 2: Checking Python dependencies..."
Write-Info "-----------------------------------------"

$requiredPackages = @("sqlite3")  # sqlite3 is built-in, but we can check others if needed

Write-Success "✅ All required packages are available (using built-in libraries)"
Write-Output ""

# Step 3: Run the local simulator
Write-Info "🚀 STEP 3: Starting local real-time simulator..."
Write-Info "-----------------------------------------------"

Write-Info "📋 Simulator Configuration:"
Write-Info "   Dataset: $DatasetFile"
Write-Info "   Batch Size: $BatchSize incidents per batch"
Write-Info "   Batch Interval: $BatchInterval seconds"
Write-Info "   AI Agents: Mock agents enabled"
Write-Output ""

Write-Info "🎯 The simulator will:"
Write-Info "   • Load incidents from your dataset"
Write-Info "   • Feed them in batches to simulate real-time streaming"
Write-Info "   • Run mock AI agents for processing"
Write-Info "   • Show real-time statistics"
Write-Info "   • Store results in local SQLite database"
Write-Output ""

Write-Warning "💡 Press Ctrl+C to stop the simulator gracefully"
Write-Output ""

try {
    $simulatorCmd = "python local_dev/realtime_simulator.py --dataset $DatasetFile --batch-size $BatchSize --interval $BatchInterval"
    Write-Info "🏃 Running: $simulatorCmd"
    Write-Output ""
    
    # Run the simulator
    Invoke-Expression $simulatorCmd
    
} catch {
    Write-Error "❌ Simulator failed to start: $_"
    exit 1
}

Write-Output ""
Write-Success "🎉 Local development session completed!"
Write-Info "💡 Next steps:"
Write-Info "   • Review the generated SQLite databases in local_dev/"
Write-Info "   • Modify AI agent logic in local_dev/realtime_simulator.py"
Write-Info "   • Test different batch sizes and intervals"
Write-Info "   • Deploy to Google Cloud using deploy_realtime.ps1"
