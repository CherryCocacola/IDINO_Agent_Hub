-- 사용자 확인 및 생성 스크립트
-- 데이터베이스에 admin 사용자가 있는지 확인하고 없으면 생성

-- 1. 현재 사용자 확인
SELECT 
    UserId,
    Email,
    FullName,
    Status,
    IsDeleted,
    IsEmailVerified,
    CreatedAt
FROM Users
WHERE Email = 'admin@example.com';

-- 2. 사용자 역할 확인
SELECT 
    u.UserId,
    u.Email,
    u.FullName,
    r.RoleName,
    r.DisplayName
FROM Users u
INNER JOIN UserRoles ur ON u.UserId = ur.UserId
INNER JOIN Roles r ON ur.RoleId = r.RoleId
WHERE u.Email = 'admin@example.com';

-- 3. 사용자가 없거나 상태가 Active가 아닌 경우 수정
-- (실행 전에 비밀번호 해시를 생성해야 함 - BCrypt로 "Admin123!" 해시 생성 필요)

-- 사용자 상태를 Active로 변경
UPDATE Users
SET Status = 'Active',
    IsDeleted = 0,
    IsEmailVerified = 1
WHERE Email = 'admin@example.com';

-- 4. 모든 사용자 목록 확인
SELECT 
    UserId,
    Email,
    FullName,
    Status,
    IsDeleted,
    CreatedAt
FROM Users
ORDER BY CreatedAt DESC;
