-- Phase 2: Presentations 테이블에 ThemeId 컬럼 추가
-- 기존 DB 사용 시 이 스크립트를 실행하세요.

IF NOT EXISTS (
  SELECT 1 FROM sys.columns
  WHERE object_id = OBJECT_ID(N'dbo.Presentations') AND name = 'ThemeId'
)
BEGIN
  ALTER TABLE dbo.Presentations
  ADD ThemeId nvarchar(50) NULL;
END
GO
