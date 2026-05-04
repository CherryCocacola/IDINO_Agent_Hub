-- ApiServiceModels 테이블 생성
-- ApiServices별 활성화할 모델을 관리하는 테이블

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[ApiServiceModels]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[ApiServiceModels] (
        [ModelId] INT IDENTITY(1,1) NOT NULL,
        [ServiceId] INT NOT NULL,
        [ModelName] NVARCHAR(100) NOT NULL,
        [Description] NVARCHAR(500) NULL,
        [IsActive] BIT NOT NULL DEFAULT 1,
        [SortOrder] INT NOT NULL DEFAULT 0,
        [ModelType] NVARCHAR(50) NULL, -- 'stable', 'preview', 'experimental'
        [CreatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        [UpdatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        CONSTRAINT [PK_ApiServiceModels] PRIMARY KEY CLUSTERED ([ModelId] ASC),
        CONSTRAINT [FK_ApiServiceModels_ApiServices] FOREIGN KEY ([ServiceId]) 
            REFERENCES [dbo].[ApiServices] ([ServiceId]) ON DELETE CASCADE
    );

    -- 인덱스 생성
    CREATE UNIQUE NONCLUSTERED INDEX [IX_ApiServiceModels_ServiceId_ModelName] 
        ON [dbo].[ApiServiceModels] ([ServiceId], [ModelName]);
    
    CREATE NONCLUSTERED INDEX [IX_ApiServiceModels_ServiceId_IsActive_SortOrder] 
        ON [dbo].[ApiServiceModels] ([ServiceId], [IsActive], [SortOrder]);

    PRINT 'ApiServiceModels 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'ApiServiceModels 테이블이 이미 존재합니다.';
END
GO

-- 시드 데이터 삽입
-- 각 서비스별 모델 데이터 추가

-- ChatGPT/OpenAI 모델
IF EXISTS (SELECT 1 FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'chatgpt')
BEGIN
    DECLARE @ChatGptServiceId INT = (SELECT [ServiceId] FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'chatgpt');
    
    IF NOT EXISTS (SELECT 1 FROM [dbo].[ApiServiceModels] WHERE [ServiceId] = @ChatGptServiceId)
    BEGIN
        INSERT INTO [dbo].[ApiServiceModels] ([ServiceId], [ModelName], [Description], [IsActive], [SortOrder], [ModelType])
        VALUES
            (@ChatGptServiceId, 'gpt-5', 'GPT-5', 1, 1, 'stable'),
            (@ChatGptServiceId, 'gpt-5-mini', 'GPT-5 Mini', 1, 2, 'stable'),
            (@ChatGptServiceId, 'gpt-5-nano', 'GPT-5 Nano', 1, 3, 'stable'),
            (@ChatGptServiceId, 'gpt-5.2', 'GPT-5.2', 1, 4, 'stable'),
            (@ChatGptServiceId, 'gpt-5.2-instant', 'GPT-5.2 Instant', 1, 5, 'stable'),
            (@ChatGptServiceId, 'gpt-5.2-thinking', 'GPT-5.2 Thinking', 1, 6, 'stable'),
            (@ChatGptServiceId, 'gpt-5.2-pro', 'GPT-5.2 Pro', 1, 7, 'stable'),
            (@ChatGptServiceId, 'gpt-4-turbo', 'GPT-4 Turbo', 1, 10, 'stable'),
            (@ChatGptServiceId, 'gpt-4o', 'GPT-4o', 1, 11, 'stable'),
            (@ChatGptServiceId, 'gpt-4', 'GPT-4', 1, 12, 'stable'),
            (@ChatGptServiceId, 'gpt-3.5-turbo', 'GPT-3.5 Turbo', 1, 13, 'stable'),
            (@ChatGptServiceId, 'gpt-4o-mini', 'GPT-4o Mini', 1, 14, 'stable');
        
        PRINT 'ChatGPT 모델 데이터가 추가되었습니다.';
    END
END
GO

-- Claude 모델
IF EXISTS (SELECT 1 FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'claude')
BEGIN
    DECLARE @ClaudeServiceId INT = (SELECT [ServiceId] FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'claude');
    
    IF NOT EXISTS (SELECT 1 FROM [dbo].[ApiServiceModels] WHERE [ServiceId] = @ClaudeServiceId)
    BEGIN
        INSERT INTO [dbo].[ApiServiceModels] ([ServiceId], [ModelName], [Description], [IsActive], [SortOrder], [ModelType])
        VALUES
            (@ClaudeServiceId, 'claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet', 1, 1, 'stable'),
            (@ClaudeServiceId, 'claude-3-opus-20240229', 'Claude 3 Opus', 1, 2, 'stable'),
            (@ClaudeServiceId, 'claude-3-sonnet-20240229', 'Claude 3 Sonnet', 1, 3, 'stable'),
            (@ClaudeServiceId, 'claude-3-haiku-20240307', 'Claude 3 Haiku', 1, 4, 'stable');
        
        PRINT 'Claude 모델 데이터가 추가되었습니다.';
    END
END
GO

-- Gemini 모델
IF EXISTS (SELECT 1 FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'gemini')
BEGIN
    DECLARE @GeminiServiceId INT = (SELECT [ServiceId] FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'gemini');
    
    IF NOT EXISTS (SELECT 1 FROM [dbo].[ApiServiceModels] WHERE [ServiceId] = @GeminiServiceId)
    BEGIN
        INSERT INTO [dbo].[ApiServiceModels] ([ServiceId], [ModelName], [Description], [IsActive], [SortOrder], [ModelType])
        VALUES
            (@GeminiServiceId, 'gemini-2.5-pro', 'Gemini 2.5 Pro', 1, 1, 'stable'),
            (@GeminiServiceId, 'gemini-2.5-flash', 'Gemini 2.5 Flash', 1, 2, 'stable'),
            (@GeminiServiceId, 'gemini-2.0-flash', 'Gemini 2.0 Flash', 1, 3, 'stable'),
            (@GeminiServiceId, 'gemini-1.5-pro', 'Gemini 1.5 Pro', 1, 4, 'stable'),
            (@GeminiServiceId, 'gemini-1.5-flash', 'Gemini 1.5 Flash', 1, 5, 'stable'),
            (@GeminiServiceId, 'gemini-3-pro-preview', 'Gemini 3 Pro Preview', 1, 10, 'preview'),
            (@GeminiServiceId, 'gemini-3-flash-preview', 'Gemini 3 Flash Preview', 1, 11, 'preview');
        
        PRINT 'Gemini 모델 데이터가 추가되었습니다.';
    END
END
GO

-- Mistral 모델
IF EXISTS (SELECT 1 FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'mistral')
BEGIN
    DECLARE @MistralServiceId INT = (SELECT [ServiceId] FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'mistral');
    
    IF NOT EXISTS (SELECT 1 FROM [dbo].[ApiServiceModels] WHERE [ServiceId] = @MistralServiceId)
    BEGIN
        INSERT INTO [dbo].[ApiServiceModels] ([ServiceId], [ModelName], [Description], [IsActive], [SortOrder], [ModelType])
        VALUES
            (@MistralServiceId, 'mistral-large-latest', 'Mistral Large', 1, 1, 'stable'),
            (@MistralServiceId, 'mistral-medium-latest', 'Mistral Medium', 1, 2, 'stable'),
            (@MistralServiceId, 'mistral-small-latest', 'Mistral Small', 1, 3, 'stable'),
            (@MistralServiceId, 'open-mixtral-8x7b', 'Mixtral 8x7B', 1, 4, 'stable'),
            (@MistralServiceId, 'open-mixtral-8x22b', 'Mixtral 8x22B', 1, 5, 'stable'),
            (@MistralServiceId, 'open-mistral-7b', 'Mistral 7B', 1, 6, 'stable');
        
        PRINT 'Mistral 모델 데이터가 추가되었습니다.';
    END
END
GO

-- Microsoft Copilot 모델 (Azure OpenAI)
IF EXISTS (SELECT 1 FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'copilot')
BEGIN
    DECLARE @CopilotServiceId INT = (SELECT [ServiceId] FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'copilot');
    
    IF NOT EXISTS (SELECT 1 FROM [dbo].[ApiServiceModels] WHERE [ServiceId] = @CopilotServiceId)
    BEGIN
        INSERT INTO [dbo].[ApiServiceModels] ([ServiceId], [ModelName], [Description], [IsActive], [SortOrder], [ModelType])
        VALUES
            (@CopilotServiceId, 'gpt-4', 'GPT-4', 1, 1, 'stable'),
            (@CopilotServiceId, 'gpt-4-turbo', 'GPT-4 Turbo', 1, 2, 'stable'),
            (@CopilotServiceId, 'gpt-35-turbo', 'GPT-3.5 Turbo', 1, 3, 'stable'),
            (@CopilotServiceId, 'gpt-4o', 'GPT-4o', 1, 4, 'stable'),
            (@CopilotServiceId, 'gpt-4o-mini', 'GPT-4o Mini', 1, 5, 'stable');
        
        PRINT 'Microsoft Copilot (Azure OpenAI) 모델 데이터가 추가되었습니다.';
    END
END
GO

-- Cursor 모델 (GitHub Copilot API 사용)
IF EXISTS (SELECT 1 FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'cursor')
BEGIN
    DECLARE @CursorServiceId INT = (SELECT [ServiceId] FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'cursor');
    
    IF NOT EXISTS (SELECT 1 FROM [dbo].[ApiServiceModels] WHERE [ServiceId] = @CursorServiceId)
    BEGIN
        INSERT INTO [dbo].[ApiServiceModels] ([ServiceId], [ModelName], [Description], [IsActive], [SortOrder], [ModelType])
        VALUES
            (@CursorServiceId, 'gpt-4', 'GPT-4', 1, 1, 'stable'),
            (@CursorServiceId, 'gpt-4-turbo', 'GPT-4 Turbo', 1, 2, 'stable'),
            (@CursorServiceId, 'gpt-3.5-turbo', 'GPT-3.5 Turbo', 1, 3, 'stable');
        
        PRINT 'Cursor (GitHub Copilot API) 모델 데이터가 추가되었습니다.';
    END
END
GO

-- Perplexity 모델
IF EXISTS (SELECT 1 FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'perplexity')
BEGIN
    DECLARE @PerplexityServiceId INT = (SELECT [ServiceId] FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'perplexity');
    
    IF NOT EXISTS (SELECT 1 FROM [dbo].[ApiServiceModels] WHERE [ServiceId] = @PerplexityServiceId)
    BEGIN
        INSERT INTO [dbo].[ApiServiceModels] ([ServiceId], [ModelName], [Description], [IsActive], [SortOrder], [ModelType])
        VALUES
            (@PerplexityServiceId, 'sonar', 'Sonar', 1, 1, 'stable'),
            (@PerplexityServiceId, 'sonar-pro', 'Sonar Pro', 1, 2, 'stable');
        
        PRINT 'Perplexity 모델 데이터가 추가되었습니다.';
    END
END
GO

-- DALL-E 모델
IF EXISTS (SELECT 1 FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'dalle')
BEGIN
    DECLARE @DalleServiceId INT = (SELECT [ServiceId] FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'dalle');
    
    IF NOT EXISTS (SELECT 1 FROM [dbo].[ApiServiceModels] WHERE [ServiceId] = @DalleServiceId)
    BEGIN
        INSERT INTO [dbo].[ApiServiceModels] ([ServiceId], [ModelName], [Description], [IsActive], [SortOrder], [ModelType])
        VALUES
            (@DalleServiceId, 'dall-e-3', 'DALL-E 3', 1, 1, 'stable'),
            (@DalleServiceId, 'dall-e-2', 'DALL-E 2', 1, 2, 'stable');
        
        PRINT 'DALL-E 모델 데이터가 추가되었습니다.';
    END
END
GO

-- Gemini Image 모델
IF EXISTS (SELECT 1 FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'gemini-image')
BEGIN
    DECLARE @GeminiImageServiceId INT = (SELECT [ServiceId] FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'gemini-image');
    
    IF NOT EXISTS (SELECT 1 FROM [dbo].[ApiServiceModels] WHERE [ServiceId] = @GeminiImageServiceId)
    BEGIN
        INSERT INTO [dbo].[ApiServiceModels] ([ServiceId], [ModelName], [Description], [IsActive], [SortOrder], [ModelType])
        VALUES
            (@GeminiImageServiceId, 'gemini-3-pro-image-preview', 'Gemini 3 Pro Image', 1, 1, 'preview'),
            (@GeminiImageServiceId, 'gemini-2.5-flash-image', 'Gemini 2.5 Flash Image', 1, 2, 'stable');
        
        PRINT 'Gemini Image 모델 데이터가 추가되었습니다.';
    END
END
GO

-- Imagen 4 모델
IF EXISTS (SELECT 1 FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'imagen4')
BEGIN
    DECLARE @Imagen4ServiceId INT = (SELECT [ServiceId] FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'imagen4');
    
    IF NOT EXISTS (SELECT 1 FROM [dbo].[ApiServiceModels] WHERE [ServiceId] = @Imagen4ServiceId)
    BEGIN
        INSERT INTO [dbo].[ApiServiceModels] ([ServiceId], [ModelName], [Description], [IsActive], [SortOrder], [ModelType])
        VALUES
            (@Imagen4ServiceId, 'imagen-4.0-generate-001', 'Imagen 4.0 Generate', 1, 1, 'stable'),
            (@Imagen4ServiceId, 'imagen-4.0-fast-generate-001', 'Imagen 4.0 Fast Generate', 1, 2, 'stable'),
            (@Imagen4ServiceId, 'imagen-4.0-ultra-generate-001', 'Imagen 4.0 Ultra Generate', 1, 3, 'stable');
        
        PRINT 'Imagen 4 모델 데이터가 추가되었습니다.';
    END
END
GO

-- Gen4 Image 모델
IF EXISTS (SELECT 1 FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'gen4-image')
BEGIN
    DECLARE @Gen4ImageServiceId INT = (SELECT [ServiceId] FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'gen4-image');
    
    IF NOT EXISTS (SELECT 1 FROM [dbo].[ApiServiceModels] WHERE [ServiceId] = @Gen4ImageServiceId)
    BEGIN
        INSERT INTO [dbo].[ApiServiceModels] ([ServiceId], [ModelName], [Description], [IsActive], [SortOrder], [ModelType])
        VALUES
            (@Gen4ImageServiceId, 'imagegeneration@006', 'Gen4 Image Generation', 1, 1, 'stable');
        
        PRINT 'Gen4 Image 모델 데이터가 추가되었습니다.';
    END
END
GO

-- Flux 2 모델
IF EXISTS (SELECT 1 FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'flux2')
BEGIN
    DECLARE @Flux2ServiceId INT = (SELECT [ServiceId] FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'flux2');
    
    IF NOT EXISTS (SELECT 1 FROM [dbo].[ApiServiceModels] WHERE [ServiceId] = @Flux2ServiceId)
    BEGIN
        INSERT INTO [dbo].[ApiServiceModels] ([ServiceId], [ModelName], [Description], [IsActive], [SortOrder], [ModelType])
        VALUES
            (@Flux2ServiceId, 'flux-2', 'Flux 2', 1, 1, 'stable'),
            (@Flux2ServiceId, 'flux-2.1', 'Flux 2.1', 1, 2, 'stable');
        
        PRINT 'Flux 2 모델 데이터가 추가되었습니다.';
    END
END
GO

-- Gen4 Video 모델
IF EXISTS (SELECT 1 FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'gen4-video')
BEGIN
    DECLARE @Gen4VideoServiceId INT = (SELECT [ServiceId] FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'gen4-video');
    
    IF NOT EXISTS (SELECT 1 FROM [dbo].[ApiServiceModels] WHERE [ServiceId] = @Gen4VideoServiceId)
    BEGIN
        INSERT INTO [dbo].[ApiServiceModels] ([ServiceId], [ModelName], [Description], [IsActive], [SortOrder], [ModelType])
        VALUES
            (@Gen4VideoServiceId, 'videogeneration@006', 'Gen4 Video Generation', 1, 1, 'stable'),
            (@Gen4VideoServiceId, 'videogeneration@006-hd', 'Gen4 Video Generation HD', 1, 2, 'stable');
        
        PRINT 'Gen4 Video 모델 데이터가 추가되었습니다.';
    END
END
GO

-- Veo 모델
IF EXISTS (SELECT 1 FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'veo')
BEGIN
    DECLARE @VeoServiceId INT = (SELECT [ServiceId] FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'veo');
    
    IF NOT EXISTS (SELECT 1 FROM [dbo].[ApiServiceModels] WHERE [ServiceId] = @VeoServiceId)
    BEGIN
        INSERT INTO [dbo].[ApiServiceModels] ([ServiceId], [ModelName], [Description], [IsActive], [SortOrder], [ModelType])
        VALUES
            (@VeoServiceId, 'veo-3.1', 'Veo 3.1', 1, 1, 'stable'),
            (@VeoServiceId, 'veo-3.0', 'Veo 3.0', 1, 2, 'stable');
        
        PRINT 'Veo 모델 데이터가 추가되었습니다.';
    END
END
GO

-- OpenAI Video (Sora) 모델
IF EXISTS (SELECT 1 FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'openai-video' OR [ServiceCode] = 'sora')
BEGIN
    DECLARE @OpenAiVideoServiceId INT = (SELECT [ServiceId] FROM [dbo].[ApiServices] WHERE [ServiceCode] = 'openai-video' OR [ServiceCode] = 'sora');
    
    IF NOT EXISTS (SELECT 1 FROM [dbo].[ApiServiceModels] WHERE [ServiceId] = @OpenAiVideoServiceId)
    BEGIN
        INSERT INTO [dbo].[ApiServiceModels] ([ServiceId], [ModelName], [Description], [IsActive], [SortOrder], [ModelType])
        VALUES
            (@OpenAiVideoServiceId, 'sora-2', 'Sora 2', 1, 1, 'stable'),
            (@OpenAiVideoServiceId, 'sora-1.5', 'Sora 1.5', 1, 2, 'stable');
        
        PRINT 'OpenAI Video (Sora) 모델 데이터가 추가되었습니다.';
    END
END
GO

PRINT '모든 ApiServiceModels 시드 데이터 삽입이 완료되었습니다.';
GO
