-- Teams 및 TeamMembers 테이블 생성 스크립트
-- 실행 날짜: 2026-01-12

USE [AIAgentManagement]
GO

-- Teams 테이블 생성
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Teams]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Teams] (
        [TeamId] INT IDENTITY(1,1) NOT NULL,
        [TeamName] NVARCHAR(100) NOT NULL,
        [Description] NVARCHAR(500) NULL,
        [Department] NVARCHAR(100) NULL,
        [ManagerId] INT NULL,
        [IsActive] BIT NOT NULL DEFAULT 1,
        [CreatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        [UpdatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        CONSTRAINT [PK_Teams] PRIMARY KEY CLUSTERED ([TeamId] ASC)
    );
    
    -- 인덱스 생성
    CREATE NONCLUSTERED INDEX [IX_Teams_ManagerId] ON [dbo].[Teams]([ManagerId]);
    CREATE NONCLUSTERED INDEX [IX_Teams_IsActive] ON [dbo].[Teams]([IsActive]);
    
    PRINT 'Teams 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'Teams 테이블이 이미 존재합니다.';
END
GO

-- TeamMembers 테이블 생성
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[TeamMembers]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[TeamMembers] (
        [TeamMemberId] INT IDENTITY(1,1) NOT NULL,
        [TeamId] INT NOT NULL,
        [UserId] INT NOT NULL,
        [Role] NVARCHAR(50) NULL,
        [JoinedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        [LeftAt] DATETIME2 NULL,
        [IsActive] BIT NOT NULL DEFAULT 1,
        [AddedBy] INT NULL,
        CONSTRAINT [PK_TeamMembers] PRIMARY KEY CLUSTERED ([TeamMemberId] ASC)
    );
    
    -- 인덱스 생성
    CREATE NONCLUSTERED INDEX [IX_TeamMembers_TeamId] ON [dbo].[TeamMembers]([TeamId]);
    CREATE NONCLUSTERED INDEX [IX_TeamMembers_UserId] ON [dbo].[TeamMembers]([UserId]);
    CREATE NONCLUSTERED INDEX [IX_TeamMembers_IsActive] ON [dbo].[TeamMembers]([IsActive]);
    CREATE UNIQUE NONCLUSTERED INDEX [IX_TeamMembers_TeamId_UserId] ON [dbo].[TeamMembers]([TeamId], [UserId]) WHERE [IsActive] = 1;
    
    PRINT 'TeamMembers 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'TeamMembers 테이블이 이미 존재합니다.';
END
GO

PRINT '스크립트 실행이 완료되었습니다.';
GO
