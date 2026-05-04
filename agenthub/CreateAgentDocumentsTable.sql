-- Agent와 KnowledgeBaseDocument를 연결하는 테이블 생성 스크립트
-- 실행 날짜: 2026-01-12

USE [AIAgentManagement]
GO

-- AgentDocuments 테이블 생성
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[AgentDocuments]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[AgentDocuments] (
        [AgentDocumentId] INT IDENTITY(1,1) NOT NULL,
        [AgentId] INT NOT NULL,
        [DocumentId] INT NOT NULL,
        [CreatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        CONSTRAINT [PK_AgentDocuments] PRIMARY KEY CLUSTERED ([AgentDocumentId] ASC)
    );
    
    -- 인덱스 생성
    CREATE NONCLUSTERED INDEX [IX_AgentDocuments_AgentId] ON [dbo].[AgentDocuments]([AgentId]);
    CREATE NONCLUSTERED INDEX [IX_AgentDocuments_DocumentId] ON [dbo].[AgentDocuments]([DocumentId]);
    CREATE UNIQUE NONCLUSTERED INDEX [IX_AgentDocuments_AgentId_DocumentId] ON [dbo].[AgentDocuments]([AgentId], [DocumentId]);
    
    PRINT 'AgentDocuments 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'AgentDocuments 테이블이 이미 존재합니다.';
END
GO

-- Agents 테이블에 EnableRag 컬럼 추가
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[Agents]') AND name = 'EnableRag')
BEGIN
    ALTER TABLE [dbo].[Agents]
    ADD [EnableRag] BIT NOT NULL DEFAULT 0;
    PRINT 'EnableRag 컬럼이 추가되었습니다.';
END
ELSE
BEGIN
    PRINT 'EnableRag 컬럼이 이미 존재합니다.';
END
GO

PRINT '스크립트 실행이 완료되었습니다.';
GO
