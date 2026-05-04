-- Admin 사용자 비밀번호 재설정 및 상태 확인 스크립트
-- BCrypt 해시는 C# 코드에서 생성해야 하므로, 여기서는 상태만 확인/수정

-- 1. 현재 사용자 상태 확인
SELECT 
    UserId,
    Email,
    FullName,
    Status,
    IsDeleted,
    IsEmailVerified,
    CreatedAt,
    UpdatedAt
FROM Users
WHERE Email = 'admin@example.com';

-- 2. 사용자 상태를 Active로 변경 (비밀번호는 C# 코드에서 재생성 필요)
UPDATE Users
SET Status = 'Active',
    IsDeleted = 0,
    IsEmailVerified = 1,
    UpdatedAt = GETUTCDATE()
WHERE Email = 'admin@example.com';

-- 3. 사용자 역할 확인
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

-- 4. 역할이 없으면 추가 (RoleId는 실제 값으로 변경 필요)
-- INSERT INTO UserRoles (UserId, RoleId, AssignedAt)
-- SELECT u.UserId, r.RoleId, GETUTCDATE()
-- FROM Users u, Roles r
-- WHERE u.Email = 'admin@example.com' 
--   AND r.RoleName = 'Admin'
--   AND NOT EXISTS (
--       SELECT 1 FROM UserRoles ur 
--       WHERE ur.UserId = u.UserId AND ur.RoleId = r.RoleId
--   );
