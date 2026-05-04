-- FAQ 테이블 생성
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Faqs]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Faqs] (
        [FaqId] INT IDENTITY(1,1) NOT NULL,
        [Question] NVARCHAR(500) NOT NULL,
        [Answer] NVARCHAR(MAX) NOT NULL,
        [Category] NVARCHAR(50) NULL,
        [SortOrder] INT NOT NULL DEFAULT 0,
        [IsActive] BIT NOT NULL DEFAULT 1,
        [CreatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        [UpdatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        CONSTRAINT [PK_Faqs] PRIMARY KEY CLUSTERED ([FaqId] ASC)
    );

    CREATE INDEX [IX_Faqs_Category] ON [dbo].[Faqs]([Category]);
    CREATE INDEX [IX_Faqs_IsActive] ON [dbo].[Faqs]([IsActive]);
    CREATE INDEX [IX_Faqs_SortOrder] ON [dbo].[Faqs]([SortOrder]);

    -- 초기 FAQ 데이터 삽입
    INSERT INTO [dbo].[Faqs] ([Question], [Answer], [Category], [SortOrder], [IsActive])
    VALUES
        (N'AI Agent란 무엇인가요?', N'AI Agent는 특정 작업을 자동으로 수행하도록 설정된 AI 어시스턴트입니다. 코드 리뷰, 문서 작성, 데이터 분석 등 다양한 작업에 특화된 Agent를 만들 수 있습니다.<br><br>각 Agent는 고유한 시스템 프롬프트를 가지고 있어, 특정 목적에 최적화된 응답을 제공합니다.', N'getting-started', 1, 1),
        (N'Agent는 어떻게 생성하나요?', N'<ol><li>Agent 실행 페이지에서 "새 Agent 추가" 버튼 클릭</li><li>Agent 이름과 설명 입력</li><li>AI 서비스 및 모델 선택</li><li>시스템 프롬프트 작성</li><li>온도, 최대 토큰 등 파라미터 설정</li><li>저장 후 테스트</li></ol>', N'agents', 1, 1),
        (N'Agent를 공개하거나 비공개로 설정할 수 있나요?', N'네, Agent 생성 시 "공개" 옵션을 선택하면 다른 사용자들도 사용할 수 있는 공개 Agent로 설정됩니다. 비공개로 설정하면 자신만 사용할 수 있는 개인 Agent가 됩니다.', N'agents', 2, 1),
        (N'API 할당량은 어떻게 관리하나요?', N'할당량 관리 페이지에서 사용자별, 서비스별 할당량을 설정할 수 있습니다. 월간 한도를 설정하면 80%, 90% 도달 시 자동으로 알림이 발송됩니다. 실시간 사용량 추적도 가능합니다.', N'api', 1, 1),
        (N'API 키는 어떻게 생성하고 관리하나요?', N'API 키 관리 페이지에서 새로운 API 키를 생성할 수 있습니다. 각 키에는 이름과 만료일을 설정할 수 있으며, 필요시 키를 비활성화하거나 삭제할 수 있습니다. 키는 생성 시 한 번만 표시되므로 안전하게 보관하세요.', N'api', 2, 1),
        (N'비용은 어떻게 청구되나요?', N'사용한 토큰 수에 따라 비용이 계산됩니다. 비용 분석 페이지에서 실시간으로 비용을 추적할 수 있으며, 서비스별, 기간별 상세 분석도 제공됩니다. 예산 설정 기능으로 비용을 관리할 수 있습니다.', N'getting-started', 2, 1),
        (N'팀원을 초대하려면 어떻게 하나요?', N'팀 관리 페이지에서 "멤버 초대" 버튼을 클릭하고 이메일 주소와 역할(관리자/일반 사용자)을 선택한 후 초대 메일을 발송하면 됩니다. 초대된 사용자는 이메일 링크를 통해 가입할 수 있습니다.', N'getting-started', 3, 1),
        (N'채팅 기능은 어떻게 사용하나요?', N'Agent 실행 페이지에서 Agent를 선택하거나 기본 모드로 채팅을 시작할 수 있습니다. 여러 AI 서비스와 동시에 대화하고 비교하는 멀티 채팅 기능도 제공됩니다. 대화 기록은 자동으로 저장됩니다.', N'getting-started', 4, 1),
        (N'RAG(Retrieval Augmented Generation) 기능은 무엇인가요?', N'RAG 기능을 활성화하면 지식베이스의 문서를 참조하여 더 정확하고 관련성 있는 응답을 제공합니다. Agent 설정에서 RAG를 활성화하고, 지식베이스에 관련 문서를 업로드하면 됩니다.', N'agents', 3, 1),
        (N'웹 검색 기능은 어떻게 사용하나요?', N'채팅 중 웹 검색 옵션을 활성화하면 최신 정보를 검색하여 응답에 포함시킬 수 있습니다. ChatGPT 서비스와 함께 사용할 때 특히 유용합니다.', N'agents', 4, 1),
        (N'사용 기록은 어디서 확인할 수 있나요?', N'사용 기록 페이지에서 모든 API 호출 내역을 확인할 수 있습니다. 날짜, 사용자, 서비스별로 필터링하여 검색할 수 있으며, CSV 형식으로 내보낼 수도 있습니다.', N'getting-started', 5, 1),
        (N'시스템 상태는 어떻게 확인하나요?', N'시스템 상태 페이지에서 데이터베이스 연결, 디스크 사용량, 메모리 사용량 등 시스템 전반의 상태를 실시간으로 모니터링할 수 있습니다.', N'troubleshooting', 1, 1),
        (N'에러가 발생하면 어떻게 하나요?', N'먼저 감사 로그 페이지에서 에러 로그를 확인하세요. 자주 발생하는 문제는 FAQ에서 해결 방법을 찾을 수 있습니다. 문제가 지속되면 지원 팀에 문의하세요.', N'troubleshooting', 2, 1),
        (N'데이터베이스 백업은 어떻게 하나요?', N'시스템 > 데이터베이스 백업 메뉴에서 수동으로 백업을 생성하거나, 자동 백업 일정을 설정할 수 있습니다. 백업 파일은 안전한 위치에 저장하세요.', N'troubleshooting', 3, 1),
        (N'할당량을 초과하면 어떻게 되나요?', N'할당량을 초과하면 해당 서비스에 대한 요청이 차단됩니다. 할당량 관리 페이지에서 한도를 조정하거나 다음 초기화일까지 대기해야 합니다.', N'api', 3, 1);

    PRINT 'Faqs 테이블이 생성되었습니다.';
END
ELSE
BEGIN
    PRINT 'Faqs 테이블이 이미 존재합니다.';
END
GO
