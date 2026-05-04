-- Delete old generic "Simulation XXX" data
DELETE FROM idino_career.tb_simulation_scenario WHERE title LIKE 'Simulation %';

-- Create realistic scenario templates and insert data
DO $$
DECLARE
    student_rec RECORD;
    scenario_templates JSONB;
    template JSONB;
    template_idx INT;
    num_scenarios INT;
    i INT;
BEGIN
    -- Define scenario templates
    scenario_templates := '[
        {
            "type": "career_path",
            "title": "백엔드 개발자 커리어 준비",
            "description": "Spring Boot, Java 기반 백엔드 개발자 목표. RESTful API 설계와 데이터베이스 최적화 역량 개발.",
            "base_state": {"variables": [{"name": "target_role", "current_value": "미정", "simulated_value": "backend_developer"}]},
            "changes": {"simulated_changes": [{"name": "target_role", "value": "backend_developer"}]},
            "predicted_outcomes": {
                "results": [
                    {"metric_name": "직무 준비도", "current_value": 52.0, "simulated_value": 78.0, "change_percent": 50.0, "impact_level": "positive", "explanation": "Java, Spring, DB 역량 강화로 준비도 향상 가능"},
                    {"metric_name": "핵심 부족 역량", "current_value": 4, "simulated_value": 1, "change_percent": -75.0, "impact_level": "positive", "explanation": "MSA 설계 경험 부족이 주요 개선 포인트"}
                ],
                "ai_analysis": {
                    "summary": "백엔드 개발자는 Java/Spring 기반 서버 개발 역량이 핵심입니다. DB 설계와 API 개발 경험을 쌓으세요.",
                    "strengths": ["Java 프로그래밍 기초 탄탄", "SQL 기본 지식 보유", "협업 경험 있음"],
                    "risks": ["대규모 트래픽 처리 경험 부족", "클라우드 인프라 이해 부족"],
                    "recommendations": ["Spring Boot 프로젝트 수행", "JPA/MyBatis 심화 학습", "Docker, K8s 기초 학습"],
                    "next_steps": ["개인 프로젝트로 REST API 구현", "DB 설계 연습"],
                    "confidence_reason": "IT기업 백엔드 채용 요건 분석 기반"
                },
                "recommendation": "백엔드 개발자 준비를 위해 Spring Boot 프로젝트와 DB 심화 학습을 권장합니다."
            },
            "confidence": 0.75
        },
        {
            "type": "career_path",
            "title": "프론트엔드 개발자 커리어 준비",
            "description": "React/TypeScript 기반 프론트엔드 개발자 목표. 사용자 경험과 UI/UX 중시하는 서비스 개발 희망.",
            "base_state": {"variables": [{"name": "target_role", "current_value": "미정", "simulated_value": "frontend_developer"}]},
            "changes": {"simulated_changes": [{"name": "target_role", "value": "frontend_developer"}]},
            "predicted_outcomes": {
                "results": [
                    {"metric_name": "직무 준비도", "current_value": 48.0, "simulated_value": 76.0, "change_percent": 58.3, "impact_level": "positive", "explanation": "React, TypeScript 심화로 준비도 대폭 향상"},
                    {"metric_name": "핵심 부족 역량", "current_value": 5, "simulated_value": 2, "change_percent": -60.0, "impact_level": "positive", "explanation": "상태관리, 성능 최적화 경험 필요"}
                ],
                "ai_analysis": {
                    "summary": "프론트엔드 개발자는 React/Vue 기반 SPA 개발과 UI/UX 이해가 핵심입니다.",
                    "strengths": ["HTML/CSS 기초 탄탄", "JavaScript ES6+ 이해", "반응형 디자인 이해"],
                    "risks": ["복잡한 상태관리 경험 부족", "테스트 코드 작성 경험 부족"],
                    "recommendations": ["React 공식 문서 정독", "Redux/Zustand 학습", "Jest/Cypress 테스팅 학습"],
                    "next_steps": ["개인 포트폴리오 사이트 제작", "오픈소스 기여 시작"],
                    "confidence_reason": "프론트엔드 개발자 채용 트렌드 분석"
                },
                "recommendation": "React와 TypeScript 심화 학습 후 포트폴리오 프로젝트를 진행하세요."
            },
            "confidence": 0.73
        },
        {
            "type": "career_path",
            "title": "데이터 사이언티스트 커리어 준비",
            "description": "네이버, 카카오, 쿠팡 등 IT기업 데이터 사이언티스트 포지션 목표. Python, SQL, ML 역량 필수.",
            "base_state": {"variables": [{"name": "target_role", "current_value": "software_engineer", "simulated_value": "data_scientist"}]},
            "changes": {"simulated_changes": [{"name": "target_role", "value": "data_scientist"}]},
            "predicted_outcomes": {
                "results": [
                    {"metric_name": "직무 준비도", "current_value": 40.0, "simulated_value": 68.0, "change_percent": 70.0, "impact_level": "positive", "explanation": "Python, SQL, 통계/ML 기초 역량 개발 필요"},
                    {"metric_name": "핵심 부족 역량", "current_value": 5, "simulated_value": 2, "change_percent": -60.0, "impact_level": "positive", "explanation": "머신러닝, 딥러닝 실무 경험 필요"}
                ],
                "ai_analysis": {
                    "summary": "데이터 사이언티스트는 통계/ML 기반 분석과 예측 모델 구현이 핵심입니다.",
                    "strengths": ["Python 기초 보유", "수학/통계 기초 탄탄", "분석적 사고력"],
                    "risks": ["ML/DL 실무 경험 부족", "대용량 데이터 처리 경험 없음"],
                    "recommendations": ["Kaggle 대회 참가", "개인 데이터 분석 프로젝트", "SQL 고급 학습"],
                    "next_steps": ["Coursera ML 강좌 수강", "Kaggle 입문 대회 참가"],
                    "confidence_reason": "IT기업 DS 채용 요건 분석"
                },
                "recommendation": "데이터 사이언티스트 전환에는 6-12개월 집중 학습이 필요합니다."
            },
            "confidence": 0.68
        },
        {
            "type": "skill_development",
            "title": "정보처리기사 자격증 취득 계획",
            "description": "2025년 정보처리기사 필기/실기 합격 목표. 국가공인 IT 자격증으로 취업 경쟁력 강화.",
            "base_state": {"variables": [{"name": "certification", "current_value": "없음", "simulated_value": "정보처리기사"}]},
            "changes": {"simulated_changes": [{"name": "certification", "value": "정보처리기사"}]},
            "predicted_outcomes": {
                "results": [
                    {"metric_name": "자격증 점수", "current_value": 0, "simulated_value": 15, "change_percent": 100.0, "impact_level": "positive", "explanation": "정보처리기사 취득 시 15점 추가"},
                    {"metric_name": "취업 경쟁력", "current_value": 60, "simulated_value": 75, "change_percent": 25.0, "impact_level": "positive", "explanation": "IT 직군 지원 시 필수 자격증"}
                ],
                "ai_analysis": {
                    "summary": "정보처리기사는 IT 직군 취업의 기본 자격증입니다. 필기 60점, 실기 60점 이상 합격.",
                    "strengths": ["컴퓨터 전공 지식 보유", "프로그래밍 경험", "충분한 준비 시간"],
                    "risks": ["실기 코딩 문제 난이도 상승 추세", "합격률 30% 내외"],
                    "recommendations": ["기출문제 3회독 이상", "실기 알고리즘 집중 연습", "오답노트 정리"],
                    "next_steps": ["시나공 필기 교재 구매", "기출문제 앱 설치"],
                    "confidence_reason": "정보처리기사 합격자 학습 패턴 분석"
                },
                "recommendation": "정보처리기사는 3개월 집중 학습으로 취득 가능합니다. 기출문제 반복이 핵심입니다."
            },
            "confidence": 0.82
        },
        {
            "type": "skill_development",
            "title": "AWS 클라우드 자격증 취득 계획",
            "description": "AWS Certified Solutions Architect - Associate 자격증 취득 목표. 클라우드 인프라 역량 강화.",
            "base_state": {"variables": [{"name": "certification", "current_value": "없음", "simulated_value": "AWS SAA"}]},
            "changes": {"simulated_changes": [{"name": "certification", "value": "AWS SAA"}]},
            "predicted_outcomes": {
                "results": [
                    {"metric_name": "클라우드 역량 점수", "current_value": 30, "simulated_value": 80, "change_percent": 166.7, "impact_level": "positive", "explanation": "AWS 핵심 서비스 설계 역량 확보"},
                    {"metric_name": "취업 경쟁력", "current_value": 65, "simulated_value": 85, "change_percent": 30.8, "impact_level": "positive", "explanation": "클라우드 기반 기업 지원 시 큰 강점"}
                ],
                "ai_analysis": {
                    "summary": "AWS SAA는 클라우드 아키텍처 설계 역량을 증명하는 글로벌 인정 자격증입니다.",
                    "strengths": ["기초 네트워크 지식 보유", "리눅스 사용 경험", "학습 의지 높음"],
                    "risks": ["실습 환경 구축 비용 발생", "영어 시험 난이도"],
                    "recommendations": ["AWS Free Tier 활용 실습", "Udemy 강좌 수강", "Practice Exam 반복"],
                    "next_steps": ["AWS 계정 생성", "SAA 학습 로드맵 수립"],
                    "confidence_reason": "AWS 자격증 합격자 학습 패턴 분석"
                },
                "recommendation": "AWS SAA는 2-3개월 학습으로 취득 가능합니다. 실습 위주 학습을 권장합니다."
            },
            "confidence": 0.78
        },
        {
            "type": "skill_development",
            "title": "Python 데이터분석 역량 강화",
            "description": "Pandas, NumPy, Matplotlib 등 데이터 분석 핵심 라이브러리 마스터. 데이터 기반 의사결정 역량 확보.",
            "base_state": {"variables": [{"name": "skill_level", "current_value": "beginner", "simulated_value": "intermediate"}]},
            "changes": {"simulated_changes": [{"name": "skill_level", "value": "intermediate"}]},
            "predicted_outcomes": {
                "results": [
                    {"metric_name": "데이터분석 역량", "current_value": 35, "simulated_value": 70, "change_percent": 100.0, "impact_level": "positive", "explanation": "실무 수준 데이터 분석 가능"},
                    {"metric_name": "프로젝트 수행 능력", "current_value": 40, "simulated_value": 75, "change_percent": 87.5, "impact_level": "positive", "explanation": "독립적인 EDA 및 시각화 가능"}
                ],
                "ai_analysis": {
                    "summary": "Python 데이터 분석은 데이터 직군 필수 역량입니다. Pandas 숙련이 핵심입니다.",
                    "strengths": ["Python 기초 문법 이해", "논리적 사고력", "통계 기초"],
                    "risks": ["실제 데이터 경험 부족", "복잡한 전처리 어려움"],
                    "recommendations": ["Kaggle 데이터셋 분석 연습", "공공데이터 활용 프로젝트", "시각화 포트폴리오 구축"],
                    "next_steps": ["Pandas 공식 문서 학습", "분석 프로젝트 1개 완료"],
                    "confidence_reason": "데이터 분석가 역량 요구사항 분석"
                },
                "recommendation": "Pandas 집중 학습 후 실제 데이터로 분석 프로젝트를 수행하세요."
            },
            "confidence": 0.80
        },
        {
            "type": "course_selection",
            "title": "2026-1학기 AI/ML 과목 집중 수강",
            "description": "인공지능개론, 머신러닝, 딥러닝 과목 수강으로 AI 역량 체계적 구축. 4학년 캡스톤 준비.",
            "base_state": {"variables": [{"name": "courses", "current_value": [], "simulated_value": ["인공지능개론", "머신러닝", "딥러닝실습"]}]},
            "changes": {"simulated_changes": [{"name": "add_courses", "value": ["인공지능개론", "머신러닝", "딥러닝실습"]}]},
            "predicted_outcomes": {
                "results": [
                    {"metric_name": "AI 역량 점수", "current_value": 25, "simulated_value": 70, "change_percent": 180.0, "impact_level": "positive", "explanation": "이론과 실습을 통한 체계적 AI 역량 구축"},
                    {"metric_name": "예상 학점", "current_value": 0, "simulated_value": 9, "change_percent": 100.0, "impact_level": "positive", "explanation": "3과목 × 3학점 = 9학점 취득 예상"}
                ],
                "ai_analysis": {
                    "summary": "AI/ML 3과목 동시 수강은 부담이 크지만 시너지 효과가 큽니다.",
                    "strengths": ["선수과목 이수 완료", "프로그래밍 역량 보유", "수학 기초 탄탄"],
                    "risks": ["과목 난이도 높음", "프로젝트 과제 많음", "시험 기간 집중 필요"],
                    "recommendations": ["선행 학습 미리 시작", "스터디 그룹 구성", "교수님 오피스아워 활용"],
                    "next_steps": ["강의계획서 미리 확인", "관련 교재 선구매"],
                    "confidence_reason": "해당 과목 수강생 성적 분포 분석"
                },
                "recommendation": "AI 트랙 집중 수강을 권장합니다. 선행 학습이 성공의 열쇠입니다."
            },
            "confidence": 0.72
        },
        {
            "type": "course_selection",
            "title": "2026-1학기 웹개발 풀스택 과목 수강",
            "description": "웹프로그래밍, 데이터베이스, 소프트웨어공학 과목으로 풀스택 개발 역량 구축.",
            "base_state": {"variables": [{"name": "courses", "current_value": [], "simulated_value": ["웹프로그래밍", "데이터베이스", "소프트웨어공학"]}]},
            "changes": {"simulated_changes": [{"name": "add_courses", "value": ["웹프로그래밍", "데이터베이스", "소프트웨어공학"]}]},
            "predicted_outcomes": {
                "results": [
                    {"metric_name": "웹개발 역량", "current_value": 30, "simulated_value": 75, "change_percent": 150.0, "impact_level": "positive", "explanation": "프론트엔드부터 백엔드, DB까지 전 영역 역량 확보"},
                    {"metric_name": "프로젝트 역량", "current_value": 35, "simulated_value": 80, "change_percent": 128.6, "impact_level": "positive", "explanation": "팀 프로젝트 경험으로 협업 역량 향상"}
                ],
                "ai_analysis": {
                    "summary": "웹개발 3과목은 실무 프로젝트 수행에 최적화된 조합입니다.",
                    "strengths": ["프로그래밍 기초 탄탄", "HTML/CSS 경험", "호기심 높음"],
                    "risks": ["팀프로젝트 부담", "기술 스택 학습량 많음"],
                    "recommendations": ["React/Vue 중 하나 선택 집중", "MySQL 기초 미리 학습", "Git 협업 연습"],
                    "next_steps": ["개발환경 세팅", "기초 HTML/CSS 복습"],
                    "confidence_reason": "웹개발 과목 수강생 취업률 분석"
                },
                "recommendation": "웹개발 풀스택 과목 조합은 취업에 매우 유리합니다."
            },
            "confidence": 0.77
        },
        {
            "type": "opportunity",
            "title": "삼성전자 대학생 인턴십 참여 효과",
            "description": "2025년 하반기 삼성전자 대학생 인턴십 지원. 서류접수 8/27~9/3, GSAT 9/21 예정.",
            "base_state": {"variables": [{"name": "internship", "current_value": "없음", "simulated_value": "삼성전자 인턴"}]},
            "changes": {"simulated_changes": [{"name": "internship", "value": "삼성전자 인턴"}]},
            "predicted_outcomes": {
                "results": [
                    {"metric_name": "취업 경쟁력", "current_value": 55, "simulated_value": 90, "change_percent": 63.6, "impact_level": "positive", "explanation": "대기업 인턴 경험으로 취업 경쟁력 대폭 상승"},
                    {"metric_name": "실무 역량", "current_value": 30, "simulated_value": 70, "change_percent": 133.3, "impact_level": "positive", "explanation": "현업 프로젝트 참여로 실무 역량 급상승"}
                ],
                "ai_analysis": {
                    "summary": "삼성전자 인턴십은 정규직 전환율 50% 이상으로 취업에 매우 유리합니다.",
                    "strengths": ["학점 3.5 이상 유지", "관련 전공", "프로젝트 경험 보유"],
                    "risks": ["GSAT 통과 필요", "높은 경쟁률", "지방 근무 가능성"],
                    "recommendations": ["GSAT 3개월 전부터 준비", "자기소개서 구체적 작성", "면접 스터디 참여"],
                    "next_steps": ["GSAT 기출문제 풀이 시작", "삼성 채용 공고 모니터링"],
                    "confidence_reason": "삼성전자 인턴 합격자 스펙 분석"
                },
                "recommendation": "삼성전자 인턴십 합격을 위해 GSAT 집중 준비를 권장합니다."
            },
            "confidence": 0.65
        },
        {
            "type": "opportunity",
            "title": "AI 스타트업 인턴십 참여",
            "description": "AI/ML 스타트업에서 3개월 인턴십 경험. 실무 프로젝트 참여와 빠른 성장 기회.",
            "base_state": {"variables": [{"name": "internship", "current_value": "없음", "simulated_value": "AI 스타트업 인턴"}]},
            "changes": {"simulated_changes": [{"name": "internship", "value": "AI 스타트업 인턴"}]},
            "predicted_outcomes": {
                "results": [
                    {"metric_name": "AI 실무 역량", "current_value": 25, "simulated_value": 65, "change_percent": 160.0, "impact_level": "positive", "explanation": "실제 AI 프로젝트 참여로 실무 역량 급상승"},
                    {"metric_name": "스타트업 이해도", "current_value": 20, "simulated_value": 80, "change_percent": 300.0, "impact_level": "positive", "explanation": "스타트업 문화와 빠른 개발 사이클 경험"}
                ],
                "ai_analysis": {
                    "summary": "AI 스타트업 인턴십은 빠른 성장과 다양한 경험을 제공합니다.",
                    "strengths": ["Python 기초 보유", "ML 관심 높음", "자기주도 학습 가능"],
                    "risks": ["체계적 교육 부족 가능", "업무 범위 불명확", "복지 제한적"],
                    "recommendations": ["인턴십 전 ML 기초 학습", "GitHub 포트폴리오 정리", "기업 기술 블로그 분석"],
                    "next_steps": ["원티드/로켓펀치 검색", "AI 스타트업 리스트업"],
                    "confidence_reason": "AI 스타트업 인턴 후기 분석"
                },
                "recommendation": "AI 스타트업 인턴십은 빠른 성장을 원하는 학생에게 추천합니다."
            },
            "confidence": 0.70
        },
        {
            "type": "opportunity",
            "title": "오픈소스 프로젝트 기여 활동",
            "description": "GitHub 오픈소스 프로젝트 기여를 통한 실력 향상과 글로벌 개발자 네트워크 구축.",
            "base_state": {"variables": [{"name": "opensource_contribution", "current_value": 0, "simulated_value": 5}]},
            "changes": {"simulated_changes": [{"name": "opensource_contribution", "value": 5}]},
            "predicted_outcomes": {
                "results": [
                    {"metric_name": "GitHub 활동 점수", "current_value": 20, "simulated_value": 80, "change_percent": 300.0, "impact_level": "positive", "explanation": "PR 머지 경험으로 기여도 대폭 상승"},
                    {"metric_name": "글로벌 네트워크", "current_value": 0, "simulated_value": 50, "change_percent": 100.0, "impact_level": "positive", "explanation": "해외 개발자와의 협업 경험"}
                ],
                "ai_analysis": {
                    "summary": "오픈소스 기여는 실력 증명과 글로벌 네트워킹에 최고의 방법입니다.",
                    "strengths": ["Git 사용 경험", "영어 문서 독해 가능", "코드 리뷰 경험"],
                    "risks": ["PR 거절 가능성", "커뮤니케이션 어려움", "시간 투자 필요"],
                    "recommendations": ["good first issue 라벨 프로젝트 선택", "문서화 기여로 시작", "코드 스타일 가이드 준수"],
                    "next_steps": ["관심 프로젝트 3개 선정", "이슈 트래커 모니터링 시작"],
                    "confidence_reason": "오픈소스 기여자 커리어 분석"
                },
                "recommendation": "오픈소스 기여는 취업 면접에서 큰 차별화 포인트가 됩니다."
            },
            "confidence": 0.75
        },
        {
            "type": "timeline",
            "title": "2027년 2월 취업 준비 완료 타임라인",
            "description": "졸업 전 취업 확정 목표. 4학년 2학기까지 주요 역량 개발 및 채용 프로세스 완료.",
            "base_state": {"variables": [{"name": "target_date", "current_value": "미정", "simulated_value": "2027-02-28"}]},
            "changes": {"simulated_changes": [{"name": "target_date", "value": "2027-02-28"}]},
            "predicted_outcomes": {
                "results": [
                    {"metric_name": "취업 준비 완료율", "current_value": 35, "simulated_value": 95, "change_percent": 171.4, "impact_level": "positive", "explanation": "단계별 준비로 취업 목표 달성 가능"},
                    {"metric_name": "남은 준비 기간", "current_value": 24, "simulated_value": 24, "change_percent": 0, "impact_level": "neutral", "explanation": "약 24개월의 준비 기간 확보"}
                ],
                "ai_analysis": {
                    "summary": "2027년 2월 취업을 위해 역량 개발, 자격증, 인턴십을 병행해야 합니다.",
                    "strengths": ["충분한 준비 기간", "명확한 목표 설정", "현실적인 계획"],
                    "risks": ["예상치 못한 변수 발생 가능", "취업 시장 변동성"],
                    "recommendations": ["분기별 마일스톤 설정", "백업 플랜 수립", "멘토 확보"],
                    "milestones": [
                        {"date": "2025-06", "goal": "정보처리기사 취득"},
                        {"date": "2025-08", "goal": "여름 인턴십 지원"},
                        {"date": "2026-01", "goal": "포트폴리오 완성"},
                        {"date": "2026-08", "goal": "공채 시즌 지원 시작"}
                    ],
                    "confidence_reason": "졸업생 취업 타임라인 분석"
                },
                "recommendation": "분기별 마일스톤을 설정하고 주기적으로 진척도를 점검하세요."
            },
            "confidence": 0.70
        },
        {
            "type": "timeline",
            "title": "2026년 상반기 공모전 입상 목표",
            "description": "SW 중심대학 공모전, 대학생 해커톤 등 참가하여 수상 경력 확보.",
            "base_state": {"variables": [{"name": "target_date", "current_value": "미정", "simulated_value": "2026-06-30"}]},
            "changes": {"simulated_changes": [{"name": "target_date", "value": "2026-06-30"}]},
            "predicted_outcomes": {
                "results": [
                    {"metric_name": "수상 경력", "current_value": 0, "simulated_value": 1, "change_percent": 100.0, "impact_level": "positive", "explanation": "공모전 입상으로 포트폴리오 강화"},
                    {"metric_name": "팀 프로젝트 경험", "current_value": 2, "simulated_value": 4, "change_percent": 100.0, "impact_level": "positive", "explanation": "공모전 참가로 협업 경험 증가"}
                ],
                "ai_analysis": {
                    "summary": "공모전 수상은 취업에서 강력한 차별화 포인트입니다.",
                    "strengths": ["아이디어 구상 능력", "개발 역량 보유", "팀원 섭외 가능"],
                    "risks": ["시간 투자 많음", "수상 보장 없음", "학업 병행 어려움"],
                    "recommendations": ["참가 공모전 3개 선정", "역할 분담 명확히", "MVP 우선 개발"],
                    "milestones": [
                        {"date": "2026-01", "goal": "공모전 리서치 및 선정"},
                        {"date": "2026-02", "goal": "팀 빌딩 및 아이디어 확정"},
                        {"date": "2026-04", "goal": "프로토타입 개발"},
                        {"date": "2026-05", "goal": "최종 제출 및 발표 준비"}
                    ],
                    "confidence_reason": "공모전 수상자 패턴 분석"
                },
                "recommendation": "실현 가능한 아이디어로 MVP를 빠르게 구현하는 것이 핵심입니다."
            },
            "confidence": 0.60
        }
    ]'::JSONB;

    -- Loop through students and assign scenarios
    FOR student_rec IN
        SELECT student_id FROM idino_career.tb_student
        ORDER BY random()
    LOOP
        -- Assign 1-3 scenarios per student
        num_scenarios := 1 + floor(random() * 3)::INT;

        FOR i IN 1..num_scenarios LOOP
            -- Pick a random template
            template_idx := floor(random() * jsonb_array_length(scenario_templates))::INT;
            template := scenario_templates->template_idx;

            INSERT INTO idino_career.tb_simulation_scenario (
                scenario_id,
                student_id,
                scenario_type,
                title,
                description,
                base_state,
                changes,
                predicted_outcomes,
                confidence_level,
                created_at,
                is_favorite,
                ins_user_id,
                ins_dt
            ) VALUES (
                gen_random_uuid(),
                student_rec.student_id,
                template->>'type',
                template->>'title',
                template->>'description',
                (template->'base_state')::JSONB,
                (template->'changes')::JSONB,
                (template->'predicted_outcomes')::JSONB,
                (template->>'confidence')::NUMERIC,
                NOW() - (random() * interval '180 days'),
                random() < 0.1,  -- 10% are favorites
                'system',
                NOW()
            );
        END LOOP;
    END LOOP;
END $$;

-- Verify results
SELECT
    CASE WHEN title LIKE 'Simulation %' THEN 'Generic' ELSE 'Realistic' END as data_type,
    COUNT(*) as count
FROM idino_career.tb_simulation_scenario
GROUP BY CASE WHEN title LIKE 'Simulation %' THEN 'Generic' ELSE 'Realistic' END;
