-- RAG 기능을 위한 테이블 생성 스크립트
-- KnowledgeBaseDocuments: 지식 베이스 문서 저장
-- DocumentChunks: 문서 청크 및 임베딩 벡터 저장

USE [AIAgentManagement]
GO

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

-- 1. KnowledgeBaseDocuments 테이블 생성
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[KnowledgeBaseDocuments]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[KnowledgeBaseDocuments](
        [DocumentId] [int] IDENTITY(1,1) NOT NULL,
        [UserId] [int] NOT NULL,
        [Title] [nvarchar](500) NOT NULL,
        [Content] [nvarchar](max) NOT NULL,
        [SourceType] [nvarchar](50) NOT NULL, -- 'KnowledgeBase' or 'UploadedFile'
        [SourceId] [nvarchar](255) NULL, -- 참조 ID (파일 경로 또는 문서 ID)
        [IsIndexed] [bit] NOT NULL DEFAULT(0), -- 인덱싱 완료 여부
        [IndexedAt] [datetime2](7) NULL,
        [CreatedAt] [datetime2](7) NOT NULL,
        [UpdatedAt] [datetime2](7) NOT NULL,
        CONSTRAINT [PK_KnowledgeBaseDocuments] PRIMARY KEY CLUSTERED 
        (
            [DocumentId] ASC
        )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
    
    -- 기본값 설정
    ALTER TABLE [dbo].[KnowledgeBaseDocuments] ADD DEFAULT (GETDATE()) FOR [CreatedAt]
    ALTER TABLE [dbo].[KnowledgeBaseDocuments] ADD DEFAULT (GETDATE()) FOR [UpdatedAt]
    
    -- 인덱스 생성
    CREATE NONCLUSTERED INDEX [IDX_KnowledgeBaseDocuments_UserId] 
        ON [dbo].[KnowledgeBaseDocuments]([UserId])
    
    CREATE NONCLUSTERED INDEX [IDX_KnowledgeBaseDocuments_SourceType_SourceId] 
        ON [dbo].[KnowledgeBaseDocuments]([SourceType], [SourceId])
    
    CREATE NONCLUSTERED INDEX [IDX_KnowledgeBaseDocuments_IsIndexed] 
        ON [dbo].[KnowledgeBaseDocuments]([IsIndexed], [IndexedAt])
END
GO

-- 2. DocumentChunks 테이블 생성
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[DocumentChunks]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[DocumentChunks](
        [ChunkId] [bigint] IDENTITY(1,1) NOT NULL,
        [DocumentId] [int] NOT NULL,
        [ChunkIndex] [int] NOT NULL, -- 청크 순서
        [Content] [nvarchar](max) NOT NULL, -- 청크 텍스트
        [Embedding] [nvarchar](max) NULL, -- JSON 배열로 벡터 저장 (예: "[0.123, 0.456, ...]")
        [Metadata] [nvarchar](max) NULL, -- JSON 형식의 메타데이터
        [CreatedAt] [datetime2](7) NOT NULL,
        CONSTRAINT [PK_DocumentChunks] PRIMARY KEY CLUSTERED 
        (
            [ChunkId] ASC
        )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
    
    -- 기본값 설정
    ALTER TABLE [dbo].[DocumentChunks] ADD DEFAULT (GETDATE()) FOR [CreatedAt]
    
    -- 인덱스 생성
    CREATE NONCLUSTERED INDEX [IDX_DocumentChunks_DocumentId] 
        ON [dbo].[DocumentChunks]([DocumentId], [ChunkIndex])
    
    -- DocumentId에 대한 외래키는 없지만 인덱스로 성능 최적화
END
GO

PRINT 'RAG 테이블 생성 완료: KnowledgeBaseDocuments, DocumentChunks'
GO
