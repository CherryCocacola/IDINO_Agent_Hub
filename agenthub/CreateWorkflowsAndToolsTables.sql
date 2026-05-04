-- Workflow 및 Tool 관련 테이블 생성
-- 실행 날짜: 2026-01-12

USE [AIAgentManagement]
GO

-- =============================================
-- 1. Tools 테이블 생성
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Tools]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Tools](
        [ToolId] [int] IDENTITY(1,1) NOT NULL,
        [ToolCode] [nvarchar](50) NOT NULL,
        [ToolName] [nvarchar](100) NOT NULL,
        [Description] [nvarchar](500) NULL,
        [ToolType] [nvarchar](20) NOT NULL, -- CSharp, Python, JavaScript, Api
        [Category] [nvarchar](50) NULL,
        [IconClass] [nvarchar](100) NULL,
        [ColorCode] [nvarchar](20) NULL,
        [CreatedBy] [int] NOT NULL,
        [IsPublic] [bit] NOT NULL DEFAULT 0,
        [IsActive] [bit] NOT NULL DEFAULT 1,
        [CreatedAt] [datetime2](7) NOT NULL DEFAULT GETDATE(),
        [UpdatedAt] [datetime2](7) NOT NULL DEFAULT GETDATE(),
        CONSTRAINT [PK_Tools] PRIMARY KEY CLUSTERED 
        (
            [ToolId] ASC
        )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY],
        CONSTRAINT [UQ_Tools_ToolCode] UNIQUE NONCLUSTERED 
        (
            [ToolCode] ASC
        )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    ) ON [PRIMARY]
    
    -- Foreign Key 추가
    ALTER TABLE [dbo].[Tools]
    ADD CONSTRAINT [FK_Tools_Users] FOREIGN KEY([CreatedBy])
    REFERENCES [dbo].[Users] ([UserId])
    ON DELETE NO ACTION
    
    -- 인덱스 추가
    CREATE NONCLUSTERED INDEX [IX_Tools_CreatedBy] ON [dbo].[Tools]
    (
        [CreatedBy] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    CREATE NONCLUSTERED INDEX [IX_Tools_ToolType] ON [dbo].[Tools]
    (
        [ToolType] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    CREATE NONCLUSTERED INDEX [IX_Tools_IsActive] ON [dbo].[Tools]
    (
        [IsActive] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    PRINT 'Tools 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'Tools 테이블이 이미 존재합니다.';
END
GO

-- =============================================
-- 2. ToolVersions 테이블 생성
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[ToolVersions]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[ToolVersions](
        [VersionId] [int] IDENTITY(1,1) NOT NULL,
        [ToolId] [int] NOT NULL,
        [Version] [nvarchar](20) NOT NULL,
        [Code] [nvarchar](max) NULL,
        [Config] [nvarchar](max) NULL, -- JSON 형식의 설정 (파라미터 정의 등)
        [IsActive] [bit] NOT NULL DEFAULT 1,
        [CreatedAt] [datetime2](7) NOT NULL DEFAULT GETDATE(),
        CONSTRAINT [PK_ToolVersions] PRIMARY KEY CLUSTERED 
        (
            [VersionId] ASC
        )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
    
    -- Foreign Key 추가
    ALTER TABLE [dbo].[ToolVersions]
    ADD CONSTRAINT [FK_ToolVersions_Tools] FOREIGN KEY([ToolId])
    REFERENCES [dbo].[Tools] ([ToolId])
    ON DELETE CASCADE
    
    -- 인덱스 추가
    CREATE NONCLUSTERED INDEX [IX_ToolVersions_ToolId] ON [dbo].[ToolVersions]
    (
        [ToolId] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    CREATE NONCLUSTERED INDEX [IX_ToolVersions_IsActive] ON [dbo].[ToolVersions]
    (
        [IsActive] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    PRINT 'ToolVersions 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'ToolVersions 테이블이 이미 존재합니다.';
END
GO

-- =============================================
-- 3. ToolExecutions 테이블 생성
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[ToolExecutions]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[ToolExecutions](
        [ExecutionId] [bigint] IDENTITY(1,1) NOT NULL,
        [ToolId] [int] NOT NULL,
        [VersionId] [int] NULL,
        [UserId] [int] NULL,
        [InputData] [nvarchar](max) NULL, -- JSON 형식
        [OutputData] [nvarchar](max) NULL, -- JSON 형식
        [Status] [nvarchar](20) NOT NULL, -- Running, Completed, Failed, Cancelled
        [ErrorMessage] [nvarchar](max) NULL,
        [ExecutionTime] [int] NULL, -- 밀리초
        [MemoryUsage] [bigint] NULL, -- 바이트
        [CreatedAt] [datetime2](7) NOT NULL DEFAULT GETDATE(),
        CONSTRAINT [PK_ToolExecutions] PRIMARY KEY CLUSTERED 
        (
            [ExecutionId] ASC
        )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
    
    -- Foreign Key 추가
    ALTER TABLE [dbo].[ToolExecutions]
    ADD CONSTRAINT [FK_ToolExecutions_Tools] FOREIGN KEY([ToolId])
    REFERENCES [dbo].[Tools] ([ToolId])
    ON DELETE NO ACTION
    
    ALTER TABLE [dbo].[ToolExecutions]
    ADD CONSTRAINT [FK_ToolExecutions_ToolVersions] FOREIGN KEY([VersionId])
    REFERENCES [dbo].[ToolVersions] ([VersionId])
    ON DELETE SET NULL
    
    ALTER TABLE [dbo].[ToolExecutions]
    ADD CONSTRAINT [FK_ToolExecutions_Users] FOREIGN KEY([UserId])
    REFERENCES [dbo].[Users] ([UserId])
    ON DELETE SET NULL
    
    -- 인덱스 추가
    CREATE NONCLUSTERED INDEX [IX_ToolExecutions_ToolId] ON [dbo].[ToolExecutions]
    (
        [ToolId] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    CREATE NONCLUSTERED INDEX [IX_ToolExecutions_UserId] ON [dbo].[ToolExecutions]
    (
        [UserId] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    CREATE NONCLUSTERED INDEX [IX_ToolExecutions_Status] ON [dbo].[ToolExecutions]
    (
        [Status] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    CREATE NONCLUSTERED INDEX [IX_ToolExecutions_CreatedAt] ON [dbo].[ToolExecutions]
    (
        [CreatedAt] DESC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    PRINT 'ToolExecutions 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'ToolExecutions 테이블이 이미 존재합니다.';
END
GO

-- =============================================
-- 4. Workflows 테이블 생성
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Workflows]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Workflows](
        [WorkflowId] [int] IDENTITY(1,1) NOT NULL,
        [WorkflowCode] [nvarchar](50) NOT NULL,
        [WorkflowName] [nvarchar](100) NOT NULL,
        [Description] [nvarchar](500) NULL,
        [WorkflowDefinition] [nvarchar](max) NULL, -- JSON 형식의 전체 Workflow 정의
        [IconClass] [nvarchar](100) NULL,
        [ColorCode] [nvarchar](20) NULL,
        [CreatedBy] [int] NOT NULL,
        [IsPublic] [bit] NOT NULL DEFAULT 0,
        [IsActive] [bit] NOT NULL DEFAULT 1,
        [CreatedAt] [datetime2](7) NOT NULL DEFAULT GETDATE(),
        [UpdatedAt] [datetime2](7) NOT NULL DEFAULT GETDATE(),
        CONSTRAINT [PK_Workflows] PRIMARY KEY CLUSTERED 
        (
            [WorkflowId] ASC
        )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY],
        CONSTRAINT [UQ_Workflows_WorkflowCode] UNIQUE NONCLUSTERED 
        (
            [WorkflowCode] ASC
        )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
    
    -- Foreign Key 추가
    ALTER TABLE [dbo].[Workflows]
    ADD CONSTRAINT [FK_Workflows_Users] FOREIGN KEY([CreatedBy])
    REFERENCES [dbo].[Users] ([UserId])
    ON DELETE NO ACTION
    
    -- 인덱스 추가
    CREATE NONCLUSTERED INDEX [IX_Workflows_CreatedBy] ON [dbo].[Workflows]
    (
        [CreatedBy] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    CREATE NONCLUSTERED INDEX [IX_Workflows_IsActive] ON [dbo].[Workflows]
    (
        [IsActive] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    PRINT 'Workflows 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'Workflows 테이블이 이미 존재합니다.';
END
GO

-- =============================================
-- 5. WorkflowNodes 테이블 생성
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[WorkflowNodes]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[WorkflowNodes](
        [NodeId] [int] IDENTITY(1,1) NOT NULL,
        [WorkflowId] [int] NOT NULL,
        [NodeCode] [nvarchar](50) NOT NULL,
        [NodeType] [nvarchar](20) NOT NULL, -- Agent, LLM, Tool, Condition, Loop, Merge, DataTransform
        [NodeConfig] [nvarchar](max) NULL, -- JSON 형식의 노드 설정
        [PositionX] [float] NULL,
        [PositionY] [float] NULL,
        [Connections] [nvarchar](max) NULL, -- JSON 형식의 연결 정보
        [SortOrder] [int] NOT NULL DEFAULT 0,
        [CreatedAt] [datetime2](7) NOT NULL DEFAULT GETDATE(),
        [UpdatedAt] [datetime2](7) NOT NULL DEFAULT GETDATE(),
        CONSTRAINT [PK_WorkflowNodes] PRIMARY KEY CLUSTERED 
        (
            [NodeId] ASC
        )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
    
    -- Foreign Key 추가
    ALTER TABLE [dbo].[WorkflowNodes]
    ADD CONSTRAINT [FK_WorkflowNodes_Workflows] FOREIGN KEY([WorkflowId])
    REFERENCES [dbo].[Workflows] ([WorkflowId])
    ON DELETE CASCADE
    
    -- 인덱스 추가
    CREATE NONCLUSTERED INDEX [IX_WorkflowNodes_WorkflowId] ON [dbo].[WorkflowNodes]
    (
        [WorkflowId] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    CREATE NONCLUSTERED INDEX [IX_WorkflowNodes_NodeType] ON [dbo].[WorkflowNodes]
    (
        [NodeType] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    PRINT 'WorkflowNodes 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'WorkflowNodes 테이블이 이미 존재합니다.';
END
GO

-- =============================================
-- 6. WorkflowExecutions 테이블 생성
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[WorkflowExecutions]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[WorkflowExecutions](
        [ExecutionId] [bigint] IDENTITY(1,1) NOT NULL,
        [WorkflowId] [int] NOT NULL,
        [UserId] [int] NULL,
        [InputData] [nvarchar](max) NULL, -- JSON 형식
        [OutputData] [nvarchar](max) NULL, -- JSON 형식
        [Status] [nvarchar](20) NOT NULL, -- Running, Completed, Failed, Cancelled
        [ErrorMessage] [nvarchar](max) NULL,
        [StartedAt] [datetime2](7) NOT NULL DEFAULT GETDATE(),
        [CompletedAt] [datetime2](7) NULL,
        [ExecutionTime] [int] NULL, -- 밀리초
        CONSTRAINT [PK_WorkflowExecutions] PRIMARY KEY CLUSTERED 
        (
            [ExecutionId] ASC
        )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
    
    -- Foreign Key 추가
    ALTER TABLE [dbo].[WorkflowExecutions]
    ADD CONSTRAINT [FK_WorkflowExecutions_Workflows] FOREIGN KEY([WorkflowId])
    REFERENCES [dbo].[Workflows] ([WorkflowId])
    ON DELETE NO ACTION
    
    ALTER TABLE [dbo].[WorkflowExecutions]
    ADD CONSTRAINT [FK_WorkflowExecutions_Users] FOREIGN KEY([UserId])
    REFERENCES [dbo].[Users] ([UserId])
    ON DELETE SET NULL
    
    -- 인덱스 추가
    CREATE NONCLUSTERED INDEX [IX_WorkflowExecutions_WorkflowId] ON [dbo].[WorkflowExecutions]
    (
        [WorkflowId] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    CREATE NONCLUSTERED INDEX [IX_WorkflowExecutions_UserId] ON [dbo].[WorkflowExecutions]
    (
        [UserId] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    CREATE NONCLUSTERED INDEX [IX_WorkflowExecutions_Status] ON [dbo].[WorkflowExecutions]
    (
        [Status] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    CREATE NONCLUSTERED INDEX [IX_WorkflowExecutions_StartedAt] ON [dbo].[WorkflowExecutions]
    (
        [StartedAt] DESC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    PRINT 'WorkflowExecutions 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'WorkflowExecutions 테이블이 이미 존재합니다.';
END
GO

-- =============================================
-- 7. WorkflowNodeExecutions 테이블 생성
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[WorkflowNodeExecutions]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[WorkflowNodeExecutions](
        [NodeExecutionId] [bigint] IDENTITY(1,1) NOT NULL,
        [ExecutionId] [bigint] NOT NULL,
        [NodeId] [int] NOT NULL,
        [InputData] [nvarchar](max) NULL, -- JSON 형식
        [OutputData] [nvarchar](max) NULL, -- JSON 형식
        [Status] [nvarchar](20) NOT NULL, -- Running, Completed, Failed, Skipped
        [ErrorMessage] [nvarchar](max) NULL,
        [StartedAt] [datetime2](7) NOT NULL DEFAULT GETDATE(),
        [CompletedAt] [datetime2](7) NULL,
        [ExecutionTime] [int] NULL, -- 밀리초
        CONSTRAINT [PK_WorkflowNodeExecutions] PRIMARY KEY CLUSTERED 
        (
            [NodeExecutionId] ASC
        )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
    
    -- Foreign Key 추가
    ALTER TABLE [dbo].[WorkflowNodeExecutions]
    ADD CONSTRAINT [FK_WorkflowNodeExecutions_WorkflowExecutions] FOREIGN KEY([ExecutionId])
    REFERENCES [dbo].[WorkflowExecutions] ([ExecutionId])
    ON DELETE CASCADE
    
    ALTER TABLE [dbo].[WorkflowNodeExecutions]
    ADD CONSTRAINT [FK_WorkflowNodeExecutions_WorkflowNodes] FOREIGN KEY([NodeId])
    REFERENCES [dbo].[WorkflowNodes] ([NodeId])
    ON DELETE NO ACTION
    
    -- 인덱스 추가
    CREATE NONCLUSTERED INDEX [IX_WorkflowNodeExecutions_ExecutionId] ON [dbo].[WorkflowNodeExecutions]
    (
        [ExecutionId] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    CREATE NONCLUSTERED INDEX [IX_WorkflowNodeExecutions_NodeId] ON [dbo].[WorkflowNodeExecutions]
    (
        [NodeId] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    CREATE NONCLUSTERED INDEX [IX_WorkflowNodeExecutions_Status] ON [dbo].[WorkflowNodeExecutions]
    (
        [Status] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    
    PRINT 'WorkflowNodeExecutions 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'WorkflowNodeExecutions 테이블이 이미 존재합니다.';
END
GO

PRINT '모든 테이블 생성 스크립트 실행이 완료되었습니다.';
GO
