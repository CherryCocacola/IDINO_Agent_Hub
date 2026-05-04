-- ============================================
-- IDINO Career - ?숈깮 ?곗씠??(110紐?
-- ?ㅼ젣 議댁옱??踰뺥븳 ?쒓뎅 ?대쫫怨??숆낵 諛곗튂
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- ?숈깮 ?뺣낫 (110紐?
-- ============================================
INSERT INTO tb_student (student_id, student_nm, university_cd, department_cd, admission_year, current_grade, current_semester, email, phone, birth_date, gender, status, career_goal, ins_user_id, ins_dt) VALUES
-- 而댄벂?곌났?숆낵 (15紐?
('2021010001', '源誘쇱?', 'UNIV001', 'DEPT001', 2021, 4, 7, 'minjun.kim@kstu.ac.kr', '010-1234-0001', '2002-03-15', 'M', 'enrolled', '諛깆뿏?쒓컻諛쒖옄', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010002', '?댁꽌??, 'UNIV001', 'DEPT001', 2021, 4, 7, 'seoyeon.lee@kstu.ac.kr', '010-1234-0002', '2002-05-22', 'F', 'enrolled', 'AI?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010003', '諛뺤???, 'UNIV001', 'DEPT001', 2021, 4, 7, 'jiho.park@kstu.ac.kr', '010-1234-0003', '2002-08-10', 'M', 'enrolled', '??ㅽ깮媛쒕컻??, 'SYSTEM', CURRENT_TIMESTAMP),
('2022010001', '理쒖삁?', 'UNIV001', 'DEPT001', 2022, 3, 5, 'yeeun.choi@kstu.ac.kr', '010-1234-0004', '2003-01-28', 'F', 'enrolled', '?곗씠?곕텇?앷?', 'SYSTEM', CURRENT_TIMESTAMP),
('2022010002', '?뺤슦吏?, 'UNIV001', 'DEPT001', 2022, 3, 5, 'woojin.jung@kstu.ac.kr', '010-1234-0005', '2003-04-05', 'M', 'enrolled', '諛깆뿏?쒓컻諛쒖옄', 'SYSTEM', CURRENT_TIMESTAMP),
('2022010003', '媛뺥븯?', 'UNIV001', 'DEPT001', 2022, 3, 5, 'haeun.kang@kstu.ac.kr', '010-1234-0006', '2003-07-12', 'F', 'enrolled', 'DevOps?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2023010001', '?ㅼ???, 'UNIV001', 'DEPT001', 2023, 2, 3, 'junseo.yoon@kstu.ac.kr', '010-1234-0007', '2004-02-18', 'M', 'enrolled', 'AI?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2023010002', '?꾩닔??, 'UNIV001', 'DEPT001', 2023, 2, 3, 'sua.lim@kstu.ac.kr', '010-1234-0008', '2004-06-25', 'F', 'enrolled', '?꾨줎?몄뿏?쒓컻諛쒖옄', 'SYSTEM', CURRENT_TIMESTAMP),
('2023010003', '?쒕룄??, 'UNIV001', 'DEPT001', 2023, 2, 3, 'doyun.han@kstu.ac.kr', '010-1234-0009', '2004-09-30', 'M', 'enrolled', '諛깆뿏?쒓컻諛쒖옄', 'SYSTEM', CURRENT_TIMESTAMP),
('2024010001', '?ㅼ?誘?, 'UNIV001', 'DEPT001', 2024, 1, 1, 'jimin.oh@kstu.ac.kr', '010-1234-0010', '2005-03-08', 'F', 'enrolled', '?곗씠?곗뿏吏?덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2024010002', '?쒗쁽??, 'UNIV001', 'DEPT001', 2024, 1, 1, 'hyunwoo.seo@kstu.ac.kr', '010-1234-0011', '2005-05-14', 'M', 'enrolled', 'AI?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2024010003', '諛곗???, 'UNIV001', 'DEPT001', 2024, 1, 1, 'jiwon.bae@kstu.ac.kr', '010-1234-0012', '2005-08-21', 'F', 'enrolled', '蹂댁븞?꾨Ц媛', 'SYSTEM', CURRENT_TIMESTAMP),
('2024010004', '?⑸???, 'UNIV001', 'DEPT001', 2024, 1, 1, 'minjae.hwang@kstu.ac.kr', '010-1234-0013', '2005-11-03', 'M', 'enrolled', '??ㅽ깮媛쒕컻??, 'SYSTEM', CURRENT_TIMESTAMP),
('2024010005', '臾몄콈??, 'UNIV001', 'DEPT001', 2024, 1, 1, 'chaewon.moon@kstu.ac.kr', '010-1234-0014', '2005-12-17', 'F', 'enrolled', '諛깆뿏?쒓컻諛쒖옄', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010004', '?≫깭??, 'UNIV001', 'DEPT001', 2021, 4, 7, 'taehyun.song@kstu.ac.kr', '010-1234-0015', '2002-10-05', 'M', 'enrolled', 'DevOps?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
-- ?뚰봽?몄썾?댄븰怨?(12紐?
('2021020001', '?좎쑀??, 'UNIV001', 'DEPT002', 2021, 4, 7, 'yuna.shin@kstu.ac.kr', '010-2234-0001', '2002-02-14', 'F', 'enrolled', '?꾨줎?몄뿏?쒓컻諛쒖옄', 'SYSTEM', CURRENT_TIMESTAMP),
('2021020002', '?μ듅??, 'UNIV001', 'DEPT002', 2021, 4, 7, 'seunghyun.jang@kstu.ac.kr', '010-2234-0002', '2002-04-28', 'M', 'enrolled', '??ㅽ깮媛쒕컻??, 'SYSTEM', CURRENT_TIMESTAMP),
('2022020001', '沅뚮굹??, 'UNIV001', 'DEPT002', 2022, 3, 5, 'nayeon.kwon@kstu.ac.kr', '010-2234-0003', '2003-03-19', 'F', 'enrolled', 'DevOps?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2022020002', '?④굔??, 'UNIV001', 'DEPT002', 2022, 3, 5, 'gunwoo.nam@kstu.ac.kr', '010-2234-0004', '2003-06-07', 'M', 'enrolled', '諛깆뿏?쒓컻諛쒖옄', 'SYSTEM', CURRENT_TIMESTAMP),
('2023020001', '?띿꽌吏?, 'UNIV001', 'DEPT002', 2023, 2, 3, 'seojin.hong@kstu.ac.kr', '010-2234-0005', '2004-01-11', 'F', 'enrolled', '?꾨줎?몄뿏?쒓컻諛쒖옄', 'SYSTEM', CURRENT_TIMESTAMP),
('2023020002', '?덉옱誘?, 'UNIV001', 'DEPT002', 2023, 2, 3, 'jaemin.ahn@kstu.ac.kr', '010-2234-0006', '2004-04-23', 'M', 'enrolled', '??ㅽ깮媛쒕컻??, 'SYSTEM', CURRENT_TIMESTAMP),
('2024020001', '?묒삁吏', 'UNIV001', 'DEPT002', 2024, 1, 1, 'yeji.yang@kstu.ac.kr', '010-2234-0007', '2005-02-09', 'F', 'enrolled', '?꾨줎?몄뿏?쒓컻諛쒖옄', 'SYSTEM', CURRENT_TIMESTAMP),
('2024020002', '怨좊???, 'UNIV001', 'DEPT002', 2024, 1, 1, 'minsu.ko@kstu.ac.kr', '010-2234-0008', '2005-07-16', 'M', 'enrolled', '諛깆뿏?쒓컻諛쒖옄', 'SYSTEM', CURRENT_TIMESTAMP),
('2024020003', '議곗???, 'UNIV001', 'DEPT002', 2024, 1, 1, 'eunseo.jo@kstu.ac.kr', '010-2234-0009', '2005-09-28', 'F', 'enrolled', 'DevOps?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2022020003', '瑜섏???, 'UNIV001', 'DEPT002', 2022, 3, 5, 'jihoon.ryu@kstu.ac.kr', '010-2234-0010', '2003-08-15', 'M', 'enrolled', '??ㅽ깮媛쒕컻??, 'SYSTEM', CURRENT_TIMESTAMP),
('2023020003', '源?쒖?', 'UNIV001', 'DEPT002', 2023, 2, 3, 'sieun.kim@kstu.ac.kr', '010-2234-0011', '2004-07-20', 'F', 'enrolled', 'UX?붿옄?대꼫', 'SYSTEM', CURRENT_TIMESTAMP),
('2024020004', '?댁???, 'UNIV001', 'DEPT002', 2024, 1, 1, 'junhyuk.lee@kstu.ac.kr', '010-2234-0012', '2005-11-25', 'M', 'enrolled', '諛깆뿏?쒓컻諛쒖옄', 'SYSTEM', CURRENT_TIMESTAMP),
-- ?꾩옄怨듯븰怨?(10紐?
('2021030001', '諛뺤냼誘?, 'UNIV001', 'DEPT003', 2021, 4, 7, 'somin.park@kstu.ac.kr', '010-3234-0001', '2002-01-20', 'F', 'enrolled', '諛섎룄泥댁뿏吏?덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2021030002', '理쒖꽦誘?, 'UNIV001', 'DEPT003', 2021, 4, 7, 'sungmin.choi@kstu.ac.kr', '010-3234-0002', '2002-06-13', 'M', 'enrolled', 'IoT?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2022030001', '?뺥븯由?, 'UNIV001', 'DEPT003', 2022, 3, 5, 'harin.jung@kstu.ac.kr', '010-3234-0003', '2003-02-25', 'F', 'enrolled', '?꾨쿋?붾뱶媛쒕컻??, 'SYSTEM', CURRENT_TIMESTAMP),
('2022030002', '源?숉쁽', 'UNIV001', 'DEPT003', 2022, 3, 5, 'donghyun.kim@kstu.ac.kr', '010-3234-0004', '2003-05-18', 'M', 'enrolled', '諛섎룄泥댁뿏吏?덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2023030001', '?댁???, 'UNIV001', 'DEPT003', 2023, 2, 3, 'jia.lee@kstu.ac.kr', '010-3234-0005', '2004-03-07', 'F', 'enrolled', '?듭떊?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2023030002', '諛뺤???, 'UNIV001', 'DEPT003', 2023, 2, 3, 'junyoung.park@kstu.ac.kr', '010-3234-0006', '2004-08-14', 'M', 'enrolled', 'IoT?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2024030001', '?좎꽌??, 'UNIV001', 'DEPT003', 2024, 1, 1, 'seoyeon.yu@kstu.ac.kr', '010-3234-0007', '2005-01-30', 'F', 'enrolled', '諛섎룄泥댁뿏吏?덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2024030002', '媛뺣???, 'UNIV001', 'DEPT003', 2024, 1, 1, 'minho.kang@kstu.ac.kr', '010-3234-0008', '2005-04-22', 'M', 'enrolled', '?꾨쿋?붾뱶媛쒕컻??, 'SYSTEM', CURRENT_TIMESTAMP),
('2024030003', '?먯삁由?, 'UNIV001', 'DEPT003', 2024, 1, 1, 'yerin.son@kstu.ac.kr', '010-3234-0009', '2005-06-18', 'F', 'enrolled', 'IoT?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2024030004', '?꾪깭以', 'UNIV001', 'DEPT003', 2024, 1, 1, 'taejun.lim@kstu.ac.kr', '010-3234-0010', '2005-10-12', 'M', 'enrolled', '諛섎룄泥댁뿏吏?덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
-- 寃쎌쁺?숆낵 (12紐?
('2021140001', '源吏??, 'UNIV001', 'DEPT014', 2021, 4, 7, 'jihyun.kim@kstu.ac.kr', '010-4234-0001', '2002-02-28', 'F', 'enrolled', '寃쎌쁺而⑥꽕?댄듃', 'SYSTEM', CURRENT_TIMESTAMP),
('2021140002', '?댁듅以', 'UNIV001', 'DEPT014', 2021, 4, 7, 'seungjun.lee@kstu.ac.kr', '010-4234-0002', '2002-05-10', 'M', 'enrolled', '留덉??낆쟾臾멸?', 'SYSTEM', CURRENT_TIMESTAMP),
('2022140001', '諛뺣???, 'UNIV001', 'DEPT014', 2022, 3, 5, 'minseo.park@kstu.ac.kr', '010-4234-0003', '2003-01-15', 'F', 'enrolled', '?쒗뭹愿由ъ옄', 'SYSTEM', CURRENT_TIMESTAMP),
('2022140002', '理쒗쁽以', 'UNIV001', 'DEPT014', 2022, 3, 5, 'hyunjun.choi@kstu.ac.kr', '010-4234-0004', '2003-04-22', 'M', 'enrolled', '寃쎌쁺而⑥꽕?댄듃', 'SYSTEM', CURRENT_TIMESTAMP),
('2023140001', '?뺤닔鍮?, 'UNIV001', 'DEPT014', 2023, 2, 3, 'subin.jung@kstu.ac.kr', '010-4234-0005', '2004-02-08', 'F', 'enrolled', '留덉??낆쟾臾멸?', 'SYSTEM', CURRENT_TIMESTAMP),
('2023140002', '媛뺣룞??, 'UNIV001', 'DEPT014', 2023, 2, 3, 'donghun.kang@kstu.ac.kr', '010-4234-0006', '2004-06-30', 'M', 'enrolled', '寃쎌쁺而⑥꽕?댄듃', 'SYSTEM', CURRENT_TIMESTAMP),
('2024140001', '?ㅼ???, 'UNIV001', 'DEPT014', 2024, 1, 1, 'jiwoo.yoon@kstu.ac.kr', '010-4234-0007', '2005-03-17', 'F', 'enrolled', '?쒗뭹愿由ъ옄', 'SYSTEM', CURRENT_TIMESTAMP),
('2024140002', '?꾩떆??, 'UNIV001', 'DEPT014', 2024, 1, 1, 'siwoo.lim@kstu.ac.kr', '010-4234-0008', '2005-07-25', 'M', 'enrolled', '留덉??낆쟾臾멸?', 'SYSTEM', CURRENT_TIMESTAMP),
('2024140003', '?쒖냼??, 'UNIV001', 'DEPT014', 2024, 1, 1, 'sohee.han@kstu.ac.kr', '010-4234-0009', '2005-09-11', 'F', 'enrolled', '寃쎌쁺而⑥꽕?댄듃', 'SYSTEM', CURRENT_TIMESTAMP),
('2022140003', '?ㅼ???, 'UNIV001', 'DEPT014', 2022, 3, 5, 'junseok.oh@kstu.ac.kr', '010-4234-0010', '2003-07-08', 'M', 'enrolled', '?щТ遺꾩꽍媛', 'SYSTEM', CURRENT_TIMESTAMP),
('2023140003', '?쒖쑀吏?, 'UNIV001', 'DEPT014', 2023, 2, 3, 'yujin.seo@kstu.ac.kr', '010-4234-0011', '2004-10-14', 'F', 'enrolled', '留덉??낆쟾臾멸?', 'SYSTEM', CURRENT_TIMESTAMP),
('2024140004', '諛고쁽??, 'UNIV001', 'DEPT014', 2024, 1, 1, 'hyunsung.bae@kstu.ac.kr', '010-4234-0012', '2005-12-05', 'M', 'enrolled', '寃쎌쁺而⑥꽕?댄듃', 'SYSTEM', CURRENT_TIMESTAMP),
-- ?듦퀎?숆낵 (10紐?
('2021130001', '源?ㅼ?', 'UNIV001', 'DEPT013', 2021, 4, 7, 'daeun.kim@kstu.ac.kr', '010-5234-0001', '2002-01-08', 'F', 'enrolled', '?곗씠?곕텇?앷?', 'SYSTEM', CURRENT_TIMESTAMP),
('2021130002', '?댁옱??, 'UNIV001', 'DEPT013', 2021, 4, 7, 'jaehyun.lee@kstu.ac.kr', '010-5234-0002', '2002-04-15', 'M', 'enrolled', '?곗씠?곗궗?댁뼵?곗뒪??, 'SYSTEM', CURRENT_TIMESTAMP),
('2022130001', '諛뺥븯??, 'UNIV001', 'DEPT013', 2022, 3, 5, 'hayoung.park@kstu.ac.kr', '010-5234-0003', '2003-03-22', 'F', 'enrolled', '?곗씠?곕텇?앷?', 'SYSTEM', CURRENT_TIMESTAMP),
('2022130002', '理쒖슦??, 'UNIV001', 'DEPT013', 2022, 3, 5, 'woohyuk.choi@kstu.ac.kr', '010-5234-0004', '2003-06-28', 'M', 'enrolled', 'AI?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2023130001', '?뺤삁??, 'UNIV001', 'DEPT013', 2023, 2, 3, 'yewon.jung@kstu.ac.kr', '010-5234-0005', '2004-01-05', 'F', 'enrolled', '?곗씠?곕텇?앷?', 'SYSTEM', CURRENT_TIMESTAMP),
('2023130002', '媛뺣?以', 'UNIV001', 'DEPT013', 2023, 2, 3, 'minjun.kang@kstu.ac.kr', '010-5234-0006', '2004-05-12', 'M', 'enrolled', '?곗씠?곗궗?댁뼵?곗뒪??, 'SYSTEM', CURRENT_TIMESTAMP),
('2024130001', '?ㅼ꽌??, 'UNIV001', 'DEPT013', 2024, 1, 1, 'seoa.yoon@kstu.ac.kr', '010-5234-0007', '2005-02-18', 'F', 'enrolled', '?곗씠?곕텇?앷?', 'SYSTEM', CURRENT_TIMESTAMP),
('2024130002', '?꾨룞??, 'UNIV001', 'DEPT013', 2024, 1, 1, 'donghyun.lim@kstu.ac.kr', '010-5234-0008', '2005-06-25', 'M', 'enrolled', 'AI?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2024130003', '?쒖?誘?, 'UNIV001', 'DEPT013', 2024, 1, 1, 'jimin.han@kstu.ac.kr', '010-5234-0009', '2005-08-30', 'F', 'enrolled', '?곗씠?곕텇?앷?', 'SYSTEM', CURRENT_TIMESTAMP),
('2024130004', '?ㅼ듅誘?, 'UNIV001', 'DEPT013', 2024, 1, 1, 'seungmin.oh@kstu.ac.kr', '010-5234-0010', '2005-11-07', 'M', 'enrolled', '?곗씠?곗궗?댁뼵?곗뒪??, 'SYSTEM', CURRENT_TIMESTAMP),
-- ?곗뾽怨듯븰怨?(8紐?
('2021060001', '源?쒖쑄', 'UNIV001', 'DEPT006', 2021, 4, 7, 'taeyoon.kim@kstu.ac.kr', '010-6234-0001', '2002-03-25', 'M', 'enrolled', '?덉쭏愿由ъ쟾臾멸?', 'SYSTEM', CURRENT_TIMESTAMP),
('2021060002', '?댁냼??, 'UNIV001', 'DEPT006', 2021, 4, 7, 'soyoung.lee@kstu.ac.kr', '010-6234-0002', '2002-07-18', 'F', 'enrolled', '?앹궛愿由ъ옄', 'SYSTEM', CURRENT_TIMESTAMP),
('2022060001', '諛뺤옱??, 'UNIV001', 'DEPT006', 2022, 3, 5, 'jaewon.park@kstu.ac.kr', '010-6234-0003', '2003-02-14', 'M', 'enrolled', '?곗씠?곕텇?앷?', 'SYSTEM', CURRENT_TIMESTAMP),
('2022060002', '理쒖쑀??, 'UNIV001', 'DEPT006', 2022, 3, 5, 'yuna.choi@kstu.ac.kr', '010-6234-0004', '2003-05-30', 'F', 'enrolled', '寃쎌쁺而⑥꽕?댄듃', 'SYSTEM', CURRENT_TIMESTAMP),
('2023060001', '?뺤듅??, 'UNIV001', 'DEPT006', 2023, 2, 3, 'seungho.jung@kstu.ac.kr', '010-6234-0005', '2004-04-10', 'M', 'enrolled', '?덉쭏愿由ъ쟾臾멸?', 'SYSTEM', CURRENT_TIMESTAMP),
('2023060002', '媛뺤???, 'UNIV001', 'DEPT006', 2023, 2, 3, 'jia.kang@kstu.ac.kr', '010-6234-0006', '2004-08-22', 'F', 'enrolled', '?쒗뭹愿由ъ옄', 'SYSTEM', CURRENT_TIMESTAMP),
('2024060001', '?ㅽ쁽??, 'UNIV001', 'DEPT006', 2024, 1, 1, 'hyunseok.yoon@kstu.ac.kr', '010-6234-0007', '2005-01-15', 'M', 'enrolled', '?앹궛愿由ъ옄', 'SYSTEM', CURRENT_TIMESTAMP),
('2024060002', '?꾨굹??, 'UNIV001', 'DEPT006', 2024, 1, 1, 'nayoon.lim@kstu.ac.kr', '010-6234-0008', '2005-05-28', 'F', 'enrolled', '?곗씠?곕텇?앷?', 'SYSTEM', CURRENT_TIMESTAMP),
-- ?붿옄?명븰怨?(8紐?
('2021250001', '源?뚯쑉', 'UNIV001', 'DEPT025', 2021, 4, 7, 'soyul.kim@kstu.ac.kr', '010-7234-0001', '2002-02-05', 'F', 'enrolled', 'UX?붿옄?대꼫', 'SYSTEM', CURRENT_TIMESTAMP),
('2021250002', '?댁???, 'UNIV001', 'DEPT025', 2021, 4, 7, 'junseo.lee@kstu.ac.kr', '010-7234-0002', '2002-06-20', 'M', 'enrolled', '洹몃옒?쎈뵒?먯씠??, 'SYSTEM', CURRENT_TIMESTAMP),
('2022250001', '諛뺤꽌??, 'UNIV001', 'DEPT025', 2022, 3, 5, 'seoyun.park@kstu.ac.kr', '010-7234-0003', '2003-01-28', 'F', 'enrolled', 'UX?붿옄?대꼫', 'SYSTEM', CURRENT_TIMESTAMP),
('2022250002', '理쒕?洹?, 'UNIV001', 'DEPT025', 2022, 3, 5, 'mingyu.choi@kstu.ac.kr', '010-7234-0004', '2003-04-15', 'M', 'enrolled', '?쒗뭹?붿옄?대꼫', 'SYSTEM', CURRENT_TIMESTAMP),
('2023250001', '?뺣떎??, 'UNIV001', 'DEPT025', 2023, 2, 3, 'dahyun.jung@kstu.ac.kr', '010-7234-0005', '2004-03-10', 'F', 'enrolled', 'UX?붿옄?대꼫', 'SYSTEM', CURRENT_TIMESTAMP),
('2023250002', '媛뺣룄??, 'UNIV001', 'DEPT025', 2023, 2, 3, 'dohyun.kang@kstu.ac.kr', '010-7234-0006', '2004-07-25', 'M', 'enrolled', '洹몃옒?쎈뵒?먯씠??, 'SYSTEM', CURRENT_TIMESTAMP),
('2024250001', '?ㅼ콈由?, 'UNIV001', 'DEPT025', 2024, 1, 1, 'chaerin.yoon@kstu.ac.kr', '010-7234-0007', '2005-02-22', 'F', 'enrolled', 'UX?붿옄?대꼫', 'SYSTEM', CURRENT_TIMESTAMP),
('2024250002', '?꾩꽦以', 'UNIV001', 'DEPT025', 2024, 1, 1, 'sungjun.lim@kstu.ac.kr', '010-7234-0008', '2005-08-14', 'M', 'enrolled', '?쒗뭹?붿옄?대꼫', 'SYSTEM', CURRENT_TIMESTAMP),
-- ?щ━?숆낵 (8紐?
('2021230001', '源?좎쭊', 'UNIV001', 'DEPT023', 2021, 4, 7, 'yujin.kim@kstu.ac.kr', '010-8234-0001', '2002-01-12', 'F', 'enrolled', '?곷떞?щ━??, 'SYSTEM', CURRENT_TIMESTAMP),
('2021230002', '?댄쁽誘?, 'UNIV001', 'DEPT023', 2021, 4, 7, 'hyunmin.lee@kstu.ac.kr', '010-8234-0002', '2002-05-28', 'M', 'enrolled', 'UX由ъ꽌泥?, 'SYSTEM', CURRENT_TIMESTAMP),
('2022230001', '諛뺤냼吏?, 'UNIV001', 'DEPT023', 2022, 3, 5, 'sojin.park@kstu.ac.kr', '010-8234-0003', '2003-02-08', 'F', 'enrolled', '?곷떞?щ━??, 'SYSTEM', CURRENT_TIMESTAMP),
('2022230002', '理쒖옱??, 'UNIV001', 'DEPT023', 2022, 3, 5, 'jaeyoon.choi@kstu.ac.kr', '010-8234-0004', '2003-06-15', 'M', 'enrolled', 'UX由ъ꽌泥?, 'SYSTEM', CURRENT_TIMESTAMP),
('2023230001', '?뺤꽌??, 'UNIV001', 'DEPT023', 2023, 2, 3, 'seohyun.jung@kstu.ac.kr', '010-8234-0005', '2004-01-20', 'F', 'enrolled', '?곷떞?щ━??, 'SYSTEM', CURRENT_TIMESTAMP),
('2023230002', '媛뺤???, 'UNIV001', 'DEPT023', 2023, 2, 3, 'junhyung.kang@kstu.ac.kr', '010-8234-0006', '2004-05-30', 'M', 'enrolled', 'HRD?꾨Ц媛', 'SYSTEM', CURRENT_TIMESTAMP),
('2024230001', '?ㅻ떎??, 'UNIV001', 'DEPT023', 2024, 1, 1, 'dain.yoon@kstu.ac.kr', '010-8234-0007', '2005-03-08', 'F', 'enrolled', '?곷떞?щ━??, 'SYSTEM', CURRENT_TIMESTAMP),
('2024230002', '?꾩젙??, 'UNIV001', 'DEPT023', 2024, 1, 1, 'jungwoo.lim@kstu.ac.kr', '010-8234-0008', '2005-07-22', 'M', 'enrolled', 'UX由ъ꽌泥?, 'SYSTEM', CURRENT_TIMESTAMP),
-- ?섑븰怨?(6紐?
('2021090001', '源誘쇱?', 'UNIV001', 'DEPT009', 2021, 4, 7, 'minji.kim@kstu.ac.kr', '010-9234-0001', '2002-02-18', 'F', 'enrolled', '?곗씠?곗궗?댁뼵?곗뒪??, 'SYSTEM', CURRENT_TIMESTAMP),
('2021090002', '?댄샇以', 'UNIV001', 'DEPT009', 2021, 4, 7, 'hojun.lee@kstu.ac.kr', '010-9234-0002', '2002-06-25', 'M', 'enrolled', '???, 'SYSTEM', CURRENT_TIMESTAMP),
('2022090001', '諛뺤???, 'UNIV001', 'DEPT009', 2022, 3, 5, 'jiyoon.park@kstu.ac.kr', '010-9234-0003', '2003-03-12', 'F', 'enrolled', '?곗씠?곕텇?앷?', 'SYSTEM', CURRENT_TIMESTAMP),
('2022090002', '理쒖꽦??, 'UNIV001', 'DEPT009', 2022, 3, 5, 'sunghyun.choi@kstu.ac.kr', '010-9234-0004', '2003-07-28', 'M', 'enrolled', '???, 'SYSTEM', CURRENT_TIMESTAMP),
('2023090001', '?뺤삁由?, 'UNIV001', 'DEPT009', 2023, 2, 3, 'yerin.jung@kstu.ac.kr', '010-9234-0005', '2004-04-05', 'F', 'enrolled', '?곗씠?곗궗?댁뼵?곗뒪??, 'SYSTEM', CURRENT_TIMESTAMP),
('2024090001', '媛뺤???, 'UNIV001', 'DEPT009', 2024, 1, 1, 'jiho.kang@kstu.ac.kr', '010-9234-0006', '2005-01-22', 'M', 'enrolled', '???, 'SYSTEM', CURRENT_TIMESTAMP),
-- 臾쇰━?숆낵 (5紐?
('2021100001', '源二쇱썝', 'UNIV001', 'DEPT010', 2021, 4, 7, 'juwon.kim@kstu.ac.kr', '010-1034-0001', '2002-03-10', 'M', 'enrolled', '?곌뎄??, 'SYSTEM', CURRENT_TIMESTAMP),
('2022100001', '?댁꽌吏?, 'UNIV001', 'DEPT010', 2022, 3, 5, 'seojin.lee@kstu.ac.kr', '010-1034-0002', '2003-01-25', 'F', 'enrolled', '諛섎룄泥댁뿏吏?덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2023100001', '諛뺣???, 'UNIV001', 'DEPT010', 2023, 2, 3, 'minsung.park@kstu.ac.kr', '010-1034-0003', '2004-02-15', 'M', 'enrolled', '?곌뎄??, 'SYSTEM', CURRENT_TIMESTAMP),
('2024100001', '理쒖닔鍮?, 'UNIV001', 'DEPT010', 2024, 1, 1, 'subin.choi@kstu.ac.kr', '010-1034-0004', '2005-04-20', 'F', 'enrolled', '諛섎룄泥댁뿏吏?덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2024100002', '?뺥깭??, 'UNIV001', 'DEPT010', 2024, 1, 1, 'taehyun.jung@kstu.ac.kr', '010-1034-0005', '2005-08-08', 'M', 'enrolled', '?곌뎄??, 'SYSTEM', CURRENT_TIMESTAMP),
-- 湲곌퀎怨듯븰怨?(6紐?
('2021040001', '源?꾩슦', 'UNIV001', 'DEPT004', 2021, 4, 7, 'hyunwoo.kim@kstu.ac.kr', '010-1134-0001', '2002-01-28', 'M', 'enrolled', '?먮룞李⑥뿏吏?덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2022040001', '?대굹??, 'UNIV001', 'DEPT004', 2022, 3, 5, 'nayeon.lee@kstu.ac.kr', '010-1134-0002', '2003-04-10', 'F', 'enrolled', '濡쒕큸怨듯븰??, 'SYSTEM', CURRENT_TIMESTAMP),
('2022040002', '諛뺣룄??, 'UNIV001', 'DEPT004', 2022, 3, 5, 'dohun.park@kstu.ac.kr', '010-1134-0003', '2003-08-22', 'M', 'enrolled', '?먮룞李⑥뿏吏?덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2023040001', '理쒖???, 'UNIV001', 'DEPT004', 2023, 2, 3, 'jian.choi@kstu.ac.kr', '010-1134-0004', '2004-03-18', 'F', 'enrolled', '?먮꼫吏?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2024040001', '?뺤슦鍮?, 'UNIV001', 'DEPT004', 2024, 1, 1, 'woobin.jung@kstu.ac.kr', '010-1134-0005', '2005-02-05', 'M', 'enrolled', '?먮룞李⑥뿏吏?덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2024040002', '媛뺤떆??, 'UNIV001', 'DEPT004', 2024, 1, 1, 'sihyun.kang@kstu.ac.kr', '010-1134-0006', '2005-06-28', 'F', 'enrolled', '濡쒕큸怨듯븰??, 'SYSTEM', CURRENT_TIMESTAMP),
-- ?뷀븰怨듯븰怨?(5紐?
('2021050001', '源?섏?', 'UNIV001', 'DEPT005', 2021, 4, 7, 'hajun.kim@kstu.ac.kr', '010-1234-1001', '2002-02-12', 'M', 'enrolled', '?뷀븰?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2022050001', '?댁＜??, 'UNIV001', 'DEPT005', 2022, 3, 5, 'jua.lee@kstu.ac.kr', '010-1234-1002', '2003-05-08', 'F', 'enrolled', '怨듭젙?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2023050001', '諛뺤떆??, 'UNIV001', 'DEPT005', 2023, 2, 3, 'siwon.park@kstu.ac.kr', '010-1234-1003', '2004-01-25', 'M', 'enrolled', '?뷀븰?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2024050001', '理쒖???, 'UNIV001', 'DEPT005', 2024, 1, 1, 'eunseo.choi@kstu.ac.kr', '010-1234-1004', '2005-03-15', 'F', 'enrolled', '怨듭젙?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
('2024050002', '?뺣?洹?, 'UNIV001', 'DEPT005', 2024, 1, 1, 'mingyu.jung@kstu.ac.kr', '010-1234-1005', '2005-07-20', 'M', 'enrolled', '?뷀븰?붿??덉뼱', 'SYSTEM', CURRENT_TIMESTAMP),
-- 寃쎌젣?숆낵 (5紐?
('2021170001', '源?쒖뿰', 'UNIV001', 'DEPT017', 2021, 4, 7, 'seoyeon2.kim@kstu.ac.kr', '010-1334-0001', '2002-04-08', 'F', 'enrolled', '湲덉쑖遺꾩꽍媛', 'SYSTEM', CURRENT_TIMESTAMP),
('2022170001', '?댁???, 'UNIV001', 'DEPT017', 2022, 3, 5, 'junhyuk2.lee@kstu.ac.kr', '010-1334-0002', '2003-02-22', 'M', 'enrolled', '寃쎌젣遺꾩꽍媛', 'SYSTEM', CURRENT_TIMESTAMP),
('2023170001', '諛뺥븯?', 'UNIV001', 'DEPT017', 2023, 2, 3, 'haeun2.park@kstu.ac.kr', '010-1334-0003', '2004-05-18', 'F', 'enrolled', '湲덉쑖遺꾩꽍媛', 'SYSTEM', CURRENT_TIMESTAMP),
('2024170001', '理쒓굔??, 'UNIV001', 'DEPT017', 2024, 1, 1, 'gunwoo.choi@kstu.ac.kr', '010-1334-0004', '2005-01-10', 'M', 'enrolled', '寃쎌젣遺꾩꽍媛', 'SYSTEM', CURRENT_TIMESTAMP),
('2024170002', '?뺤닔??, 'UNIV001', 'DEPT017', 2024, 1, 1, 'sua.jung@kstu.ac.kr', '010-1334-0005', '2005-04-28', 'F', 'enrolled', '湲덉쑖遺꾩꽍媛', 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- ?숈깮蹂??꾩쟻 ?깆쟻 ?붿빟 ?앹꽦
-- ============================================
INSERT INTO tb_cumulative_summary (student_id, total_credits_earned, major_credits_earned, liberal_credits_earned, cumulative_gpa, major_gpa, completion_rate, ins_user_id, ins_dt)
SELECT
    student_id,
    CASE current_grade
        WHEN 4 THEN FLOOR(95 + RANDOM() * 15)
        WHEN 3 THEN FLOOR(60 + RANDOM() * 15)
        WHEN 2 THEN FLOOR(30 + RANDOM() * 15)
        WHEN 1 THEN FLOOR(0 + RANDOM() * 10)
    END as total_credits_earned,
    CASE current_grade
        WHEN 4 THEN FLOOR(45 + RANDOM() * 10)
        WHEN 3 THEN FLOOR(25 + RANDOM() * 10)
        WHEN 2 THEN FLOOR(10 + RANDOM() * 8)
        WHEN 1 THEN FLOOR(0 + RANDOM() * 5)
    END as major_credits_earned,
    CASE current_grade
        WHEN 4 THEN FLOOR(24 + RANDOM() * 4)
        WHEN 3 THEN FLOOR(15 + RANDOM() * 5)
        WHEN 2 THEN FLOOR(8 + RANDOM() * 4)
        WHEN 1 THEN FLOOR(0 + RANDOM() * 3)
    END as liberal_credits_earned,
    ROUND((2.5 + RANDOM() * 2.0)::numeric, 2) as cumulative_gpa,
    ROUND((2.5 + RANDOM() * 2.0)::numeric, 2) as major_gpa,
    CASE current_grade
        WHEN 4 THEN ROUND((75 + RANDOM() * 20)::numeric, 1)
        WHEN 3 THEN ROUND((45 + RANDOM() * 15)::numeric, 1)
        WHEN 2 THEN ROUND((22 + RANDOM() * 10)::numeric, 1)
        WHEN 1 THEN ROUND((0 + RANDOM() * 8)::numeric, 1)
    END as completion_rate,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student;

-- ============================================
-- ?숈깮蹂???웾 ?꾪솴 ?앹꽦
-- ============================================
INSERT INTO tb_student_competency (student_id, competency_cd, current_score, target_score, gap_score, status, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    c.competency_cd,
    ROUND((40 + RANDOM() * 55)::numeric, 1) as current_score,
    85 as target_score,
    0 as gap_score,
    CASE
        WHEN RANDOM() < 0.2 THEN 'excellent'
        WHEN RANDOM() < 0.4 THEN 'good'
        WHEN RANDOM() < 0.6 THEN 'average'
        WHEN RANDOM() < 0.8 THEN 'improve'
        ELSE 'focus'
    END as status,
    CASE
        WHEN RANDOM() < 0.3 THEN 'up'
        WHEN RANDOM() < 0.6 THEN 'stable'
        ELSE 'down'
    END as trend,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN tb_competency c;

-- gap_score ?낅뜲?댄듃
UPDATE tb_student_competency
SET gap_score = current_score - target_score;
