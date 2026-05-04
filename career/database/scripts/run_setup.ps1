# IDINO Career Database Setup Script (PowerShell)
# Run with: .\run_setup.ps1

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "IDINO Career Database Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$env:PGHOST = "localhost"
$env:PGPORT = "5432"
$env:PGUSER = "postgres"
$env:PGDATABASE = "postgres"
$env:PGPASSWORD = "2012"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

try {
    # Step 1: Drop and recreate schema
    Write-Host "[1/3] Dropping and recreating schema..." -ForegroundColor Yellow
    psql -c "DROP SCHEMA IF EXISTS idino_career CASCADE; CREATE SCHEMA idino_career;"
    if ($LASTEXITCODE -ne 0) { throw "Failed to create schema" }
    Write-Host "Done!" -ForegroundColor Green
    Write-Host ""

    # Step 2: Run DDL
    Write-Host "[2/3] Running DDL script..." -ForegroundColor Yellow
    Push-Location $ScriptDir
    psql -f "00_full_ddl.sql"
    if ($LASTEXITCODE -ne 0) { throw "Failed to run DDL" }
    Write-Host "Done!" -ForegroundColor Green
    Write-Host ""

    # Step 3: Generate and load test data
    Write-Host "[3/3] Generating and loading test data..." -ForegroundColor Yellow
    python generate_test_data.py --students 200 --output 04_generated_test_data.sql
    if ($LASTEXITCODE -ne 0) { throw "Failed to generate test data" }

    psql -f "04_generated_test_data.sql"
    if ($LASTEXITCODE -ne 0) { throw "Failed to load test data" }
    Write-Host "Done!" -ForegroundColor Green
    Pop-Location
    Write-Host ""

    Write-Host "============================================" -ForegroundColor Green
    Write-Host "Database setup complete!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Schema: idino_career" -ForegroundColor White
    Write-Host "Connection: jdbc:postgresql://localhost:5432/postgres" -ForegroundColor White
    Write-Host ""

    # Verify data
    Write-Host "Verifying data counts..." -ForegroundColor Yellow
    $tables = @(
        "tb_student",
        "tb_course",
        "tb_enrollment",
        "tb_grade",
        "tb_competency",
        "tb_skill",
        "tb_student_competency",
        "tb_student_skill",
        "tb_opportunity",
        "tb_coaching_goal",
        "tb_badge",
        "tb_advisor"
    )

    foreach ($table in $tables) {
        $count = psql -t -c "SELECT COUNT(*) FROM idino_career.$table;"
        Write-Host "  $table : $($count.Trim())" -ForegroundColor White
    }
}
catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    Pop-Location -ErrorAction SilentlyContinue
    exit 1
}
