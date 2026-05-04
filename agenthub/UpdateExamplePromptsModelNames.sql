-- ExamplePrompts 테이블의 모델 이름을 업데이트
-- gemini-3.0-pro-image를 gemini-3-pro-image-preview로 변경하거나
-- 모든 모델에 적용되도록 NULL로 변경

-- 옵션 1: 모델 이름을 업데이트 (특정 모델에만 적용)
-- UPDATE [dbo].[ExamplePrompts]
-- SET [Model] = N'gemini-3-pro-image-preview'
-- WHERE [Model] = N'gemini-3.0-pro-image' AND [ServiceCode] = N'gemini-image';

-- 옵션 2: 모든 모델에 적용되도록 Model을 NULL로 변경 (권장)
-- 이렇게 하면 모델이 변경되어도 예제 프롬프트가 계속 표시됩니다.
UPDATE [dbo].[ExamplePrompts]
SET [Model] = NULL
WHERE ([Model] = N'gemini-3.0-pro-image' OR [Model] = N'gemini-3-pro-image-preview')
  AND [ServiceCode] = N'gemini-image';

PRINT 'ExamplePrompts의 모델 이름이 업데이트되었습니다. (Model = NULL로 변경하여 모든 모델에 적용)';
PRINT '영향받은 레코드 수를 확인하려면 다음 쿼리를 실행하세요:';
PRINT 'SELECT COUNT(*) FROM [dbo].[ExamplePrompts] WHERE [ServiceCode] = N''gemini-image'' AND [Model] IS NULL';
GO
