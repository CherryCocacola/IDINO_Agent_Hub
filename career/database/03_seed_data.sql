-- ============================================
-- IDINO Career Seed Data
-- ?숆탳, ?④낵??? ?숆낵, 援먯닔, 怨쇰ぉ, ?숈깮 湲곕낯 ?곗씠??-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 1. ?숆탳 ?뺣낫
-- ============================================
INSERT INTO tb_university (university_cd, university_nm, university_nm_en, address, website, use_fg, ins_user_id, ins_dt)
VALUES ('UNIV001', '?쒓뎅怨쇳븰湲곗닠??숆탳', 'Korea Science and Technology University', '?쒖슱?밸퀎??媛뺣궓援??뚰뿤?濡?123', 'https://www.kstu.ac.kr', 'Y', 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 2. ?④낵???(8媛?
-- ============================================
INSERT INTO tb_college (college_cd, university_cd, college_nm, college_nm_en, sort_order, ins_user_id, ins_dt) VALUES
('COL001', 'UNIV001', '怨듦낵???, 'College of Engineering', 1, 'SYSTEM', CURRENT_TIMESTAMP),
('COL002', 'UNIV001', '?먯뿰怨쇳븰???, 'College of Natural Sciences', 2, 'SYSTEM', CURRENT_TIMESTAMP),
('COL003', 'UNIV001', '寃쎌쁺???, 'College of Business', 3, 'SYSTEM', CURRENT_TIMESTAMP),
('COL004', 'UNIV001', '?몃Ц???, 'College of Humanities', 4, 'SYSTEM', CURRENT_TIMESTAMP),
('COL005', 'UNIV001', '?ы쉶怨쇳븰???, 'College of Social Sciences', 5, 'SYSTEM', CURRENT_TIMESTAMP),
('COL006', 'UNIV001', '?덉닠???, 'College of Arts', 6, 'SYSTEM', CURRENT_TIMESTAMP),
('COL007', 'UNIV001', '?섍낵???, 'College of Medicine', 7, 'SYSTEM', CURRENT_TIMESTAMP),
('COL008', 'UNIV001', '援먯쑁???, 'College of Education', 8, 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 3. ?숆낵 ?뺣낫 (30媛?
-- ============================================
INSERT INTO tb_department (department_cd, college_cd, department_nm, department_nm_en, graduation_credits, sort_order, ins_user_id, ins_dt) VALUES
-- 怨듦낵???(8媛?
('DEPT001', 'COL001', '而댄벂?곌났?숆낵', 'Computer Science and Engineering', 130, 1, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT002', 'COL001', '?뚰봽?몄썾?댄븰怨?, 'Software Engineering', 130, 2, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT003', 'COL001', '?꾩옄怨듯븰怨?, 'Electronics Engineering', 130, 3, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT004', 'COL001', '湲곌퀎怨듯븰怨?, 'Mechanical Engineering', 130, 4, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT005', 'COL001', '?뷀븰怨듯븰怨?, 'Chemical Engineering', 130, 5, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT006', 'COL001', '?곗뾽怨듯븰怨?, 'Industrial Engineering', 130, 6, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT007', 'COL001', '嫄댁텞怨듯븰怨?, 'Architectural Engineering', 140, 7, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT008', 'COL001', '?좎냼?ш났?숆낵', 'Materials Science and Engineering', 130, 8, 'SYSTEM', CURRENT_TIMESTAMP),
-- ?먯뿰怨쇳븰???(5媛?
('DEPT009', 'COL002', '?섑븰怨?, 'Mathematics', 120, 1, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT010', 'COL002', '臾쇰━?숆낵', 'Physics', 120, 2, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT011', 'COL002', '?뷀븰怨?, 'Chemistry', 120, 3, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT012', 'COL002', '?앸챸怨쇳븰怨?, 'Life Sciences', 120, 4, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT013', 'COL002', '?듦퀎?숆낵', 'Statistics', 120, 5, 'SYSTEM', CURRENT_TIMESTAMP),
-- 寃쎌쁺???(4媛?
('DEPT014', 'COL003', '寃쎌쁺?숆낵', 'Business Administration', 120, 1, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT015', 'COL003', '?뚭퀎?숆낵', 'Accounting', 120, 2, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT016', 'COL003', '援?젣?듭긽?숆낵', 'International Trade', 120, 3, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT017', 'COL003', '寃쎌젣?숆낵', 'Economics', 120, 4, 'SYSTEM', CURRENT_TIMESTAMP),
-- ?몃Ц???(4媛?
('DEPT018', 'COL004', '援?뼱援?Ц?숆낵', 'Korean Language and Literature', 120, 1, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT019', 'COL004', '?곸뼱?곷Ц?숆낵', 'English Language and Literature', 120, 2, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT020', 'COL004', '泥좏븰怨?, 'Philosophy', 120, 3, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT021', 'COL004', '??궗?숆낵', 'History', 120, 4, 'SYSTEM', CURRENT_TIMESTAMP),
-- ?ы쉶怨쇳븰???(3媛?
('DEPT022', 'COL005', '?ы쉶?숆낵', 'Sociology', 120, 1, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT023', 'COL005', '?щ━?숆낵', 'Psychology', 120, 2, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT024', 'COL005', '?됱젙?숆낵', 'Public Administration', 120, 3, 'SYSTEM', CURRENT_TIMESTAMP),
-- ?덉닠???(3媛?
('DEPT025', 'COL006', '?붿옄?명븰怨?, 'Design', 130, 1, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT026', 'COL006', '?뚯븙?숆낵', 'Music', 130, 2, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT027', 'COL006', '誘몄닠?숆낵', 'Fine Arts', 130, 3, 'SYSTEM', CURRENT_TIMESTAMP),
-- ?섍낵???(2媛?
('DEPT028', 'COL007', '?섏삁怨?, 'Pre-Medicine', 140, 1, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT029', 'COL007', '媛꾪샇?숆낵', 'Nursing', 140, 2, 'SYSTEM', CURRENT_TIMESTAMP),
-- 援먯쑁???(1媛?
('DEPT030', 'COL008', '援먯쑁?숆낵', 'Education', 130, 1, 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 4. 援먯닔 ?뺣낫 (25紐?
-- ============================================
INSERT INTO tb_professor (professor_cd, professor_nm, department_cd, email, position, specialty, ins_user_id, ins_dt) VALUES
-- 而댄벂?곌났?숆낵
('PROF001', '源?곸닔', 'DEPT001', 'yskim@kstu.ac.kr', '援먯닔', '?멸났吏?? 湲곌퀎?숈뒿', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF002', '?댁젙誘?, 'DEPT001', 'jmlee@kstu.ac.kr', '遺援먯닔', '?곗씠?곕쿋?댁뒪, 鍮낅뜲?댄꽣', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF003', '諛뺤꽌??, 'DEPT001', 'sypark@kstu.ac.kr', '議곌탳??, '而댄벂?곕퉬?? ?λ윭??, 'SYSTEM', CURRENT_TIMESTAMP),
-- ?뚰봽?몄썾?댄븰怨?('PROF004', '理쒖???, 'DEPT002', 'jhchoi@kstu.ac.kr', '援먯닔', '?뚰봽?몄썾?닿났?? ?대씪?곕뱶', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF005', '?뺣떎?', 'DEPT002', 'dejung@kstu.ac.kr', '遺援먯닔', '?밴컻諛? 紐⑤컮?쇱빋', 'SYSTEM', CURRENT_TIMESTAMP),
-- ?꾩옄怨듯븰怨?('PROF006', '?쒕???, 'DEPT003', 'mshan@kstu.ac.kr', '援먯닔', '諛섎룄泥? ?뚮줈?ㅺ퀎', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF007', '?ㅼ???, 'DEPT003', 'jhoh@kstu.ac.kr', '議곌탳??, '?듭떊?쒖뒪?? IoT', 'SYSTEM', CURRENT_TIMESTAMP),
-- 湲곌퀎怨듯븰怨?('PROF008', '媛뺤듅??, 'DEPT004', 'shkang@kstu.ac.kr', '援먯닔', '濡쒕큸怨듯븰, ?먮룞??, 'SYSTEM', CURRENT_TIMESTAMP),
('PROF009', '?ㅼ삁吏?, 'DEPT004', 'yjyoon@kstu.ac.kr', '遺援먯닔', '?댁뿭?? ?먮꼫吏', 'SYSTEM', CURRENT_TIMESTAMP),
-- 寃쎌쁺?숆낵
('PROF010', '?≫깭??, 'DEPT014', 'tysong@kstu.ac.kr', '援먯닔', '?꾨왂寃쎌쁺, 議곗쭅?됰룞', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF011', '?꾩닔吏?, 'DEPT014', 'sjlim@kstu.ac.kr', '遺援먯닔', '留덉??? ?뚮퉬?먰뻾??, 'SYSTEM', CURRENT_TIMESTAMP),
-- ?뚭퀎?숆낵
('PROF012', '議고쁽??, 'DEPT015', 'hwjo@kstu.ac.kr', '援먯닔', '?щТ?뚭퀎, ?몃Т?뚭퀎', 'SYSTEM', CURRENT_TIMESTAMP),
-- ?섑븰怨?('PROF013', '諛깆듅誘?, 'DEPT009', 'smbaek@kstu.ac.kr', '援먯닔', '?댁꽍?? ?꾩긽?섑븰', 'SYSTEM', CURRENT_TIMESTAMP),
-- 臾쇰━?숆낵
('PROF014', '?좊룞??, 'DEPT010', 'dhshin@kstu.ac.kr', '援먯닔', '?묒옄臾쇰━, ?낆옄臾쇰━', 'SYSTEM', CURRENT_TIMESTAMP),
-- ?뷀븰怨?('PROF015', '?좎???, 'DEPT011', 'jhyu@kstu.ac.kr', '遺援먯닔', '?좉린?뷀븰, 怨좊텇?먰솕??, 'SYSTEM', CURRENT_TIMESTAMP),
-- ?듦퀎?숆낵
('PROF016', '沅뚮룄??, 'DEPT013', 'dykwon@kstu.ac.kr', '援먯닔', '?듦퀎?대줎, ?곗씠?곕텇??, 'SYSTEM', CURRENT_TIMESTAMP),
-- ?щ━?숆낵
('PROF017', '臾몄???, 'DEPT023', 'jymoon@kstu.ac.kr', '遺援먯닔', '?몄??щ━, 諛쒕떖?щ━', 'SYSTEM', CURRENT_TIMESTAMP),
-- ?붿옄?명븰怨?('PROF018', '?덉꽭??, 'DEPT025', 'shan@kstu.ac.kr', '援먯닔', 'UX/UI?붿옄?? ?쒓컖?붿옄??, 'SYSTEM', CURRENT_TIMESTAMP),
-- ?앸챸怨쇳븰怨?('PROF019', '?⑸?吏', 'DEPT012', 'mjhwang@kstu.ac.kr', '議곌탳??, '遺꾩옄?앸Ъ?? ?좎쟾??, 'SYSTEM', CURRENT_TIMESTAMP),
-- ?곗뾽怨듯븰怨?('PROF020', '?쒖???, 'DEPT006', 'jhseo@kstu.ac.kr', '援먯닔', '?앹궛愿由? ?덉쭏寃쎌쁺', 'SYSTEM', CURRENT_TIMESTAMP),
-- ?뷀븰怨듯븰怨?('PROF021', '?묐???, 'DEPT005', 'mryang@kstu.ac.kr', '遺援먯닔', '怨듭젙?ㅺ퀎, 珥됰ℓ怨듯븰', 'SYSTEM', CURRENT_TIMESTAMP),
-- 寃쎌젣?숆낵
('PROF022', '?대룄??, 'DEPT017', 'dhlee@kstu.ac.kr', '援먯닔', '嫄곗떆寃쎌젣, 湲덉쑖寃쎌젣', 'SYSTEM', CURRENT_TIMESTAMP),
-- ?곸뼱?곷Ц?숆낵
('PROF023', '源?섏?', 'DEPT019', 'hekim@kstu.ac.kr', '遺援먯닔', '?곷?臾명븰, 鍮꾪룊?대줎', 'SYSTEM', CURRENT_TIMESTAMP),
-- 媛꾪샇?숆낵
('PROF024', '諛뺤냼??, 'DEPT029', 'sypark2@kstu.ac.kr', '援먯닔', '?깆씤媛꾪샇, ?묎툒媛꾪샇', 'SYSTEM', CURRENT_TIMESTAMP),
-- 援먯쑁?숆낵
('PROF025', '?뺥븳寃?, 'DEPT030', 'hkjung@kstu.ac.kr', '議곌탳??, '援먯쑁怨쇱젙, 援먯쑁怨듯븰', 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 5. ?숆린 ?뺣낫
-- ============================================
INSERT INTO tb_term (term_cd, term_nm, start_date, end_date, registration_start, registration_end, ins_user_id, ins_dt) VALUES
('2023-1', '2023?숇뀈??1?숆린', '2023-03-02', '2023-06-23', '2023-02-15', '2023-02-28', 'SYSTEM', CURRENT_TIMESTAMP),
('2023-2', '2023?숇뀈??2?숆린', '2023-09-01', '2023-12-22', '2023-08-15', '2023-08-31', 'SYSTEM', CURRENT_TIMESTAMP),
('2024-1', '2024?숇뀈??1?숆린', '2024-03-04', '2024-06-21', '2024-02-15', '2024-02-29', 'SYSTEM', CURRENT_TIMESTAMP),
('2024-2', '2024?숇뀈??2?숆린', '2024-09-02', '2024-12-20', '2024-08-15', '2024-08-31', 'SYSTEM', CURRENT_TIMESTAMP),
('2025-1', '2025?숇뀈??1?숆린', '2025-03-03', '2025-06-20', '2025-02-17', '2025-02-28', 'SYSTEM', CURRENT_TIMESTAMP),
('2025-2', '2025?숇뀈??2?숆린', '2025-09-01', '2025-12-19', '2025-08-18', '2025-08-29', 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 6. 怨쇰ぉ ?뺣낫 (55媛?
-- ============================================
INSERT INTO tb_course (course_cd, course_nm, department_cd, credits, course_type, course_category, grade_level, description, ins_user_id, ins_dt) VALUES
-- 而댄벂?곌났?숆낵 ?꾧났 (12怨쇰ぉ)
('CS101', '?꾨줈洹몃옒諛띻린珥?, 'DEPT001', 3, '?꾧났?꾩닔', '湲곗큹', 1, 'Python???댁슜???꾨줈洹몃옒諛?湲곗큹 ?숈뒿', 'SYSTEM', CURRENT_TIMESTAMP),
('CS102', '而댄벂?곌뎄議?, 'DEPT001', 3, '?꾧났?꾩닔', '湲곗큹', 1, '而댄벂???섎뱶?⑥뼱 援ъ“? ?숈옉 ?먮━', 'SYSTEM', CURRENT_TIMESTAMP),
('CS201', '?먮즺援ъ“', 'DEPT001', 3, '?꾧났?꾩닔', '湲곗큹', 2, '?⑥쑉?곸씤 ?곗씠????κ낵 泥섎━ 援ъ“', 'SYSTEM', CURRENT_TIMESTAMP),
('CS202', '?뚭퀬由ъ쬁', 'DEPT001', 3, '?꾧났?꾩닔', '湲곗큹', 2, '臾몄젣 ?닿껐???꾪븳 ?뚭퀬由ъ쬁 ?ㅺ퀎? 遺꾩꽍', 'SYSTEM', CURRENT_TIMESTAMP),
('CS203', '?댁쁺泥댁젣', 'DEPT001', 3, '?꾧났?꾩닔', '?ы솕', 2, '?댁쁺泥댁젣??援ъ“? ?먮━', 'SYSTEM', CURRENT_TIMESTAMP),
('CS301', '?곗씠?곕쿋?댁뒪', 'DEPT001', 3, '?꾧났?꾩닔', '?ы솕', 3, '愿怨꾪삎 ?곗씠?곕쿋?댁뒪 ?ㅺ퀎? 援ы쁽', 'SYSTEM', CURRENT_TIMESTAMP),
('CS302', '?뚰봽?몄썾?닿났??, 'DEPT001', 3, '?꾧났?좏깮', '?ы솕', 3, '?뚰봽?몄썾??媛쒕컻 諛⑸쾿濡좉낵 ?꾨줈?앺듃 愿由?, 'SYSTEM', CURRENT_TIMESTAMP),
('CS303', '而댄벂?곕꽕?몄썙??, 'DEPT001', 3, '?꾧났?꾩닔', '?ы솕', 3, '?ㅽ듃?뚰겕 ?꾨줈?좎퐳怨??듭떊 ?먮━', 'SYSTEM', CURRENT_TIMESTAMP),
('CS401', '?멸났吏??, 'DEPT001', 3, '?꾧났?좏깮', '?묒슜', 4, '湲곌퀎?숈뒿怨??λ윭??湲곗큹', 'SYSTEM', CURRENT_TIMESTAMP),
('CS402', '鍮낅뜲?댄꽣遺꾩꽍', 'DEPT001', 3, '?꾧났?좏깮', '?묒슜', 4, '??⑸웾 ?곗씠??泥섎━? 遺꾩꽍', 'SYSTEM', CURRENT_TIMESTAMP),
('CS403', '罹≪뒪?ㅻ뵒?먯씤', 'DEPT001', 3, '?꾧났?꾩닔', '?ㅼ뒿', 4, '醫낇빀?ㅺ퀎 ?꾨줈?앺듃', 'SYSTEM', CURRENT_TIMESTAMP),
('CS404', '?뺣낫蹂댁븞', 'DEPT001', 3, '?꾧났?좏깮', '?묒슜', 4, '?뷀샇?숆낵 ?쒖뒪??蹂댁븞', 'SYSTEM', CURRENT_TIMESTAMP),
-- ?뚰봽?몄썾?댄븰怨?(8怨쇰ぉ)
('SW101', '?뱁봽濡쒓렇?섎컢', 'DEPT002', 3, '?꾧났?꾩닔', '湲곗큹', 1, 'HTML, CSS, JavaScript 湲곗큹', 'SYSTEM', CURRENT_TIMESTAMP),
('SW201', '媛앹껜吏?ν봽濡쒓렇?섎컢', 'DEPT002', 3, '?꾧났?꾩닔', '湲곗큹', 2, 'Java瑜??댁슜??媛앹껜吏???ㅺ퀎', 'SYSTEM', CURRENT_TIMESTAMP),
('SW301', '紐⑤컮?쇱빋媛쒕컻', 'DEPT002', 3, '?꾧났?좏깮', '?ы솕', 3, 'Android/iOS ??媛쒕컻', 'SYSTEM', CURRENT_TIMESTAMP),
('SW302', '?대씪?곕뱶而댄벂??, 'DEPT002', 3, '?꾧났?좏깮', '?ы솕', 3, 'AWS, GCP 湲곕컲 ?대씪?곕뱶 ?쒕퉬??, 'SYSTEM', CURRENT_TIMESTAMP),
('SW303', '?곕툕?듭뒪', 'DEPT002', 3, '?꾧났?좏깮', '?묒슜', 3, 'CI/CD? ?명봽???먮룞??, 'SYSTEM', CURRENT_TIMESTAMP),
('SW401', '??ㅽ깮媛쒕컻', 'DEPT002', 3, '?꾧났?좏깮', '?묒슜', 4, '?꾨줎?몄뿏?쒖? 諛깆뿏???듯빀 媛쒕컻', 'SYSTEM', CURRENT_TIMESTAMP),
('SW402', '留덉씠?щ줈?쒕퉬?ㅼ븘?ㅽ뀓泥?, 'DEPT002', 3, '?꾧났?좏깮', '?묒슜', 4, 'MSA ?ㅺ퀎? 援ы쁽', 'SYSTEM', CURRENT_TIMESTAMP),
('SW403', 'AI?쒕퉬?ㅺ컻諛?, 'DEPT002', 3, '?꾧났?좏깮', '?묒슜', 4, 'AI 紐⑤뜽 ?쒕튃怨?MLOps', 'SYSTEM', CURRENT_TIMESTAMP),
-- ?꾩옄怨듯븰怨?(6怨쇰ぉ)
('EE101', '?꾧린?뚮줈', 'DEPT003', 3, '?꾧났?꾩닔', '湲곗큹', 1, '?꾧린?뚮줈 遺꾩꽍 湲곗큹', 'SYSTEM', CURRENT_TIMESTAMP),
('EE201', '?붿??몃끉由ъ꽕怨?, 'DEPT003', 3, '?꾧났?꾩닔', '湲곗큹', 2, '?붿????뚮줈 ?ㅺ퀎', 'SYSTEM', CURRENT_TIMESTAMP),
('EE301', '諛섎룄泥닿났??, 'DEPT003', 3, '?꾧났?꾩닔', '?ы솕', 3, '諛섎룄泥??뚯옄? 怨듭젙', 'SYSTEM', CURRENT_TIMESTAMP),
('EE302', '?듭떊?쒖뒪??, 'DEPT003', 3, '?꾧났?좏깮', '?ы솕', 3, '臾댁꽑?듭떊怨??좏샇泥섎━', 'SYSTEM', CURRENT_TIMESTAMP),
('EE401', '?꾨쿋?붾뱶?쒖뒪??, 'DEPT003', 3, '?꾧났?좏깮', '?묒슜', 4, '?꾨쿋?붾뱶 ?섎뱶?⑥뼱? ?뚰봽?몄썾??, 'SYSTEM', CURRENT_TIMESTAMP),
('EE402', 'IoT?쒖뒪??, 'DEPT003', 3, '?꾧났?좏깮', '?묒슜', 4, '?щЪ?명꽣???ㅺ퀎? 援ы쁽', 'SYSTEM', CURRENT_TIMESTAMP),
-- 寃쎌쁺?숆낵 (8怨쇰ぉ)
('BA101', '寃쎌쁺?숈썝濡?, 'DEPT014', 3, '?꾧났?꾩닔', '湲곗큹', 1, '寃쎌쁺?숈쓽 湲곕낯 媛쒕뀗怨??먮━', 'SYSTEM', CURRENT_TIMESTAMP),
('BA102', '?뚭퀎?먮━', 'DEPT014', 3, '?꾧났?꾩닔', '湲곗큹', 1, '?щТ?뚭퀎??湲곗큹', 'SYSTEM', CURRENT_TIMESTAMP),
('BA201', '留덉??낆썝濡?, 'DEPT014', 3, '?꾧났?꾩닔', '湲곗큹', 2, '留덉??낆쓽 湲곕낯 媛쒕뀗怨??꾨왂', 'SYSTEM', CURRENT_TIMESTAMP),
('BA202', '議곗쭅?됰룞濡?, 'DEPT014', 3, '?꾧났?좏깮', '?ы솕', 2, '議곗쭅 ???멸컙 ?됰룞???댄빐', 'SYSTEM', CURRENT_TIMESTAMP),
('BA301', '?щТ愿由?, 'DEPT014', 3, '?꾧났?꾩닔', '?ы솕', 3, '湲곗뾽 ?щТ ?섏궗寃곗젙', 'SYSTEM', CURRENT_TIMESTAMP),
('BA302', '?꾨왂寃쎌쁺', 'DEPT014', 3, '?꾧났?좏깮', '?ы솕', 3, '湲곗뾽 ?꾨왂 ?섎┰怨??ㅽ뻾', 'SYSTEM', CURRENT_TIMESTAMP),
('BA401', '寃쎌쁺?뺣낫?쒖뒪??, 'DEPT014', 3, '?꾧났?좏깮', '?묒슜', 4, 'IT瑜??쒖슜??寃쎌쁺 ?곸떊', 'SYSTEM', CURRENT_TIMESTAMP),
('BA402', '李쎌뾽寃쎌쁺', 'DEPT014', 3, '?꾧났?좏깮', '?묒슜', 4, '?ㅽ??몄뾽 李쎌뾽怨??댁쁺', 'SYSTEM', CURRENT_TIMESTAMP),
-- ?섑븰怨?(4怨쇰ぉ)
('MA101', '誘몄쟻遺꾪븰', 'DEPT009', 3, '?꾧났?꾩닔', '湲곗큹', 1, '?쇰???諛??ㅻ???誘몄쟻遺?, 'SYSTEM', CURRENT_TIMESTAMP),
('MA201', '?좏삎??섑븰', 'DEPT009', 3, '?꾧났?꾩닔', '湲곗큹', 2, '踰≫꽣怨듦컙怨??됰젹?대줎', 'SYSTEM', CURRENT_TIMESTAMP),
('MA301', '?뺣쪧濡?, 'DEPT009', 3, '?꾧났?좏깮', '?ы솕', 3, '?뺣쪧?대줎怨??묒슜', 'SYSTEM', CURRENT_TIMESTAMP),
('MA302', '?섏튂?댁꽍', 'DEPT009', 3, '?꾧났?좏깮', '?ы솕', 3, '?섏튂??臾몄젣?닿껐 諛⑸쾿', 'SYSTEM', CURRENT_TIMESTAMP),
-- ?듦퀎?숆낵 (4怨쇰ぉ)
('ST101', '?듦퀎?숆컻濡?, 'DEPT013', 3, '?꾧났?꾩닔', '湲곗큹', 1, '?듦퀎?숈쓽 湲곕낯 媛쒕뀗', 'SYSTEM', CURRENT_TIMESTAMP),
('ST201', '?섎━?듦퀎??, 'DEPT013', 3, '?꾧났?꾩닔', '?ы솕', 2, '?듦퀎?대줎???섎━??湲곗큹', 'SYSTEM', CURRENT_TIMESTAMP),
('ST301', '?뚭?遺꾩꽍', 'DEPT013', 3, '?꾧났?좏깮', '?ы솕', 3, '?뚭?紐⑦삎???대줎怨??묒슜', 'SYSTEM', CURRENT_TIMESTAMP),
('ST302', '?곗씠?곕쭏?대떇', 'DEPT013', 3, '?꾧났?좏깮', '?묒슜', 3, '?곗씠?곗뿉???⑦꽩 諛쒓껄', 'SYSTEM', CURRENT_TIMESTAMP),
-- 援먯뼇怨쇰ぉ (9怨쇰ぉ)
('GE101', '??숆??곌린', NULL, 2, '援먯뼇?꾩닔', '湲곗큹', 1, '?쇰━??湲?곌린 ?λ젰 諛곗뼇', 'SYSTEM', CURRENT_TIMESTAMP),
('GE102', '?곸뼱?뚰솕', NULL, 2, '援먯뼇?꾩닔', '湲곗큹', 1, '?ㅼ슜 ?곸뼱 ?뚰솕 ?λ젰', 'SYSTEM', CURRENT_TIMESTAMP),
('GE103', '李쎌쓽?곸궗怨?, NULL, 2, '援먯뼇?꾩닔', '湲곗큹', 1, '李쎌쓽??臾몄젣?닿껐 諛⑸쾿', 'SYSTEM', CURRENT_TIMESTAMP),
('GE201', '?쇰━?鍮꾪뙋?곸궗怨?, NULL, 2, '援먯뼇?좏깮', '?ы솕', 2, '?쇰━???ш퀬???⑥뼇', 'SYSTEM', CURRENT_TIMESTAMP),
('GE202', '?꾨??ы쉶??ㅻ━', NULL, 2, '援먯뼇?좏깮', '?ы솕', 2, '?꾨? ?ы쉶???ㅻ━??臾몄젣', 'SYSTEM', CURRENT_TIMESTAMP),
('GE203', '怨쇳븰湲곗닠怨쇱궗??, NULL, 2, '援먯뼇?좏깮', '?ы솕', 2, '怨쇳븰湲곗닠???ы쉶???곹뼢', 'SYSTEM', CURRENT_TIMESTAMP),
('GE301', '由щ뜑??낵??뚰겕', NULL, 2, '援먯뼇?좏깮', '?묒슜', 3, '?④낵?곸씤 由щ뜑??낵 ?묒뾽', 'SYSTEM', CURRENT_TIMESTAMP),
('GE302', '湲濡쒕쾶而ㅻ??덉??댁뀡', NULL, 2, '援먯뼇?좏깮', '?묒슜', 3, '援?젣???섏궗?뚰넻 ?λ젰', 'SYSTEM', CURRENT_TIMESTAMP),
('GE303', '吏꾨줈?ㅺ퀎?痍⑥뾽?꾨왂', NULL, 2, '援먯뼇?좏깮', '?묒슜', 3, '吏꾨줈 ?먯깋怨?痍⑥뾽 以鍮?, 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 7. ?좎닔怨쇰ぉ ?뺣낫
-- ============================================
INSERT INTO tb_prerequisite (course_cd, prerequisite_course_cd, prerequisite_type, ins_user_id, ins_dt) VALUES
('CS201', 'CS101', 'required', 'SYSTEM', CURRENT_TIMESTAMP),
('CS202', 'CS201', 'required', 'SYSTEM', CURRENT_TIMESTAMP),
('CS203', 'CS102', 'required', 'SYSTEM', CURRENT_TIMESTAMP),
('CS301', 'CS201', 'required', 'SYSTEM', CURRENT_TIMESTAMP),
('CS303', 'CS203', 'recommended', 'SYSTEM', CURRENT_TIMESTAMP),
('CS401', 'CS202', 'required', 'SYSTEM', CURRENT_TIMESTAMP),
('CS402', 'CS301', 'required', 'SYSTEM', CURRENT_TIMESTAMP),
('CS403', 'CS302', 'recommended', 'SYSTEM', CURRENT_TIMESTAMP),
('SW201', 'SW101', 'required', 'SYSTEM', CURRENT_TIMESTAMP),
('SW301', 'SW201', 'required', 'SYSTEM', CURRENT_TIMESTAMP),
('SW401', 'SW301', 'recommended', 'SYSTEM', CURRENT_TIMESTAMP),
('EE201', 'EE101', 'required', 'SYSTEM', CURRENT_TIMESTAMP),
('EE301', 'EE201', 'required', 'SYSTEM', CURRENT_TIMESTAMP),
('BA301', 'BA102', 'required', 'SYSTEM', CURRENT_TIMESTAMP),
('MA201', 'MA101', 'required', 'SYSTEM', CURRENT_TIMESTAMP),
('ST201', 'ST101', 'required', 'SYSTEM', CURRENT_TIMESTAMP),
('ST301', 'ST201', 'required', 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 8. 援먯닔-?대떦怨쇰ぉ 留ㅽ븨
-- ============================================
INSERT INTO tb_professor_course (professor_cd, course_cd, is_primary, ins_user_id, ins_dt) VALUES
('PROF001', 'CS401', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF001', 'CS402', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF002', 'CS301', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF002', 'CS402', 'N', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF003', 'CS401', 'N', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF004', 'CS302', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF004', 'SW302', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF005', 'SW101', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF005', 'SW301', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF006', 'EE301', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF007', 'EE302', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF007', 'EE402', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF010', 'BA302', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF011', 'BA201', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF012', 'BA102', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF013', 'MA101', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF013', 'MA201', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF016', 'ST101', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF016', 'ST201', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('PROF016', 'ST302', 'Y', 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 9. ??웾 ?뺤쓽
-- ============================================
INSERT INTO tb_competency (competency_cd, competency_nm, competency_nm_en, definition, category, weight, max_score, ins_user_id, ins_dt) VALUES
('COMP001', '?꾨Ц吏??, 'Professional Knowledge', '?꾧났 遺꾩빞?????源딆? ?댄빐? 理쒖떊 吏??, '?꾨Ц??, 25.00, 100, 'SYSTEM', CURRENT_TIMESTAMP),
('COMP002', '臾몄젣?닿껐', 'Problem Solving', '蹂듭옟??臾몄젣瑜?遺꾩꽍?섍퀬 李쎌쓽?곸쑝濡??닿껐?섎뒗 ?λ젰', '??웾', 20.00, 100, 'SYSTEM', CURRENT_TIMESTAMP),
('COMP003', '?뚰넻?묒뾽', 'Communication & Collaboration', '?④낵?곸씤 ?섏궗?뚰넻怨???뚰겕 ?λ젰', '??웾', 20.00, 100, 'SYSTEM', CURRENT_TIMESTAMP),
('COMP004', '吏곸뾽?ㅻ━', 'Professional Ethics', '梨낆엫媛먭낵 ?ㅻ━?섏떇??媛뽰텣 ?쒕룄', '?쒕룄', 15.00, 100, 'SYSTEM', CURRENT_TIMESTAMP),
('COMP005', '湲濡쒕쾶??웾', 'Global Competency', '?멸뎅???λ젰怨?援?젣???쒖빞', '??웾', 10.00, 100, 'SYSTEM', CURRENT_TIMESTAMP),
('COMP006', '?먭린二쇰룄?숈뒿', 'Self-directed Learning', '?ㅼ뒪濡??숈뒿?섍퀬 ?깆옣?섎뒗 ?λ젰', '?쒕룄', 10.00, 100, 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 10. ?ㅽ궗 ?뺤쓽
-- ============================================
INSERT INTO tb_skill (skill_cd, skill_nm, skill_nm_en, synonyms, category, difficulty, ins_user_id, ins_dt) VALUES
('SKL001', 'Python', 'Python', ARRAY['?뚯씠??], 'technical', 2, 'SYSTEM', CURRENT_TIMESTAMP),
('SKL002', 'Java', 'Java', ARRAY['?먮컮'], 'technical', 3, 'SYSTEM', CURRENT_TIMESTAMP),
('SKL003', 'JavaScript', 'JavaScript', ARRAY['?먮컮?ㅽ겕由쏀듃', 'JS'], 'technical', 2, 'SYSTEM', CURRENT_TIMESTAMP),
('SKL004', 'SQL', 'SQL', ARRAY['?곗씠?곕쿋?댁뒪'], 'technical', 2, 'SYSTEM', CURRENT_TIMESTAMP),
('SKL005', 'Machine Learning', 'Machine Learning', ARRAY['湲곌퀎?숈뒿', 'ML'], 'technical', 4, 'SYSTEM', CURRENT_TIMESTAMP),
('SKL006', 'Deep Learning', 'Deep Learning', ARRAY['?λ윭??, 'DL'], 'technical', 5, 'SYSTEM', CURRENT_TIMESTAMP),
('SKL007', 'Data Analysis', 'Data Analysis', ARRAY['?곗씠?곕텇??], 'technical', 3, 'SYSTEM', CURRENT_TIMESTAMP),
('SKL008', 'Cloud Computing', 'Cloud Computing', ARRAY['?대씪?곕뱶', 'AWS', 'GCP'], 'technical', 4, 'SYSTEM', CURRENT_TIMESTAMP),
('SKL009', 'Problem Solving', 'Problem Solving', ARRAY['臾몄젣?닿껐'], 'soft', 3, 'SYSTEM', CURRENT_TIMESTAMP),
('SKL010', 'Communication', 'Communication', ARRAY['?섏궗?뚰넻', '而ㅻ??덉??댁뀡'], 'soft', 2, 'SYSTEM', CURRENT_TIMESTAMP),
('SKL011', 'Teamwork', 'Teamwork', ARRAY['??뚰겕', '?묒뾽'], 'soft', 2, 'SYSTEM', CURRENT_TIMESTAMP),
('SKL012', 'Leadership', 'Leadership', ARRAY['由щ뜑??], 'soft', 4, 'SYSTEM', CURRENT_TIMESTAMP),
('SKL013', 'Project Management', 'Project Management', ARRAY['?꾨줈?앺듃愿由?, 'PM'], 'soft', 4, 'SYSTEM', CURRENT_TIMESTAMP),
('SKL014', 'English', 'English', ARRAY['?곸뼱'], 'domain', 3, 'SYSTEM', CURRENT_TIMESTAMP),
('SKL015', 'Presentation', 'Presentation', ARRAY['?꾨젅?좏뀒?댁뀡', '諛쒗몴'], 'soft', 3, 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 11. 吏곷Т ?뺤쓽
-- ============================================
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, worknet_code, industry, description, ins_user_id, ins_dt) VALUES
('ROLE001', '諛깆뿏?쒓컻諛쒖옄', 'Backend Developer', '13301', 'IT/?뚰봽?몄썾??, '?쒕쾭 ?ъ씠??媛쒕컻 諛?API ?ㅺ퀎', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE002', '?꾨줎?몄뿏?쒓컻諛쒖옄', 'Frontend Developer', '13301', 'IT/?뚰봽?몄썾??, '???꾨줎?몄뿏??媛쒕컻 諛?UI 援ы쁽', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE003', '?곗씠?곕텇?앷?', 'Data Analyst', '13302', 'IT/?뚰봽?몄썾??, '?곗씠??遺꾩꽍 諛??몄궗?댄듃 ?꾩텧', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE004', '?곗씠?곗뿏吏?덉뼱', 'Data Engineer', '13302', 'IT/?뚰봽?몄썾??, '?곗씠???뚯씠?꾨씪??援ъ텞 諛?愿由?, 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE005', 'AI?붿??덉뼱', 'AI Engineer', '13303', 'IT/?뚰봽?몄썾??, 'AI/ML 紐⑤뜽 媛쒕컻 諛??쒕퉬?ㅽ솕', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE006', 'DevOps?붿??덉뼱', 'DevOps Engineer', '13304', 'IT/?뚰봽?몄썾??, '?명봽???먮룞??諛?CI/CD 援ъ텞', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE007', '??ㅽ깮媛쒕컻??, 'Full Stack Developer', '13301', 'IT/?뚰봽?몄썾??, '?꾨줎?몄뿏?쒖? 諛깆뿏???듯빀 媛쒕컻', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE008', '蹂댁븞?꾨Ц媛', 'Security Specialist', '13305', 'IT/?뚰봽?몄썾??, '?뺣낫蹂댁븞 諛??쒖뒪??蹂댁븞', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE009', '寃쎌쁺而⑥꽕?댄듃', 'Management Consultant', '12201', '寃쎌쁺/而⑥꽕??, '湲곗뾽 ?꾨왂 ?섎┰ 諛?寃쎌쁺 ?먮Ц', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE010', '留덉??낆쟾臾멸?', 'Marketing Specialist', '12301', '留덉???愿묎퀬', '留덉????꾨왂 ?섎┰ 諛??ㅽ뻾', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE011', 'UX?붿옄?대꼫', 'UX Designer', '13401', 'IT/?뚰봽?몄썾??, 'UI/UX ?붿옄??諛??ъ슜??寃쏀뿕 ?ㅺ퀎', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE012', '?쒗뭹愿由ъ옄', 'Product Manager', '12101', 'IT/?뚰봽?몄썾??, '?쒗뭹 湲고쉷 諛?濡쒕뱶留?愿由?, 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 12. 吏곷Т蹂???웾 ?붽뎄?ы빆
-- ============================================
INSERT INTO tb_role_requirement (role_cd, competency_cd, required_level, importance, ins_user_id, ins_dt) VALUES
-- 諛깆뿏?쒓컻諛쒖옄
('ROLE001', 'COMP001', 85, 'high', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE001', 'COMP002', 80, 'high', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE001', 'COMP003', 70, 'medium', 'SYSTEM', CURRENT_TIMESTAMP),
-- ?곗씠?곕텇?앷?
('ROLE003', 'COMP001', 80, 'high', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE003', 'COMP002', 85, 'high', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE003', 'COMP003', 75, 'medium', 'SYSTEM', CURRENT_TIMESTAMP),
-- AI?붿??덉뼱
('ROLE005', 'COMP001', 90, 'high', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE005', 'COMP002', 85, 'high', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE005', 'COMP005', 70, 'medium', 'SYSTEM', CURRENT_TIMESTAMP),
-- 寃쎌쁺而⑥꽕?댄듃
('ROLE009', 'COMP001', 75, 'high', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE009', 'COMP002', 85, 'high', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE009', 'COMP003', 90, 'high', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE009', 'COMP005', 80, 'high', 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 13. 怨쇰ぉ-??웾 留ㅽ븨
-- ============================================
INSERT INTO tb_course_competency_map (course_cd, competency_cd, contribution_weight, ins_user_id, ins_dt) VALUES
('CS101', 'COMP001', 0.70, 'SYSTEM', CURRENT_TIMESTAMP),
('CS101', 'COMP002', 0.30, 'SYSTEM', CURRENT_TIMESTAMP),
('CS201', 'COMP001', 0.60, 'SYSTEM', CURRENT_TIMESTAMP),
('CS201', 'COMP002', 0.40, 'SYSTEM', CURRENT_TIMESTAMP),
('CS202', 'COMP001', 0.50, 'SYSTEM', CURRENT_TIMESTAMP),
('CS202', 'COMP002', 0.50, 'SYSTEM', CURRENT_TIMESTAMP),
('CS301', 'COMP001', 0.60, 'SYSTEM', CURRENT_TIMESTAMP),
('CS302', 'COMP003', 0.40, 'SYSTEM', CURRENT_TIMESTAMP),
('CS302', 'COMP002', 0.30, 'SYSTEM', CURRENT_TIMESTAMP),
('CS401', 'COMP001', 0.80, 'SYSTEM', CURRENT_TIMESTAMP),
('CS401', 'COMP002', 0.20, 'SYSTEM', CURRENT_TIMESTAMP),
('CS403', 'COMP002', 0.30, 'SYSTEM', CURRENT_TIMESTAMP),
('CS403', 'COMP003', 0.40, 'SYSTEM', CURRENT_TIMESTAMP),
('GE301', 'COMP003', 0.70, 'SYSTEM', CURRENT_TIMESTAMP),
('GE302', 'COMP003', 0.40, 'SYSTEM', CURRENT_TIMESTAMP),
('GE302', 'COMP005', 0.60, 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 14. 鍮꾧탳怨??꾨줈洹몃옩
-- ============================================
INSERT INTO tb_program (program_cd, program_nm, program_type, organizer, start_date, end_date, competency_contributions, ins_user_id, ins_dt) VALUES
('PGM001', '?쇱꽦 SDS ?섍퀎 ?명꽩??, 'internship', '?쇱꽦 SDS', '2025-07-01', '2025-08-31', '{"COMP001": 0.4, "COMP003": 0.3}', 'SYSTEM', CURRENT_TIMESTAMP),
('PGM002', '?ㅼ씠踰?遺?ㅽ듃罹좏봽', 'bootcamp', '?ㅼ씠踰?, '2025-01-15', '2025-06-30', '{"COMP001": 0.5, "COMP002": 0.3}', 'SYSTEM', CURRENT_TIMESTAMP),
('PGM003', 'AI 寃쎌쭊???, 'contest', '怨쇳븰湲곗닠?뺣낫?듭떊遺', '2025-09-01', '2025-11-30', '{"COMP001": 0.3, "COMP002": 0.5}', 'SYSTEM', CURRENT_TIMESTAMP),
('PGM004', '李쎌뾽?숈븘由?SEED', 'club', '李쎌뾽吏?먯꽱??, '2025-03-01', '2025-12-31', '{"COMP002": 0.3, "COMP003": 0.4}', 'SYSTEM', CURRENT_TIMESTAMP),
('PGM005', '?댁쇅 遊됱궗?쒕룞', 'volunteer', '援?젣援먮쪟泥?, '2025-07-15', '2025-08-15', '{"COMP003": 0.3, "COMP005": 0.5}', 'SYSTEM', CURRENT_TIMESTAMP),
('PGM006', 'AWS ?대씪?곕뱶 ?먭꺽利?怨쇱젙', 'certificate', 'AWS', '2025-04-01', '2025-05-31', '{"COMP001": 0.6, "COMP006": 0.3}', 'SYSTEM', CURRENT_TIMESTAMP),
('PGM007', 'Google Developer Student Club', 'club', 'Google', '2025-03-01', '2025-12-31', '{"COMP001": 0.4, "COMP003": 0.3}', 'SYSTEM', CURRENT_TIMESTAMP),
('PGM008', '?고븰?묐젰 ?꾨줈?앺듃', 'project', '?고븰?묐젰??, '2025-03-01', '2025-11-30', '{"COMP001": 0.3, "COMP002": 0.3, "COMP003": 0.3}', 'SYSTEM', CURRENT_TIMESTAMP);
