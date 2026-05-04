@echo off
chcp 65001 > nul
echo ============================================
echo IDINO Career Database Setup
echo ============================================
echo.

set PGHOST=localhost
set PGPORT=5432
set PGUSER=postgres
set PGDATABASE=postgres
set PGPASSWORD=2012

echo [1/3] Dropping and recreating schema...
psql -c "DROP SCHEMA IF EXISTS idino_career CASCADE; CREATE SCHEMA idino_career;"
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to create schema
    pause
    exit /b 1
)
echo Done!
echo.

echo [2/3] Running DDL script...
psql -f 00_full_ddl.sql
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to run DDL
    pause
    exit /b 1
)
echo Done!
echo.

echo [3/3] Generating and loading test data...
python generate_test_data.py --students 200 --output 04_generated_test_data.sql
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to generate test data
    pause
    exit /b 1
)

psql -f 04_generated_test_data.sql
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to load test data
    pause
    exit /b 1
)
echo Done!
echo.

echo ============================================
echo Database setup complete!
echo ============================================
echo.
echo Schema: idino_career
echo Connection: jdbc:postgresql://localhost:5432/postgres
echo.
pause
