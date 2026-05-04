-- Tutorials 테이블 생성
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Tutorials]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Tutorials] (
        [TutorialId] INT IDENTITY(1,1) NOT NULL,
        [Title] NVARCHAR(200) NOT NULL,
        [Description] NVARCHAR(1000) NULL,
        [VideoUrl] NVARCHAR(500) NULL,
        [ThumbnailUrl] NVARCHAR(500) NULL,
        [Duration] NVARCHAR(50) NULL,
        [Category] NVARCHAR(50) NULL,
        [SortOrder] INT NOT NULL DEFAULT 0,
        [IsActive] BIT NOT NULL DEFAULT 1,
        [ViewCount] INT NOT NULL DEFAULT 0,
        [CreatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        [UpdatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        CONSTRAINT [PK_Tutorials] PRIMARY KEY CLUSTERED ([TutorialId] ASC)
    );

    CREATE INDEX [IX_Tutorials_Category] ON [dbo].[Tutorials]([Category]);
    CREATE INDEX [IX_Tutorials_IsActive] ON [dbo].[Tutorials]([IsActive]);
    CREATE INDEX [IX_Tutorials_SortOrder] ON [dbo].[Tutorials]([SortOrder]);

    -- 초기 튜토리얼 데이터 삽입
    INSERT INTO [dbo].[Tutorials] ([Title], [Description], [VideoUrl], [Duration], [Category], [SortOrder], [IsActive])
    VALUES
        (N'시작하기 (5분)', N'기본 설정 및 첫 Agent 만들기', N'https://www.youtube.com/watch?v=example1', N'5분', N'getting-started', 1, 1),
        (N'Agent 빌더 (10분)', N'프롬프트 최적화 기법', N'https://www.youtube.com/watch?v=example2', N'10분', N'agents', 1, 1),
        (N'팀 협업 (8분)', N'팀원 초대 및 권한 관리', N'https://www.youtube.com/watch?v=example3', N'8분', N'getting-started', 2, 1),
        (N'API 연동 가이드 (12분)', N'API 키 생성 및 사용 방법', N'https://www.youtube.com/watch?v=example4', N'12분', N'api', 1, 1),
        (N'RAG 기능 활용 (15분)', N'지식베이스 구축 및 RAG 설정', N'https://www.youtube.com/watch?v=example5', N'15분', N'agents', 2, 1);

    PRINT 'Tutorials 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'Tutorials 테이블이 이미 존재합니다.';
END
GO
