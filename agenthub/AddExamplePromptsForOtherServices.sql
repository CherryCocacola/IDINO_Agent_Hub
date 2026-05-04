-- 다른 이미지 생성 서비스들을 위한 예제 프롬프트 추가
-- DALL-E, Flux, Imagen 등 다양한 서비스와 모델에 대한 예제 프롬프트

-- DALL-E 서비스용 예제 프롬프트
INSERT INTO [dbo].[ExamplePrompts] ([Title], [Prompt], [Description], [ServiceCode], [Model], [Category], [IconClass], [SortOrder], [IsActive])
VALUES
    (N'DALL-E: 고품질 풍경', N'A breathtaking landscape photograph of a serene mountain lake at sunset, with snow-capped peaks in the background, crystal clear water reflecting the golden sky, surrounded by pine trees, professional photography, 4K quality, natural lighting, vibrant colors', N'DALL-E로 생성하는 고품질 자연 풍경 이미지입니다.', N'dalle', N'dall-e-3', N'풍경', N'bi bi-mountain', 31, 1),
    (N'DALL-E: 추상 아트', N'Abstract art piece with vibrant colors, geometric shapes, flowing lines, modern minimalist style, high contrast, bold brushstrokes, contemporary art, gallery quality, artistic composition', N'DALL-E로 생성하는 현대적인 추상 아트워크입니다.', N'dalle', N'dall-e-3', N'아트워크', N'bi bi-palette', 32, 1),
    (N'DALL-E: 제품 사진', N'Professional product photography of a modern smartphone on a clean white background, studio lighting, high resolution, commercial photography style, minimalist design, sharp focus, professional quality', N'DALL-E로 생성하는 상업용 제품 사진입니다.', N'dalle', N'dall-e-3', N'제품', N'bi bi-box-seam', 33, 1),
    (N'DALL-E: 캐릭터 디자인', N'Cute cartoon character design, friendly expression, vibrant colors, modern illustration style, detailed features, professional character art, suitable for animation, charming and appealing', N'DALL-E로 생성하는 귀여운 캐릭터 디자인입니다.', N'dalle', N'dall-e-3', N'캐릭터', N'bi bi-person-heart', 34, 1),
    (N'DALL-E: 건축물 렌더링', N'Modern architectural rendering of a futuristic building, glass and steel structure, urban environment, dramatic lighting, professional architectural visualization, high detail, realistic materials', N'DALL-E로 생성하는 미래지향적인 건축물 렌더링입니다.', N'dalle', N'dall-e-3', N'건축', N'bi bi-building', 35, 1);

-- Flux 2 서비스용 예제 프롬프트
INSERT INTO [dbo].[ExamplePrompts] ([Title], [Prompt], [Description], [ServiceCode], [Model], [Category], [IconClass], [SortOrder], [IsActive])
VALUES
    (N'Flux: 고품질 풍경', N'A breathtaking landscape photograph of a serene mountain lake at sunset, with snow-capped peaks in the background, crystal clear water reflecting the golden sky, surrounded by pine trees, professional photography, 4K quality, natural lighting, vibrant colors', N'Flux 2로 생성하는 고품질 자연 풍경 이미지입니다.', N'flux2', N'flux-2', N'풍경', N'bi bi-mountain', 36, 1),
    (N'Flux: 추상 아트', N'Abstract art piece with vibrant colors, geometric shapes, flowing lines, modern minimalist style, high contrast, bold brushstrokes, contemporary art, gallery quality, artistic composition', N'Flux 2로 생성하는 현대적인 추상 아트워크입니다.', N'flux2', N'flux-2', N'아트워크', N'bi bi-palette', 37, 1),
    (N'Flux: 판타지 일러스트', N'Fantasy illustration of a magical forest with glowing mushrooms, mystical creatures, ethereal atmosphere, detailed fantasy art, vibrant magical colors, enchanting scene, high fantasy style', N'Flux 2로 생성하는 판타지 세계관의 마법적인 일러스트입니다.', N'flux2', N'flux-2', N'판타지', N'bi bi-stars', 38, 1),
    (N'Flux: 디지털 아트', N'Digital artwork, cyberpunk aesthetic, neon lighting effects, futuristic design, computer graphics, digital art, high resolution, sharp details, modern digital art', N'Flux 2로 생성하는 사이버펑크 스타일의 디지털 아트워크입니다.', N'flux2', N'flux-2', N'디지털아트', N'bi bi-display', 39, 1),
    (N'Flux: 캐릭터 디자인', N'Cute cartoon character design, friendly expression, vibrant colors, modern illustration style, detailed features, professional character art, suitable for animation, charming and appealing', N'Flux 2로 생성하는 귀여운 캐릭터 디자인입니다.', N'flux2', N'flux-2', N'캐릭터', N'bi bi-person-heart', 40, 1);

-- Imagen 4 서비스용 예제 프롬프트
INSERT INTO [dbo].[ExamplePrompts] ([Title], [Prompt], [Description], [ServiceCode], [Model], [Category], [IconClass], [SortOrder], [IsActive])
VALUES
    (N'Imagen: 고품질 풍경', N'A breathtaking landscape photograph of a serene mountain lake at sunset, with snow-capped peaks in the background, crystal clear water reflecting the golden sky, surrounded by pine trees, professional photography, 4K quality, natural lighting, vibrant colors', N'Imagen 4로 생성하는 고품질 자연 풍경 이미지입니다.', N'imagen4', N'imagen-4.0', N'풍경', N'bi bi-mountain', 41, 1),
    (N'Imagen: 제품 사진', N'Professional product photography of a modern smartphone on a clean white background, studio lighting, high resolution, commercial photography style, minimalist design, sharp focus, professional quality', N'Imagen 4로 생성하는 상업용 제품 사진입니다.', N'imagen4', N'imagen-4.0', N'제품', N'bi bi-box-seam', 42, 1),
    (N'Imagen: 음식 사진', N'Gourmet food photography of an elegant dish, restaurant quality presentation, natural lighting, appetizing colors, professional food styling, high resolution, mouth-watering appearance', N'Imagen 4로 생성하는 고급 레스토랑 수준의 음식 사진입니다.', N'imagen4', N'imagen-4.0', N'음식', N'bi bi-egg-fried', 43, 1),
    (N'Imagen: 건축물 렌더링', N'Modern architectural rendering of a futuristic building, glass and steel structure, urban environment, dramatic lighting, professional architectural visualization, high detail, realistic materials', N'Imagen 4로 생성하는 미래지향적인 건축물 렌더링입니다.', N'imagen4', N'imagen-4.0', N'건축', N'bi bi-building', 44, 1),
    (N'Imagen: 패션 사진', N'High-end fashion styling photography, trendy clothing, professional fashion photography, studio lighting, model pose, fashion magazine style, luxury brand feel, sophisticated presentation', N'Imagen 4로 생성하는 고급 패션 브랜드 스타일의 전문 사진입니다.', N'imagen4', N'imagen-4.0', N'패션', N'bi bi-bag-heart', 45, 1);

-- Gen4 Image 서비스용 예제 프롬프트
INSERT INTO [dbo].[ExamplePrompts] ([Title], [Prompt], [Description], [ServiceCode], [Model], [Category], [IconClass], [SortOrder], [IsActive])
VALUES
    (N'Gen4: 고품질 풍경', N'A breathtaking landscape photograph of a serene mountain lake at sunset, with snow-capped peaks in the background, crystal clear water reflecting the golden sky, surrounded by pine trees, professional photography, 4K quality, natural lighting, vibrant colors', N'Gen4 Image로 생성하는 고품질 자연 풍경 이미지입니다.', N'gen4-image', N'imagegeneration@006', N'풍경', N'bi bi-mountain', 46, 1),
    (N'Gen4: 추상 아트', N'Abstract art piece with vibrant colors, geometric shapes, flowing lines, modern minimalist style, high contrast, bold brushstrokes, contemporary art, gallery quality, artistic composition', N'Gen4 Image로 생성하는 현대적인 추상 아트워크입니다.', N'gen4-image', N'imagegeneration@006', N'아트워크', N'bi bi-palette', 47, 1),
    (N'Gen4: 제품 사진', N'Professional product photography of a modern smartphone on a clean white background, studio lighting, high resolution, commercial photography style, minimalist design, sharp focus, professional quality', N'Gen4 Image로 생성하는 상업용 제품 사진입니다.', N'gen4-image', N'imagegeneration@006', N'제품', N'bi bi-box-seam', 48, 1),
    (N'Gen4: 건축물 렌더링', N'Modern architectural rendering of a futuristic building, glass and steel structure, urban environment, dramatic lighting, professional architectural visualization, high detail, realistic materials', N'Gen4 Image로 생성하는 미래지향적인 건축물 렌더링입니다.', N'gen4-image', N'imagegeneration@006', N'건축', N'bi bi-building', 49, 1),
    (N'Gen4: 판타지 일러스트', N'Fantasy illustration of a magical forest with glowing mushrooms, mystical creatures, ethereal atmosphere, detailed fantasy art, vibrant magical colors, enchanting scene, high fantasy style', N'Gen4 Image로 생성하는 판타지 세계관의 마법적인 일러스트입니다.', N'gen4-image', N'imagegeneration@006', N'판타지', N'bi bi-stars', 50, 1);

PRINT '다른 이미지 생성 서비스들을 위한 예제 프롬프트가 삽입되었습니다.';
PRINT 'DALL-E: 5개, Flux 2: 5개, Imagen 4: 5개, Gen4 Image: 5개';
GO
