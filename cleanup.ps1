#!/usr/bin/env pwsh
# City Pulse Project Cleanup Script
# Removes unnecessary files while keeping essential components for cloud deployment and local testing

param(
    [switch]$DryRun,
    [switch]$Help
)

function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

if ($Help) {
    Write-Info "City Pulse Cleanup Script"
    Write-Info "========================"
    Write-Output ""
    Write-Output "Removes unnecessary files while keeping essential components for:"
    Write-Output "• Cloud deployment (Google Cloud)"
    Write-Output "• Local testing with Docker"
    Write-Output "• Local development environment"
    Write-Output ""
    Write-Output "USAGE:"
    Write-Output "  .\cleanup.ps1 [-DryRun] [-Help]"
    Write-Output ""
    Write-Output "OPTIONS:"
    Write-Output "  -DryRun    Show what would be deleted without actually deleting"
    Write-Output "  -Help      Show this help message"
    Write-Output ""
    exit 0
}

Write-Info "CITY PULSE PROJECT CLEANUP"
Write-Info "=========================="
Write-Output ""

if ($DryRun) {
    Write-Warning "DRY RUN MODE - No files will be deleted"
    Write-Output ""
}

# Define files and directories to remove
$itemsToRemove = @(
    # Duplicate/Redundant Files
    "data_gen",
    "local_dev\run_local.py",
    "local_dev\simple_test.py", 
    "local_dev\test_local.py",
    "local_dev\requirements_local.txt",
    
    # Documentation Duplicates
    "README_REALTIME.md",
    "client\README.md",
    "local_dev\README.md",
    
    # Sample/Schema Files
    "sample_data _schema.json",
    "infra\embeddings_schema.json",
    
    # Generated/Runtime Files (can be recreated)
    "historical_incidents.json",
    "local_incidents.db",
    
    # Redundant Scripts
    "deploy.sh",
    "quick_start.ps1",
    
    # Unused Components
    "embed",
    "memgraph_job"
)

$totalSize = 0
$deletedCount = 0

Write-Info "Files and directories to remove:"
Write-Info "--------------------------------"

foreach ($item in $itemsToRemove) {
    if (Test-Path $item) {
        if (Test-Path $item -PathType Container) {
            # Directory
            $size = (Get-ChildItem $item -Recurse -File | Measure-Object -Property Length -Sum).Sum
            $sizeStr = if ($size -gt 1MB) { "$([math]::Round($size/1MB, 2)) MB" } else { "$([math]::Round($size/1KB, 2)) KB" }
            Write-Warning "📁 $item/ ($sizeStr)"
        } else {
            # File
            $size = (Get-Item $item).Length
            $sizeStr = if ($size -gt 1MB) { "$([math]::Round($size/1MB, 2)) MB" } else { "$([math]::Round($size/1KB, 2)) KB" }
            Write-Warning "📄 $item ($sizeStr)"
        }
        $totalSize += $size
        $deletedCount++
    } else {
        Write-Info "⚪ $item (not found)"
    }
}

Write-Output ""
Write-Info "Summary:"
Write-Info "--------"
Write-Info "Items to remove: $deletedCount"
Write-Info "Total size: $([math]::Round($totalSize/1MB, 2)) MB"
Write-Output ""

if ($deletedCount -eq 0) {
    Write-Success "✅ Project is already clean!"
    exit 0
}

if ($DryRun) {
    Write-Info "This was a dry run. Use '.\cleanup.ps1' to actually delete files."
    exit 0
}

# Confirm deletion
Write-Warning "⚠️  This will permanently delete $deletedCount items ($([math]::Round($totalSize/1MB, 2)) MB)"
$confirm = Read-Host "Continue? (y/N)"

if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Info "Cleanup cancelled."
    exit 0
}

Write-Output ""
Write-Info "🗑️  Cleaning up project..."

foreach ($item in $itemsToRemove) {
    if (Test-Path $item) {
        try {
            if (Test-Path $item -PathType Container) {
                Remove-Item $item -Recurse -Force
                Write-Success "✅ Removed directory: $item/"
            } else {
                Remove-Item $item -Force
                Write-Success "✅ Removed file: $item"
            }
        } catch {
            Write-Error "❌ Failed to remove: $item"
            Write-Error "   Error: $($_.Exception.Message)"
        }
    }
}

Write-Output ""
Write-Success "🎉 CLEANUP COMPLETE!"
Write-Success "==================="
Write-Output ""

Write-Info "✅ KEPT (Essential for deployment):"
Write-Info "• agents/ - AI agents for cloud"
Write-Info "• streaming/ - Real-time processor"
Write-Info "• api/ - API service"
Write-Info "• infra/ - Terraform infrastructure"
Write-Info "• client/ - Dashboard UI"
Write-Info "• local_dev/ - Local development tools"
Write-Info "• Docker files and deployment scripts"
Write-Output ""

Write-Info "🚀 Your project is now optimized for:"
Write-Info "• Cloud deployment (Google Cloud)"
Write-Info "• Local testing with Docker"
Write-Info "• Local development environment"
Write-Output ""

Write-Warning "💡 To regenerate removed files:"
Write-Warning "• Dataset: python local_dev/generate_dataset.py"
Write-Warning "• Database: Will be created automatically by simulator"
