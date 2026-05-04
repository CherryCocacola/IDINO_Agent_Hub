-- 금칙어 테이블 생성 스크립트

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[BannedWords]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[BannedWords] (
        [BannedWordId] INT IDENTITY(1,1) NOT NULL,
        [Word] NVARCHAR(200) NOT NULL,
        [AgentId] INT NULL,
        [Description] NVARCHAR(500) NULL,
        [IsActive] BIT NOT NULL DEFAULT 1,
        [CreatedBy] INT NOT NULL,
        [CreatedAt] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [UpdatedAt] DATETIME2 NOT NULL DEFAULT GETDATE(),
        CONSTRAINT [PK_BannedWords] PRIMARY KEY CLUSTERED ([BannedWordId] ASC),
        CONSTRAINT [FK_BannedWords_Agents] FOREIGN KEY ([AgentId]) REFERENCES [dbo].[Agents]([AgentId]) ON DELETE CASCADE,
        CONSTRAINT [FK_BannedWords_Users] FOREIGN KEY ([CreatedBy]) REFERENCES [dbo].[Users]([UserId])
    );

    -- 인덱스 생성
    CREATE NONCLUSTERED INDEX [IDX_BannedWords_AgentId_IsActive] 
        ON [dbo].[BannedWords]([AgentId] ASC, [IsActive] ASC)
        WHERE [AgentId] IS NOT NULL;

    CREATE NONCLUSTERED INDEX [IDX_BannedWords_Word_IsActive] 
        ON [dbo].[BannedWords]([Word] ASC, [IsActive] ASC);

    -- 전역 금칙어용 인덱스 (AgentId IS NULL)
    CREATE NONCLUSTERED INDEX [IDX_BannedWords_Global_IsActive] 
        ON [dbo].[BannedWords]([IsActive] ASC)
        WHERE [AgentId] IS NULL;

    -- 페이징 성능 향상을 위한 인덱스 (CreatedAt DESC 정렬 최적화)
    CREATE NONCLUSTERED INDEX [IDX_BannedWords_AgentId_CreatedAt] 
        ON [dbo].[BannedWords]([AgentId] ASC, [CreatedAt] DESC);

    -- 전역 금칙어 페이징 최적화 인덱스
    CREATE NONCLUSTERED INDEX [IDX_BannedWords_Global_CreatedAt] 
        ON [dbo].[BannedWords]([CreatedAt] DESC)
        WHERE [AgentId] IS NULL;

    PRINT 'BannedWords 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'BannedWords 테이블이 이미 존재합니다.';
END
GO
