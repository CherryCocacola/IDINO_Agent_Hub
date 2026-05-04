-- PiiDetectionLogs 테이블 생성
-- 실행 날짜: 2026-02-12

USE [AIAgentManagement]
GO

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[PiiDetectionLogs]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[PiiDetectionLogs](
        [LogId] [int] IDENTITY(1,1) NOT NULL,
        [UserId] [int] NULL,
        [AgentId] [int] NULL,
        [ConversationId] [int] NULL,
        [DetectionType] [nvarchar](50) NOT NULL,
        [OriginalMessage] [nvarchar](max) NOT NULL,
        [ActionTaken] [nvarchar](50) NOT NULL,
        [DetectedAt] [datetime2](7) NOT NULL,
        [IpAddress] [nvarchar](50) NULL,
        CONSTRAINT [PK_PiiDetectionLogs] PRIMARY KEY CLUSTERED ([LogId] ASC)
    )
    
    -- 인덱스 생성
    CREATE NONCLUSTERED INDEX [IDX_PiiDetectionLogs_UserId_DetectedAt]
    ON [dbo].[PiiDetectionLogs] ([UserId] ASC, [DetectedAt] DESC)
    
    CREATE NONCLUSTERED INDEX [IDX_PiiDetectionLogs_AgentId_DetectedAt]
    ON [dbo].[PiiDetectionLogs] ([AgentId] ASC, [DetectedAt] DESC)
    
    CREATE NONCLUSTERED INDEX [IDX_PiiDetectionLogs_DetectionType]
    ON [dbo].[PiiDetectionLogs] ([DetectionType] ASC)
    
    CREATE NONCLUSTERED INDEX [IDX_PiiDetectionLogs_DetectedAt]
    ON [dbo].[PiiDetectionLogs] ([DetectedAt] DESC)
    
    PRINT 'PiiDetectionLogs 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'PiiDetectionLogs 테이블이 이미 존재합니다.';
END
GO
