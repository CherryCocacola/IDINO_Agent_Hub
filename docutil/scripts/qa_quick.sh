#!/bin/bash
echo "============================================"
echo "  DocUtil Quick QA"
echo "============================================"

echo "Running quick qa-tester agent..."
claude --agent qa-tester "Run quick QA: API scenario tests and AI quality check only. \
Skip edge cases and cross-module impact. \
Print score and critical issues to console."
