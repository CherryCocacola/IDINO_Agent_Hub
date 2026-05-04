-- ApiKeys 테이블에 AgentId 컬럼 추가 (Agent 전용 API Key 지원)

IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID(N'[dbo].[ApiKeys]') 
    AND name = 'AgentId'
)
BEGIN
    ALTER TABLE [dbo].[ApiKeys]
    ADD [AgentId] INT NULL;

    CREATE NONCLUSTERED INDEX [IDX_ApiKeys_AgentId] 
        ON [dbo].[ApiKeys]([AgentId] ASC)
        WHERE [AgentId] IS NOT NULL;

    PRINT 'ApiKeys 테이블에 AgentId 컬럼과 인덱스가 추가되었습니다.';
END
ELSE
BEGIN
    PRINT 'ApiKeys 테이블에 AgentId 컬럼이 이미 존재합니다.';
END
GO
