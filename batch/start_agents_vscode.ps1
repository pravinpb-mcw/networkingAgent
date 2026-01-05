# PowerShell script to run agents on CURRENT/MAIN screen (for demo recording)
# Usage: .\start_agents_vscode.ps1

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "   STARTING AGENTS ON MAIN SCREEN" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Load .env file
$envFile = "$PSScriptRoot\..\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.+)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Variable -Name $key -Value $value -Scope Script
        }
    }
}

$PYTHON_EXE = "$BASE_PATH\.wenv\Scripts\python.exe"
$PROJECT_ROOT = "$BASE_PATH\networkingAgent"

# Function to start process on current monitor
function Start-OnCurrentMonitor {
    param($Title, $Command)
    
    # Start process and immediately move to foreground (current monitor)
    $process = Start-Process cmd -ArgumentList "/k `"title $Title && cd /d `"$PROJECT_ROOT`" && $Command`"" -PassThru -WindowStyle Normal
    
    # Bring window to front (forces it to current screen)
    Start-Sleep -Milliseconds 500
    Add-Type -TypeDefinition @"
        using System;
        using System.Runtime.InteropServices;
        public class WinAPI {
            [DllImport("user32.dll")]
            public static extern bool SetForegroundWindow(IntPtr hWnd);
            [DllImport("user32.dll")]
            public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
        }
"@
    [WinAPI]::ShowWindow($process.MainWindowHandle, 9) # SW_RESTORE
    [WinAPI]::SetForegroundWindow($process.MainWindowHandle)
}

Write-Host "[1/3] Starting Agent 1 on main screen..." -ForegroundColor Green
Start-OnCurrentMonitor "Agent 1 - Risk Calculation" "`"$PYTHON_EXE`" agents\agent_1_risk_calculation.py --continuous 10"

Start-Sleep -Seconds 3

Write-Host "[2/3] Starting Agent 2 on main screen..." -ForegroundColor Green
Start-OnCurrentMonitor "Agent 2 - Nearest AP" "`"$PYTHON_EXE`" agents\agent_2_nearest_ap.py --continuous 10"

Start-Sleep -Seconds 3

Write-Host "[3/3] Starting Agent 3 on main screen..." -ForegroundColor Green
Start-OnCurrentMonitor "Agent 3 - Failover" "`"$PYTHON_EXE`" agents\agent_3_failover_suggestion.py --continuous 10"

Write-Host ""
Write-Host "✓ All agents started on MAIN screen!" -ForegroundColor Green
Write-Host "Windows are now visible on your current monitor for recording." -ForegroundColor Yellow
