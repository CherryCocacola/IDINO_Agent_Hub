-- Agents 테이블에 EnableRag 컬럼 추가
-- 실행 날짜: 2026-01-12

USE [AIAgentManagement]
GO

-- EnableRag 컬럼 추가
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[Agents]') AND name = 'EnableRag')
BEGIN
    ALTER TABLE [dbo].[Agents]
    ADD [EnableRag] BIT NOT NULL DEFAULT 0;
    PRINT 'EnableRag 컬럼이 Agents 테이블에 추가되었습니다.';
END
ELSE
BEGIN
    PRINT 'EnableRag 컬럼이 이미 Agents 테이블에 존재합니다.';
END
GO

PRINT '스크립트 실행이 완료되었습니다.';
GO
