#!/bin/bash
echo "============================================"
echo "  DocUtil Full QA Tests"
echo "============================================"

echo "Running qa-tester agent..."
claude --agent qa-tester "Run full QA test suite. \
Test all layers: API scenarios, edge cases, AI quality, cross-module impact. \
Generate report to tests/qa_reports/$(date +%Y%m%d_%H%M)_report.md \
Print the overall score and any critical issues to console."
