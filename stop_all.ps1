#!/usr/bin/env pwsh
# Stop All City Pulse Services
# Cleans up local services and frees ports for Docker

function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

Write-Info "STOPPING ALL CITY PULSE SERVICES"
Write-Info "================================"
Write-Output ""

# Stop PowerShell background jobs
Write-Info "1. Stopping PowerShell jobs..."
$jobs = Get-Job
if ($jobs.Count -gt 0) {
    Write-Info "Found $($jobs.Count) background jobs"
    foreach ($job in $jobs) {
        Write-Info "   Stopping Job $($job.Id): $($job.Name)"
        Stop-Job $job.Id
    }
    Get-Job | Remove-Job -Force
    Write-Success "✅ All PowerShell jobs stopped"
} else {
    Write-Info "No PowerShell jobs running"
}

Write-Output ""

# Check and kill processes using port 3001
Write-Info "2. Checking port 3001..."
try {
    $portProcesses = netstat -ano | findstr :3001
    if ($portProcesses) {
        Write-Warning "Processes using port 3001:"
        $portProcesses | ForEach-Object {
            if ($_ -match '\s+(\d+)$') {
                $pid = $matches[1]
                try {
                    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                    if ($process) {
                        Write-Warning "   PID $pid - $($process.ProcessName)"
                        Write-Info "   Killing process $pid..."
                        Stop-Process -Id $pid -Force
                        Write-Success "   ✅ Killed PID $pid"
                    }
                } catch {
                    Write-Warning "   Could not kill PID $pid"
                }
            }
        }
    } else {
        Write-Success "✅ Port 3001 is free"
    }
} catch {
    Write-Info "Could not check port 3001 (may already be free)"
}

Write-Output ""

# Stop Docker containers
Write-Info "3. Stopping Docker containers..."
try {
    $containers = docker ps -q --filter "name=city-pulse"
    if ($containers) {
        Write-Info "Stopping City Pulse Docker containers..."
        docker stop $containers
        Write-Success "✅ Docker containers stopped"
    } else {
        Write-Info "No City Pulse Docker containers running"
    }
} catch {
    Write-Info "Docker not available or no containers running"
}

Write-Output ""

# Verify ports are free
Write-Info "4. Verifying ports are free..."
$port3001 = netstat -ano | findstr :3001
$port3002 = netstat -ano | findstr :3002

if (-not $port3001) {
    Write-Success "✅ Port 3001 is free"
} else {
    Write-Warning "⚠️  Port 3001 still in use"
}

if (-not $port3002) {
    Write-Success "✅ Port 3002 is free"
} else {
    Write-Warning "⚠️  Port 3002 still in use"
}

Write-Output ""
Write-Success "🎉 CLEANUP COMPLETE!"
Write-Success "==================="
Write-Output ""

Write-Info "Now you can run:"
Write-Info "• Local services:  .\start_simple.ps1"
Write-Info "• Docker services: docker-compose up --build"
Write-Info "• Docker (alt port): http://localhost:3002"
Write-Output ""
