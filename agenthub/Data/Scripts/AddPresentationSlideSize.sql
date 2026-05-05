-- Phase 1: Presentations 테이블에 SlideSize 컬럼 추가
-- 기존 DB 사용 시 이 스크립트를 실행하세요.

IF NOT EXISTS (
  SELECT 1 FROM sys.columns
  WHERE object_id = OBJECT_ID(N'dbo.Presentations') AND name = 'SlideSize'
)
BEGIN
  ALTER TABLE dbo.Presentations
  ADD SlideSize nvarchar(20) NULL;
END
GO
