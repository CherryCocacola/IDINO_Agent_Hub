-- API 키 테이블 생성 스크립트

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[ApiKeys]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[ApiKeys] (
        [ApiKeyId] INT IDENTITY(1,1) NOT NULL,
        [UserId] INT NOT NULL,
        [KeyName] NVARCHAR(100) NOT NULL,
        [ServiceCode] NVARCHAR(50) NOT NULL,
        [EncryptedKey] NVARCHAR(500) NOT NULL,
        [Description] NVARCHAR(500) NULL,
        [ExpiresAt] DATETIME2 NULL,
        [IsActive] BIT NOT NULL DEFAULT 1,
        [LastUsedAt] DATETIME2 NULL,
        [UsageCount] INT NOT NULL DEFAULT 0,
        [CreatedAt] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [UpdatedAt] DATETIME2 NOT NULL DEFAULT GETDATE(),
        CONSTRAINT [PK_ApiKeys] PRIMARY KEY CLUSTERED ([ApiKeyId] ASC)
    );

    -- 인덱스 생성
    CREATE NONCLUSTERED INDEX [IDX_ApiKeys_UserId] 
        ON [dbo].[ApiKeys]([UserId] ASC);

    CREATE NONCLUSTERED INDEX [IDX_ApiKeys_ServiceCode] 
        ON [dbo].[ApiKeys]([ServiceCode] ASC);

    CREATE NONCLUSTERED INDEX [IDX_ApiKeys_IsActive] 
        ON [dbo].[ApiKeys]([IsActive] ASC);

    PRINT 'ApiKeys 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'ApiKeys 테이블이 이미 존재합니다.';
END
GO
