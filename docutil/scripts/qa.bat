@echo off
echo ============================================
echo   DocUtil Full QA Tests
echo ============================================

for /f "tokens=1-4 delims=/ " %%a in ('date /t') do set TODAY=%%a%%b%%c
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set NOW=%%a%%b

echo Running qa-tester agent...
claude --agent qa-tester "Run full QA test suite. Test all layers: API scenarios, edge cases, AI quality, cross-module impact. Generate report to tests/qa_reports/%TODAY%_%NOW%_report.md. Print the overall score and any critical issues to console."
