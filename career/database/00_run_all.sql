-- ============================================
-- IDINO Career Database - Master Run Script
-- 紐⑤뱺 ?ㅽ겕由쏀듃瑜??쒖꽌?濡??ㅽ뻾
-- ============================================
--
-- ?ㅽ뻾 諛⑸쾿:
-- psql -h localhost -p 5432 -U postgres -d postgres -f 00_run_all.sql
-- ?먮뒗 媛??뚯씪???쒖꽌?濡??ㅽ뻾
--
-- ?곌껐 ?뺣낫:
-- Host: localhost
-- Port: 5432
-- Database: postgres
-- Schema: idino_career
-- User: postgres
-- Password: 2012
-- ============================================

-- ?ㅽ겕由쏀듃 ?ㅽ뻾 ?쒖꽌:
-- 1. 01_schema_create.sql    - ?ㅽ궎留?諛?湲곕낯 ?뚯씠釉??앹꽦
-- 2. 02_techspec_tables.sql  - TechSpec 愿???뚯씠釉??앹꽦
-- 3. 03_seed_data.sql        - ?숆탳, ?숆낵, 援먯닔, 怨쇰ぉ, ??웾 ??留덉뒪???곗씠??-- 4. 04_seed_students.sql    - ?숈깮 110紐??곗씠??-- 5. 05_seed_enrollments.sql - ?섍컯?좎껌, ?깆쟻, ?쒕룞, 議몄뾽???곗씠??-- 6. 10_p1_p2_extensions.sql - P1/P2 ?뺤옣 ?뚯씠釉?(Phase 7-13)
-- 7. 06_seed_p1_skills.sql   - P1 ?ㅽ궗 洹몃옒???곗씠??-- 8. 07_seed_p1_coaching.sql - P1 AI 肄붿묶 ?곗씠??-- 9. 08_seed_p1_opportunities.sql - P1 湲고쉶 留덉폆?뚮젅?댁뒪 ?곗씠??-- 10. 09_seed_p1_risk.sql    - P1 由ъ뒪???뚮┝ ?곗씠??-- 11. 10_seed_p2_badges.sql  - P2 諭껋?/?⑥뒪?ы듃 ?곗씠??-- 12. 11_seed_p2_simulation.sql - P2 ?쒕??덉씠???곗씠??-- 13. 12_seed_p2_advisor.sql - P2 ?대뱶諛붿씠? ?곗씠??
\echo '=========================================='
\echo 'IDINO Career Database Setup Starting...'
\echo '=========================================='

-- 1. Schema and Basic Tables
\echo ''
\echo '[1/13] Creating schema and basic tables...'
\i 01_schema_create.sql
\echo '[1/13] Done!'

-- 2. TechSpec Tables
\echo ''
\echo '[2/13] Creating TechSpec related tables...'
\i 02_techspec_tables.sql
\echo '[2/13] Done!'

-- 3. Master Data
\echo ''
\echo '[3/13] Inserting master data (university, departments, courses, professors)...'
\i 03_seed_data.sql
\echo '[3/13] Done!'

-- 4. Student Data
\echo ''
\echo '[4/13] Inserting student data (110 students)...'
\i 04_seed_students.sql
\echo '[4/13] Done!'

-- 5. Enrollment and Activity Data
\echo ''
\echo '[5/13] Inserting enrollment, grade, and activity data...'
\i 05_seed_enrollments.sql
\echo '[5/13] Done!'

-- 6. P1/P2 Extension Tables
\echo ''
\echo '[6/13] Creating P1/P2 extension tables (Phase 7-13)...'
\i 10_p1_p2_extensions.sql
\echo '[6/13] Done!'

-- 7. P1 Skills Data
\echo ''
\echo '[7/13] Inserting P1 skill graph data...'
\i 06_seed_p1_skills.sql
\echo '[7/13] Done!'

-- 8. P1 Coaching Data
\echo ''
\echo '[8/13] Inserting P1 AI coaching data...'
\i 07_seed_p1_coaching.sql
\echo '[8/13] Done!'

-- 9. P1 Opportunities Data
\echo ''
\echo '[9/13] Inserting P1 opportunity marketplace data...'
\i 08_seed_p1_opportunities.sql
\echo '[9/13] Done!'

-- 10. P1 Risk Data
\echo ''
\echo '[10/13] Inserting P1 risk alert data...'
\i 09_seed_p1_risk.sql
\echo '[10/13] Done!'

-- 11. P2 Badges Data
\echo ''
\echo '[11/13] Inserting P2 badge/passport data...'
\i 10_seed_p2_badges.sql
\echo '[11/13] Done!'

-- 12. P2 Simulation Data
\echo ''
\echo '[12/13] Inserting P2 simulation data...'
\i 11_seed_p2_simulation.sql
\echo '[12/13] Done!'

-- 13. P2 Advisor Data
\echo ''
\echo '[13/13] Inserting P2 advisor data...'
\i 12_seed_p2_advisor.sql
\echo '[13/13] Done!'

\echo ''
\echo '=========================================='
\echo 'IDINO Career Database Setup Complete!'
\echo '=========================================='
\echo ''
\echo 'Summary:'
\echo '- Schema: idino_career'
\echo '- University: 1'
\echo '- Colleges: 8'
\echo '- Departments: 30'
\echo '- Professors: 25'
\echo '- Courses: 55'
\echo '- Students: 110'
\echo '- Competencies: 6'
\echo '- Skills: 15'
\echo '- Roles: 12'
\echo '- Programs: 8'
\echo ''
\echo 'P1/P2 Extensions:'
\echo '- Role-Skill Maps: ~70'
\echo '- Student Skills: ~600'
\echo '- Skill Gap Analysis: ~80'
\echo '- Coaching Goals: ~220'
\echo '- Coaching Plans: ~120'
\echo '- Opportunities: ~50'
\echo '- Risk Alerts: ~80'
\echo '- Badges: 25'
\echo '- Student Badges: ~300'
\echo '- Skill Passports: ~110'
\echo '- Simulation Scenarios: ~70'
\echo '- Advisor Assignments: ~110'
\echo '- Advisor Notes: ~70'
\echo ''
\echo 'Connection: jdbc:postgresql://localhost:5432/postgres'
\echo 'Schema: idino_career'
\echo ''
