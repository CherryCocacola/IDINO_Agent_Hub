-- ============================================
-- IDINO Career - Realistic What-if Simulation Seed Data
-- Based on Real Korean Job Market Data (2024-2025)
-- Sources: Samsung Careers, Linkareer, AWS Certification, Q-net
-- Created: 2026-01-24
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- tb_simulation_scenario - Realistic Scenarios
-- Uses new schema: title, description, base_state, changes, predicted_outcomes, confidence_level
-- ============================================

-- Clean up previous realistic seed data
DELETE FROM tb_simulation_scenario WHERE ins_user_id = 'REALISTIC_SEED';

-- ============================================
-- 1. Career Path Scenarios (career_path)
-- Based on actual Korean job market data
-- ============================================

-- 삼성전자 DS부문 반도체 엔지니어 목표 시나리오
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level, ins_user_id
) VALUES (
    '20002268',
    'career_path',
    '삼성전자 DS부문 반도체 설계 엔지니어 목표',
    '2025년 하반기 삼성전자 DS부문 대학생 인턴 지원을 위한 준비도 분석. 서류접수 8/27~9/3, 발표 10/2 예정.',
    '{"variables": [{"name": "target_role", "current_value": "미정", "simulated_value": "semiconductor_engineer"}]}'::jsonb,
    '{"simulated_changes": [{"name": "target_role", "value": "semiconductor_engineer"}]}'::jsonb,
    '{"results": [
        {"metric_name": "직무 준비도", "current_value": 45.0, "simulated_value": 72.0, "change_percent": 60.0, "impact_level": "positive", "explanation": "회로설계, Verilog, VLSI 역량 집중 개발 필요"},
        {"metric_name": "핵심 부족 역량", "current_value": 4, "simulated_value": 2, "change_percent": -50.0, "impact_level": "positive", "explanation": "중요도 높은 부족 역량: VLSI 설계, Verilog HDL"}
    ], "recommendation": "삼성 DS부문 인턴 지원을 위해 회로설계 및 Verilog 역량 강화를 권장합니다. GSAT 준비도 병행하세요.", "ai_analysis": {"summary": "삼성 DS부문 반도체 설계 직무는 높은 기술력을 요구합니다. 현재 준비도 45%에서 집중 학습 시 72%까지 향상 가능합니다.", "strengths": ["전공 기초가 탄탄함", "프로그래밍 기초 보유", "학점 3.7 이상 유지"], "risks": ["Verilog 경험 부족", "GSAT 준비 필요", "인턴 경험 없음"], "recommendations": ["Verilog/VHDL 온라인 강좌 수강", "GSAT 모의고사 연습", "반도체 관련 프로젝트 수행"], "next_steps": ["Coursera 디지털회로 강좌 등록", "GSAT 기출문제 풀이 시작"], "confidence_reason": "DS부문 인턴 합격자 평균 스펙 기준 분석"}}'::jsonb,
    0.72,
    'REALISTIC_SEED'
);

-- 삼성전자 DX부문 소프트웨어 개발자 목표 시나리오
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level, ins_user_id
) VALUES (
    '20002269',
    'career_path',
    '삼성전자 DX부문 소프트웨어 개발자 목표',
    '2025년 상반기 삼성전자 DX부문 SW개발 직무 인턴 지원. 서류접수 3/10~3/17, 합격자 평균스펙: 학점 3.7, 토익 850+, 인턴 1~2회.',
    '{"variables": [{"name": "target_role", "current_value": "미정", "simulated_value": "software_developer"}]}'::jsonb,
    '{"simulated_changes": [{"name": "target_role", "value": "software_developer"}]}'::jsonb,
    '{"results": [
        {"metric_name": "직무 준비도", "current_value": 55.0, "simulated_value": 78.0, "change_percent": 41.8, "impact_level": "positive", "explanation": "Java, Spring, 알고리즘 역량 강화로 준비도 향상 가능"},
        {"metric_name": "핵심 부족 역량", "current_value": 3, "simulated_value": 1, "change_percent": -66.7, "impact_level": "positive", "explanation": "중요도 높은 부족 역량: 시스템 설계 경험"}
    ], "recommendation": "SW개발 직무 준비도가 양호합니다. 알고리즘 문제풀이와 프로젝트 경험을 더 쌓으세요.", "ai_analysis": {"summary": "DX부문 SW개발은 Java/Spring 기반 개발 역량이 핵심입니다. 코딩테스트 준비가 필수입니다.", "strengths": ["Java 기초 탄탄", "웹개발 프로젝트 경험 보유", "Github 활동 활발"], "risks": ["알고리즘 문제풀이 부족", "대규모 시스템 경험 없음", "SW역량테스트 준비 필요"], "recommendations": ["백준/프로그래머스 하루 2문제 풀이", "토이 프로젝트로 MSA 경험", "SW역량테스트 A형 준비"], "next_steps": ["알고리즘 스터디 가입", "사이드 프로젝트 시작"], "confidence_reason": "2025 상반기 삼성 합격자 스펙 데이터 기반"}}'::jsonb,
    0.78,
    'REALISTIC_SEED'
);

-- 데이터 사이언티스트 커리어패스 시나리오
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level, ins_user_id
) VALUES (
    '20002270',
    'career_path',
    '데이터 사이언티스트 커리어 준비',
    '네이버, 카카오, 쿠팡 등 IT기업 데이터 사이언티스트 포지션 목표. Python, SQL, ML 역량 필수.',
    '{"variables": [{"name": "target_role", "current_value": "software_engineer", "simulated_value": "data_scientist"}]}'::jsonb,
    '{"simulated_changes": [{"name": "target_role", "value": "data_scientist"}]}'::jsonb,
    '{"results": [
        {"metric_name": "직무 준비도", "current_value": 40.0, "simulated_value": 68.0, "change_percent": 70.0, "impact_level": "positive", "explanation": "Python, SQL, 통계/ML 기초, Pandas/Numpy 역량 개발 필요"},
        {"metric_name": "핵심 부족 역량", "current_value": 5, "simulated_value": 2, "change_percent": -60.0, "impact_level": "positive", "explanation": "부족 역량: 머신러닝, 딥러닝, 대용량 데이터 처리"}
    ], "recommendation": "데이터 사이언티스트 전환에는 6-12개월의 집중 학습이 필요합니다. Kaggle 프로젝트로 포트폴리오를 구축하세요.", "ai_analysis": {"summary": "데이터 사이언티스트는 통계/ML 기반 데이터 분석 및 예측 모델 구현 역량이 핵심입니다. 대학원 진학자도 많은 분야입니다.", "strengths": ["Python 프로그래밍 기초 보유", "수학/통계 기초 탄탄", "분석적 사고력"], "risks": ["ML/DL 실무 경험 부족", "대용량 데이터 처리 경험 없음", "포트폴리오 부족"], "recommendations": ["Kaggle 대회 참가", "개인 데이터 분석 프로젝트 수행", "SQL 고급 학습", "Pytorch/TensorFlow 학습"], "next_steps": ["Coursera ML 강좌 수강", "Kaggle 입문 대회 참가"], "confidence_reason": "IT기업 데이터 사이언티스트 채용 요건 분석"}}'::jsonb,
    0.68,
    'REALISTIC_SEED'
);

-- AI 엔지니어 커리어패스 시나리오
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level, ins_user_id
) VALUES (
    '20002271',
    'career_path',
    'AI/ML 엔지니어 커리어 목표',
    '네이버 웹툰, OP.GG 등 AI 활용 기업의 MLOps/AI Engineer 포지션 목표. 생성형 AI 이해 필수.',
    '{"variables": [{"name": "target_role", "current_value": "backend_developer", "simulated_value": "ai_engineer"}]}'::jsonb,
    '{"simulated_changes": [{"name": "target_role", "value": "ai_engineer"}]}'::jsonb,
    '{"results": [
        {"metric_name": "직무 준비도", "current_value": 35.0, "simulated_value": 65.0, "change_percent": 85.7, "impact_level": "positive", "explanation": "딥러닝, MLOps, 클라우드(AWS/Azure) 역량 필수"},
        {"metric_name": "예상 연봉 범위", "current_value": 4000, "simulated_value": 6500, "change_percent": 62.5, "impact_level": "positive", "explanation": "AI 엔지니어 초봉 6,000~7,000만원 예상 (2025년 기준)"}
    ], "recommendation": "AI 엔지니어는 높은 수요와 연봉을 제공하지만 진입장벽도 높습니다. 체계적인 학습 계획이 필요합니다.", "ai_analysis": {"summary": "AI 엔지니어 시장은 생성형 AI 폭발적 성장으로 수요가 급증 중입니다. 클라우드 기반 MLOps 경험이 핵심 차별화 요소입니다.", "strengths": ["프로그래밍 기초 탄탄", "빠른 학습 능력", "새로운 기술에 대한 관심"], "risks": ["딥러닝 실무 경험 부족", "GPU 환경 경험 필요", "MLOps 파이프라인 이해 부족"], "recommendations": ["Hugging Face 모델 파인튜닝 경험", "AWS SageMaker 실습", "개인 AI 프로젝트 GitHub 공개", "생성형 AI API 활용 프로젝트"], "next_steps": ["LLM 파인튜닝 튜토리얼 따라하기", "AWS 프리티어로 ML 서비스 체험"], "confidence_reason": "AI 엔지니어 채용공고 및 연봉 데이터 분석 (2025년 기준)"}}'::jsonb,
    0.65,
    'REALISTIC_SEED'
);

-- ============================================
-- 2. Skill Development Scenarios (skill_development)
-- Based on actual certification data
-- ============================================

-- AWS 자격증 취득 시나리오
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level, ins_user_id
) VALUES (
    '20002268',
    'skill_development',
    'AWS 클라우드 자격증 취득 계획',
    'AWS Certified Cloud Practitioner → Solutions Architect Associate 단계별 취득. 2025년 자격증 보유자 평균 연봉: Associate 약 6,000만원.',
    '{"variables": [{"name": "skill_aws_cloud", "current_value": 1, "simulated_value": 3}, {"name": "hours_per_week", "current_value": 0, "simulated_value": 10}]}'::jsonb,
    '{"simulated_changes": [{"name": "skill_aws_cloud", "value": 3}, {"name": "hours_per_week", "value": 10}]}'::jsonb,
    '{"results": [
        {"metric_name": "AWS Cloud 레벨", "current_value": 1, "simulated_value": 3, "change_percent": 200.0, "impact_level": "positive", "explanation": "스킬 레벨 1 → 3 향상 (예상 학습시간: 120시간)"},
        {"metric_name": "예상 소요 시간", "current_value": 0, "simulated_value": 120, "change_percent": 100.0, "impact_level": "neutral", "explanation": "총 120시간 학습 필요 (주 10시간 기준 약 12주)"},
        {"metric_name": "예상 역량 점수 증가", "current_value": 0, "simulated_value": 15.0, "change_percent": 15.0, "impact_level": "positive", "explanation": "클라우드 역량 점수 약 15점 증가 예상"}
    ], "recommendation": "AWS 자격증은 클라우드 취업 시장에서 높은 가치를 가집니다. Cloud Practitioner부터 시작하세요.", "ai_analysis": {"summary": "AWS 자격증 보유자 연봉 프리미엄 10-20%. 클라우드 마이그레이션 시장 연평균 28.24% 성장 전망(~2029년).", "strengths": ["온라인 학습 자료 풍부", "무료 재응시 프로모션 활용 가능", "실무 연계성 높음"], "risks": ["영어 시험 부담", "실습 환경 비용 발생 가능", "지속적 갱신 필요"], "recommendations": ["AWS Free Tier로 실습", "Udemy/Coursera 강좌 활용", "덤프 문제로 시험 패턴 익히기", "2월 15일까지 무료 재응시 프로모션 활용"], "next_steps": ["AWS 계정 생성 및 Free Tier 활성화", "Cloud Practitioner 학습 계획 수립"], "confidence_reason": "AWS 자격증 취득자 데이터 및 시장 전망 분석"}}'::jsonb,
    0.85,
    'REALISTIC_SEED'
);

-- 정보처리기사 자격증 시나리오
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level, ins_user_id
) VALUES (
    '20002269',
    'skill_development',
    '정보처리기사 자격증 취득 계획',
    '2025년 정보처리기사 시험 준비. 1회차: 필기 2월/실기 4월, 2회차: 필기 5월/실기 7월, 3회차: 필기 8월/실기 11월. 평균 합격률: 필기 35%, 실기 45%.',
    '{"variables": [{"name": "skill_certification", "current_value": 0, "simulated_value": 1}, {"name": "hours_per_week", "current_value": 0, "simulated_value": 15}]}'::jsonb,
    '{"simulated_changes": [{"name": "skill_certification", "value": 1}, {"name": "hours_per_week", "value": 15}]}'::jsonb,
    '{"results": [
        {"metric_name": "자격증 취득", "current_value": 0, "simulated_value": 1, "change_percent": 100.0, "impact_level": "positive", "explanation": "정보처리기사 자격증 취득 예상"},
        {"metric_name": "예상 소요 시간", "current_value": 0, "simulated_value": 200, "change_percent": 100.0, "impact_level": "neutral", "explanation": "총 200시간 학습 필요 (주 15시간 기준 약 13주)"},
        {"metric_name": "취업 경쟁력 증가", "current_value": 60, "simulated_value": 75, "change_percent": 25.0, "impact_level": "positive", "explanation": "IT기업, 공공기관, 금융권 취업 시 우대"}
    ], "recommendation": "정보처리기사는 IT 분야 필수 자격증입니다. 실기 시험 합격률이 낮으니 실습에 충분한 시간을 투자하세요.", "ai_analysis": {"summary": "정보처리기사는 데이터베이스 관리, 시스템 설계, 소프트웨어 개발 역량을 인증하는 국가공인 자격증입니다.", "strengths": ["IT/데이터 분야 전문성 인정", "공공기관/금융권 가산점", "승진/보수 우대"], "risks": ["필기 합격률 35%로 낮음", "실기 실습 환경 필요", "C/Java 프로그래밍 필수"], "recommendations": ["기출문제 5개년 반복 풀이", "실기는 SQL과 프로그래밍 집중", "수제비/이기적 교재 활용", "온라인 모의고사 활용"], "next_steps": ["2025년 시험일정 확인 및 접수", "기출문제 분석 시작"], "confidence_reason": "Q-net 정보처리기사 시험 데이터 분석"}}'::jsonb,
    0.75,
    'REALISTIC_SEED'
);

-- Python/데이터분석 스킬 개발 시나리오
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level, ins_user_id
) VALUES (
    '20002270',
    'skill_development',
    'Python 데이터분석 역량 강화',
    'Python, Pandas, NumPy, 시각화(Matplotlib/Seaborn) 역량 개발. 데이터 사이언티스트 필수 스킬.',
    '{"variables": [{"name": "skill_python", "current_value": 2, "simulated_value": 4}, {"name": "skill_pandas", "current_value": 1, "simulated_value": 4}, {"name": "hours_per_week", "current_value": 0, "simulated_value": 12}]}'::jsonb,
    '{"simulated_changes": [{"name": "skill_python", "value": 4}, {"name": "skill_pandas", "value": 4}, {"name": "hours_per_week", "value": 12}]}'::jsonb,
    '{"results": [
        {"metric_name": "Python 레벨", "current_value": 2, "simulated_value": 4, "change_percent": 100.0, "impact_level": "positive", "explanation": "스킬 레벨 2 → 4 향상 (예상 학습시간: 90시간)"},
        {"metric_name": "Pandas 레벨", "current_value": 1, "simulated_value": 4, "change_percent": 300.0, "impact_level": "positive", "explanation": "스킬 레벨 1 → 4 향상 (예상 학습시간: 120시간)"},
        {"metric_name": "예상 역량 점수 증가", "current_value": 0, "simulated_value": 18.0, "change_percent": 18.0, "impact_level": "positive", "explanation": "데이터분석 역량 점수 약 18점 증가 예상"}
    ], "recommendation": "Python 데이터분석 역량은 데이터 사이언티스트, 데이터 애널리스트 취업의 핵심입니다.", "ai_analysis": {"summary": "Python은 데이터 분석, ML/DL의 표준 언어입니다. Pandas와 함께 실무에서 가장 많이 사용됩니다.", "strengths": ["방대한 학습 자료", "실무 활용도 높음", "커뮤니티 지원 활발"], "risks": ["고급 기능 학습 곡선", "최적화 기법 별도 학습 필요"], "recommendations": ["Kaggle 데이터셋으로 실습", "개인 분석 프로젝트 진행", "GitHub에 노트북 공개", "통계 기초도 함께 학습"], "next_steps": ["점프 투 파이썬 완독", "Kaggle Titanic 대회 도전"], "confidence_reason": "데이터 사이언티스트 채용공고 분석"}}'::jsonb,
    0.82,
    'REALISTIC_SEED'
);

-- ============================================
-- 3. Opportunity Scenarios (opportunity)
-- Based on actual Korean internship programs
-- ============================================

-- 삼성전자 인턴십 참여 시나리오
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level, ins_user_id
) VALUES (
    '20002268',
    'opportunity',
    '삼성전자 대학생 인턴십 참여 효과',
    '삼성전자 DS/DX부문 8주 인턴십 참여 시 경력 개발 효과 분석. 정규직 전환율 약 70%.',
    '{"variables": [{"name": "opportunity_type", "current_value": "없음", "simulated_value": "internship"}, {"name": "duration_months", "current_value": 0, "simulated_value": 2}]}'::jsonb,
    '{"simulated_changes": [{"name": "opportunity_type", "value": "internship"}, {"name": "duration_months", "value": 2}]}'::jsonb,
    '{"results": [
        {"metric_name": "경력 점수 증가", "current_value": 10, "simulated_value": 60, "change_percent": 500.0, "impact_level": "positive", "explanation": "대기업 인턴 경험으로 경력 점수 50점 향상"},
        {"metric_name": "포트폴리오 가치", "current_value": 10, "simulated_value": 50, "change_percent": 400.0, "impact_level": "positive", "explanation": "실무 경험으로 포트폴리오 가치 40점 증가"},
        {"metric_name": "네트워크 확장", "current_value": 0, "simulated_value": 30, "change_percent": 100.0, "impact_level": "positive", "explanation": "예상 새로운 연결: 약 30명"}
    ], "recommendation": "삼성 인턴십은 정규직 전환 가능성이 높아 최우선 기회입니다. GSAT과 면접 준비를 철저히 하세요.", "ai_analysis": {"summary": "삼성전자 인턴십은 국내 최고 수준의 경력 개발 기회입니다. 정규직 전환율 약 70%로 취업 직결 가능성이 높습니다.", "strengths": ["대기업 실무 경험 획득", "정규직 전환 가능성 높음", "네트워크 구축 기회", "체계적인 교육 프로그램"], "risks": ["경쟁률 매우 높음 (100:1 이상)", "GSAT 통과 필요", "지방 근무 가능성"], "recommendations": ["GSAT 집중 준비", "직무 관련 프로젝트 경험 쌓기", "삼성 기업문화 이해", "면접 스터디 참여"], "next_steps": ["삼성채용 홈페이지 회원가입", "GSAT 기출문제 분석 시작"], "confidence_reason": "2025 삼성 인턴 합격후기 및 채용 데이터 분석"}}'::jsonb,
    0.92,
    'REALISTIC_SEED'
);

-- SK하이닉스 인턴십 시나리오
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level, ins_user_id
) VALUES (
    '20002269',
    'opportunity',
    'SK하이닉스 대학생 인턴십 참여',
    'SK하이닉스 반도체 설계/공정 인턴십 참여 효과 분석. 이천/청주 근무.',
    '{"variables": [{"name": "opportunity_type", "current_value": "없음", "simulated_value": "internship"}, {"name": "duration_months", "current_value": 0, "simulated_value": 2}]}'::jsonb,
    '{"simulated_changes": [{"name": "opportunity_type", "value": "internship"}, {"name": "duration_months", "value": 2}]}'::jsonb,
    '{"results": [
        {"metric_name": "경력 점수 증가", "current_value": 10, "simulated_value": 55, "change_percent": 450.0, "impact_level": "positive", "explanation": "반도체 대기업 인턴 경험으로 경력 점수 45점 향상"},
        {"metric_name": "포트폴리오 가치", "current_value": 10, "simulated_value": 45, "change_percent": 350.0, "impact_level": "positive", "explanation": "반도체 실무 경험으로 포트폴리오 가치 35점 증가"},
        {"metric_name": "네트워크 확장", "current_value": 0, "simulated_value": 25, "change_percent": 100.0, "impact_level": "positive", "explanation": "예상 새로운 연결: 약 25명"}
    ], "recommendation": "SK하이닉스 인턴십도 반도체 업계 진출에 매우 유리합니다. 메모리 반도체 기술에 대한 이해를 높이세요.", "ai_analysis": {"summary": "SK하이닉스는 메모리 반도체 세계 2위 기업으로, 인턴십을 통해 최첨단 반도체 기술을 경험할 수 있습니다.", "strengths": ["세계적 수준 기술력 경험", "복지 수준 높음", "정규직 전환 기회"], "risks": ["이천/청주 지방 근무", "경쟁률 높음", "전공 관련성 중요"], "recommendations": ["반도체 공정 기초 학습", "SKCT 유형 파악", "면접에서 기술 관심도 어필"], "next_steps": ["SK Careers 회원가입", "반도체 기초 강의 수강"], "confidence_reason": "SK하이닉스 채용 정보 및 합격 후기 분석"}}'::jsonb,
    0.85,
    'REALISTIC_SEED'
);

-- 스타트업 인턴십 시나리오
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level, ins_user_id
) VALUES (
    '20002270',
    'opportunity',
    'AI 스타트업 인턴십 참여',
    'AI/데이터 스타트업 3개월 인턴십. 실무 중심 경험과 빠른 성장 기회.',
    '{"variables": [{"name": "opportunity_type", "current_value": "없음", "simulated_value": "internship"}, {"name": "duration_months", "current_value": 0, "simulated_value": 3}]}'::jsonb,
    '{"simulated_changes": [{"name": "opportunity_type", "value": "internship"}, {"name": "duration_months", "value": 3}]}'::jsonb,
    '{"results": [
        {"metric_name": "경력 점수 증가", "current_value": 10, "simulated_value": 45, "change_percent": 350.0, "impact_level": "positive", "explanation": "스타트업 실무 경험으로 경력 점수 35점 향상"},
        {"metric_name": "포트폴리오 가치", "current_value": 10, "simulated_value": 55, "change_percent": 450.0, "impact_level": "positive", "explanation": "실제 프로덕트 기여로 포트폴리오 가치 45점 증가"},
        {"metric_name": "스킬 성장 속도", "current_value": 1.0, "simulated_value": 2.5, "change_percent": 150.0, "impact_level": "positive", "explanation": "스타트업 환경에서 스킬 성장 속도 2.5배"}
    ], "recommendation": "스타트업 인턴십은 빠른 성장과 실무 중심 경험에 유리합니다. 단, 기업 안정성을 확인하세요.", "ai_analysis": {"summary": "AI 스타트업은 빠른 기술 성장과 다양한 역할 경험이 가능합니다. 대기업보다 실무 투입이 빠릅니다.", "strengths": ["실무 중심 업무", "빠른 피드백과 성장", "다양한 역할 경험", "자유로운 문화"], "risks": ["고용 안정성 낮음", "체계적 교육 부족", "긴 근무시간 가능성"], "recommendations": ["기업 투자 현황 확인", "CEO/팀 면담 요청", "구체적 업무 범위 확인"], "next_steps": ["AI 스타트업 채용 플랫폼 가입", "관심 기업 리스트업"], "confidence_reason": "AI 스타트업 인턴 경험자 인터뷰 분석"}}'::jsonb,
    0.78,
    'REALISTIC_SEED'
);

-- 오픈소스 프로젝트 참여 시나리오
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level, ins_user_id
) VALUES (
    '20002271',
    'opportunity',
    '오픈소스 프로젝트 기여 활동',
    'GitHub 오픈소스 프로젝트 기여. 글로벌 개발자 커뮤니티 참여와 실력 향상.',
    '{"variables": [{"name": "opportunity_type", "current_value": "없음", "simulated_value": "project"}, {"name": "duration_months", "current_value": 0, "simulated_value": 6}]}'::jsonb,
    '{"simulated_changes": [{"name": "opportunity_type", "value": "project"}, {"name": "duration_months", "value": 6}]}'::jsonb,
    '{"results": [
        {"metric_name": "경력 점수 증가", "current_value": 10, "simulated_value": 35, "change_percent": 250.0, "impact_level": "positive", "explanation": "오픈소스 기여로 경력 점수 25점 향상"},
        {"metric_name": "포트폴리오 가치", "current_value": 10, "simulated_value": 50, "change_percent": 400.0, "impact_level": "positive", "explanation": "공개된 기여 내역으로 포트폴리오 가치 40점 증가"},
        {"metric_name": "네트워크 확장", "current_value": 0, "simulated_value": 15, "change_percent": 100.0, "impact_level": "positive", "explanation": "글로벌 개발자 네트워크 확장"}
    ], "recommendation": "오픈소스 기여는 실력 증명과 글로벌 네트워크 구축에 효과적입니다. 관심 프로젝트를 찾아 시작하세요.", "ai_analysis": {"summary": "오픈소스 기여는 해외 기업 취업, 글로벌 네트워크 구축에 매우 유리합니다. 코드 리뷰를 통해 실력도 향상됩니다.", "strengths": ["글로벌 네트워크", "코드 품질 향상", "취업 시 강력한 증거", "무료 학습 기회"], "risks": ["시간 투자 필요", "진입 장벽 있음", "리젝션 경험 가능"], "recommendations": ["good first issue 라벨 찾기", "문서화/번역부터 시작", "작은 버그 수정으로 시작", "커뮤니티 활동 참여"], "next_steps": ["관심 기술 스택의 프로젝트 탐색", "GitHub 프로필 정리"], "confidence_reason": "오픈소스 기여자 커리어 데이터 분석"}}'::jsonb,
    0.72,
    'REALISTIC_SEED'
);

-- ============================================
-- 4. Course Selection Scenarios (course_selection)
-- ============================================

-- AI/ML 과목 집중 수강 시나리오
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level, ins_user_id
) VALUES (
    '20002268',
    'course_selection',
    '2026-1학기 AI/ML 과목 집중 수강',
    '머신러닝, 딥러닝, 데이터마이닝 과목 수강 시 GPA 및 역량 영향 분석.',
    '{"variables": [{"name": "course", "current_value": "CS401", "simulated_value": "A"}, {"name": "course", "current_value": "CS402", "simulated_value": "A"}, {"name": "course", "current_value": "CS403", "simulated_value": "B+"}]}'::jsonb,
    '{"simulated_changes": [{"name": "course_CS401", "value": "A"}, {"name": "course_CS402", "value": "A"}, {"name": "course_CS403", "value": "B+"}]}'::jsonb,
    '{"results": [
        {"metric_name": "예상 GPA 변화", "current_value": 3.65, "simulated_value": 3.72, "change_percent": 1.9, "impact_level": "positive", "explanation": "GPA 3.65 → 3.72 (변화: +0.07)"},
        {"metric_name": "취득 학점", "current_value": 90, "simulated_value": 99, "change_percent": 10.0, "impact_level": "positive", "explanation": "9학점 추가 취득 (총 99학점)"},
        {"metric_name": "AI 역량 기여도", "current_value": 0, "simulated_value": 25.0, "change_percent": 25.0, "impact_level": "positive", "explanation": "AI/ML 역량 점수 약 25점 향상 예상"}
    ], "recommendation": "AI/ML 과목 집중 수강은 데이터 사이언티스트/AI 엔지니어 목표에 적합합니다.", "ai_analysis": {"summary": "AI/ML 관련 과목 수강은 해당 분야 취업에 필수적입니다. 단, 수학적 기초가 탄탄해야 좋은 성적을 받을 수 있습니다.", "strengths": ["취업 시 직접 연관 과목", "실습 프로젝트 경험", "교수님 추천서 가능"], "risks": ["과목 난이도 높음", "수학 기초 필요", "학점 관리 부담"], "recommendations": ["선형대수, 확률통계 선수강 확인", "프로젝트 팀원 미리 섭외", "GPU 환경 접근 확보"], "next_steps": ["수강신청 일정 확인", "선수과목 이수 여부 점검"], "confidence_reason": "AI/ML 과목 성적 분포 및 취업 데이터 분석"}}'::jsonb,
    0.78,
    'REALISTIC_SEED'
);

-- 웹개발 풀스택 과목 수강 시나리오
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level, ins_user_id
) VALUES (
    '20002269',
    'course_selection',
    '2026-1학기 웹개발 풀스택 과목 수강',
    '웹프로그래밍, 데이터베이스, 소프트웨어공학 과목 수강 시 영향 분석.',
    '{"variables": [{"name": "course", "current_value": "SW201", "simulated_value": "A"}, {"name": "course", "current_value": "SW202", "simulated_value": "A"}, {"name": "course", "current_value": "SW301", "simulated_value": "A"}]}'::jsonb,
    '{"simulated_changes": [{"name": "course_SW201", "value": "A"}, {"name": "course_SW202", "value": "A"}, {"name": "course_SW301", "value": "A"}]}'::jsonb,
    '{"results": [
        {"metric_name": "예상 GPA 변화", "current_value": 3.50, "simulated_value": 3.65, "change_percent": 4.3, "impact_level": "positive", "explanation": "GPA 3.50 → 3.65 (변화: +0.15)"},
        {"metric_name": "취득 학점", "current_value": 80, "simulated_value": 89, "change_percent": 11.3, "impact_level": "positive", "explanation": "9학점 추가 취득 (총 89학점)"},
        {"metric_name": "웹개발 역량 기여도", "current_value": 0, "simulated_value": 22.0, "change_percent": 22.0, "impact_level": "positive", "explanation": "웹개발 역량 점수 약 22점 향상 예상"}
    ], "recommendation": "풀스택 웹개발 과목 조합은 프론트엔드/백엔드 개발자 취업에 적합합니다.", "ai_analysis": {"summary": "웹개발 과목은 취업 시장 수요가 높고 프로젝트로 포트폴리오 구축이 용이합니다.", "strengths": ["취업 연계성 높음", "프로젝트 결과물 획득", "팀워크 경험"], "risks": ["프로젝트 부담 큼", "팀 협업 갈등 가능", "최신 기술 트렌드 빠른 변화"], "recommendations": ["개인 프로젝트도 병행", "GitHub 포트폴리오 관리", "React/Spring 추가 학습"], "next_steps": ["수강신청 준비", "팀 프로젝트 아이디어 구상"], "confidence_reason": "웹개발 과목 취업률 및 성적 분포 분석"}}'::jsonb,
    0.82,
    'REALISTIC_SEED'
);

-- ============================================
-- 5. Timeline Scenarios (timeline)
-- ============================================

-- 4학년 2학기 취업 준비 완료 타임라인
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level, ins_user_id
) VALUES (
    '20002268',
    'timeline',
    '2027년 2월 취업 준비 완료 타임라인',
    '4학년 2학기 졸업 시점에 대기업 SW개발 취업 준비 완료 목표.',
    '{"variables": [{"name": "timeline_type", "current_value": "job_ready", "simulated_value": "job_ready"}, {"name": "target_date", "current_value": "2026-01-24", "simulated_value": "2027-02-28"}]}'::jsonb,
    '{"simulated_changes": [{"name": "timeline_type", "value": "job_ready"}, {"name": "target_date", "value": "2027-02-28"}]}'::jsonb,
    '{"results": [
        {"metric_name": "목표 달성 확률", "current_value": 0, "simulated_value": 75.0, "change_percent": 75.0, "impact_level": "positive", "explanation": "현재 준비도와 남은 기간 기준 75% 달성 가능"},
        {"metric_name": "필요 노력량", "current_value": 0, "simulated_value": 15, "change_percent": 100.0, "impact_level": "neutral", "explanation": "주당 15시간 추가 노력 필요"}
    ], "recommendation": "13개월 내 취업 준비 완료는 충분히 가능합니다. 체계적인 계획 수립이 필요합니다.", "ai_analysis": {"summary": "2027년 2월 대기업 취업 목표 달성을 위해 단계별 준비가 필요합니다.", "strengths": ["충분한 준비 기간", "학점 관리 가능", "인턴 경험 확보 시간 있음"], "risks": ["게으름 위험", "경쟁률 상승 추세", "예상치 못한 변수"], "recommendations": ["2025 하반기 인턴 지원", "알고리즘 꾸준히 풀기", "토익 850+ 확보", "프로젝트 포트폴리오 완성"], "next_steps": ["월별 목표 수립", "스터디 그룹 결성"], "confidence_reason": "취업 준비 기간 및 스펙 요구사항 분석"}}'::jsonb,
    0.75,
    'REALISTIC_SEED'
);

-- 추가 학생들에 대한 시나리오 생성 (더 많은 데이터)
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level, ins_user_id
)
SELECT
    s.student_id,
    'career_path',
    '백엔드 개발자 커리어 준비',
    'Java/Spring 기반 백엔드 개발자 목표. 네이버, 카카오, 토스 등 IT기업 타겟.',
    '{"variables": [{"name": "target_role", "current_value": "미정", "simulated_value": "backend_developer"}]}'::jsonb,
    '{"simulated_changes": [{"name": "target_role", "value": "backend_developer"}]}'::jsonb,
    ('{"results": [{"metric_name": "직무 준비도", "current_value": ' || (40 + FLOOR(RANDOM() * 20))::text || ', "simulated_value": ' || (65 + FLOOR(RANDOM() * 20))::text || ', "change_percent": 50.0, "impact_level": "positive", "explanation": "Java, Spring, JPA 역량 강화 필요"}], "recommendation": "백엔드 개발자는 꾸준한 수요가 있는 직무입니다.", "ai_analysis": {"summary": "백엔드 개발자는 안정적인 커리어 패스입니다.", "strengths": ["수요 많음", "연봉 양호"], "risks": ["경쟁 치열"], "recommendations": ["알고리즘 학습", "프로젝트 경험"], "next_steps": ["Spring 학습"], "confidence_reason": "채용시장 분석"}}')::jsonb,
    (0.65 + RANDOM() * 0.2)::DECIMAL(3,2),
    'REALISTIC_SEED'
FROM tb_student s
WHERE s.current_grade >= 2
LIMIT 20;

-- 프론트엔드 개발자 시나리오 추가
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level, ins_user_id
)
SELECT
    s.student_id,
    'career_path',
    '프론트엔드 개발자 커리어 준비',
    'React/TypeScript 기반 프론트엔드 개발자 목표. 사용자 경험과 UI/UX 중시.',
    '{"variables": [{"name": "target_role", "current_value": "미정", "simulated_value": "frontend_developer"}]}'::jsonb,
    '{"simulated_changes": [{"name": "target_role", "value": "frontend_developer"}]}'::jsonb,
    ('{"results": [{"metric_name": "직무 준비도", "current_value": ' || (35 + FLOOR(RANDOM() * 20))::text || ', "simulated_value": ' || (60 + FLOOR(RANDOM() * 25))::text || ', "change_percent": 60.0, "impact_level": "positive", "explanation": "React, TypeScript, CSS 역량 강화 필요"}], "recommendation": "프론트엔드 개발자는 UI/UX에 관심이 있다면 적합합니다.", "ai_analysis": {"summary": "프론트엔드 시장은 계속 성장 중입니다.", "strengths": ["시각적 결과물", "빠른 피드백"], "risks": ["기술 변화 빠름"], "recommendations": ["React 학습", "포트폴리오 구축"], "next_steps": ["개인 프로젝트 시작"], "confidence_reason": "채용시장 분석"}}')::jsonb,
    (0.60 + RANDOM() * 0.25)::DECIMAL(3,2),
    'REALISTIC_SEED'
FROM tb_student s
WHERE s.current_grade >= 2
LIMIT 15;

-- ============================================
-- Verification Query
-- ============================================

-- SELECT scenario_type, COUNT(*) as count
-- FROM tb_simulation_scenario
-- WHERE ins_user_id = 'REALISTIC_SEED'
-- GROUP BY scenario_type
-- ORDER BY count DESC;
