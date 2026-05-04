-- ExamplePrompts 데이터 수정 (잘린 프롬프트 복구)
-- 이미 저장된 데이터가 잘렸다면 이 스크립트로 수정할 수 있습니다.

UPDATE [dbo].[ExamplePrompts]
SET [Prompt] = N'일몰 무렵 평화로운 산 호수의 숨막히는 풍경 사진, 배경에 눈 덮인 봉우리, 황금빛 하늘을 반사하는 맑은 물, 소나무로 둘러싸인 호수, 전문 사진 촬영, 4K 품질, 자연광, 생동감 있는 색상'
WHERE [Title] = N'고품질 풍경 사진' AND [ServiceCode] = N'gemini-image';

UPDATE [dbo].[ExamplePrompts]
SET [Prompt] = N'생동감 있는 색상의 추상 미술 작품, 기하학적 형태, 유동적인 선, 현대적인 미니멀 스타일, 높은 대비, 대담한 붓질, 현대 미술, 갤러리 품질, 예술적 구성'
WHERE [Title] = N'추상 아트워크' AND [ServiceCode] = N'gemini-image';

UPDATE [dbo].[ExamplePrompts]
SET [Prompt] = N'깨끗한 흰색 배경 위의 현대적인 스마트폰 전문 제품 사진, 스튜디오 조명, 고해상도, 상업 사진 스타일, 미니멀 디자인, 선명한 초점, 전문 품질'
WHERE [Title] = N'제품 사진' AND [ServiceCode] = N'gemini-image';

UPDATE [dbo].[ExamplePrompts]
SET [Prompt] = N'귀여운 만화 캐릭터 디자인, 친근한 표정, 생동감 있는 색상, 현대적인 일러스트 스타일, 세밀한 특징, 전문 캐릭터 아트, 애니메이션에 적합, 매력적이고 매혹적인'
WHERE [Title] = N'캐릭터 디자인' AND [ServiceCode] = N'gemini-image';

UPDATE [dbo].[ExamplePrompts]
SET [Prompt] = N'미래지향적인 건물의 현대적 건축 렌더링, 유리와 강철 구조, 도시 환경, 극적인 조명, 전문 건축 시각화, 높은 디테일, 사실적인 재료'
WHERE [Title] = N'건축물 렌더링' AND [ServiceCode] = N'gemini-image';

UPDATE [dbo].[ExamplePrompts]
SET [Prompt] = N'우아한 요리의 미식 사진, 레스토랑 품질의 연출, 자연광, 식욕을 돋우는 색상, 전문 음식 스타일링, 고해상도, 입맛 돋우는 외관'
WHERE [Title] = N'음식 사진' AND [ServiceCode] = N'gemini-image';

UPDATE [dbo].[ExamplePrompts]
SET [Prompt] = N'빛나는 버섯이 있는 마법의 숲의 판타지 일러스트, 신비로운 생물, 환상적인 분위기, 세밀한 판타지 아트, 생동감 있는 마법의 색상, 매혹적인 장면, 하이 판타지 스타일'
WHERE [Title] = N'판타지 일러스트' AND [ServiceCode] = N'gemini-image';

UPDATE [dbo].[ExamplePrompts]
SET [Prompt] = N'번화한 도시의 도시 야경, 네온 사인, 고층 건물, 번잡한 거리, 영화적 분위기, 극적인 도시 풍경 사진, 활기찬 밤 문화, 전문 품질'
WHERE [Title] = N'도시 야경' AND [ServiceCode] = N'gemini-image';

UPDATE [dbo].[ExamplePrompts]
SET [Prompt] = N'자연 서식지에서 위엄 있는 사자의 전문 야생 동물 사진, 골든 아워 조명, 세밀한 털 질감, 강력한 자세, 내셔널 지오그래픽 스타일, 고품질 자연 사진'
WHERE [Title] = N'동물 사진' AND [ServiceCode] = N'gemini-image';

UPDATE [dbo].[ExamplePrompts]
SET [Prompt] = N'분자 구조의 과학 일러스트, 세밀한 과학 다이어그램, 교육적 스타일, 깔끔한 선, 전문 과학 시각화, 정보적이고 정확한, 현대 과학 아트'
WHERE [Title] = N'과학 기술 일러스트' AND [ServiceCode] = N'gemini-image';

PRINT 'ExamplePrompts 데이터가 수정되었습니다.';
GO
