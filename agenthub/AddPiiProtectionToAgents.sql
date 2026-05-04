-- Agents 테이블에 개인정보 보호 관련 컬럼 추가
-- 실행 날짜: 2026-01-26

USE [AIAgentManagement]
GO

-- PiiProtectionEnabled 컬럼 추가
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[Agents]') AND name = 'PiiProtectionEnabled')
BEGIN
    ALTER TABLE [dbo].[Agents]
    ADD [PiiProtectionEnabled] BIT NOT NULL DEFAULT 1;
    PRINT 'PiiProtectionEnabled 컬럼이 Agents 테이블에 추가되었습니다.';
END
ELSE
BEGIN
    PRINT 'PiiProtectionEnabled 컬럼이 이미 Agents 테이블에 존재합니다.';
END
GO

-- PiiProtectionMode 컬럼 추가
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[Agents]') AND name = 'PiiProtectionMode')
BEGIN
    ALTER TABLE [dbo].[Agents]
    ADD [PiiProtectionMode] NVARCHAR(20) NULL;
    PRINT 'PiiProtectionMode 컬럼이 Agents 테이블에 추가되었습니다.';
END
ELSE
BEGIN
    PRINT 'PiiProtectionMode 컬럼이 이미 Agents 테이블에 존재합니다.';
END
GO

-- 전역 설정 기본값 삽입
IF NOT EXISTS (SELECT * FROM [dbo].[SystemSettings] WHERE [SettingKey] = 'PiiProtection.Enabled')
BEGIN
    INSERT INTO [dbo].[SystemSettings] ([SettingKey], [SettingValue], [DataType], [Category], [Description], [IsEncrypted], [CreatedAt], [UpdatedAt])
    VALUES (N'PiiProtection.Enabled', N'true', N'Boolean', N'Privacy', N'개인정보 보호 활성화 여부 (전역 기본값)', 0, GETUTCDATE(), GETUTCDATE());
    PRINT '전역 설정 PiiProtection.Enabled가 추가되었습니다.';
END
ELSE
BEGIN
    PRINT '전역 설정 PiiProtection.Enabled가 이미 존재합니다.';
END
GO

IF NOT EXISTS (SELECT * FROM [dbo].[SystemSettings] WHERE [SettingKey] = 'PiiProtection.Mode')
BEGIN
    INSERT INTO [dbo].[SystemSettings] ([SettingKey], [SettingValue], [DataType], [Category], [Description], [IsEncrypted], [CreatedAt], [UpdatedAt])
    VALUES (N'PiiProtection.Mode', N'Block', N'String', N'Privacy', N'개인정보 보호 모드: Block(차단) 또는 Mask(마스킹)', 0, GETUTCDATE(), GETUTCDATE());
    PRINT '전역 설정 PiiProtection.Mode가 추가되었습니다.';
END
ELSE
BEGIN
    PRINT '전역 설정 PiiProtection.Mode가 이미 존재합니다.';
END
GO

IF NOT EXISTS (SELECT * FROM [dbo].[SystemSettings] WHERE [SettingKey] = 'PiiProtection.DetectionTypes')
BEGIN
    INSERT INTO [dbo].[SystemSettings] ([SettingKey], [SettingValue], [DataType], [Category], [Description], [IsEncrypted], [CreatedAt], [UpdatedAt])
    VALUES (N'PiiProtection.DetectionTypes', N'["PhoneNumber","ResidentNumber","CreditCard","Email","AccountNumber","DriverLicense","PassportNumber","AlienRegistrationNumber"]', N'JSON', N'Privacy', N'감지할 개인정보 유형 목록 (JSON 배열)', 0, GETUTCDATE(), GETUTCDATE());
    PRINT '전역 설정 PiiProtection.DetectionTypes가 추가되었습니다.';
END
ELSE
BEGIN
    -- 기존 값이 있으면 새로운 유형 추가 (기존 값 유지)
    UPDATE [dbo].[SystemSettings]
    SET [SettingValue] = N'["PhoneNumber","ResidentNumber","CreditCard","Email","AccountNumber","DriverLicense","PassportNumber","AlienRegistrationNumber"]',
        [UpdatedAt] = GETUTCDATE()
    WHERE [SettingKey] = 'PiiProtection.DetectionTypes';
    PRINT '전역 설정 PiiProtection.DetectionTypes가 업데이트되었습니다.';
END
GO

PRINT '';
PRINT '스크립트 실행이 완료되었습니다.';
PRINT '모든 Agent는 기본적으로 개인정보 보호가 활성화되며, 전역 설정(차단 모드)을 사용합니다.';
GO
