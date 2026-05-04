-- Presentations 테이블 생성
-- 실행 날짜: 2026-01-12

USE [AIAgentManagement]
GO

-- Presentations 테이블 생성
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Presentations]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Presentations](
        [PresentationId] [int] IDENTITY(1,1) NOT NULL,
        [UserId] [int] NOT NULL,
        [Title] [nvarchar](200) NOT NULL,
        [Slides] [nvarchar](max) NULL,
        [CreatedAt] [datetime2](7) NOT NULL,
        [UpdatedAt] [datetime2](7) NOT NULL,
        CONSTRAINT [PK_Presentations] PRIMARY KEY CLUSTERED 
        (
            [PresentationId] ASC
        )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
    
    -- Foreign Key 추가
    ALTER TABLE [dbo].[Presentations]
    ADD CONSTRAINT [FK_Presentations_Users] FOREIGN KEY([UserId])
    REFERENCES [dbo].[Users] ([UserId])
    ON DELETE CASCADE
    
    -- 인덱스 추가
    CREATE NONCLUSTERED INDEX [IX_Presentations_UserId] ON [dbo].[Presentations]
    (
        [UserId] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    CREATE NONCLUSTERED INDEX [IX_Presentations_UpdatedAt] ON [dbo].[Presentations]
    (
        [UpdatedAt] DESC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    PRINT 'Presentations 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'Presentations 테이블이 이미 존재합니다.';
END
GO

PRINT '스크립트 실행이 완료되었습니다.';
GO
