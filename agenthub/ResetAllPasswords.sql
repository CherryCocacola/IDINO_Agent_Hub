-- 모든 사용자의 비밀번호를 새로운 값으로 업데이트하는 SQL
-- 주의: BCrypt 해시는 SQL에서 직접 생성할 수 없으므로 C# 코드로 생성해야 합니다.

-- ========================================
-- 방법 1: C# 코드로 해시 생성 후 사용
-- ========================================
-- 다음 C# 코드를 실행하여 해시 값을 생성하세요:
-- 
-- string passwordHash = BCrypt.Net.BCrypt.HashPassword("Admin123!");
-- Console.WriteLine(passwordHash);
--
-- 생성된 해시 값을 아래 UPDATE 문의 'YOUR_HASH_VALUE' 부분에 넣어주세요.

-- 모든 사용자 비밀번호 업데이트
UPDATE Users
SET PasswordHash = 'YOUR_HASH_VALUE',  -- 여기에 C#에서 생성한 해시 값 입력
    UpdatedAt = GETUTCDATE()
WHERE IsDeleted = 0;

-- 특정 사용자만 업데이트 (더 안전)
UPDATE Users
SET PasswordHash = 'YOUR_HASH_VALUE',  -- 여기에 C#에서 생성한 해시 값 입력
    UpdatedAt = GETUTCDATE()
WHERE Email = 'admin@example.com'
  AND IsDeleted = 0;

-- ========================================
-- 방법 2: 현재 사용자 목록 및 해시 상태 확인
-- ========================================
SELECT 
    UserId,
    Email,
    FullName,
    Status,
    IsDeleted,
    LEN(PasswordHash) AS PasswordHashLength,
    LEFT(PasswordHash, 20) AS HashPreview, -- BCrypt 해시는 $2a$11$ 같은 형식으로 시작
    CASE 
        WHEN PasswordHash LIKE '$2a$%' THEN 'BCrypt ($2a$)'
        WHEN PasswordHash LIKE '$2b$%' THEN 'BCrypt ($2b$)'
        WHEN PasswordHash LIKE '$2y$%' THEN 'BCrypt ($2y$)'
        ELSE 'Unknown Format'
    END AS HashType,
    CreatedAt,
    UpdatedAt
FROM Users
WHERE IsDeleted = 0
ORDER BY UserId;

-- ========================================
-- 방법 3: 비밀번호 해시가 비어있거나 잘못된 사용자 찾기
-- ========================================
SELECT 
    UserId,
    Email,
    FullName,
    Status,
    PasswordHash,
    CASE 
        WHEN PasswordHash IS NULL OR PasswordHash = '' THEN 'Empty'
        WHEN PasswordHash NOT LIKE '$2%' THEN 'Invalid Format'
        ELSE 'Valid'
    END AS HashStatus
FROM Users
WHERE IsDeleted = 0
  AND (PasswordHash IS NULL 
       OR PasswordHash = '' 
       OR PasswordHash NOT LIKE '$2%');

-- ========================================
-- 예시: 실제 해시 값 예시 (실제로는 C#에서 생성)
-- ========================================
-- BCrypt 해시는 다음과 같은 형식입니다:
-- $2a$11$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy
-- $2a$11$rBV2jDe07AnotFyada1e0uE59Y6G9xA6Y5L3.bCRMyBT0Ft3KiX6y
--
-- 주의: 각 해시 값은 고유하며, 같은 비밀번호라도 매번 다른 해시가 생성됩니다.
-- 하지만 BCrypt.Verify()로 검증할 수 있습니다.
