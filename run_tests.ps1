# ============================================================
# Customer Success FTE - Test Runner (PowerShell)
# ============================================================
# Usage: .\run_tests.ps1                          # Unit tests only
#        .\run_tests.ps1 -Phase 3                 # Specific phase
#        .\run_tests.ps1 -IncludeIntegration      # Include integration tests (needs Docker)
#        .\run_tests.ps1 -SkipInstall             # Skip pip install
# ============================================================

param(
    [int]$Phase = 0,          # 0 = all phases, 3/4/5 = specific
    [switch]$SkipInstall,
    [switch]$Verbose,
    [switch]$IncludeIntegration
)

$ErrorActionPreference = "Continue"
$ProjectRoot = $PSScriptRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Customer Success FTE - Test Runner" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# -----------------------------------------------------------
# Step 1: Check Python
# -----------------------------------------------------------
Write-Host "[1/4] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  OK: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python not found. Install Python 3.11+" -ForegroundColor Red
    exit 1
}

# -----------------------------------------------------------
# Step 2: Create virtual environment (if not exists)
# -----------------------------------------------------------
$venvPath = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "[2/4] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
    Write-Host "  OK: Virtual environment created at .venv" -ForegroundColor Green
} else {
    Write-Host "[2/4] Virtual environment already exists" -ForegroundColor Green
}

# Activate venv
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    . $activateScript
    Write-Host "  OK: Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Could not activate venv, using system Python" -ForegroundColor Yellow
}

# -----------------------------------------------------------
# Step 3: Install dependencies
# -----------------------------------------------------------
if (-not $SkipInstall) {
    Write-Host "[3/4] Installing test dependencies..." -ForegroundColor Yellow

    # Core test dependencies
    pip install pytest pytest-asyncio pytest-cov httpx --quiet 2>&1 | Out-Null

    # Phase-specific requirements
    $phases = @(3, 4, 5)
    if ($Phase -ne 0) { $phases = @($Phase) }

    foreach ($p in $phases) {
        $reqFile = switch ($p) {
            3 { Join-Path $ProjectRoot "phase-3-multi-channel-ingestion\requirements.txt" }
            4 { Join-Path $ProjectRoot "phase-4-agent-intelligence-logic\requirements.txt" }
            5 { Join-Path $ProjectRoot "phase-5-response-delivery-egress\requirements.txt" }
        }
        if (Test-Path $reqFile) {
            Write-Host "  Installing Phase $p dependencies..." -ForegroundColor Gray
            pip install -r $reqFile --quiet 2>&1 | Out-Null
        }
    }
    Write-Host "  OK: Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "[3/4] Skipping dependency install (--SkipInstall)" -ForegroundColor Gray
}

# -----------------------------------------------------------
# Step 4: Run Tests
# -----------------------------------------------------------
Write-Host "[4/4] Running tests..." -ForegroundColor Yellow
Write-Host ""

$script:totalPassed = 0
$script:totalFailed = 0
$script:totalErrors = 0
$script:results = @()

function Run-PhaseTests {
    param(
        [string]$PhaseName,
        [string]$PhasePath,
        [string]$TestType
    )

    $testDir = Join-Path $PhasePath "tests\$TestType"
    if (-not (Test-Path $testDir)) { return }

    $testFiles = Get-ChildItem -Path $testDir -Filter "test_*.py" -ErrorAction SilentlyContinue
    if ($testFiles.Count -eq 0) { return }

    Write-Host "  --- $PhaseName ($TestType) ---" -ForegroundColor Magenta

    # Change to phase directory so PYTHONPATH="." works for app imports
    Push-Location $PhasePath
    $env:PYTHONPATH = "."

    foreach ($testFile in $testFiles) {
        $testName = $testFile.Name
        Write-Host "    Running $testName... " -NoNewline

        $relTestPath = "tests\$TestType\$testName"
        if ($Verbose) {
            $output = python -m pytest $relTestPath -v --tb=short --no-header 2>&1
        } else {
            $output = python -m pytest $relTestPath --tb=short --no-header -q 2>&1
        }

        $exitCode = $LASTEXITCODE
        $outputText = $output -join "`n"

        # Parse results
        $passedMatch = [regex]::Match($outputText, '(\d+) passed')
        $failedMatch = [regex]::Match($outputText, '(\d+) failed')
        $errorMatch  = [regex]::Match($outputText, '(\d+) error')

        $passed = if ($passedMatch.Success) { [int]$passedMatch.Groups[1].Value } else { 0 }
        $failed = if ($failedMatch.Success) { [int]$failedMatch.Groups[1].Value } else { 0 }
        $errors = if ($errorMatch.Success)  { [int]$errorMatch.Groups[1].Value }  else { 0 }

        if ($exitCode -eq 0) {
            Write-Host "PASSED ($passed tests)" -ForegroundColor Green
        } elseif ($exitCode -eq 5) {
            Write-Host "NO TESTS COLLECTED" -ForegroundColor Yellow
        } else {
            Write-Host "FAILED ($failed failed, $errors errors)" -ForegroundColor Red
            if ($Verbose) {
                Write-Host $outputText -ForegroundColor DarkGray
            }
        }

        $script:totalPassed += $passed
        $script:totalFailed += $failed
        $script:totalErrors += $errors

        $script:results += [PSCustomObject]@{
            Phase    = $PhaseName
            Type     = $TestType
            File     = $testName
            Passed   = $passed
            Failed   = $failed
            Errors   = $errors
            Status   = if ($exitCode -eq 0) { "PASS" } elseif ($exitCode -eq 5) { "SKIP" } else { "FAIL" }
        }
    }

    Pop-Location
}

# Run each phase
[System.Collections.ArrayList]$phasesToRun = @()

if ($Phase -eq 0 -or $Phase -eq 3) {
    $null = $phasesToRun.Add([PSCustomObject]@{Name="Phase 3 (Ingestion)"; PhasePath=(Join-Path $ProjectRoot "phase-3-multi-channel-ingestion")})
}
if ($Phase -eq 0 -or $Phase -eq 4) {
    $null = $phasesToRun.Add([PSCustomObject]@{Name="Phase 4 (Agent)"; PhasePath=(Join-Path $ProjectRoot "phase-4-agent-intelligence-logic")})
}
if ($Phase -eq 0 -or $Phase -eq 5) {
    $null = $phasesToRun.Add([PSCustomObject]@{Name="Phase 5 (Delivery)"; PhasePath=(Join-Path $ProjectRoot "phase-5-response-delivery-egress")})
}

foreach ($phaseItem in $phasesToRun) {
    Write-Host ""
    Write-Host "=== $($phaseItem.Name) ===" -ForegroundColor Cyan
    Run-PhaseTests -PhaseName $phaseItem.Name -PhasePath $phaseItem.PhasePath -TestType "unit"
    if ($IncludeIntegration) {
        Run-PhaseTests -PhaseName $phaseItem.Name -PhasePath $phaseItem.PhasePath -TestType "integration"
    }
}

if (-not $IncludeIntegration) {
    Write-Host ""
    Write-Host "  NOTE: Integration tests skipped (need Docker services)." -ForegroundColor Yellow
    Write-Host "  Run with -IncludeIntegration flag to include them." -ForegroundColor Yellow
}

# -----------------------------------------------------------
# Summary
# -----------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TEST SUMMARY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Count overall
$totalP = ($script:results | Measure-Object -Property Passed -Sum).Sum
$totalF = ($script:results | Measure-Object -Property Failed -Sum).Sum
$totalE = ($script:results | Measure-Object -Property Errors -Sum).Sum
$passFiles = @($script:results | Where-Object { $_.Status -eq "PASS" }).Count
$failFiles = @($script:results | Where-Object { $_.Status -eq "FAIL" }).Count
$skipFiles = @($script:results | Where-Object { $_.Status -eq "SKIP" }).Count

Write-Host ""
Write-Host "  Test Files:  $($script:results.Count) total, $passFiles passed, $failFiles failed, $skipFiles skipped" -ForegroundColor White
Write-Host "  Test Cases:  $totalP passed, $totalF failed, $totalE errors" -ForegroundColor White
Write-Host ""

if ($totalF -eq 0 -and $totalE -eq 0) {
    Write-Host "  RESULT: ALL TESTS PASSED" -ForegroundColor Green
} else {
    Write-Host "  RESULT: SOME TESTS FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Failed files:" -ForegroundColor Red
    $script:results | Where-Object { $_.Status -eq "FAIL" } | ForEach-Object {
        Write-Host "    - $($_.Phase) / $($_.Type) / $($_.File)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

# Return exit code
if ($totalF -gt 0 -or $totalE -gt 0) { exit 1 } else { exit 0 }
