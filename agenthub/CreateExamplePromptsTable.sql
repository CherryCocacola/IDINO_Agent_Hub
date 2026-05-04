-- ExamplePrompts 테이블 생성
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[ExamplePrompts]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[ExamplePrompts] (
        [ExamplePromptId] INT IDENTITY(1,1) NOT NULL,
        [Title] NVARCHAR(200) NOT NULL,
        [Prompt] NVARCHAR(MAX) NOT NULL,
        [Description] NVARCHAR(1000) NULL,
        [ServiceCode] NVARCHAR(50) NULL,
        [Model] NVARCHAR(100) NULL,
        [Category] NVARCHAR(50) NULL,
        [IconClass] NVARCHAR(100) NULL,
        [SortOrder] INT NOT NULL DEFAULT 0,
        [IsActive] BIT NOT NULL DEFAULT 1,
        [CreatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        [UpdatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        CONSTRAINT [PK_ExamplePrompts] PRIMARY KEY CLUSTERED ([ExamplePromptId] ASC)
    );

    CREATE INDEX [IX_ExamplePrompts_ServiceCode] ON [dbo].[ExamplePrompts]([ServiceCode]);
    CREATE INDEX [IX_ExamplePrompts_IsActive] ON [dbo].[ExamplePrompts]([IsActive]);
    CREATE INDEX [IX_ExamplePrompts_SortOrder] ON [dbo].[ExamplePrompts]([SortOrder]);
    CREATE INDEX [IX_ExamplePrompts_Category] ON [dbo].[ExamplePrompts]([Category]);

    -- 초기 Nano Banana (Gemini Image) 예제 프롬프트 데이터 삽입
    -- Model을 NULL로 설정하여 모든 모델에 적용되도록 함 (모델 변경에 영향받지 않음)
    INSERT INTO [dbo].[ExamplePrompts] ([Title], [Prompt], [Description], [ServiceCode], [Model], [Category], [IconClass], [SortOrder], [IsActive])
    VALUES
        (N'고품질 풍경 사진', N'일몰 무렵 평화로운 산 호수의 숨막히는 풍경 사진, 배경에 눈 덮인 봉우리, 황금빛 하늘을 반사하는 맑은 물, 소나무로 둘러싸인 호수, 전문 사진 촬영, 4K 품질, 자연광, 생동감 있는 색상', N'자연 풍경을 아름답게 표현한 고품질 이미지를 생성합니다. 산, 호수, 하늘 등 자연의 아름다움을 포착합니다.', N'gemini-image', NULL, N'풍경', N'bi bi-mountain', 1, 1),
        (N'추상 아트워크', N'생동감 있는 색상의 추상 미술 작품, 기하학적 형태, 유동적인 선, 현대적인 미니멀 스타일, 높은 대비, 대담한 붓질, 현대 미술, 갤러리 품질, 예술적 구성', N'추상적이고 현대적인 아트워크를 생성합니다. 기하학적 형태와 생동감 있는 색상으로 구성됩니다.', N'gemini-image', NULL, N'아트워크', N'bi bi-palette', 2, 1),
        (N'제품 사진', N'깨끗한 흰색 배경 위의 현대적인 스마트폰 전문 제품 사진, 스튜디오 조명, 고해상도, 상업 사진 스타일, 미니멀 디자인, 선명한 초점, 전문 품질', N'상업용 제품 사진을 생성합니다. 깔끔한 배경과 전문적인 조명으로 제품을 돋보이게 합니다.', N'gemini-image', NULL, N'제품', N'bi bi-box-seam', 3, 1),
        (N'캐릭터 디자인', N'귀여운 만화 캐릭터 디자인, 친근한 표정, 생동감 있는 색상, 현대적인 일러스트 스타일, 세밀한 특징, 전문 캐릭터 아트, 애니메이션에 적합, 매력적이고 매혹적인', N'애니메이션에 적합한 귀여운 캐릭터 디자인을 생성합니다. 친근하고 매력적인 표현으로 그려집니다.', N'gemini-image', NULL, N'캐릭터', N'bi bi-person-heart', 4, 1),
        (N'건축물 렌더링', N'미래지향적인 건물의 현대적 건축 렌더링, 유리와 강철 구조, 도시 환경, 극적인 조명, 전문 건축 시각화, 높은 디테일, 사실적인 재료', N'현대적이고 미래지향적인 건축물을 시각화합니다. 전문적인 건축 렌더링 스타일로 표현됩니다.', N'gemini-image', NULL, N'건축', N'bi bi-building', 5, 1),
        (N'음식 사진', N'우아한 요리의 미식 사진, 레스토랑 품질의 연출, 자연광, 식욕을 돋우는 색상, 전문 음식 스타일링, 고해상도, 입맛 돋우는 외관', N'고급 레스토랑 수준의 음식 사진을 생성합니다. 식욕을 돋우는 아름다운 연출로 표현됩니다.', N'gemini-image', NULL, N'음식', N'bi bi-egg-fried', 6, 1),
        (N'판타지 일러스트', N'빛나는 버섯이 있는 마법의 숲의 판타지 일러스트, 신비로운 생물, 환상적인 분위기, 세밀한 판타지 아트, 생동감 있는 마법의 색상, 매혹적인 장면, 하이 판타지 스타일', N'판타지 세계관의 마법적인 일러스트를 생성합니다. 신비롭고 환상적인 분위기를 연출합니다.', N'gemini-image', NULL, N'판타지', N'bi bi-stars', 7, 1),
        (N'도시 야경', N'번화한 도시의 도시 야경, 네온 사인, 고층 건물, 번잡한 거리, 영화적 분위기, 극적인 도시 풍경 사진, 활기찬 밤 문화, 전문 품질', N'활기찬 도시의 야경을 포착합니다. 네온 사인과 고층 건물이 어우러진 도시의 밤을 표현합니다.', N'gemini-image', NULL, N'도시', N'bi bi-building-fill', 8, 1),
        (N'동물 사진', N'자연 서식지에서 위엄 있는 사자의 전문 야생 동물 사진, 골든 아워 조명, 세밀한 털 질감, 강력한 자세, 내셔널 지오그래픽 스타일, 고품질 자연 사진', N'야생 동물의 자연스러운 모습을 포착한 전문 사진을 생성합니다. 자연 서식지에서의 생생한 모습을 담습니다.', N'gemini-image', NULL, N'동물', N'bi bi-heart-pulse', 9, 1),
        (N'과학 기술 일러스트', N'분자 구조의 과학 일러스트, 세밀한 과학 다이어그램, 교육적 스타일, 깔끔한 선, 전문 과학 시각화, 정보적이고 정확한, 현대 과학 아트', N'과학적이고 교육적인 일러스트를 생성합니다. 분자 구조나 과학적 개념을 시각적으로 표현합니다.', N'gemini-image', NULL, N'과학', N'bi bi-cpu', 10, 1);

    PRINT 'ExamplePrompts 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'ExamplePrompts 테이블이 이미 존재합니다.';
END
GO
