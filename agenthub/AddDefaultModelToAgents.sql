-- Add DefaultModel column to Agents table
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.Agents') 
    AND name = 'DefaultModel'
)
BEGIN
    ALTER TABLE [dbo].[Agents]
    ADD [DefaultModel] NVARCHAR(100) NULL;
    
    PRINT 'DefaultModel column added to Agents table';
END
ELSE
BEGIN
    PRINT 'DefaultModel column already exists in Agents table';
END
GO
