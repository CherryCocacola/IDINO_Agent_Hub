-- 금칙어 테이블 성능 최적화 인덱스 추가 스크립트
-- 페이징 성능 향상을 위한 인덱스 추가

-- 기존 인덱스 확인
IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IDX_BannedWords_AgentId_CreatedAt' AND object_id = OBJECT_ID('dbo.BannedWords'))
BEGIN
    PRINT '인덱스 IDX_BannedWords_AgentId_CreatedAt가 이미 존재합니다.';
END
ELSE
BEGIN
    -- 페이징 성능 향상을 위한 인덱스 (AgentId + CreatedAt DESC 정렬 최적화)
    CREATE NONCLUSTERED INDEX [IDX_BannedWords_AgentId_CreatedAt] 
        ON [dbo].[BannedWords]([AgentId] ASC, [CreatedAt] DESC);
    PRINT '인덱스 IDX_BannedWords_AgentId_CreatedAt가 생성되었습니다.';
END
GO

-- 전역 금칙어 페이징 최적화 인덱스
IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IDX_BannedWords_Global_CreatedAt' AND object_id = OBJECT_ID('dbo.BannedWords'))
BEGIN
    PRINT '인덱스 IDX_BannedWords_Global_CreatedAt가 이미 존재합니다.';
END
ELSE
BEGIN
    CREATE NONCLUSTERED INDEX [IDX_BannedWords_Global_CreatedAt] 
        ON [dbo].[BannedWords]([CreatedAt] DESC)
        WHERE [AgentId] IS NULL;
    PRINT '인덱스 IDX_BannedWords_Global_CreatedAt가 생성되었습니다.';
END
GO

PRINT '';
PRINT '금칙어 테이블 성능 최적화 인덱스 추가가 완료되었습니다.';
PRINT '이 인덱스들은 페이징 쿼리의 성능을 크게 향상시킵니다.';
GO
