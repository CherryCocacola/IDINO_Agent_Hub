-- 문자열 잘림 오류(문자열이나 이진 데이터는 잘립니다) 해결을 위한 스크립트
-- Presentations 테이블의 모든 문자열 컬럼 크기를 확실히 설정합니다.
-- SQL Server에서 실행하세요.

IF OBJECT_ID('Presentations', 'U') IS NOT NULL
BEGIN
    -- Title: 200자 (필수)
    IF EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('Presentations') AND name = 'Title')
    BEGIN
        ALTER TABLE Presentations ALTER COLUMN Title nvarchar(200) NOT NULL;
        PRINT 'Presentations.Title -> nvarchar(200)';
    END

    -- ThemeId: 50자 (선택)
    IF EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('Presentations') AND name = 'ThemeId')
    BEGIN
        ALTER TABLE Presentations ALTER COLUMN ThemeId nvarchar(50) NULL;
        PRINT 'Presentations.ThemeId -> nvarchar(50)';
    END

    -- Slides: max (JSON 저장용, 가장 중요)
    IF EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('Presentations') AND name = 'Slides')
    BEGIN
        ALTER TABLE Presentations ALTER COLUMN Slides nvarchar(max) NULL;
        PRINT 'Presentations.Slides -> nvarchar(max)';
    END

    PRINT 'Presentations 테이블 컬럼 수정 완료.';
END
ELSE
BEGIN
    PRINT 'Presentations 테이블을 찾을 수 없습니다.';
END
