Set up the .claude/ directory structure for this project.

1. Create directories:
   mkdir -p .claude/rules        (or mkdir .claude\rules on Windows)
   mkdir -p .claude/agents       (or mkdir .claude\agents on Windows)
   mkdir -p tests/qa_reports     (or mkdir tests\qa_reports on Windows)

2. Copy rule files into .claude/rules/:
   - architecture.md (I'll provide content)
   - anti-patterns.md (I'll provide content)
   - domain-model.md (I'll provide content)
   - testing.md (I'll provide content)
   - agent-collaboration.md (I'll provide content)

3. Copy agent file into .claude/agents/:
   - qa-tester.md (I'll provide content)

4. Create convenience scripts:
   - scripts/qa.sh + scripts/qa.bat (full QA test, Linux + Windows)
   - scripts/qa_quick.sh + scripts/qa_quick.bat (quick QA test, Linux + Windows)
   - chmod +x *.sh (Linux only)

5. Update .gitignore:
   - Add: .claude/settings.local.json
   - Add: tests/qa_reports/*.md

6. Add .gitkeep to tests/qa_reports/

7. Replace root CLAUDE.md with lean version (~100 lines).
   Current CLAUDE.md content should be redistributed into .claude/rules/ files.

These files in .claude/rules/ are automatically loaded by Claude Code
with the same priority as CLAUDE.md. No @import needed.

I'll paste the content for each file one at a time. Start by creating the directories.
