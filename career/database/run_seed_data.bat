@echo off
REM ============================================
REM IDINO Career - Seed Data Execution Script
REM Date: 2026-01-26
REM ============================================

echo ==========================================
echo IDINO Career - Seed Data Execution
echo ==========================================

REM PostgreSQL connection settings
SET PGHOST=localhost
SET PGPORT=5432
SET PGDATABASE=postgres
SET PGUSER=postgres

echo.
echo Please enter PostgreSQL password:
SET /P PGPASSWORD=

echo.
echo [1/2] Running 18_complete_seed_data_fix.sql...
psql -f "18_complete_seed_data_fix.sql"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to run 18_complete_seed_data_fix.sql
    pause
    exit /b 1
)

echo.
echo [2/2] Running 19_additional_opportunities.sql...
psql -f "19_additional_opportunities.sql"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to run 19_additional_opportunities.sql
    pause
    exit /b 1
)

echo.
echo ==========================================
echo All seed data scripts completed successfully!
echo ==========================================
pause
