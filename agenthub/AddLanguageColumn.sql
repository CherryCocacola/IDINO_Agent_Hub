-- Add Language column to ChatConversations table
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[ChatConversations]') AND name = 'Language')
BEGIN
    ALTER TABLE [dbo].[ChatConversations]
    ADD [Language] [nvarchar](10) NULL;
END
GO

-- Update existing conversations to use 'auto' as default language
UPDATE [dbo].[ChatConversations]
SET [Language] = 'auto'
WHERE [Language] IS NULL;
GO
