-- PresentationTemplates 테이블 생성
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[PresentationTemplates]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[PresentationTemplates] (
        [TemplateId] INT IDENTITY(1,1) NOT NULL,
        [TemplateName] NVARCHAR(200) NOT NULL,
        [Description] NVARCHAR(500) NULL,
        [TemplateFilePath] NVARCHAR(500) NOT NULL,
        [TemplateStructure] NVARCHAR(MAX) NULL,
        [Category] NVARCHAR(50) NOT NULL DEFAULT 'business',
        [IsPublic] BIT NOT NULL DEFAULT 0,
        [CreatedBy] INT NULL,
        [CreatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        [UpdatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        CONSTRAINT [PK_PresentationTemplates] PRIMARY KEY CLUSTERED ([TemplateId] ASC),
        CONSTRAINT [FK_PresentationTemplates_Users] FOREIGN KEY ([CreatedBy]) REFERENCES [dbo].[Users] ([UserId])
    );

    -- 인덱스 생성
    CREATE NONCLUSTERED INDEX [IX_PresentationTemplates_Category] ON [dbo].[PresentationTemplates] ([Category]);
    CREATE NONCLUSTERED INDEX [IX_PresentationTemplates_IsPublic] ON [dbo].[PresentationTemplates] ([IsPublic]);
    CREATE NONCLUSTERED INDEX [IX_PresentationTemplates_CreatedBy] ON [dbo].[PresentationTemplates] ([CreatedBy]);
    
    PRINT 'PresentationTemplates 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'PresentationTemplates 테이블이 이미 존재합니다.';
END
GO
