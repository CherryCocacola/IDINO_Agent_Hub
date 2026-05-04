-- ApiServices 테이블 데이터 복구용 INSERT 문
-- 실수로 삭제된 ApiServices 데이터를 복구합니다.

-- 기존 데이터 확인 및 삭제 (선택사항)
-- DELETE FROM [dbo].[ApiServices];
-- GO

-- Chat 서비스
INSERT INTO [dbo].[ApiServices] ([ServiceCode], [ServiceName], [Description], [IconClass], [ColorCode], [ApiEndpoint], [DefaultModel], [CostPerRequest], [ServiceType], [IsActive], [SortOrder], [CreatedAt], [UpdatedAt])
VALUES
    ('chatgpt', 'ChatGPT', 'OpenAI ChatGPT API', 'bi-chat-square-text', '#00c9ff', 'https://api.openai.com/v1', 'gpt-4-turbo', 0.03, 'Chat', 1, 1, GETUTCDATE(), GETUTCDATE()),
    ('claude', 'Claude', 'Anthropic Claude API', 'bi-robot', '#667eea', 'https://api.anthropic.com/v1', 'claude-3-sonnet', 0.03, 'Chat', 1, 2, GETUTCDATE(), GETUTCDATE()),
    ('cursor', 'Cursor', 'Cursor AI', 'bi-code-slash', '#f093fb', NULL, NULL, 0.02, 'Chat', 1, 3, GETUTCDATE(), GETUTCDATE()),
    ('copilot', 'Microsoft Copilot', 'Microsoft Copilot (Azure OpenAI)', 'bi-microsoft', '#00A4EF', NULL, 'gpt-4', 0.02, 'Chat', 1, 4, GETUTCDATE(), GETUTCDATE()),
    ('gemini', 'Gemini', 'Google Gemini API', 'bi-google', '#4285f4', 'https://generativelanguage.googleapis.com/v1beta', 'gemini-1.5-flash', 0.02, 'Chat', 1, 5, GETUTCDATE(), GETUTCDATE()),
    ('mistral', 'Mistral', 'Mistral AI API', 'bi-stars', '#FF6B35', 'https://api.mistral.ai/v1', 'mistral-large-latest', 0.02, 'Chat', 1, 6, GETUTCDATE(), GETUTCDATE());
GO

-- Image Generation 서비스
INSERT INTO [dbo].[ApiServices] ([ServiceCode], [ServiceName], [Description], [IconClass], [ColorCode], [ApiEndpoint], [DefaultModel], [CostPerRequest], [ServiceType], [IsActive], [SortOrder], [CreatedAt], [UpdatedAt])
VALUES
    ('dalle', 'DALL-E 3', 'OpenAI DALL-E 3 이미지 생성', 'bi-image', '#10a37f', 'https://api.openai.com/v1', 'dall-e-3', 0.04, 'ImageGeneration', 1, 10, GETUTCDATE(), GETUTCDATE()),
    ('gemini-image', 'Gemini 3 Pro Image', 'Google Gemini 3 Pro Image 생성 (Nano banana Pro)', 'bi-image', '#4285f4', 'https://generativelanguage.googleapis.com/v1beta', 'gemini-3.0-pro-image', 0.03, 'ImageGeneration', 1, 11, GETUTCDATE(), GETUTCDATE()),
    ('imagen4', 'Imagen 4', 'Google Imagen 4 이미지 생성', 'bi-image', '#34a853', 'https://generativelanguage.googleapis.com/v1beta', 'imagen-4.0-generate-001', 0.04, 'ImageGeneration', 1, 12, GETUTCDATE(), GETUTCDATE()),
    ('gen4-image', 'Gen4 Image', 'Google Vertex AI Gen4 Image 생성', 'bi-image', '#ea4335', 'https://us-central1-aiplatform.googleapis.com/v1', 'imagegeneration@006', 0.04, 'ImageGeneration', 1, 13, GETUTCDATE(), GETUTCDATE()),
    ('flux2', 'Flux 2', 'Stability AI Flux 2 이미지 생성', 'bi-image', '#6366f1', 'https://api.stability.ai/v2beta', 'flux-2', 0.03, 'ImageGeneration', 1, 14, GETUTCDATE(), GETUTCDATE());
GO

-- Video Generation 서비스
INSERT INTO [dbo].[ApiServices] ([ServiceCode], [ServiceName], [Description], [IconClass], [ColorCode], [ApiEndpoint], [DefaultModel], [CostPerRequest], [ServiceType], [IsActive], [SortOrder], [CreatedAt], [UpdatedAt])
VALUES
    ('gen4-video', 'Gen4 Video', 'Google Vertex AI Gen4 영상 생성', 'bi-camera-video', '#ea4335', 'https://us-central1-aiplatform.googleapis.com/v1', 'videogeneration@006', 0.10, 'VideoGeneration', 1, 20, GETUTCDATE(), GETUTCDATE()),
    ('veo', 'Veo 3.1', 'Google Veo 3.1 영상 생성', 'bi-camera-video-fill', '#4285f4', 'https://generativelanguage.googleapis.com/v1beta', 'veo-3.1', 0.12, 'VideoGeneration', 1, 21, GETUTCDATE(), GETUTCDATE()),
    ('openai-video', 'OpenAI Video', 'OpenAI 비디오 생성 (Sora)', 'bi-camera-reels', '#10a37f', 'https://api.openai.com/v1', 'sora-2', 0.15, 'VideoGeneration', 1, 22, GETUTCDATE(), GETUTCDATE());
GO

PRINT 'ApiServices 데이터가 성공적으로 삽입되었습니다.';
PRINT '총 ' + CAST(@@ROWCOUNT AS VARCHAR) + '개의 서비스가 추가되었습니다.';
GO

-- 삽입된 서비스 확인
SELECT 
    [ServiceId],
    [ServiceCode],
    [ServiceName],
    [ServiceType],
    [IsActive],
    [SortOrder]
FROM [dbo].[ApiServices]
ORDER BY [ServiceType], [SortOrder];
GO
