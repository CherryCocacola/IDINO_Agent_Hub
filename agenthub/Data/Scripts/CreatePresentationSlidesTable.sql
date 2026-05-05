-- ============================================================
-- PresentationSlides 테이블 생성 및 기존 데이터 마이그레이션
-- Presentations.Slides (nvarchar max JSON) → 슬라이드별 1행
-- '문자열 잘림' 오류 근본 해결 — Content 컬럼은 nvarchar(max)
-- ============================================================

-- 1. PresentationSlides 테이블 생성 (없을 때만)
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'PresentationSlides')
BEGIN
    CREATE TABLE [dbo].[PresentationSlides] (
        [SlideId]          NVARCHAR(50)    NOT NULL PRIMARY KEY,
        [PresentationId]   INT             NOT NULL,
        [SlideNumber]      INT             NOT NULL,
        [Title]            NVARCHAR(500)   NOT NULL DEFAULT '',
        [Content]          NVARCHAR(MAX)   NOT NULL DEFAULT '',
        [Layout]           NVARCHAR(50)    NOT NULL DEFAULT 'title-content',
        [ImageUrl]         NVARCHAR(2000)  NULL,
        [ImageDescription] NVARCHAR(2000)  NULL,
        [ImagePrompt]      NVARCHAR(2000)  NULL,
        [ChartsJson]       NVARCHAR(MAX)   NULL,
        [TablesJson]       NVARCHAR(MAX)   NULL,
        [ImagesJson]       NVARCHAR(MAX)   NULL,
        [CreatedAt]        DATETIME2       NOT NULL DEFAULT GETUTCDATE(),
        [UpdatedAt]        DATETIME2       NOT NULL DEFAULT GETUTCDATE(),
        CONSTRAINT [FK_PresentationSlides_Presentations]
            FOREIGN KEY ([PresentationId])
            REFERENCES [dbo].[Presentations]([PresentationId])
            ON DELETE CASCADE
    );

    CREATE INDEX [IX_PresentationSlides_PresentationId_SlideNumber]
        ON [dbo].[PresentationSlides] ([PresentationId], [SlideNumber]);

    PRINT 'PresentationSlides 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'PresentationSlides 테이블이 이미 존재합니다.';
END
GO

-- 2. 기존 Presentations.Slides JSON → PresentationSlides 행으로 마이그레이션
--    이미 PresentationSlides에 행이 있는 프레젠테이션은 건너뜁니다.
DECLARE @PresentationId INT;
DECLARE @Slides NVARCHAR(MAX);
DECLARE @MigratedCount INT = 0;
DECLARE @ErrorCount INT = 0;

DECLARE pres_cursor CURSOR FOR
    SELECT PresentationId, Slides
    FROM Presentations
    WHERE Slides IS NOT NULL
      AND LEN(Slides) > 2
      AND PresentationId NOT IN (SELECT DISTINCT PresentationId FROM PresentationSlides);

OPEN pres_cursor;
FETCH NEXT FROM pres_cursor INTO @PresentationId, @Slides;

WHILE @@FETCH_STATUS = 0
BEGIN
    BEGIN TRY
        -- OPENJSON으로 슬라이드 배열 파싱
        INSERT INTO [dbo].[PresentationSlides]
            (SlideId, PresentationId, SlideNumber, Title, Content, Layout,
             ImageUrl, ImageDescription, ImagePrompt,
             ChartsJson, TablesJson, ImagesJson,
             CreatedAt, UpdatedAt)
        SELECT
            ISNULL(JSON_VALUE(slide.value, '$.slideId'),  NEWID()),
            @PresentationId,
            ISNULL(CAST(JSON_VALUE(slide.value, '$.slideNumber') AS INT), ROW_NUMBER() OVER (ORDER BY slide.[key])),
            ISNULL(JSON_VALUE(slide.value, '$.title'), ''),
            ISNULL(JSON_QUERY(slide.value, '$.content'),
                   ISNULL(JSON_VALUE(slide.value, '$.content'), '')),
            ISNULL(JSON_VALUE(slide.value, '$.layout'), 'title-content'),
            JSON_VALUE(slide.value, '$.imageUrl'),
            JSON_VALUE(slide.value, '$.imageDescription'),
            JSON_VALUE(slide.value, '$.imagePrompt'),
            JSON_QUERY(slide.value, '$.charts'),
            JSON_QUERY(slide.value, '$.tables'),
            JSON_QUERY(slide.value, '$.images'),
            GETUTCDATE(),
            GETUTCDATE()
        FROM OPENJSON(@Slides) AS slide;

        SET @MigratedCount = @MigratedCount + 1;
    END TRY
    BEGIN CATCH
        SET @ErrorCount = @ErrorCount + 1;
        PRINT CONCAT('마이그레이션 실패 (PresentationId=', @PresentationId, '): ', ERROR_MESSAGE());
    END CATCH;

    FETCH NEXT FROM pres_cursor INTO @PresentationId, @Slides;
END;

CLOSE pres_cursor;
DEALLOCATE pres_cursor;

PRINT CONCAT('마이그레이션 완료: 성공=', @MigratedCount, ', 실패=', @ErrorCount);
GO
