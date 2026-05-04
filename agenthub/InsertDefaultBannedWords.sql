-- 금칙어 기본 데이터 삽입 스크립트
-- 관리자가 시스템에서 차단하고 싶은 단어/문구를 등록합니다.
-- 주의: 실제 사용 환경에 맞게 금칙어 목록을 검토하고 수정하세요.

-- 주의: CreatedBy는 관리자 사용자 ID로 변경해야 합니다.
-- 아래 쿼리로 관리자 사용자 ID를 확인하세요:
-- SELECT UserId FROM [dbo].[Users] WHERE Email = 'admin@example.com' OR (SELECT COUNT(*) FROM [dbo].[UserRoles] ur INNER JOIN [dbo].[Roles] r ON ur.RoleId = r.RoleId WHERE ur.UserId = Users.UserId AND r.RoleName = 'Admin') > 0;

DECLARE @AdminUserId INT;
SELECT TOP 1 @AdminUserId = UserId 
FROM [dbo].[Users] u
INNER JOIN [dbo].[UserRoles] ur ON u.UserId = ur.UserId
INNER JOIN [dbo].[Roles] r ON ur.RoleId = r.RoleId
WHERE r.RoleName = 'Admin' AND u.IsDeleted = 0
ORDER BY u.UserId;

IF @AdminUserId IS NULL
BEGIN
    PRINT '경고: 관리자 사용자를 찾을 수 없습니다. CreatedBy 값을 수동으로 설정해주세요.';
    SET @AdminUserId = 1; -- 기본값 (필요시 수정)
END

PRINT '관리자 사용자 ID: ' + CAST(@AdminUserId AS VARCHAR);

-- 기존 데이터 확인
IF EXISTS (SELECT 1 FROM [dbo].[BannedWords])
BEGIN
    PRINT '경고: BannedWords 테이블에 이미 데이터가 있습니다.';
    PRINT '기존 데이터를 삭제하려면 다음 명령을 실행하세요:';
    PRINT 'DELETE FROM [dbo].[BannedWords];';
    PRINT '';
END

-- 전역 금칙어 삽입 (AgentId = NULL)
-- 실제 사용 환경에 맞게 금칙어를 추가/수정하세요.
-- 주의: 아래 목록은 일반적인 예시입니다. 실제 욕설이나 부적절한 단어는 직접 추가해야 합니다.

INSERT INTO [dbo].[BannedWords] ([Word], [AgentId], [Description], [IsActive], [CreatedBy], [CreatedAt], [UpdatedAt])
VALUES
    -- 카테고리 1: 스팸/광고 관련 (실제 사용 가능)
    (N'무료체험', NULL, N'스팸 광고', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'광고문의', NULL, N'스팸 광고', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'광고주모집', NULL, N'스팸 광고', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'홍보문의', NULL, N'스팸 광고', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'협찬문의', NULL, N'스팸 광고', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'광고주', NULL, N'스팸 광고', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'제휴문의', NULL, N'스팸 광고', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'광고제휴', NULL, N'스팸 광고', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 2: 개인정보 요구 관련
    (N'비밀번호알려줘', NULL, N'개인정보 요구', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'계정정보', NULL, N'개인정보 요구', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'신용카드번호', NULL, N'개인정보 요구', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'주민등록번호', NULL, N'개인정보 요구', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'통장번호', NULL, N'개인정보 요구', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'비밀번호', NULL, N'개인정보 요구', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'계정비밀번호', NULL, N'개인정보 요구', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'개인정보알려줘', NULL, N'개인정보 요구', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 3: 피싱/사기 관련
    (N'당첨되었습니다', NULL, N'피싱 메시지', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'지급대기중', NULL, N'피싱 메시지', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'확인하러가기', NULL, N'피싱 메시지', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'지금바로', NULL, N'피싱 메시지', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'한정특가', NULL, N'피싱 메시지', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'당첨되셨습니다', NULL, N'피싱 메시지', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'경품지급', NULL, N'피싱 메시지', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'상금수령', NULL, N'피싱 메시지', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'이벤트당첨', NULL, N'피싱 메시지', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'무료증정', NULL, N'피싱 메시지', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 4: 불법/유해 콘텐츠 관련
    (N'불법사이트', NULL, N'불법 사이트 홍보', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법다운로드', NULL, N'불법 다운로드 유도', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'해킹', NULL, N'해킹 관련 콘텐츠', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'크랙', NULL, N'불법 소프트웨어 크랙', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'키젠', NULL, N'불법 소프트웨어 키젠', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법프로그램', NULL, N'불법 프로그램', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'무단침입', NULL, N'불법 침입', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'해킹프로그램', NULL, N'해킹 프로그램', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법소프트웨어', NULL, N'불법 소프트웨어', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 5: 성인/부적절 콘텐츠 관련
    (N'성인사이트', NULL, N'부적절한 콘텐츠', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'성인콘텐츠', NULL, N'부적절한 콘텐츠', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'성인영상', NULL, N'부적절한 콘텐츠', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 6: 도박/불법 사행성
    (N'도박사이트', NULL, N'불법 도박 사이트', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법도박', NULL, N'불법 도박', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'사행성게임', NULL, N'사행성 게임', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'온라인도박', NULL, N'온라인 도박', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'베팅사이트', NULL, N'베팅 사이트', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법베팅', NULL, N'불법 베팅', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 7: 마약/약물 관련
    (N'마약', NULL, N'불법 약물', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'대마초', NULL, N'불법 약물', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'약물구매', NULL, N'불법 약물', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'마약구매', NULL, N'불법 약물', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'마약판매', NULL, N'불법 약물', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 8: 기타 부적절한 표현
    (N'자살', NULL, N'자해/자살 관련', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'자해', NULL, N'자해/자살 관련', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'폭력', NULL, N'폭력 관련', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'테러', NULL, N'테러 관련', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'폭탄', NULL, N'위험물 관련', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 9: 스팸/홍보 문구
    (N'클릭하세요', NULL, N'스팸 문구', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'지금확인', NULL, N'스팸 문구', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'지금접속', NULL, N'스팸 문구', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'무료다운로드', NULL, N'스팸 문구', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'지금가입', NULL, N'스팸 문구', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'지금신청', NULL, N'스팸 문구', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'한정오늘', NULL, N'스팸 문구', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'오늘마감', NULL, N'스팸 문구', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 10: 불법거래/사기 관련
    (N'불법거래', NULL, N'불법 거래', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'사기사이트', NULL, N'사기 사이트', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'가짜사이트', NULL, N'가짜 사이트', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'피싱사이트', NULL, N'피싱 사이트', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'사기업체', NULL, N'사기 업체', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법판매', NULL, N'불법 판매', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법구매', NULL, N'불법 구매', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'대리구매', NULL, N'불법 대리구매', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 11: 개인정보 유출/판매
    (N'개인정보판매', NULL, N'개인정보 판매', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'정보판매', NULL, N'정보 판매', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'명단판매', NULL, N'명단 판매', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'연락처판매', NULL, N'연락처 판매', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'이메일판매', NULL, N'이메일 판매', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'전화번호판매', NULL, N'전화번호 판매', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 12: 불법촬영/몰카 관련
    (N'몰카', NULL, N'불법 촬영', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법촬영', NULL, N'불법 촬영', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'도촬', NULL, N'불법 촬영', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'무단촬영', NULL, N'무단 촬영', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법영상', NULL, N'불법 영상', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 13: 성매매/불법 성행위
    (N'성매매', NULL, N'불법 성매매', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'매춘', NULL, N'불법 성매매', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'성인서비스', NULL, N'불법 성인서비스', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'출장마사지', NULL, N'불법 성인서비스', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'성인업소', NULL, N'불법 성인업소', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 14: 불법대출/사채
    (N'사채', NULL, N'불법 사채', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법대출', NULL, N'불법 대출', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'고리대금', NULL, N'고리대금', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'무담보대출', NULL, N'불법 대출', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'신용불량자대출', NULL, N'불법 대출', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'급전', NULL, N'불법 대출', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 15: 불법의료/성형
    (N'불법의료', NULL, N'불법 의료', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'무면허의료', NULL, N'무면허 의료', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법성형', NULL, N'불법 성형', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'무면허성형', NULL, N'무면허 성형', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법시술', NULL, N'불법 시술', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 16: 불법유통/위조품
    (N'위조품', NULL, N'위조품 판매', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'짝퉁', NULL, N'위조품 판매', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법복제', NULL, N'불법 복제', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법유통', NULL, N'불법 유통', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'가짜상품', NULL, N'가짜 상품', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'모조품', NULL, N'모조품 판매', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 17: 불법취업/알바
    (N'불법알바', NULL, N'불법 알바', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법취업', NULL, N'불법 취업', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법구인', NULL, N'불법 구인', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'사기알바', NULL, N'사기 알바', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'가짜채용', NULL, N'가짜 채용', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 18: 불법투자/다단계
    (N'다단계', NULL, N'다단계 판매', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'피라미드', NULL, N'피라미드 사기', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법투자', NULL, N'불법 투자', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'사기투자', NULL, N'사기 투자', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'가짜투자', NULL, N'가짜 투자', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법모집', NULL, N'불법 모집', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 19: 불법게임/도박 확장
    (N'불법게임', NULL, N'불법 게임', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'도박앱', NULL, N'도박 앱', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'온라인카지노', NULL, N'온라인 카지노', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법카지노', NULL, N'불법 카지노', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법토토', NULL, N'불법 토토', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 20: 불법광고/홍보 확장
    (N'불법광고', NULL, N'불법 광고', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'스팸메일', NULL, N'스팸 메일', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'스팸문자', NULL, N'스팸 문자', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법홍보', NULL, N'불법 홍보', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'무단광고', NULL, N'무단 광고', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 21: 불법수집/스크래핑
    (N'불법수집', NULL, N'불법 정보수집', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'무단수집', NULL, N'무단 정보수집', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법스크래핑', NULL, N'불법 스크래핑', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'데이터수집', NULL, N'불법 데이터수집', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 22: 불법계정/아이디
    (N'불법계정', NULL, N'불법 계정', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'계정거래', NULL, N'계정 거래', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'아이디판매', NULL, N'아이디 판매', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'계정판매', NULL, N'계정 판매', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법아이디', NULL, N'불법 아이디', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 23: 불법서비스/대행
    (N'불법대행', NULL, N'불법 대행', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법서비스', NULL, N'불법 서비스', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'가짜서비스', NULL, N'가짜 서비스', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'사기서비스', NULL, N'사기 서비스', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 24: 불법상품/제품
    (N'불법상품', NULL, N'불법 상품', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법제품', NULL, N'불법 제품', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'가짜제품', NULL, N'가짜 제품', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법수입', NULL, N'불법 수입', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'밀수', NULL, N'밀수품', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    
    -- 카테고리 25: 불법사업/영업
    (N'불법사업', NULL, N'불법 사업', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법영업', NULL, N'불법 영업', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'무허가영업', NULL, N'무허가 영업', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE()),
    (N'불법업체', NULL, N'불법 업체', 1, @AdminUserId, GETUTCDATE(), GETUTCDATE());

PRINT '전역 금칙어 ' + CAST(@@ROWCOUNT AS VARCHAR) + '개가 삽입되었습니다.';
GO

-- 삽입된 금칙어 확인
SELECT 
    [BannedWordId],
    [Word],
    CASE 
        WHEN [AgentId] IS NULL THEN N'전역'
        ELSE CAST([AgentId] AS VARCHAR) + N'번 Agent'
    END AS [적용범위],
    [Description],
    CASE 
        WHEN [IsActive] = 1 THEN N'활성'
        ELSE N'비활성'
    END AS [상태],
    [CreatedAt]
FROM [dbo].[BannedWords]
ORDER BY [AgentId], [CreatedAt];
GO

PRINT '';
PRINT '금칙어 기본 데이터 삽입이 완료되었습니다.';
PRINT '';
PRINT '주의사항:';
PRINT '1. 실제 욕설이나 부적절한 단어는 UI에서 직접 추가하거나 SQL을 수정하여 추가하세요.';
PRINT '2. 위 목록은 일반적인 예시이며, 실제 사용 환경에 맞게 수정이 필요합니다.';
PRINT '3. 금칙어는 부분 일치로 검사되므로, 너무 짧은 단어는 의도치 않은 차단을 유발할 수 있습니다.';
PRINT '4. 예: "마약"을 금칙어로 등록하면 "마약중독"도 차단됩니다.';
PRINT '5. 필요시 UI의 금칙어 관리 페이지에서 추가/수정/삭제할 수 있습니다.';
GO
