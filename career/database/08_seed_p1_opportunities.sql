-- ============================================
-- IDINO Career - P1 Phase 8: Opportunities Seed Data
-- Opportunities, Recommendations, Applications
-- Created: 2026-01-07
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 1. Opportunities (湲곗〈 4媛?+ ?좉퇋 ~46媛?= 珥?50媛?
-- ============================================

DELETE FROM tb_opportunity_application WHERE ins_user_id = 'SEED_SCRIPT';
DELETE FROM tb_opportunity_recommendation WHERE ins_user_id = 'SEED_SCRIPT';
DELETE FROM tb_opportunity WHERE ins_user_id = 'SEED_SCRIPT';

-- Internships (?명꽩??20媛?
INSERT INTO tb_opportunity (opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, tags, department_cds, competency_contributions, skill_contributions, ins_user_id, ins_dt) VALUES
('internship', 'LG?꾩옄 DX?쇳꽣 SW 媛쒕컻 ?명꽩', 'LG?꾩옄', '紐⑤컮??諛?IoT ?뚮옯??媛쒕컻 ?명꽩?? ?ㅼ젣 ?쒗뭹 媛쒕컻??李몄뿬', '{"min_gpa": 3.2, "skills": ["Java", "Android"], "grade": [3, 4]}', '{"salary": "??250留뚯썝", "meal": true, "certificate": true}', '2025-04-01', '2025-04-30', '2025-07-01', '2025-08-31', '?쒖슱?밸퀎???곷벑?ш뎄', FALSE, 10, 'open', ARRAY['SW媛쒕컻', '紐⑤컮??, 'IoT'], ARRAY['DEPT001', 'DEPT002', 'DEPT003'], '{"COMP001": 0.4, "COMP003": 0.3}', '{"SKL002": 0.5, "SKL003": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '移댁뭅???쒕쾭 媛쒕컻 ?명꽩', '移댁뭅??, '移댁뭅???쒕퉬??諛깆뿏??媛쒕컻 ?명꽩. Spring Boot, Kotlin 湲곕컲', '{"min_gpa": 3.5, "skills": ["Java", "Spring"], "grade": [3, 4]}', '{"salary": "??300留뚯썝", "meal": true, "housing": true}', '2025-05-01', '2025-05-31', '2025-07-01', '2025-08-31', '寃쎄린???깅궓??遺꾨떦援?, FALSE, 15, 'open', ARRAY['諛깆뿏??, 'Java', 'Spring'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.5, "COMP002": 0.3}', '{"SKL002": 0.6, "SKL004": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '?ㅼ씠踰?AI Lab ?곌뎄 ?명꽩', '?ㅼ씠踰?, 'NLP/CV ?곌뎄 ?명꽩. 理쒖떊 AI ?곌뎄??李몄뿬', '{"min_gpa": 3.7, "skills": ["Python", "PyTorch", "ML"], "grade": [3, 4]}', '{"salary": "??350留뚯썝", "research_support": true}', '2025-03-15', '2025-04-15', '2025-06-01', '2025-08-31', '寃쎄린???깅궓??遺꾨떦援?, TRUE, 8, 'open', ARRAY['AI', 'ML', 'NLP', '?곌뎄'], ARRAY['DEPT001', 'DEPT013'], '{"COMP001": 0.6, "COMP002": 0.3}', '{"SKL005": 0.5, "SKL006": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', 'SK?붾젅肄?AI 媛쒕컻 ?명꽩', 'SK?붾젅肄?, 'AI 湲곕컲 ?듭떊 ?쒕퉬??媛쒕컻 ?명꽩??, '{"min_gpa": 3.3, "skills": ["Python", "TensorFlow"], "grade": [3, 4]}', '{"salary": "??280留뚯썝", "meal": true}', '2025-04-15', '2025-05-15', '2025-07-01', '2025-08-31', '?쒖슱?밸퀎??以묎뎄', FALSE, 12, 'open', ARRAY['AI', '?듭떊', 'Python'], ARRAY['DEPT001', 'DEPT003'], '{"COMP001": 0.4, "COMP002": 0.3}', '{"SKL001": 0.5, "SKL005": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '?꾨??먮룞李?SW ?명꽩', '?꾨??먮룞李?, '?먯쑉二쇳뻾/而ㅻ꽖?곕뱶移?SW 媛쒕컻 ?명꽩', '{"min_gpa": 3.4, "skills": ["C++", "Python"], "grade": [3, 4]}', '{"salary": "??270留뚯썝", "housing": true}', '2025-05-01', '2025-05-31', '2025-07-15', '2025-09-15', '寃쎄린???붿꽦??, FALSE, 20, 'open', ARRAY['?먯쑉二쇳뻾', 'SW媛쒕컻', '?먮룞李?], ARRAY['DEPT001', 'DEPT003', 'DEPT004'], '{"COMP001": 0.5, "COMP002": 0.3}', '{"SKL001": 0.4, "SKL009": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '荑좏뙜 ?곗씠??遺꾩꽍 ?명꽩', '荑좏뙜', '?댁빱癒몄뒪 ?곗씠??遺꾩꽍 諛?鍮꾩쫰?덉뒪 ?몄궗?댄듃 ?꾩텧', '{"min_gpa": 3.3, "skills": ["SQL", "Python", "Statistics"], "grade": [3, 4]}', '{"salary": "??290留뚯썝", "meal": true}', '2025-04-01', '2025-04-30', '2025-06-15', '2025-08-15', '?쒖슱?밸퀎???≫뙆援?, FALSE, 8, 'open', ARRAY['?곗씠?곕텇??, 'SQL', 'Python'], ARRAY['DEPT001', 'DEPT013', 'DEPT014'], '{"COMP001": 0.4, "COMP002": 0.4}', '{"SKL004": 0.5, "SKL007": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '?좎뒪 ?꾨줎?몄뿏???명꽩', '?좎뒪', 'React 湲곕컲 湲덉쑖 ?쒕퉬???꾨줎?몄뿏??媛쒕컻', '{"min_gpa": 3.4, "skills": ["JavaScript", "React"], "grade": [3, 4]}', '{"salary": "??320留뚯썝", "meal": true}', '2025-05-15', '2025-06-15', '2025-07-01', '2025-08-31', '?쒖슱?밸퀎??媛뺣궓援?, TRUE, 10, 'open', ARRAY['?꾨줎?몄뿏??, 'React', '??뚰겕'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.4, "COMP002": 0.3}', '{"SKL003": 0.6, "SKL001": 0.2}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '諛곕떖?섎?議??쒕쾭 ?명꽩', '?곗븘?쒗삎?쒕뱾', '?洹쒕え ?몃옒??泥섎━ 諛깆뿏???쒖뒪??媛쒕컻', '{"min_gpa": 3.3, "skills": ["Java", "Spring", "AWS"], "grade": [3, 4]}', '{"salary": "??300留뚯썝", "meal": true, "books": true}', '2025-04-01', '2025-05-01', '2025-06-15', '2025-08-15', '?쒖슱?밸퀎???≫뙆援?, TRUE, 12, 'open', ARRAY['諛깆뿏??, 'Java', '?洹쒕え?쒖뒪??], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.5, "COMP002": 0.3}', '{"SKL002": 0.5, "SKL008": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '?쇱씤 ?뚮옯??媛쒕컻 ?명꽩', '?쇱씤?뚮윭??, '湲濡쒕쾶 硫붿떊? ?뚮옯??媛쒕컻 李몄뿬', '{"min_gpa": 3.5, "skills": ["Java", "Kotlin", "Spring"], "grade": [3, 4]}', '{"salary": "??310留뚯썝", "japanese_class": true}', '2025-05-01', '2025-06-01', '2025-07-01', '2025-08-31', '寃쎄린???깅궓??遺꾨떦援?, FALSE, 15, 'open', ARRAY['?뚮옯??, 'Java', '湲濡쒕쾶'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.5, "COMP005": 0.2}', '{"SKL002": 0.5, "SKL014": 0.2}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '?붿뵪?뚰봽??寃뚯엫 AI ?명꽩', '?붿뵪?뚰봽??, '寃뚯엫 AI 諛?NPC ?됰룞 紐⑤뜽留??곌뎄', '{"min_gpa": 3.4, "skills": ["Python", "ML", "Game"], "grade": [3, 4]}', '{"salary": "??280留뚯썝", "game_benefits": true}', '2025-06-01', '2025-06-30', '2025-08-01', '2025-10-31', '寃쎄린???깅궓??遺꾨떦援?, FALSE, 6, 'open', ARRAY['寃뚯엫AI', 'ML', '寃뚯엫媛쒕컻'], ARRAY['DEPT001'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL005": 0.5, "SKL001": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '?쇱꽦?꾩옄 諛섎룄泥?SW ?명꽩', '?쇱꽦?꾩옄', '諛섎룄泥??ㅺ퀎 ?먮룞??諛?遺꾩꽍 ?꾧뎄 媛쒕컻', '{"min_gpa": 3.5, "skills": ["Python", "C++"], "grade": [3, 4]}', '{"salary": "??280留뚯썝", "housing": true}', '2025-04-15', '2025-05-15', '2025-07-01', '2025-08-31', '寃쎄린???붿꽦??, FALSE, 25, 'open', ARRAY['諛섎룄泥?, 'SW媛쒕컻', 'EDA'], ARRAY['DEPT001', 'DEPT003'], '{"COMP001": 0.5, "COMP002": 0.3}', '{"SKL001": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', 'SK?섏씠?됱뒪 ?곗씠???명꽩', 'SK?섏씠?됱뒪', '?쒖“ ?곗씠??遺꾩꽍 諛??덉쭏 ?덉륫 紐⑤뜽 媛쒕컻', '{"min_gpa": 3.4, "skills": ["Python", "SQL", "Statistics"], "grade": [3, 4]}', '{"salary": "??270留뚯썝", "housing": true}', '2025-05-01', '2025-05-31', '2025-07-15', '2025-09-15', '寃쎄린???댁쿇??, FALSE, 10, 'open', ARRAY['?곗씠?곕텇??, '?쒖“', 'Python'], ARRAY['DEPT001', 'DEPT006', 'DEPT013'], '{"COMP001": 0.4, "COMP002": 0.4}', '{"SKL001": 0.4, "SKL007": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', 'KB援?????IT ?명꽩', 'KB援?????, '?붿???湲덉쑖 ?쒕퉬??媛쒕컻 諛??댁쁺', '{"min_gpa": 3.3, "skills": ["Java"], "grade": [3, 4]}', '{"salary": "??240留뚯썝", "meal": true}', '2025-06-01', '2025-06-30', '2025-07-15', '2025-09-15', '?쒖슱?밸퀎??以묎뎄', FALSE, 20, 'open', ARRAY['湲덉쑖IT', 'Java', '?붿??멸툑??], ARRAY['DEPT001', 'DEPT014'], '{"COMP001": 0.3, "COMP004": 0.3}', '{"SKL002": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '濡?뜲?뺣낫?듭떊 ?명꽩', '濡?뜲?뺣낫?듭떊', '?좏넻/臾쇰쪟 IT ?쒖뒪??媛쒕컻', '{"min_gpa": 3.0, "skills": ["Java", "Oracle"], "grade": [3, 4]}', '{"salary": "??230留뚯썝", "meal": true}', '2025-05-15', '2025-06-15', '2025-07-01', '2025-08-31', '?쒖슱?밸퀎???≫뙆援?, FALSE, 15, 'open', ARRAY['?좏넻IT', 'Java', 'Oracle'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.3, "COMP003": 0.3}', '{"SKL002": 0.4, "SKL004": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '?ъ뒪肄봊CT ?대씪?곕뱶 ?명꽩', '?ъ뒪肄봊CT', '?대씪?곕뱶 ?명봽???댁쁺 諛??먮룞??, '{"min_gpa": 3.2, "skills": ["Linux", "AWS", "Python"], "grade": [3, 4]}', '{"salary": "??250留뚯썝", "certificate_support": true}', '2025-04-01', '2025-04-30', '2025-06-15', '2025-08-15', '寃쎄린???깅궓??, FALSE, 8, 'open', ARRAY['?대씪?곕뱶', 'DevOps', 'AWS'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.4, "COMP002": 0.3}', '{"SKL008": 0.6, "SKL001": 0.2}', 'SEED_SCRIPT', CURRENT_TIMESTAMP);

-- Contests (怨듬え??10媛?
INSERT INTO tb_opportunity (opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, tags, department_cds, competency_contributions, skill_contributions, ins_user_id, ins_dt) VALUES
('contest', 'TOPCIT 寃쎌쭊???, '?뺣낫?듭떊湲고쉷?됯???, 'SW ??웾 ?됯? 諛?寃쎌쭊???, '{"grade": [2, 3, 4]}', '{"prize": "???500留뚯썝", "certificate": true}', '2025-03-01', '2025-04-30', '2025-05-15', '2025-05-15', '?꾧뎅', FALSE, 500, 'open', ARRAY['SW??웾', 'TOPCIT', '寃쎌쭊???], ARRAY['DEPT001', 'DEPT002', 'DEPT003'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL009": 0.5}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', '?쇱꽦 ?대㉫?뚰겕 ?쇰Ц???, '?쇱꽦?꾩옄', '????????곌뎄 ?쇰Ц 怨듬え??, '{"min_gpa": 3.5, "grade": [3, 4]}', '{"prize": "???3000留뚯썝", "internship": true}', '2025-09-01', '2025-11-30', '2026-01-15', '2026-02-15', '?⑤씪??, TRUE, 1000, 'open', ARRAY['?곌뎄', '?쇰Ц', '湲곗닠'], ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT010'], '{"COMP001": 0.6, "COMP002": 0.3}', '{"SKL009": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', '李쎌뾽寃쎌쭊???StartupCON', '以묒냼踰ㅼ쿂湲곗뾽遺', '??숈깮 李쎌뾽 ?꾩씠?붿뼱 寃쎌쭊???, '{"grade": [1, 2, 3, 4]}', '{"prize": "???2000留뚯썝", "incubating": true}', '2025-04-01', '2025-05-31', '2025-06-15', '2025-07-15', '?쒖슱', FALSE, 200, 'open', ARRAY['李쎌뾽', '?ㅽ??몄뾽', '?꾩씠?붿뼱'], ARRAY['DEPT014', 'DEPT001', 'DEPT002'], '{"COMP002": 0.4, "COMP003": 0.4}', '{"SKL013": 0.3, "SKL015": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', 'ACM-ICPC ?쒓뎅 ?덉꽑', 'ACM', '援?젣 ??숈깮 ?꾨줈洹몃옒諛?寃쎌쭊????쒓뎅 ?덉꽑', '{"skills": ["Algorithm"], "grade": [1, 2, 3, 4]}', '{"prize": "蹂몄꽑 吏꾩텧沅?, "travel_support": true}', '2025-09-01', '2025-09-30', '2025-10-15', '2025-10-15', '?쒖슱', FALSE, 300, 'open', ARRAY['?뚭퀬由ъ쬁', 'ICPC', '?꾨줈洹몃옒諛?], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.3, "COMP002": 0.6}', '{"SKL009": 0.7}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', '鍮낅뜲?댄꽣 遺꾩꽍 寃쎌쭊???, '?쒓뎅?곗씠?곗궛?낆쭊?μ썝', '?ㅼ젣 ?곗씠?곕? ?쒖슜??遺꾩꽍 寃쎌쭊???, '{"skills": ["Python", "SQL", "ML"], "grade": [2, 3, 4]}', '{"prize": "???1000留뚯썝", "certificate": true}', '2025-07-01', '2025-08-31', '2025-09-01', '2025-10-31', '?⑤씪??, TRUE, 400, 'open', ARRAY['鍮낅뜲?댄꽣', '?곗씠?곕텇??, 'ML'], ARRAY['DEPT001', 'DEPT013'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL007": 0.5, "SKL005": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', '?댁빱??Korea', '怨쇳븰湲곗닠?뺣낫?듭떊遺', '24?쒓컙 吏묒쨷 媛쒕컻 ?댁빱??, '{"grade": [1, 2, 3, 4]}', '{"prize": "???500留뚯썝", "networking": true}', '2025-05-01', '2025-05-31', '2025-06-20', '2025-06-21', '?쒖슱', FALSE, 150, 'open', ARRAY['?댁빱??, '媛쒕컻', '?묒뾽'], ARRAY['DEPT001', 'DEPT002', 'DEPT025'], '{"COMP002": 0.4, "COMP003": 0.4}', '{"SKL011": 0.4, "SKL009": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', 'UX/UI ?붿옄???댁썙??, '?쒓뎅?붿옄?몄쭊?μ썝', '?ъ슜??寃쏀뿕 以묒떖 ?붿옄??怨듬え??, '{"grade": [2, 3, 4]}', '{"prize": "???800留뚯썝", "exhibition": true}', '2025-04-01', '2025-06-30', '2025-07-15', '2025-08-15', '?쒖슱', TRUE, 200, 'open', ARRAY['UX', 'UI', '?붿옄??], ARRAY['DEPT025', 'DEPT002'], '{"COMP002": 0.4, "COMP003": 0.3}', '{"SKL009": 0.4, "SKL015": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', '留덉???怨듬え??, '??쒖긽怨듯쉶?섏냼', '釉뚮옖??留덉????꾨왂 怨듬え??, '{"grade": [2, 3, 4]}', '{"prize": "???500留뚯썝", "internship": true}', '2025-03-15', '2025-05-15', '2025-06-01', '2025-06-30', '?⑤씪??, TRUE, 300, 'open', ARRAY['留덉???, '釉뚮옖??, '?꾨왂'], ARRAY['DEPT014'], '{"COMP002": 0.3, "COMP003": 0.4}', '{"SKL010": 0.3, "SKL015": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', '湲덉쑖 ?꾩씠?붿뼱 怨듬え??, '湲덉쑖?꾩썝??, '??뚰겕 ?쒕퉬???꾩씠?붿뼱 怨듬え??, '{"grade": [3, 4]}', '{"prize": "???1000留뚯썝", "mentoring": true}', '2025-05-01', '2025-07-31', '2025-08-15', '2025-09-30', '?쒖슱', FALSE, 100, 'open', ARRAY['??뚰겕', '湲덉쑖', '?꾩씠?붿뼱'], ARRAY['DEPT014', 'DEPT001'], '{"COMP002": 0.5, "COMP003": 0.3}', '{"SKL009": 0.4, "SKL013": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', '?뺣낫蹂댄샇 CTF', '?쒓뎅?명꽣?룹쭊?μ썝', '?ъ씠踰꾨낫??Capture The Flag ???, '{"skills": ["Security", "Linux"], "grade": [2, 3, 4]}', '{"prize": "???300留뚯썝", "certificate": true}', '2025-08-01', '2025-09-15', '2025-10-01', '2025-10-02', '?쒖슱', FALSE, 100, 'open', ARRAY['蹂댁븞', 'CTF', '?댄궧'], ARRAY['DEPT001', 'DEPT003'], '{"COMP001": 0.4, "COMP002": 0.5}', '{"SKL009": 0.5}', 'SEED_SCRIPT', CURRENT_TIMESTAMP);

-- Labs/Research (?곌뎄??10媛?
INSERT INTO tb_opportunity (opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, tags, department_cds, competency_contributions, skill_contributions, ins_user_id, ins_dt) VALUES
('lab', 'AI?듯빀?곌뎄???숇??곌뎄??, 'AI?듯빀?숆낵', '?λ윭??湲곕컲 而댄벂??鍮꾩쟾 ?곌뎄', '{"min_gpa": 3.7, "skills": ["Python", "PyTorch"], "grade": [3, 4]}', '{"stipend": "??30留뚯썝", "paper_coauthor": true}', '2025-02-01', '2025-02-28', '2025-03-01', '2025-12-31', '援먮궡', FALSE, 3, 'open', ARRAY['AI', '?λ윭??, 'CV'], ARRAY['DEPT001'], '{"COMP001": 0.6, "COMP002": 0.3}', '{"SKL006": 0.5, "SKL001": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('lab', 'NLP ?곌뎄???숇??곌뎄??, '而댄벂?곌났?숆낵', '?먯뿰??泥섎━ 諛?????쒖뒪???곌뎄', '{"min_gpa": 3.6, "skills": ["Python", "NLP"], "grade": [3, 4]}', '{"stipend": "??25留뚯썝", "conference": true}', '2025-02-15', '2025-03-15', '2025-03-01', '2025-12-31', '援먮궡', TRUE, 2, 'open', ARRAY['NLP', '?먯뿰?댁쿂由?, '?곌뎄'], ARRAY['DEPT001'], '{"COMP001": 0.6, "COMP002": 0.3}', '{"SKL001": 0.4, "SKL005": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('lab', '?곗씠?곕쭏?대떇 ?곌뎄??, '?듦퀎?숆낵', '?듦퀎 湲곕컲 ?곗씠??遺꾩꽍 諛??덉륫 紐⑤뜽 ?곌뎄', '{"min_gpa": 3.5, "skills": ["R", "Python", "Statistics"], "grade": [3, 4]}', '{"stipend": "??20留뚯썝", "paper_coauthor": true}', '2025-03-01', '2025-03-31', '2025-04-01', '2025-12-31', '援먮궡', FALSE, 3, 'open', ARRAY['?곗씠?곕쭏?대떇', '?듦퀎', 'R'], ARRAY['DEPT013'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL007": 0.5}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('lab', '濡쒕큸怨듯븰 ?곌뎄??, '湲곌퀎怨듯븰怨?, '?곗뾽??濡쒕큸 ?쒖뼱 諛??먮룞???곌뎄', '{"min_gpa": 3.4, "skills": ["C++", "ROS"], "grade": [3, 4]}', '{"stipend": "??30留뚯썝", "equipment": true}', '2025-02-01', '2025-02-28', '2025-03-01', '2025-12-31', '援먮궡', FALSE, 2, 'open', ARRAY['濡쒕큸', '?먮룞??, 'ROS'], ARRAY['DEPT004', 'DEPT003'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL009": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('lab', '?뺣낫蹂댁븞 ?곌뎄??, '而댄벂?곌났?숆낵', '?뷀샇??諛??쒖뒪??蹂댁븞 ?곌뎄', '{"min_gpa": 3.6, "skills": ["C", "Security"], "grade": [3, 4]}', '{"stipend": "??25留뚯썝", "conference": true}', '2025-03-01', '2025-03-31', '2025-04-01', '2025-12-31', '援먮궡', FALSE, 2, 'open', ARRAY['蹂댁븞', '?뷀샇??, '?곌뎄'], ARRAY['DEPT001'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL009": 0.5}', 'SEED_SCRIPT', CURRENT_TIMESTAMP);

-- Projects (?꾨줈?앺듃 10媛?
INSERT INTO tb_opportunity (opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, tags, department_cds, competency_contributions, skill_contributions, ins_user_id, ins_dt) VALUES
('project', '?고븰?묐젰 罹≪뒪???꾨줈?앺듃', '?고븰?묐젰??, '湲곗뾽 ?곌퀎 ?ㅼ쟾 ?꾨줈?앺듃. ?ㅼ젣 鍮꾩쫰?덉뒪 臾몄젣 ?닿껐', '{"min_gpa": 3.0, "grade": [4]}', '{"stipend": "?꾨줈?앺듃??50留뚯썝", "certificate": true}', '2025-02-01', '2025-02-28', '2025-03-01', '2025-11-30', '援먮궡/湲곗뾽', TRUE, 30, 'open', ARRAY['罹≪뒪??, '?고븰?묐젰', '?꾨줈?앺듃'], ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT006'], '{"COMP002": 0.4, "COMP003": 0.4}', '{"SKL011": 0.4, "SKL013": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('project', '?ㅽ뵂?뚯뒪 而⑦듃由щ럭???꾩뭅?곕?', '?뺣낫?듭떊?곗뾽吏꾪씎??, '?ㅽ뵂?뚯뒪 ?꾨줈?앺듃 湲곗뿬 ?꾨줈洹몃옩', '{"skills": ["Git", "Python"], "grade": [2, 3, 4]}', '{"certificate": true, "mentoring": true}', '2025-05-01', '2025-06-30', '2025-07-01', '2025-10-31', '?⑤씪??, TRUE, 100, 'open', ARRAY['?ㅽ뵂?뚯뒪', 'Git', '?묒뾽'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.4, "COMP003": 0.4}', '{"SKL001": 0.3, "SKL011": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('project', '?ы쉶怨듯뿄 IT 遊됱궗 ?꾨줈?앺듃', '?ы쉶遊됱궗?쇳꽣', 'IT ?뚯쇅 怨꾩링???꾪븳 ?쒕퉬??媛쒕컻', '{"grade": [2, 3, 4]}', '{"certificate": true, "volunteer_hours": 40}', '2025-03-01', '2025-03-31', '2025-04-01', '2025-06-30', '援먮궡', FALSE, 20, 'open', ARRAY['遊됱궗', 'IT', '?ы쉶怨듯뿄'], ARRAY['DEPT001', 'DEPT002'], '{"COMP003": 0.5, "COMP004": 0.3}', '{"SKL011": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('project', 'AI ?ㅽ??몄뾽 MVP 媛쒕컻', '李쎌뾽吏?먯꽱??, '?덈퉬 李쎌뾽???AI ?쒗뭹 MVP 媛쒕컻 李몄뿬', '{"skills": ["Python", "ML"], "grade": [3, 4]}', '{"stipend": "??50留뚯썝", "equity_option": true}', '2025-04-01', '2025-04-30', '2025-05-01', '2025-08-31', '李쎌뾽蹂댁쑁?쇳꽣', TRUE, 10, 'open', ARRAY['?ㅽ??몄뾽', 'AI', 'MVP'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.4, "COMP002": 0.4}', '{"SKL005": 0.4, "SKL013": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('project', '?ㅻ쭏?몄틺?쇱뒪 ??媛쒕컻', '援먮Т泥?, '?숆탳 怨듭떇 紐⑤컮????湲곕뒫 媛쒕컻 李몄뿬', '{"skills": ["React", "Node.js"], "grade": [3, 4]}', '{"stipend": "?꾨줈?앺듃 100留뚯썝", "reference": true}', '2025-03-01', '2025-03-15', '2025-04-01', '2025-07-31', '援먮궡', TRUE, 5, 'open', ARRAY['紐⑤컮?쇱빋', 'React', '罹좏띁??], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.4, "COMP003": 0.3}', '{"SKL003": 0.5}', 'SEED_SCRIPT', CURRENT_TIMESTAMP);

-- Scholarships (?ν븰湲?5媛?
INSERT INTO tb_opportunity (opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, tags, department_cds, competency_contributions, skill_contributions, ins_user_id, ins_dt) VALUES
('scholarship', '?쇱꽦?꾩옄 誘몃옒?몄옱 ?ν븰湲?, '?쇱꽦?꾩옄', 'SW 遺꾩빞 ?곗닔 ?숈깮 ?ν븰湲?, '{"min_gpa": 3.8, "grade": [2, 3]}', '{"amount": "??500留뚯썝", "internship_priority": true}', '2025-02-01', '2025-02-28', '2025-03-01', '2026-02-28', '?대떦?놁쓬', TRUE, 20, 'open', ARRAY['?ν븰湲?, 'SW', '?쇱꽦'], ARRAY['DEPT001', 'DEPT002', 'DEPT003'], '{"COMP001": 0.3}', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('scholarship', 'Google Women Techmakers ?ν븰湲?, 'Google', '?ъ꽦 SW ?몄옱 ?≪꽦 ?ν븰湲?, '{"min_gpa": 3.5, "gender": "F", "grade": [2, 3]}', '{"amount": "300留뚯썝", "conference": true}', '2025-04-01', '2025-05-31', '2025-09-01', '2026-08-31', '?대떦?놁쓬', TRUE, 10, 'open', ARRAY['?ν븰湲?, '?ъ꽦', 'Google'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.2, "COMP005": 0.2}', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('scholarship', '援?? ?닿났怨??ν븰湲?, '?쒓뎅?ν븰?щ떒', '?닿났怨꾩뿴 ?곗닔 ?숈깮 吏??, '{"min_gpa": 3.5, "grade": [1, 2, 3, 4]}', '{"amount": "?꾩븸?깅줉湲?, "living_expense": true}', '2025-01-15', '2025-02-15', '2025-03-01', '2026-02-28', '?대떦?놁쓬', TRUE, 100, 'open', ARRAY['?ν븰湲?, '?닿났怨?, '援???ν븰'], ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT009', 'DEPT010', 'DEPT013'], '{"COMP001": 0.2}', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('scholarship', '?꾨??먮룞李?湲濡쒕쾶 由щ뜑???ν븰湲?, '?꾨??먮룞李?, '湲濡쒕쾶 由щ뜑 ?묒꽦 ?ν븰湲?, '{"min_gpa": 3.6, "skills": ["English"], "grade": [3, 4]}', '{"amount": "??400留뚯썝", "overseas_program": true}', '2025-03-01', '2025-04-30', '2025-06-01', '2026-05-31', '?대떦?놁쓬', TRUE, 15, 'open', ARRAY['?ν븰湲?, '湲濡쒕쾶', '?꾨?'], ARRAY['DEPT001', 'DEPT003', 'DEPT004', 'DEPT014'], '{"COMP005": 0.4}', '{"SKL014": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('scholarship', 'SW 以묒떖????깆쟻?곗닔 ?ν븰湲?, '?숆탳', 'SW以묒떖????ы븰???깆쟻 ?곗닔 ?ν븰湲?, '{"min_gpa": 4.0, "grade": [1, 2, 3, 4]}', '{"amount": "100留뚯썝"}', '2025-02-15', '2025-03-15', '2025-03-01', '2025-08-31', '?대떦?놁쓬', TRUE, 30, 'open', ARRAY['?ν븰湲?, 'SW以묒떖???, '?깆쟻?곗닔'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.2}', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP);

-- ============================================
-- 2. Opportunity Recommendations (~120 records)
-- ============================================

INSERT INTO tb_opportunity_recommendation (student_id, opportunity_id, match_score, match_reasons, status, recommended_at, ins_user_id, ins_dt)
SELECT
    s.student_id,
    o.opportunity_id,
    (60 + RANDOM() * 35)::DECIMAL(5,2),
    CASE
        WHEN o.opportunity_type = 'internship' THEN '["skill_match", "gpa_eligible", "grade_match"]'::JSONB
        WHEN o.opportunity_type = 'contest' THEN '["interest_match", "skill_match"]'::JSONB
        WHEN o.opportunity_type = 'lab' THEN '["gpa_eligible", "department_match", "research_interest"]'::JSONB
        WHEN o.opportunity_type = 'project' THEN '["skill_match", "availability"]'::JSONB
        ELSE '["department_match", "gpa_eligible"]'::JSONB
    END,
    CASE WHEN RANDOM() > 0.7 THEN 'viewed' WHEN RANDOM() > 0.4 THEN 'saved' ELSE 'recommended' END,
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '30 days'),
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    SELECT opportunity_id, opportunity_type
    FROM tb_opportunity
    WHERE ins_user_id = 'SEED_SCRIPT'
    ORDER BY RANDOM()
    LIMIT 3
) o
WHERE s.department_cd IN ('DEPT001', 'DEPT002', 'DEPT013', 'DEPT014')
ON CONFLICT (student_id, opportunity_id) DO NOTHING;

-- ============================================
-- 3. Opportunity Applications (~70 records)
-- ============================================

INSERT INTO tb_opportunity_application (student_id, opportunity_id, applied_at, status, cover_letter, attachments, reviewer_notes, decision_at, ins_user_id, ins_dt)
SELECT
    r.student_id,
    r.opportunity_id,
    r.recommended_at + INTERVAL '3 days',
    CASE
        WHEN RANDOM() > 0.8 THEN 'accepted'
        WHEN RANDOM() > 0.6 THEN 'under_review'
        WHEN RANDOM() > 0.3 THEN 'submitted'
        ELSE 'rejected'
    END,
    '?대떦 湲고쉶??吏?먰빀?덈떎. ?????웾怨??댁젙?쇰줈 醫뗭? 寃곌낵瑜?留뚮뱾?대궡寃좎뒿?덈떎.',
    '[{"name": "resume.pdf", "url": "/files/resume.pdf"}, {"name": "portfolio.pdf", "url": "/files/portfolio.pdf"}]'::JSONB,
    CASE WHEN RANDOM() > 0.5 THEN '?곗닔??吏?먯옄. 硫댁젒 ??? ELSE NULL END,
    CASE WHEN RANDOM() > 0.5 THEN r.recommended_at + INTERVAL '10 days' ELSE NULL END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_opportunity_recommendation r
WHERE r.ins_user_id = 'SEED_SCRIPT'
AND r.status IN ('saved', 'viewed')
AND RANDOM() > 0.4;

-- ============================================
-- Success message
-- ============================================
DO $$
DECLARE
    opp_count INT;
    rec_count INT;
    app_count INT;
BEGIN
    SELECT COUNT(*) INTO opp_count FROM tb_opportunity WHERE ins_user_id = 'SEED_SCRIPT';
    SELECT COUNT(*) INTO rec_count FROM tb_opportunity_recommendation WHERE ins_user_id = 'SEED_SCRIPT';
    SELECT COUNT(*) INTO app_count FROM tb_opportunity_application WHERE ins_user_id = 'SEED_SCRIPT';

    RAISE NOTICE '=== P1 Opportunities Seed Data Created ===';
    RAISE NOTICE 'tb_opportunity: % records', opp_count;
    RAISE NOTICE 'tb_opportunity_recommendation: % records', rec_count;
    RAISE NOTICE 'tb_opportunity_application: % records', app_count;
END $$;
