-- =====================================================
-- 44_fix_skills_risks_simulation.sql
-- 스킬그래프, 위험알림, 시뮬레이션 데이터 수정
-- =====================================================
-- 근본 원인:
-- 1. tb_role_skill_map에 학과별 스킬(SKM~SKG) 매핑 없음 → 빈 그래프
-- 2. tb_risk_alert에 시드 데이터 부족 → 모두 0
-- 3. tb_simulation_scenario의 JSONB가 서비스 기대 형식과 불일치
-- =====================================================

SET search_path TO idino_career, public;

BEGIN;

-- =====================================================
-- Part 1: 역할-스킬 매핑 추가 (tb_role_skill_map)
-- 기존 SK01-SK15 매핑은 유지, 새 스킬코드만 추가
-- =====================================================

INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt)
VALUES
-- ─── 의료: ROLE101(의사) → SKM001-007 ───
('ROLE101', 'SKM001', 5, 'critical',    92.0, 'stable',  'FIX_44', NOW()),
('ROLE101', 'SKM002', 5, 'critical',    95.0, 'stable',  'FIX_44', NOW()),
('ROLE101', 'SKM003', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),
('ROLE101', 'SKM004', 5, 'critical',    96.0, 'stable',  'FIX_44', NOW()),
('ROLE101', 'SKM005', 4, 'important',   80.0, 'growing', 'FIX_44', NOW()),
('ROLE101', 'SKM006', 4, 'important',   85.0, 'stable',  'FIX_44', NOW()),
('ROLE101', 'SKM007', 3, 'nice_to_have',75.0, 'growing', 'FIX_44', NOW()),

-- ─── 간호: ROLE102(간호사) → SKN001-007 ───
('ROLE102', 'SKN001', 5, 'critical',    94.0, 'stable',  'FIX_44', NOW()),
('ROLE102', 'SKN002', 5, 'critical',    92.0, 'stable',  'FIX_44', NOW()),
('ROLE102', 'SKN003', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE102', 'SKN004', 4, 'important',   88.0, 'stable',  'FIX_44', NOW()),
('ROLE102', 'SKN005', 3, 'important',   82.0, 'stable',  'FIX_44', NOW()),
('ROLE102', 'SKN006', 3, 'important',   78.0, 'stable',  'FIX_44', NOW()),
('ROLE102', 'SKN007', 4, 'critical',    90.0, 'growing', 'FIX_44', NOW()),

-- ─── 물리치료/보건: ROLE103-104,106 → SKH001-007 ───
('ROLE103', 'SKH001', 5, 'critical',    92.0, 'stable',  'FIX_44', NOW()),
('ROLE103', 'SKH002', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE103', 'SKH003', 4, 'important',   85.0, 'stable',  'FIX_44', NOW()),
('ROLE103', 'SKH004', 5, 'critical',    95.0, 'growing', 'FIX_44', NOW()),
('ROLE103', 'SKH005', 3, 'important',   78.0, 'stable',  'FIX_44', NOW()),
('ROLE103', 'SKH006', 4, 'important',   82.0, 'growing', 'FIX_44', NOW()),
('ROLE103', 'SKH007', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),

('ROLE104', 'SKH001', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE104', 'SKH002', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),
('ROLE104', 'SKH003', 5, 'critical',    94.0, 'stable',  'FIX_44', NOW()),
('ROLE104', 'SKH004', 3, 'nice_to_have',72.0, 'stable',  'FIX_44', NOW()),
('ROLE104', 'SKH005', 3, 'important',   78.0, 'stable',  'FIX_44', NOW()),
('ROLE104', 'SKH006', 3, 'important',   76.0, 'stable',  'FIX_44', NOW()),
('ROLE104', 'SKH007', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),

('ROLE106', 'SKH001', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),
('ROLE106', 'SKH002', 3, 'important',   82.0, 'stable',  'FIX_44', NOW()),
('ROLE106', 'SKH003', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE106', 'SKH004', 3, 'nice_to_have',70.0, 'stable',  'FIX_44', NOW()),
('ROLE106', 'SKH005', 3, 'important',   78.0, 'stable',  'FIX_44', NOW()),
('ROLE106', 'SKH006', 4, 'critical',    86.0, 'growing', 'FIX_44', NOW()),
('ROLE106', 'SKH007', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),

-- ─── 약사: ROLE105 → SKP001-007 ───
('ROLE105', 'SKP001', 5, 'critical',    96.0, 'stable',  'FIX_44', NOW()),
('ROLE105', 'SKP002', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE105', 'SKP003', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),
('ROLE105', 'SKP004', 4, 'important',   85.0, 'stable',  'FIX_44', NOW()),
('ROLE105', 'SKP005', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE105', 'SKP006', 4, 'important',   82.0, 'stable',  'FIX_44', NOW()),
('ROLE105', 'SKP007', 5, 'critical',    94.0, 'growing', 'FIX_44', NOW()),

-- ─── IT직: ROLE01-08 → SKE001-007 ───
('ROLE01', 'SKE001', 5, 'critical',    95.0, 'growing', 'FIX_44', NOW()),
('ROLE01', 'SKE002', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE01', 'SKE003', 4, 'critical',    92.0, 'stable',  'FIX_44', NOW()),
('ROLE01', 'SKE004', 4, 'important',   88.0, 'stable',  'FIX_44', NOW()),
('ROLE01', 'SKE005', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE01', 'SKE006', 3, 'important',   82.0, 'stable',  'FIX_44', NOW()),
('ROLE01', 'SKE007', 3, 'important',   90.0, 'growing', 'FIX_44', NOW()),

('ROLE02', 'SKE001', 3, 'important',   85.0, 'growing', 'FIX_44', NOW()),
('ROLE02', 'SKE002', 3, 'nice_to_have',78.0, 'stable',  'FIX_44', NOW()),
('ROLE02', 'SKE003', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE02', 'SKE004', 3, 'important',   82.0, 'stable',  'FIX_44', NOW()),
('ROLE02', 'SKE005', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE02', 'SKE006', 3, 'important',   82.0, 'stable',  'FIX_44', NOW()),
('ROLE02', 'SKE007', 3, 'nice_to_have',78.0, 'growing', 'FIX_44', NOW()),

('ROLE03', 'SKE001', 5, 'critical',    96.0, 'growing', 'FIX_44', NOW()),
('ROLE03', 'SKE003', 5, 'critical',    94.0, 'stable',  'FIX_44', NOW()),
('ROLE03', 'SKE004', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE03', 'SKE005', 3, 'important',   82.0, 'stable',  'FIX_44', NOW()),
('ROLE03', 'SKE006', 3, 'nice_to_have',76.0, 'stable',  'FIX_44', NOW()),

('ROLE04', 'SKE001', 5, 'critical',    94.0, 'growing', 'FIX_44', NOW()),
('ROLE04', 'SKE003', 5, 'critical',    96.0, 'stable',  'FIX_44', NOW()),
('ROLE04', 'SKE004', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE04', 'SKE005', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),
('ROLE04', 'SKE006', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE04', 'SKE007', 4, 'critical',    92.0, 'growing', 'FIX_44', NOW()),

('ROLE05', 'SKE001', 5, 'critical',    98.0, 'growing', 'FIX_44', NOW()),
('ROLE05', 'SKE004', 4, 'important',   88.0, 'stable',  'FIX_44', NOW()),
('ROLE05', 'SKE005', 5, 'critical',    92.0, 'growing', 'FIX_44', NOW()),
('ROLE05', 'SKE006', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE05', 'SKE007', 4, 'important',   90.0, 'growing', 'FIX_44', NOW()),

('ROLE06', 'SKE001', 4, 'critical',    90.0, 'growing', 'FIX_44', NOW()),
('ROLE06', 'SKE003', 3, 'important',   82.0, 'stable',  'FIX_44', NOW()),
('ROLE06', 'SKE006', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),
('ROLE06', 'SKE007', 5, 'critical',    98.0, 'growing', 'FIX_44', NOW()),

('ROLE07', 'SKE001', 4, 'critical',    92.0, 'growing', 'FIX_44', NOW()),
('ROLE07', 'SKE002', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE07', 'SKE003', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE07', 'SKE004', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE07', 'SKE005', 3, 'important',   82.0, 'stable',  'FIX_44', NOW()),
('ROLE07', 'SKE006', 3, 'important',   84.0, 'stable',  'FIX_44', NOW()),
('ROLE07', 'SKE007', 4, 'important',   90.0, 'growing', 'FIX_44', NOW()),

('ROLE08', 'SKE001', 4, 'critical',    90.0, 'growing', 'FIX_44', NOW()),
('ROLE08', 'SKE003', 3, 'important',   82.0, 'stable',  'FIX_44', NOW()),
('ROLE08', 'SKE004', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE08', 'SKE005', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),
('ROLE08', 'SKE006', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),

-- ─── 경영: ROLE09-12, ROLE211-215 → SKB001-007 ───
('ROLE09', 'SKB001', 5, 'critical',    94.0, 'growing', 'FIX_44', NOW()),
('ROLE09', 'SKB002', 4, 'important',   88.0, 'stable',  'FIX_44', NOW()),
('ROLE09', 'SKB003', 4, 'important',   85.0, 'stable',  'FIX_44', NOW()),
('ROLE09', 'SKB004', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE09', 'SKB005', 4, 'critical',    90.0, 'growing', 'FIX_44', NOW()),
('ROLE09', 'SKB006', 3, 'important',   82.0, 'growing', 'FIX_44', NOW()),
('ROLE09', 'SKB007', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),

('ROLE10', 'SKB001', 3, 'important',   82.0, 'stable',  'FIX_44', NOW()),
('ROLE10', 'SKB002', 5, 'critical',    96.0, 'growing', 'FIX_44', NOW()),
('ROLE10', 'SKB005', 4, 'critical',    90.0, 'growing', 'FIX_44', NOW()),
('ROLE10', 'SKB006', 4, 'important',   85.0, 'growing', 'FIX_44', NOW()),
('ROLE10', 'SKB007', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),

('ROLE12', 'SKB001', 4, 'critical',    90.0, 'growing', 'FIX_44', NOW()),
('ROLE12', 'SKB002', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE12', 'SKB005', 3, 'important',   84.0, 'growing', 'FIX_44', NOW()),
('ROLE12', 'SKB007', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),

('ROLE211', 'SKB003', 5, 'critical',    96.0, 'stable',  'FIX_44', NOW()),
('ROLE211', 'SKB004', 5, 'critical',    94.0, 'stable',  'FIX_44', NOW()),
('ROLE211', 'SKB005', 4, 'important',   88.0, 'growing', 'FIX_44', NOW()),
('ROLE211', 'SKB001', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE211', 'SKB006', 3, 'important',   78.0, 'growing', 'FIX_44', NOW()),

('ROLE212', 'SKB003', 5, 'critical',    94.0, 'stable',  'FIX_44', NOW()),
('ROLE212', 'SKB004', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE212', 'SKB005', 3, 'important',   82.0, 'growing', 'FIX_44', NOW()),

('ROLE213', 'SKB001', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE213', 'SKB006', 3, 'important',   78.0, 'growing', 'FIX_44', NOW()),

('ROLE214', 'SKB004', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),
('ROLE214', 'SKB006', 4, 'critical',    90.0, 'growing', 'FIX_44', NOW()),

('ROLE215', 'SKB004', 5, 'critical',    92.0, 'stable',  'FIX_44', NOW()),
('ROLE215', 'SKB005', 4, 'important',   86.0, 'growing', 'FIX_44', NOW()),

-- ─── 법/행정: ROLE201-204, ROLE261-264 → SKL001-007 ───
('ROLE201', 'SKL001', 3, 'important',   78.0, 'stable',  'FIX_44', NOW()),
('ROLE201', 'SKL002', 3, 'important',   76.0, 'stable',  'FIX_44', NOW()),
('ROLE201', 'SKL003', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE201', 'SKL005', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),
('ROLE201', 'SKL007', 3, 'important',   82.0, 'stable',  'FIX_44', NOW()),

('ROLE202', 'SKL001', 5, 'critical',    96.0, 'stable',  'FIX_44', NOW()),
('ROLE202', 'SKL002', 5, 'critical',    94.0, 'stable',  'FIX_44', NOW()),
('ROLE202', 'SKL003', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE202', 'SKL004', 3, 'important',   80.0, 'growing', 'FIX_44', NOW()),
('ROLE202', 'SKL005', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE202', 'SKL006', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),
('ROLE202', 'SKL007', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),

('ROLE203', 'SKL001', 5, 'critical',    94.0, 'stable',  'FIX_44', NOW()),
('ROLE203', 'SKL002', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE203', 'SKL005', 5, 'critical',    92.0, 'stable',  'FIX_44', NOW()),
('ROLE203', 'SKL006', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE203', 'SKL007', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),

('ROLE204', 'SKL001', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE204', 'SKL004', 4, 'critical',    88.0, 'growing', 'FIX_44', NOW()),
('ROLE204', 'SKL005', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),
('ROLE204', 'SKL007', 5, 'critical',    92.0, 'stable',  'FIX_44', NOW()),

('ROLE261', 'SKL001', 3, 'important',   78.0, 'stable',  'FIX_44', NOW()),
('ROLE261', 'SKL003', 5, 'critical',    94.0, 'stable',  'FIX_44', NOW()),
('ROLE261', 'SKL005', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),
('ROLE261', 'SKL007', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),

('ROLE262', 'SKL001', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE262', 'SKL002', 3, 'important',   78.0, 'stable',  'FIX_44', NOW()),
('ROLE262', 'SKL003', 4, 'critical',    86.0, 'stable',  'FIX_44', NOW()),
('ROLE262', 'SKL005', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),

('ROLE263', 'SKL005', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),

('ROLE264', 'SKL001', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE264', 'SKL004', 5, 'critical',    96.0, 'growing', 'FIX_44', NOW()),
('ROLE264', 'SKL005', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE264', 'SKL007', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),

-- ─── 교육: ROLE221-224, ROLE251-253 → SKD001-007 ───
('ROLE221', 'SKD001', 5, 'critical',    94.0, 'stable',  'FIX_44', NOW()),
('ROLE221', 'SKD002', 5, 'critical',    96.0, 'stable',  'FIX_44', NOW()),
('ROLE221', 'SKD003', 4, 'important',   86.0, 'growing', 'FIX_44', NOW()),
('ROLE221', 'SKD004', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE221', 'SKD005', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE221', 'SKD006', 4, 'important',   88.0, 'stable',  'FIX_44', NOW()),
('ROLE221', 'SKD007', 3, 'nice_to_have',75.0, 'growing', 'FIX_44', NOW()),

('ROLE222', 'SKD001', 5, 'critical',    94.0, 'stable',  'FIX_44', NOW()),
('ROLE222', 'SKD002', 5, 'critical',    96.0, 'stable',  'FIX_44', NOW()),
('ROLE222', 'SKD003', 4, 'important',   84.0, 'growing', 'FIX_44', NOW()),
('ROLE222', 'SKD004', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE222', 'SKD005', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),
('ROLE222', 'SKD006', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),

('ROLE223', 'SKD001', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE223', 'SKD002', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE223', 'SKD003', 3, 'important',   80.0, 'growing', 'FIX_44', NOW()),
('ROLE223', 'SKD005', 5, 'critical',    96.0, 'stable',  'FIX_44', NOW()),

('ROLE224', 'SKD001', 5, 'critical',    94.0, 'stable',  'FIX_44', NOW()),
('ROLE224', 'SKD002', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE224', 'SKD003', 4, 'important',   86.0, 'growing', 'FIX_44', NOW()),
('ROLE224', 'SKD004', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),
('ROLE224', 'SKD006', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE224', 'SKD007', 5, 'critical',    96.0, 'growing', 'FIX_44', NOW()),

('ROLE251', 'SKD001', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),
('ROLE251', 'SKD003', 5, 'critical',    94.0, 'growing', 'FIX_44', NOW()),
('ROLE251', 'SKD005', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),

('ROLE252', 'SKD001', 5, 'critical',    96.0, 'stable',  'FIX_44', NOW()),
('ROLE252', 'SKD003', 5, 'critical',    96.0, 'growing', 'FIX_44', NOW()),
('ROLE252', 'SKD005', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),

('ROLE253', 'SKD001', 5, 'critical',    96.0, 'stable',  'FIX_44', NOW()),
('ROLE253', 'SKD003', 5, 'critical',    94.0, 'growing', 'FIX_44', NOW()),
('ROLE253', 'SKD006', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),

-- ─── 인문: ROLE241-242 → SKU001-007 ───
('ROLE241', 'SKU001', 5, 'critical',    94.0, 'stable',  'FIX_44', NOW()),
('ROLE241', 'SKU002', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE241', 'SKU003', 3, 'important',   82.0, 'growing', 'FIX_44', NOW()),
('ROLE241', 'SKU004', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE241', 'SKU005', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE241', 'SKU006', 3, 'nice_to_have',75.0, 'stable',  'FIX_44', NOW()),
('ROLE241', 'SKU007', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),

('ROLE242', 'SKU001', 5, 'critical',    96.0, 'stable',  'FIX_44', NOW()),
('ROLE242', 'SKU002', 5, 'critical',    94.0, 'stable',  'FIX_44', NOW()),
('ROLE242', 'SKU003', 4, 'important',   88.0, 'growing', 'FIX_44', NOW()),
('ROLE242', 'SKU004', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),
('ROLE242', 'SKU005', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE242', 'SKU006', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),
('ROLE242', 'SKU007', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),

-- ─── 예술/디자인: ROLE243-245, ROLE301-306 → SKA001-007 ───
('ROLE243', 'SKA001', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE243', 'SKA002', 5, 'critical',    96.0, 'growing', 'FIX_44', NOW()),
('ROLE243', 'SKA003', 3, 'important',   80.0, 'growing', 'FIX_44', NOW()),
('ROLE243', 'SKA006', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE243', 'SKA007', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),

('ROLE244', 'SKA001', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE244', 'SKA002', 5, 'critical',    94.0, 'growing', 'FIX_44', NOW()),
('ROLE244', 'SKA003', 4, 'important',   86.0, 'growing', 'FIX_44', NOW()),
('ROLE244', 'SKA007', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),

('ROLE245', 'SKA001', 3, 'important',   82.0, 'stable',  'FIX_44', NOW()),
('ROLE245', 'SKA002', 5, 'critical',    96.0, 'growing', 'FIX_44', NOW()),
('ROLE245', 'SKA003', 3, 'important',   80.0, 'growing', 'FIX_44', NOW()),
('ROLE245', 'SKA006', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),

('ROLE301', 'SKA001', 3, 'important',   82.0, 'stable',  'FIX_44', NOW()),
('ROLE301', 'SKA002', 5, 'critical',    96.0, 'growing', 'FIX_44', NOW()),
('ROLE301', 'SKA003', 4, 'important',   86.0, 'growing', 'FIX_44', NOW()),
('ROLE301', 'SKA006', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE301', 'SKA007', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),

('ROLE302', 'SKA001', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),
('ROLE302', 'SKA002', 5, 'critical',    94.0, 'growing', 'FIX_44', NOW()),
('ROLE302', 'SKA006', 5, 'critical',    92.0, 'stable',  'FIX_44', NOW()),
('ROLE302', 'SKA007', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),

('ROLE303', 'SKA001', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE303', 'SKA003', 5, 'critical',    96.0, 'growing', 'FIX_44', NOW()),
('ROLE303', 'SKA006', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE303', 'SKA007', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),

('ROLE304', 'SKA001', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE304', 'SKA004', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),
('ROLE304', 'SKA005', 5, 'critical',    94.0, 'growing', 'FIX_44', NOW()),
('ROLE304', 'SKA006', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),

('ROLE305', 'SKA001', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE305', 'SKA004', 5, 'critical',    96.0, 'stable',  'FIX_44', NOW()),
('ROLE305', 'SKA005', 4, 'important',   88.0, 'growing', 'FIX_44', NOW()),
('ROLE305', 'SKA006', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),

('ROLE306', 'SKA001', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),
('ROLE306', 'SKA002', 5, 'critical',    94.0, 'growing', 'FIX_44', NOW()),
('ROLE306', 'SKA006', 5, 'critical',    92.0, 'stable',  'FIX_44', NOW()),
('ROLE306', 'SKA007', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),

-- ─── 과학: ROLE014(?), ROLE501-504 → SKS001-007 ───
('ROLE501', 'SKS001', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE501', 'SKS002', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),
('ROLE501', 'SKS003', 5, 'critical',    96.0, 'growing', 'FIX_44', NOW()),
('ROLE501', 'SKS004', 4, 'critical',    90.0, 'growing', 'FIX_44', NOW()),
('ROLE501', 'SKS005', 4, 'important',   86.0, 'growing', 'FIX_44', NOW()),
('ROLE501', 'SKS006', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),
('ROLE501', 'SKS007', 3, 'important',   82.0, 'stable',  'FIX_44', NOW()),

('ROLE502', 'SKS001', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE502', 'SKS003', 5, 'critical',    94.0, 'growing', 'FIX_44', NOW()),
('ROLE502', 'SKS004', 4, 'important',   86.0, 'growing', 'FIX_44', NOW()),
('ROLE502', 'SKS005', 4, 'important',   88.0, 'growing', 'FIX_44', NOW()),
('ROLE502', 'SKS006', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),
('ROLE502', 'SKS007', 3, 'important',   82.0, 'stable',  'FIX_44', NOW()),

('ROLE503', 'SKS001', 5, 'critical',    96.0, 'stable',  'FIX_44', NOW()),
('ROLE503', 'SKS002', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE503', 'SKS003', 4, 'important',   88.0, 'growing', 'FIX_44', NOW()),
('ROLE503', 'SKS004', 4, 'critical',    90.0, 'growing', 'FIX_44', NOW()),
('ROLE503', 'SKS005', 4, 'important',   86.0, 'growing', 'FIX_44', NOW()),

('ROLE504', 'SKS001', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE504', 'SKS002', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE504', 'SKS003', 4, 'critical',    90.0, 'growing', 'FIX_44', NOW()),
('ROLE504', 'SKS004', 4, 'critical',    92.0, 'growing', 'FIX_44', NOW()),
('ROLE504', 'SKS005', 4, 'important',   86.0, 'growing', 'FIX_44', NOW()),
('ROLE504', 'SKS006', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),
('ROLE504', 'SKS007', 3, 'important',   82.0, 'stable',  'FIX_44', NOW()),

-- ─── 일반: ROLE401-403 → SKG001-007 ───
('ROLE401', 'SKG001', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE401', 'SKG002', 3, 'important',   82.0, 'stable',  'FIX_44', NOW()),
('ROLE401', 'SKG003', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE401', 'SKG004', 4, 'critical',    88.0, 'stable',  'FIX_44', NOW()),
('ROLE401', 'SKG005', 3, 'important',   80.0, 'growing', 'FIX_44', NOW()),
('ROLE401', 'SKG006', 3, 'important',   78.0, 'stable',  'FIX_44', NOW()),
('ROLE401', 'SKG007', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),

('ROLE402', 'SKG001', 5, 'critical',    94.0, 'stable',  'FIX_44', NOW()),
('ROLE402', 'SKG002', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE402', 'SKG003', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE402', 'SKG004', 4, 'important',   86.0, 'stable',  'FIX_44', NOW()),
('ROLE402', 'SKG005', 3, 'nice_to_have',75.0, 'growing', 'FIX_44', NOW()),
('ROLE402', 'SKG006', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),
('ROLE402', 'SKG007', 4, 'important',   84.0, 'stable',  'FIX_44', NOW()),

('ROLE403', 'SKG001', 5, 'critical',    96.0, 'stable',  'FIX_44', NOW()),
('ROLE403', 'SKG002', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE403', 'SKG003', 3, 'important',   78.0, 'stable',  'FIX_44', NOW()),
('ROLE403', 'SKG004', 4, 'critical',    90.0, 'stable',  'FIX_44', NOW()),
('ROLE403', 'SKG005', 3, 'nice_to_have',75.0, 'growing', 'FIX_44', NOW()),
('ROLE403', 'SKG006', 3, 'important',   80.0, 'stable',  'FIX_44', NOW()),
('ROLE403', 'SKG007', 4, 'important',   84.0, 'stable',  'FIX_44', NOW())

ON CONFLICT (role_cd, skill_cd) DO NOTHING;

DO $$ BEGIN RAISE NOTICE 'Part 1 완료: 역할-스킬 매핑 추가 (%s rows)', (SELECT count(*) FROM tb_role_skill_map WHERE ins_user_id = 'FIX_44'); END $$;

-- =====================================================
-- Part 2: 스킬 관계 추가 (tb_skill_relation) - 그래프 엣지
-- 카테고리당 5~6개 관계
-- =====================================================

INSERT INTO tb_skill_relation (skill_cd_from, skill_cd_to, relation_type, strength, ins_user_id, ins_dt)
VALUES
-- medical
('SKM001', 'SKM004', 'prerequisite',   0.90, 'FIX_44', NOW()),
('SKM001', 'SKM007', 'builds_on',      0.70, 'FIX_44', NOW()),
('SKM002', 'SKM006', 'complementary',  0.75, 'FIX_44', NOW()),
('SKM003', 'SKM001', 'prerequisite',   0.85, 'FIX_44', NOW()),
('SKM004', 'SKM006', 'complementary',  0.70, 'FIX_44', NOW()),
('SKM005', 'SKM002', 'complementary',  0.65, 'FIX_44', NOW()),

-- nursing
('SKN001', 'SKN002', 'prerequisite',   0.90, 'FIX_44', NOW()),
('SKN003', 'SKN001', 'prerequisite',   0.85, 'FIX_44', NOW()),
('SKN003', 'SKN004', 'builds_on',      0.80, 'FIX_44', NOW()),
('SKN005', 'SKN001', 'complementary',  0.70, 'FIX_44', NOW()),
('SKN006', 'SKN007', 'builds_on',      0.75, 'FIX_44', NOW()),

-- pharmacy
('SKP002', 'SKP001', 'prerequisite',   0.90, 'FIX_44', NOW()),
('SKP003', 'SKP001', 'prerequisite',   0.85, 'FIX_44', NOW()),
('SKP001', 'SKP007', 'builds_on',      0.90, 'FIX_44', NOW()),
('SKP004', 'SKP005', 'complementary',  0.75, 'FIX_44', NOW()),
('SKP006', 'SKP007', 'complementary',  0.70, 'FIX_44', NOW()),

-- health
('SKH001', 'SKH002', 'prerequisite',   0.90, 'FIX_44', NOW()),
('SKH002', 'SKH003', 'builds_on',      0.85, 'FIX_44', NOW()),
('SKH003', 'SKH004', 'builds_on',      0.80, 'FIX_44', NOW()),
('SKH005', 'SKH006', 'complementary',  0.70, 'FIX_44', NOW()),
('SKH006', 'SKH007', 'builds_on',      0.75, 'FIX_44', NOW()),

-- engineering
('SKE001', 'SKE004', 'prerequisite',   0.90, 'FIX_44', NOW()),
('SKE002', 'SKE004', 'prerequisite',   0.85, 'FIX_44', NOW()),
('SKE004', 'SKE005', 'builds_on',      0.90, 'FIX_44', NOW()),
('SKE003', 'SKE007', 'builds_on',      0.75, 'FIX_44', NOW()),
('SKE006', 'SKE007', 'complementary',  0.70, 'FIX_44', NOW()),
('SKE001', 'SKE007', 'builds_on',      0.80, 'FIX_44', NOW()),

-- business
('SKB001', 'SKB002', 'builds_on',      0.80, 'FIX_44', NOW()),
('SKB003', 'SKB004', 'prerequisite',   0.90, 'FIX_44', NOW()),
('SKB005', 'SKB001', 'complementary',  0.75, 'FIX_44', NOW()),
('SKB006', 'SKB007', 'complementary',  0.70, 'FIX_44', NOW()),
('SKB002', 'SKB007', 'builds_on',      0.75, 'FIX_44', NOW()),

-- law_admin
('SKL001', 'SKL002', 'prerequisite',   0.85, 'FIX_44', NOW()),
('SKL001', 'SKL003', 'prerequisite',   0.85, 'FIX_44', NOW()),
('SKL002', 'SKL006', 'builds_on',      0.80, 'FIX_44', NOW()),
('SKL005', 'SKL006', 'complementary',  0.75, 'FIX_44', NOW()),
('SKL006', 'SKL007', 'builds_on',      0.85, 'FIX_44', NOW()),

-- education
('SKD001', 'SKD002', 'prerequisite',   0.85, 'FIX_44', NOW()),
('SKD001', 'SKD003', 'builds_on',      0.80, 'FIX_44', NOW()),
('SKD004', 'SKD006', 'builds_on',      0.85, 'FIX_44', NOW()),
('SKD005', 'SKD007', 'complementary',  0.75, 'FIX_44', NOW()),
('SKD002', 'SKD006', 'complementary',  0.70, 'FIX_44', NOW()),

-- humanities
('SKU001', 'SKU004', 'builds_on',      0.80, 'FIX_44', NOW()),
('SKU002', 'SKU005', 'builds_on',      0.85, 'FIX_44', NOW()),
('SKU003', 'SKU006', 'complementary',  0.75, 'FIX_44', NOW()),
('SKU004', 'SKU006', 'prerequisite',   0.80, 'FIX_44', NOW()),
('SKU001', 'SKU007', 'complementary',  0.70, 'FIX_44', NOW()),

-- arts
('SKA001', 'SKA002', 'prerequisite',   0.85, 'FIX_44', NOW()),
('SKA002', 'SKA003', 'builds_on',      0.80, 'FIX_44', NOW()),
('SKA004', 'SKA005', 'builds_on',      0.80, 'FIX_44', NOW()),
('SKA006', 'SKA007', 'builds_on',      0.85, 'FIX_44', NOW()),
('SKA001', 'SKA006', 'complementary',  0.75, 'FIX_44', NOW()),

-- science
('SKS001', 'SKS003', 'prerequisite',   0.85, 'FIX_44', NOW()),
('SKS002', 'SKS003', 'prerequisite',   0.80, 'FIX_44', NOW()),
('SKS003', 'SKS004', 'builds_on',      0.85, 'FIX_44', NOW()),
('SKS004', 'SKS005', 'builds_on',      0.80, 'FIX_44', NOW()),
('SKS005', 'SKS006', 'complementary',  0.75, 'FIX_44', NOW()),
('SKS006', 'SKS007', 'complementary',  0.70, 'FIX_44', NOW()),

-- general
('SKG001', 'SKG006', 'builds_on',      0.85, 'FIX_44', NOW()),
('SKG002', 'SKG003', 'complementary',  0.80, 'FIX_44', NOW()),
('SKG004', 'SKG002', 'builds_on',      0.75, 'FIX_44', NOW()),
('SKG005', 'SKG006', 'complementary',  0.70, 'FIX_44', NOW()),
('SKG003', 'SKG007', 'complementary',  0.70, 'FIX_44', NOW())

ON CONFLICT (skill_cd_from, skill_cd_to, relation_type) DO NOTHING;

DO $$ BEGIN RAISE NOTICE 'Part 2 완료: 스킬 관계 추가 (%s rows)', (SELECT count(*) FROM tb_skill_relation WHERE ins_user_id = 'FIX_44'); END $$;

-- =====================================================
-- Part 3: 위험 알림 시드 데이터 (tb_risk_alert)
-- risk_type 컬럼 사용 (서비스 코드 기준)
-- 대상: 2023~2025 입학 학생 중 결정론적 샘플링
-- =====================================================

-- 대상 학생 temp table
CREATE TEMP TABLE tmp_alert_students AS
SELECT student_id, current_grade,
       abs(hashtext(student_id)) % 100 AS h
FROM tb_student
WHERE admission_year BETWEEN 2023 AND 2025;

CREATE INDEX idx_tmp_alert_h ON tmp_alert_students(h);

-- GPA 위험 알림 (h < 15 → ~15% 학생)
INSERT INTO tb_risk_alert (student_id, risk_type, severity, title, description, status, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'gpa',
    CASE
        WHEN s.h < 5  THEN 'critical'
        WHEN s.h < 10 THEN 'high'
        ELSE 'medium'
    END,
    CASE
        WHEN s.h < 5  THEN '학점 위기 - 학사 경고 위험'
        WHEN s.h < 10 THEN '학점 주의 - 개선 필요'
        ELSE '학점 향상 권장'
    END,
    CASE
        WHEN s.h < 5  THEN '현재 GPA가 학사 경고 기준 미만입니다. 즉시 학업 상담을 받으세요.'
        WHEN s.h < 10 THEN '현재 GPA가 경고 기준에 근접합니다. 학습 전략 점검이 필요합니다.'
        ELSE 'GPA 향상이 권장됩니다. 목표 기업/대학원 지원을 위해 노력하세요.'
    END,
    'active',
    'FIX_44',
    NOW() - (s.h || ' days')::interval
FROM tmp_alert_students s
WHERE s.h < 15;

-- 학점이수 위험 알림 (15 <= h < 30 → ~15%)
INSERT INTO tb_risk_alert (student_id, risk_type, severity, title, description, status, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'credits',
    CASE
        WHEN s.h < 20 THEN 'high'
        ELSE 'medium'
    END,
    '학점 이수 부족 - ' || (s.current_grade * 30 - 10 - s.h) || '학점 미달',
    '현재 ' || s.current_grade || '학년으로 예상 이수 학점 대비 부족합니다. 수강 계획을 검토하세요.',
    'active',
    'FIX_44',
    NOW() - (s.h || ' days')::interval
FROM tmp_alert_students s
WHERE s.h >= 15 AND s.h < 30;

-- 졸업요건 위험 (30 <= h < 40, 3학년 이상만)
INSERT INTO tb_risk_alert (student_id, risk_type, severity, title, description, status, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'graduation',
    CASE
        WHEN s.h < 35 THEN 'high'
        ELSE 'medium'
    END,
    '졸업요건 충족 위험',
    '졸업까지 필요한 학점이 많습니다. 졸업요건 상담을 받고, 계절학기 수강 계획을 세우세요.',
    'active',
    'FIX_44',
    NOW() - ((s.h - 30) * 2 || ' days')::interval
FROM tmp_alert_students s
WHERE s.h >= 30 AND s.h < 40
  AND s.current_grade >= 3;

-- 스킬갭 위험 (40 <= h < 55 → ~15%)
INSERT INTO tb_risk_alert (student_id, risk_type, severity, title, description, status, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'skill_gap',
    CASE
        WHEN s.h < 45 THEN 'high'
        ELSE 'medium'
    END,
    '목표 직무 스킬 갭 - ' || (60 + s.h) || '%',
    '목표 직무 대비 스킬 갭이 큽니다. 스킬 개발 계획을 세우고, 관련 프로젝트/강의를 찾아보세요.',
    'active',
    'FIX_44',
    NOW() - ((s.h - 40) || ' days')::interval
FROM tmp_alert_students s
WHERE s.h >= 40 AND s.h < 55;

-- 선수과목 위험 (55 <= h < 65 → ~10%)
INSERT INTO tb_risk_alert (student_id, risk_type, severity, title, description, status, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'prerequisite',
    'high',
    '선수과목 미이수 주의',
    '다음 학기 수강 예정 과목의 선수과목이 미이수 상태입니다. 수강 계획을 재검토하세요.',
    'active',
    'FIX_44',
    NOW() - ((s.h - 55) || ' days')::interval
FROM tmp_alert_students s
WHERE s.h >= 55 AND s.h < 65;

-- 해결된 알림 일부 추가 (65 <= h < 75 → ~10%, resolved 상태)
INSERT INTO tb_risk_alert (student_id, risk_type, severity, title, description, status, resolved_at, resolution_notes, ins_user_id, ins_dt)
SELECT
    s.student_id,
    CASE s.h % 3
        WHEN 0 THEN 'gpa'
        WHEN 1 THEN 'credits'
        ELSE 'skill_gap'
    END,
    'medium',
    CASE s.h % 3
        WHEN 0 THEN '학점 향상 완료'
        WHEN 1 THEN '학점 이수 보완 완료'
        ELSE '스킬 갭 개선 완료'
    END,
    '이전에 발생한 위험이 해결되었습니다.',
    'resolved',
    NOW() - ((s.h - 65) || ' days')::interval,
    '학생 자체 해결',
    'FIX_44',
    NOW() - ((s.h - 55) || ' days')::interval
FROM tmp_alert_students s
WHERE s.h >= 65 AND s.h < 75;

DROP TABLE IF EXISTS tmp_alert_students;

DO $$ BEGIN RAISE NOTICE 'Part 3 완료: 위험 알림 시드 데이터 (%s rows)', (SELECT count(*) FROM tb_risk_alert WHERE ins_user_id = 'FIX_44'); END $$;

-- =====================================================
-- Part 4: 시뮬레이션 시나리오 JSONB 재구성
-- base_state → {"variables": [...]}
-- predicted_outcomes → {"results": [...], "recommendation": "...", "ai_analysis": null}
-- =====================================================

-- 카테고리-시나리오타입별 변환 매핑 temp table
CREATE TEMP TABLE tmp_sim_transform (
    category VARCHAR(20),
    scenario_type VARCHAR(30),
    variables_json TEXT,
    results_json TEXT,
    recommendation TEXT
);

INSERT INTO tmp_sim_transform VALUES
-- medical × career_path
('medical', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"의사","impact_description":"의사 커리어 목표 설정"},{"name":"gpa_target","current_value":"3.5","simulated_value":"4.0","impact_description":"GPA 목표 상향"},{"name":"clinical_hours","current_value":"0","simulated_value":"500","impact_description":"임상실습 시간 확보"}]',
 '[{"metric_name":"커리어 준비도","current_value":45,"simulated_value":75,"change_percent":66.7,"impact_level":"positive","explanation":"의사 국가시험 준비 경로 확보"},{"metric_name":"임상 경험","current_value":10,"simulated_value":60,"change_percent":500.0,"impact_level":"positive","explanation":"임상실습으로 실무 역량 대폭 향상"},{"metric_name":"학업 성취","current_value":70,"simulated_value":85,"change_percent":21.4,"impact_level":"positive","explanation":"GPA 향상으로 본과 진학 경쟁력 강화"}]',
 '본과 진학을 위해 기초의학 과목 성적 관리와 임상실습 경험을 병행하세요.'),

-- medical × skill_development
('medical', 'skill_development',
 '[{"name":"study_hours","current_value":"10","simulated_value":"20","impact_description":"주간 학습 시간 증가"},{"name":"study_group","current_value":"미참여","simulated_value":"참여","impact_description":"스터디 그룹 참여"}]',
 '[{"metric_name":"기초의학 이해도","current_value":50,"simulated_value":85,"change_percent":70.0,"impact_level":"positive","explanation":"심화 학습으로 기초의학 역량 크게 향상"},{"metric_name":"시험 준비도","current_value":40,"simulated_value":78,"change_percent":95.0,"impact_level":"positive","explanation":"체계적 학습으로 시험 대비 강화"}]',
 '기초의학 과목 스터디 그룹 참여와 주간 학습 시간 확대를 권장합니다.'),

-- medical × opportunity
('medical', 'opportunity',
 '[{"name":"volunteer_hours","current_value":"0","simulated_value":"100","impact_description":"의료 봉사시간 확보"},{"name":"clinical_observation","current_value":"미참여","simulated_value":"참여","impact_description":"임상 관찰 프로그램 참여"}]',
 '[{"metric_name":"공감 능력","current_value":50,"simulated_value":90,"change_percent":80.0,"impact_level":"positive","explanation":"봉사활동으로 환자 공감 능력 향상"},{"metric_name":"포트폴리오 강도","current_value":30,"simulated_value":85,"change_percent":183.3,"impact_level":"positive","explanation":"봉사 경험이 포트폴리오 크게 강화"}]',
 '지역사회 의료봉사와 임상관찰 프로그램에 적극 참여하세요.'),

-- nursing × career_path
('nursing', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"간호사","impact_description":"간호사 커리어 목표 설정"},{"name":"clinical_hours","current_value":"0","simulated_value":"1000","impact_description":"임상실습 시간 확보"}]',
 '[{"metric_name":"커리어 준비도","current_value":40,"simulated_value":78,"change_percent":95.0,"impact_level":"positive","explanation":"간호사 면허시험 준비 경로 확보"},{"metric_name":"임상 역량","current_value":15,"simulated_value":65,"change_percent":333.3,"impact_level":"positive","explanation":"임상실습으로 실무 역량 대폭 향상"}]',
 '간호사 국가시험 준비와 병원 임상실습을 병행하세요.'),

-- nursing × skill_development
('nursing', 'skill_development',
 '[{"name":"simulation_lab","current_value":"미참여","simulated_value":"참여","impact_description":"시뮬레이션 실습 참여"},{"name":"additional_courses","current_value":"0","simulated_value":"2","impact_description":"추가 전공 과목 수강"}]',
 '[{"metric_name":"임상 스킬","current_value":45,"simulated_value":82,"change_percent":82.2,"impact_level":"positive","explanation":"시뮬레이션 실습으로 임상 역량 강화"},{"metric_name":"응급 대응","current_value":30,"simulated_value":70,"change_percent":133.3,"impact_level":"positive","explanation":"응급 상황 대응 능력 향상"}]',
 '시뮬레이션 실습실 활용과 아동/모성간호학 추가 수강을 권장합니다.'),

-- nursing × opportunity
('nursing', 'opportunity',
 '[{"name":"hospital_practice","current_value":"미참여","simulated_value":"대학병원","impact_description":"대학병원 임상실습"},{"name":"mentoring","current_value":"미참여","simulated_value":"참여","impact_description":"선배 간호사 멘토링"}]',
 '[{"metric_name":"실무 능력","current_value":20,"simulated_value":88,"change_percent":340.0,"impact_level":"positive","explanation":"병원 실습으로 실무 능력 대폭 향상"},{"metric_name":"전문성","current_value":35,"simulated_value":85,"change_percent":142.9,"impact_level":"positive","explanation":"멘토링으로 전문 역량 강화"}]',
 '대학병원 임상실습 참여와 선배 간호사 멘토링을 적극 활용하세요.'),

-- pharmacy × career_path
('pharmacy', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"약사","impact_description":"약사 커리어 목표 설정"},{"name":"target_exam","current_value":"미정","simulated_value":"약사국가시험","impact_description":"국가시험 준비"}]',
 '[{"metric_name":"커리어 준비도","current_value":38,"simulated_value":76,"change_percent":100.0,"impact_level":"positive","explanation":"약사 면허시험 준비 경로 확보"},{"metric_name":"약학 전문성","current_value":40,"simulated_value":72,"change_percent":80.0,"impact_level":"positive","explanation":"전문 약학 역량 향상"}]',
 '약사 국가시험 준비와 제약 실습 경험을 병행하세요.'),

-- pharmacy × skill_development
('pharmacy', 'skill_development',
 '[{"name":"lab_practice","current_value":"기본","simulated_value":"심화","impact_description":"실험실습 심화"},{"name":"additional_courses","current_value":"0","simulated_value":"2","impact_description":"임상약학 추가 수강"}]',
 '[{"metric_name":"약학 스킬","current_value":45,"simulated_value":83,"change_percent":84.4,"impact_level":"positive","explanation":"심화 실습으로 약학 역량 강화"},{"metric_name":"약물 지식","current_value":50,"simulated_value":80,"change_percent":60.0,"impact_level":"positive","explanation":"추가 과목으로 약물 지식 확대"}]',
 '약리학 심화 실습과 임상약학 추가 수강을 권장합니다.'),

-- pharmacy × opportunity
('pharmacy', 'opportunity',
 '[{"name":"internship","current_value":"미참여","simulated_value":"제약회사","impact_description":"제약회사 인턴십"},{"name":"research_project","current_value":"미참여","simulated_value":"참여","impact_description":"연구 프로젝트 참여"}]',
 '[{"metric_name":"산업 이해도","current_value":20,"simulated_value":85,"change_percent":325.0,"impact_level":"positive","explanation":"인턴십으로 제약 산업 이해도 대폭 향상"},{"metric_name":"네트워크","current_value":10,"simulated_value":80,"change_percent":700.0,"impact_level":"positive","explanation":"업계 네트워크 구축"}]',
 '제약회사 인턴십 참여와 연구 프로젝트 경험을 쌓으세요.'),

-- health × career_path
('health', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"보건전문가","impact_description":"보건 전문가 목표 설정"},{"name":"certification","current_value":"미취득","simulated_value":"보건전문자격증","impact_description":"자격증 취득 계획"}]',
 '[{"metric_name":"커리어 준비도","current_value":35,"simulated_value":74,"change_percent":111.4,"impact_level":"positive","explanation":"보건 전문가 경로 확보"},{"metric_name":"자격증 준비","current_value":20,"simulated_value":78,"change_percent":290.0,"impact_level":"positive","explanation":"자격증 취득 준비 강화"}]',
 '보건 전문 자격증 취득과 의료기관 실습을 병행하세요.'),

-- health × skill_development
('health', 'skill_development',
 '[{"name":"practical_training","current_value":"기본","simulated_value":"심화","impact_description":"실습 훈련 심화"},{"name":"additional_courses","current_value":"0","simulated_value":"2","impact_description":"재활의학 등 추가 수강"}]',
 '[{"metric_name":"의료 지식","current_value":45,"simulated_value":80,"change_percent":77.8,"impact_level":"positive","explanation":"심화 학습으로 의료 지식 향상"},{"metric_name":"실무 능력","current_value":35,"simulated_value":75,"change_percent":114.3,"impact_level":"positive","explanation":"실습 훈련으로 실무 역량 강화"}]',
 '재활의학, 병리학 추가 수강과 실습 훈련 심화를 권장합니다.'),

-- health × opportunity
('health', 'opportunity',
 '[{"name":"facility_practice","current_value":"미참여","simulated_value":"의료기관","impact_description":"의료기관 현장실습"},{"name":"mentoring","current_value":"미참여","simulated_value":"참여","impact_description":"지도교수 멘토링"}]',
 '[{"metric_name":"실무 역량","current_value":25,"simulated_value":85,"change_percent":240.0,"impact_level":"positive","explanation":"현장실습으로 실무 역량 대폭 향상"},{"metric_name":"전문 성장","current_value":30,"simulated_value":78,"change_percent":160.0,"impact_level":"positive","explanation":"멘토링으로 전문가 성장 경로 확보"}]',
 '의료기관 현장실습 참여와 지도교수 멘토링을 활용하세요.'),

-- engineering × career_path
('engineering', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"소프트웨어 개발자","impact_description":"개발자 커리어 목표"},{"name":"certifications","current_value":"0","simulated_value":"정보처리기사","impact_description":"자격증 취득"},{"name":"portfolio","current_value":"없음","simulated_value":"3개 프로젝트","impact_description":"포트폴리오 구축"}]',
 '[{"metric_name":"커리어 준비도","current_value":40,"simulated_value":76,"change_percent":90.0,"impact_level":"positive","explanation":"IT 전문가 취업 경쟁력 확보"},{"metric_name":"기술 역량","current_value":45,"simulated_value":80,"change_percent":77.8,"impact_level":"positive","explanation":"포트폴리오로 기술력 입증"},{"metric_name":"자격증","current_value":0,"simulated_value":72,"change_percent":100.0,"impact_level":"positive","explanation":"정보처리기사 취득으로 기본 역량 인증"}]',
 '정보처리기사 자격증 취득과 개인 프로젝트 포트폴리오 구축을 병행하세요.'),

-- engineering × skill_development
('engineering', 'skill_development',
 '[{"name":"coding_practice","current_value":"주 5시간","simulated_value":"주 15시간","impact_description":"코딩 연습 시간 증가"},{"name":"algorithm_study","current_value":"미시작","simulated_value":"매일 1문제","impact_description":"알고리즘 학습 시작"}]',
 '[{"metric_name":"코딩 실력","current_value":50,"simulated_value":85,"change_percent":70.0,"impact_level":"positive","explanation":"집중 연습으로 코딩 실력 향상"},{"metric_name":"알고리즘","current_value":30,"simulated_value":78,"change_percent":160.0,"impact_level":"positive","explanation":"알고리즘 학습으로 문제해결력 강화"}]',
 'Python/Java 코딩 연습과 알고리즘 문제풀이를 꾸준히 하세요.'),

-- engineering × opportunity
('engineering', 'opportunity',
 '[{"name":"internship","current_value":"미참여","simulated_value":"IT기업","impact_description":"IT 기업 인턴십"},{"name":"team_project","current_value":"0","simulated_value":"1","impact_description":"팀 프로젝트 참여"}]',
 '[{"metric_name":"실무 경험","current_value":15,"simulated_value":88,"change_percent":486.7,"impact_level":"positive","explanation":"인턴십으로 실무 경험 대폭 확보"},{"metric_name":"업계 이해","current_value":20,"simulated_value":80,"change_percent":300.0,"impact_level":"positive","explanation":"IT 산업 현장 이해도 향상"}]',
 'IT 기업 인턴십 참여와 팀 프로젝트 경험을 적극 쌓으세요.'),

-- business × career_path
('business', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"경영 컨설턴트","impact_description":"컨설턴트 커리어 목표"},{"name":"mba_plan","current_value":"미정","simulated_value":"MBA 진학","impact_description":"MBA 진학 계획"}]',
 '[{"metric_name":"커리어 준비도","current_value":35,"simulated_value":74,"change_percent":111.4,"impact_level":"positive","explanation":"경영 전문가 경로 확보"},{"metric_name":"비즈니스 역량","current_value":40,"simulated_value":78,"change_percent":95.0,"impact_level":"positive","explanation":"비즈니스 분석 역량 강화"}]',
 'CPA/경영지도사 자격증 준비와 MBA 진학 계획을 구체화하세요.'),

-- business × skill_development
('business', 'skill_development',
 '[{"name":"case_study","current_value":"0","simulated_value":"10건","impact_description":"케이스 스터디 수행"},{"name":"data_analysis","current_value":"기초","simulated_value":"중급","impact_description":"데이터 분석 역량 향상"}]',
 '[{"metric_name":"분석 역량","current_value":40,"simulated_value":83,"change_percent":107.5,"impact_level":"positive","explanation":"케이스 스터디로 분석력 향상"},{"metric_name":"전략 사고","current_value":35,"simulated_value":78,"change_percent":122.9,"impact_level":"positive","explanation":"전략적 사고력 강화"}]',
 '데이터 분석 역량 강화와 실제 기업 케이스 스터디를 병행하세요.'),

-- business × opportunity
('business', 'opportunity',
 '[{"name":"internship","current_value":"미참여","simulated_value":"대기업","impact_description":"대기업 인턴십"},{"name":"department","current_value":"미정","simulated_value":"경영기획","impact_description":"경영기획 부서 배치"}]',
 '[{"metric_name":"비즈니스 스킬","current_value":25,"simulated_value":85,"change_percent":240.0,"impact_level":"positive","explanation":"인턴십으로 비즈니스 스킬 대폭 향상"},{"metric_name":"커리어 명확성","current_value":30,"simulated_value":82,"change_percent":173.3,"impact_level":"positive","explanation":"현장 경험으로 진로 방향 명확화"}]',
 '대기업/중견기업 인턴십에 적극 지원하세요.'),

-- law_admin × career_path
('law_admin', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"법률전문가","impact_description":"법조인 커리어 목표"},{"name":"bar_exam","current_value":"미정","simulated_value":"법학적성시험","impact_description":"법학적성시험 준비"}]',
 '[{"metric_name":"커리어 준비도","current_value":30,"simulated_value":72,"change_percent":140.0,"impact_level":"positive","explanation":"법률 전문가 경로 확보"},{"metric_name":"법률 지식","current_value":40,"simulated_value":78,"change_percent":95.0,"impact_level":"positive","explanation":"법학 핵심 과목 역량 강화"}]',
 '법학적성시험 준비와 법률 핵심 과목 성적 관리를 병행하세요.'),

-- law_admin × skill_development
('law_admin', 'skill_development',
 '[{"name":"moot_court","current_value":"미참여","simulated_value":"참여","impact_description":"모의재판 참여"},{"name":"additional_courses","current_value":"0","simulated_value":"형법,상법","impact_description":"추가 법학 과목 수강"}]',
 '[{"metric_name":"법률 분석","current_value":40,"simulated_value":83,"change_percent":107.5,"impact_level":"positive","explanation":"법률 분석 역량 크게 향상"},{"metric_name":"논증 능력","current_value":35,"simulated_value":80,"change_percent":128.6,"impact_level":"positive","explanation":"모의재판으로 논증 능력 강화"}]',
 '모의재판 참여와 형법/상법 추가 수강을 권장합니다.'),

-- law_admin × opportunity
('law_admin', 'opportunity',
 '[{"name":"practice","current_value":"미참여","simulated_value":"법률사무소","impact_description":"법률사무소 실습"},{"name":"case_study","current_value":"0","simulated_value":"5건","impact_description":"실제 사례 분석"}]',
 '[{"metric_name":"실무 능력","current_value":15,"simulated_value":85,"change_percent":466.7,"impact_level":"positive","explanation":"법률사무소 실습으로 실무 역량 대폭 향상"},{"metric_name":"법률 문서","current_value":20,"simulated_value":80,"change_percent":300.0,"impact_level":"positive","explanation":"실무 문서 작성 능력 강화"}]',
 '법률사무소/공공기관 실습에 적극 참여하세요.'),

-- education × career_path
('education', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"교육전문가","impact_description":"교원 커리어 목표"},{"name":"target_exam","current_value":"미정","simulated_value":"교원임용시험","impact_description":"임용시험 준비"}]',
 '[{"metric_name":"커리어 준비도","current_value":35,"simulated_value":75,"change_percent":114.3,"impact_level":"positive","explanation":"교원 임용 경로 확보"},{"metric_name":"교수 역량","current_value":40,"simulated_value":80,"change_percent":100.0,"impact_level":"positive","explanation":"교육 전문 역량 강화"}]',
 '교원임용시험 준비와 교직 이수 과정을 체계적으로 수행하세요.'),

-- education × skill_development
('education', 'skill_development',
 '[{"name":"micro_teaching","current_value":"미참여","simulated_value":"참여","impact_description":"마이크로 티칭 실습"},{"name":"additional_skills","current_value":"0","simulated_value":"상담기법,교육평가","impact_description":"추가 역량 개발"}]',
 '[{"metric_name":"교수법","current_value":40,"simulated_value":83,"change_percent":107.5,"impact_level":"positive","explanation":"마이크로 티칭으로 교수법 향상"},{"metric_name":"학생 이해","current_value":45,"simulated_value":80,"change_percent":77.8,"impact_level":"positive","explanation":"교육심리 역량 강화"}]',
 '마이크로 티칭 실습과 상담기법/교육평가 추가 학습을 권장합니다.'),

-- education × opportunity
('education', 'opportunity',
 '[{"name":"teaching_practice","current_value":"미참여","simulated_value":"중학교","impact_description":"교생실습 참여"},{"name":"class_management","current_value":"미경험","simulated_value":"경험","impact_description":"학급 운영 경험"}]',
 '[{"metric_name":"실제 교수","current_value":10,"simulated_value":88,"change_percent":780.0,"impact_level":"positive","explanation":"교생실습으로 실전 교수 역량 확보"},{"metric_name":"학급 운영","current_value":5,"simulated_value":78,"change_percent":1460.0,"impact_level":"positive","explanation":"학급 운영 경험으로 교사 역량 강화"}]',
 '교생실습에 적극 참여하고 학급 운영 경험을 쌓으세요.'),

-- humanities × career_path
('humanities', 'career_path',
 '[{"name":"target_path","current_value":"미정","simulated_value":"대학원/문화산업","impact_description":"진로 방향 설정"},{"name":"language_cert","current_value":"미취득","simulated_value":"취득","impact_description":"어학 자격증 취득"}]',
 '[{"metric_name":"커리어 준비도","current_value":30,"simulated_value":70,"change_percent":133.3,"impact_level":"positive","explanation":"인문학 전문가 경로 확보"},{"metric_name":"학술 역량","current_value":40,"simulated_value":78,"change_percent":95.0,"impact_level":"positive","explanation":"학술 연구 역량 강화"}]',
 '대학원 진학 준비와 어학 자격증 취득을 병행하세요.'),

-- humanities × skill_development
('humanities', 'skill_development',
 '[{"name":"thesis_writing","current_value":"미경험","simulated_value":"경험","impact_description":"논문 작성 경험"},{"name":"foreign_language","current_value":"중급","simulated_value":"고급","impact_description":"외국어 역량 향상"}]',
 '[{"metric_name":"연구 역량","current_value":35,"simulated_value":82,"change_percent":134.3,"impact_level":"positive","explanation":"논문 작성으로 연구 역량 향상"},{"metric_name":"비판적 분석","current_value":40,"simulated_value":78,"change_percent":95.0,"impact_level":"positive","explanation":"비판적 분석력 강화"}]',
 '외국어 심화 학습과 논문 작성 경험을 권장합니다.'),

-- humanities × opportunity
('humanities', 'opportunity',
 '[{"name":"exchange_program","current_value":"미참여","simulated_value":"영어권","impact_description":"해외 교환학생"},{"name":"cultural_immersion","current_value":"미경험","simulated_value":"경험","impact_description":"문화 체험"}]',
 '[{"metric_name":"어학 향상","current_value":40,"simulated_value":88,"change_percent":120.0,"impact_level":"positive","explanation":"교환학생으로 어학 역량 대폭 향상"},{"metric_name":"글로벌 시야","current_value":25,"simulated_value":82,"change_percent":228.0,"impact_level":"positive","explanation":"해외 경험으로 글로벌 관점 확대"}]',
 '해외 교환학생 프로그램에 적극 참여하세요.'),

-- arts × career_path
('arts', 'career_path',
 '[{"name":"target_path","current_value":"미정","simulated_value":"크리에이터/디자이너","impact_description":"예술 전문가 목표"},{"name":"portfolio","current_value":"없음","simulated_value":"구축","impact_description":"포트폴리오 구축"}]',
 '[{"metric_name":"커리어 준비도","current_value":30,"simulated_value":72,"change_percent":140.0,"impact_level":"positive","explanation":"예술 전문가 경로 확보"},{"metric_name":"창작 역량","current_value":45,"simulated_value":80,"change_percent":77.8,"impact_level":"positive","explanation":"창작 역량 강화"}]',
 '포트폴리오 구축과 전시회/공모전 참여를 병행하세요.'),

-- arts × skill_development
('arts', 'skill_development',
 '[{"name":"workshop","current_value":"미참여","simulated_value":"참여","impact_description":"창작 워크숍 참여"},{"name":"media_production","current_value":"기초","simulated_value":"중급","impact_description":"미디어 제작 역량 향상"}]',
 '[{"metric_name":"창작 능력","current_value":45,"simulated_value":85,"change_percent":88.9,"impact_level":"positive","explanation":"워크숍으로 창작 능력 향상"},{"metric_name":"기술 스킬","current_value":35,"simulated_value":78,"change_percent":122.9,"impact_level":"positive","explanation":"미디어 제작 기술 강화"}]',
 '창작 워크숍 참여와 미디어 제작 실습을 권장합니다.'),

-- arts × opportunity
('arts', 'opportunity',
 '[{"name":"competitions","current_value":"0","simulated_value":"3회","impact_description":"공모전 참여"},{"name":"exhibition","current_value":"미참여","simulated_value":"개인전","impact_description":"전시회 개최"}]',
 '[{"metric_name":"포트폴리오","current_value":25,"simulated_value":88,"change_percent":252.0,"impact_level":"positive","explanation":"공모전/전시회로 포트폴리오 대폭 강화"},{"metric_name":"인지도","current_value":10,"simulated_value":75,"change_percent":650.0,"impact_level":"positive","explanation":"작품 활동으로 인지도 향상"}]',
 '작품 공모전/전시회에 적극 참여하여 포트폴리오를 강화하세요.'),

-- science × career_path
('science', 'career_path',
 '[{"name":"target_path","current_value":"미정","simulated_value":"대학원/연구소","impact_description":"연구원 커리어 목표"},{"name":"research_paper","current_value":"없음","simulated_value":"1편","impact_description":"연구 논문 발표"}]',
 '[{"metric_name":"커리어 준비도","current_value":30,"simulated_value":74,"change_percent":146.7,"impact_level":"positive","explanation":"연구원 경로 확보"},{"metric_name":"연구 역량","current_value":35,"simulated_value":80,"change_percent":128.6,"impact_level":"positive","explanation":"연구 역량 강화"}]',
 '대학원 진학 준비와 연구 논문 발표 경험을 쌓으세요.'),

-- science × skill_development
('science', 'skill_development',
 '[{"name":"research_project","current_value":"미참여","simulated_value":"참여","impact_description":"연구 프로젝트 참여"},{"name":"statistical_analysis","current_value":"기초","simulated_value":"중급","impact_description":"통계분석 역량 향상"}]',
 '[{"metric_name":"실험 역량","current_value":40,"simulated_value":83,"change_percent":107.5,"impact_level":"positive","explanation":"연구 프로젝트로 실험 역량 향상"},{"metric_name":"데이터 분석","current_value":35,"simulated_value":80,"change_percent":128.6,"impact_level":"positive","explanation":"통계분석 역량 강화"}]',
 '실험 연구 프로젝트 참여와 통계분석 심화 학습을 권장합니다.'),

-- science × opportunity
('science', 'opportunity',
 '[{"name":"lab_intern","current_value":"미참여","simulated_value":"대학연구실","impact_description":"연구실 인턴"},{"name":"paper_contribution","current_value":"없음","simulated_value":"공동저자","impact_description":"논문 기여"}]',
 '[{"metric_name":"연구 역량","current_value":20,"simulated_value":88,"change_percent":340.0,"impact_level":"positive","explanation":"연구실 인턴으로 연구 역량 대폭 향상"},{"metric_name":"학술 네트워크","current_value":10,"simulated_value":78,"change_percent":680.0,"impact_level":"positive","explanation":"학계 네트워크 구축"}]',
 '대학 연구실 학부 인턴에 적극 참여하세요.'),

-- general × career_path
('general', 'career_path',
 '[{"name":"career_exploration","current_value":"미시작","simulated_value":"완료","impact_description":"진로 탐색 수행"},{"name":"skill_assessment","current_value":"미실시","simulated_value":"완료","impact_description":"역량 진단 실시"}]',
 '[{"metric_name":"커리어 준비도","current_value":25,"simulated_value":70,"change_percent":180.0,"impact_level":"positive","explanation":"진로 탐색으로 방향 설정"},{"metric_name":"자기 이해","current_value":30,"simulated_value":75,"change_percent":150.0,"impact_level":"positive","explanation":"역량 진단으로 자기 이해 향상"}]',
 '진로 탐색과 역량 진단을 먼저 수행하세요.'),

-- general × skill_development
('general', 'skill_development',
 '[{"name":"soft_skill_workshop","current_value":"미참여","simulated_value":"참여","impact_description":"소프트스킬 워크숍"},{"name":"additional_skills","current_value":"0","simulated_value":"리더십,팀워크","impact_description":"핵심 역량 개발"}]',
 '[{"metric_name":"의사소통","current_value":45,"simulated_value":82,"change_percent":82.2,"impact_level":"positive","explanation":"워크숍으로 의사소통 역량 향상"},{"metric_name":"문제해결","current_value":40,"simulated_value":78,"change_percent":95.0,"impact_level":"positive","explanation":"핵심 역량 강화"}]',
 '소프트스킬 워크숍 참여와 리더십/팀워크 역량 개발을 권장합니다.'),

-- general × opportunity
('general', 'opportunity',
 '[{"name":"exchange_program","current_value":"미참여","simulated_value":"교환학생","impact_description":"교환학생 프로그램"},{"name":"language_study","current_value":"기초","simulated_value":"중급","impact_description":"어학 학습"}]',
 '[{"metric_name":"글로벌 역량","current_value":20,"simulated_value":85,"change_percent":325.0,"impact_level":"positive","explanation":"교환학생으로 글로벌 역량 대폭 향상"},{"metric_name":"어학 능력","current_value":30,"simulated_value":80,"change_percent":166.7,"impact_level":"positive","explanation":"어학 능력 향상"}]',
 '해외 교환학생 프로그램 참여를 적극 권장합니다.');

-- 카테고리 매핑 (43번 스크립트와 동일 로직)
CREATE TEMP TABLE tmp_dept_cat_44 AS
SELECT
    d.department_cd,
    CASE
        WHEN d.department_nm ~ '의예|의학|의생명|의공학|의료IT|식의약' THEN 'medical'
        WHEN d.department_nm ~ '간호' THEN 'nursing'
        WHEN d.department_nm ~ '약학|제약' THEN 'pharmacy'
        WHEN d.department_nm ~ '물리치료|임상병리|작업치료|응급구조|보건|방사선|반려동물|헬스케어|스포츠|재활' THEN 'health'
        WHEN d.department_nm ~ '컴퓨터|AI|소프트웨어|반도체|전자|기계|전기|게임|멀티미디어|나노|건축|건설|소방|스마트물류|산업|로봇|융합기술|배터리|웹툰영상|정보통신' THEN 'engineering'
        WHEN d.department_nm ~ '경영|통상|MBA' THEN 'business'
        WHEN d.department_nm ~ '법학|경찰|행정' THEN 'law_admin'
        WHEN d.department_nm ~ '교육|상담|사회복지|발달|특수교육|유아' THEN 'education'
        WHEN d.department_nm ~ '어문|인문|역사|문화콘텐츠|문화유산|차문화|통일|영어영문' THEN 'humanities'
        WHEN d.department_nm ~ '음악|디자인|미디어|공연|영상' THEN 'arts'
        WHEN d.department_nm ~ '생명과학|화학|통계|환경|신소재' THEN 'science'
        ELSE 'general'
    END AS category
FROM tb_department d;

-- UPDATE: base_state를 {"variables": [...]} 형식으로 변환
UPDATE tb_simulation_scenario ss
SET
    base_state = jsonb_build_object('variables', (st.variables_json)::jsonb),
    predicted_outcomes = jsonb_build_object(
        'results', (st.results_json)::jsonb,
        'recommendation', st.recommendation,
        'ai_analysis', null
    ),
    upd_user_id = 'FIX_44',
    upd_dt = NOW()
FROM tb_student s
JOIN tmp_dept_cat_44 dc ON s.department_cd = dc.department_cd
JOIN tmp_sim_transform st ON dc.category = st.category
WHERE ss.student_id = s.student_id
  AND ss.scenario_type = st.scenario_type
  AND ss.ins_user_id = 'BULK_FIX';

DROP TABLE IF EXISTS tmp_sim_transform;
DROP TABLE IF EXISTS tmp_dept_cat_44;

DO $$ BEGIN RAISE NOTICE 'Part 4 완료: 시뮬레이션 시나리오 JSONB 재구성'; END $$;

COMMIT;

-- =====================================================
-- 검증 쿼리 (수동 실행)
-- =====================================================

-- 1. 역할-스킬 매핑 확인
-- SELECT role_cd, count(*) FROM tb_role_skill_map WHERE ins_user_id = 'FIX_44' GROUP BY role_cd ORDER BY role_cd;

-- 2. 스킬 그래프 노드 확인 (ROLE101 예시)
-- SELECT s.skill_cd, s.skill_nm, rsm.required_level, rsm.importance
-- FROM tb_skill s
-- JOIN tb_role_skill_map rsm ON s.skill_cd = rsm.skill_cd
-- WHERE rsm.role_cd = 'ROLE101' AND s.use_fg = 'Y';

-- 3. 스킬 관계 확인
-- SELECT * FROM tb_skill_relation WHERE ins_user_id = 'FIX_44' LIMIT 20;

-- 4. 위험 알림 확인
-- SELECT risk_type, severity, count(*) FROM tb_risk_alert WHERE ins_user_id = 'FIX_44' GROUP BY risk_type, severity ORDER BY risk_type, severity;

-- 5. 시뮬레이션 시나리오 JSONB 확인
-- SELECT scenario_type, base_state->'variables'->0->>'name' as first_var, predicted_outcomes->'results'->0->>'metric_name' as first_metric
-- FROM tb_simulation_scenario WHERE upd_user_id = 'FIX_44' LIMIT 10;
