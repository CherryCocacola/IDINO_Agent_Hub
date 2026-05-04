-- ApiServices 테이블에 ServiceType 컬럼 추가
-- 실행 날짜: 2026-01-12

USE [AIAgentManagement]
GO

-- ServiceType 컬럼 추가
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[ApiServices]') AND name = 'ServiceType')
BEGIN
    ALTER TABLE [dbo].[ApiServices]
    ADD [ServiceType] NVARCHAR(50) NOT NULL DEFAULT 'Chat';
    PRINT 'ServiceType 컬럼이 추가되었습니다.';
END
ELSE
BEGIN
    PRINT 'ServiceType 컬럼이 이미 존재합니다.';
END
GO

-- 기존 서비스들의 ServiceType을 'Chat'으로 설정 (이미 기본값이지만 명시적으로 업데이트)
UPDATE [dbo].[ApiServices]
SET [ServiceType] = 'Chat'
WHERE [ServiceType] IS NULL OR [ServiceType] = '';
GO

PRINT '스크립트 실행이 완료되었습니다.';
GO
