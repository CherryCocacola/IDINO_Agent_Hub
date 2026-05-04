-- Mistral AI 서비스 추가 스크립트

-- Mistral 서비스가 이미 존재하는지 확인
IF NOT EXISTS (SELECT * FROM ApiServices WHERE ServiceCode = 'mistral')
BEGIN
    INSERT INTO ApiServices (
        ServiceCode, 
        ServiceName, 
        Description, 
        IconClass, 
        ColorCode, 
        ApiEndpoint, 
        DefaultModel, 
        CostPerRequest, 
        ServiceType, 
        IsActive, 
        SortOrder, 
        CreatedAt, 
        UpdatedAt
    )
    VALUES (
        'mistral', 
        'Mistral', 
        'Mistral AI API', 
        'bi-stars', 
        '#FF6B35', 
        'https://api.mistral.ai/v1', 
        'mistral-large-latest', 
        0.02, 
        'Chat', 
        1, 
        6, 
        GETDATE(), 
        GETDATE()
    );
    
    PRINT 'Mistral 서비스가 추가되었습니다.';
END
ELSE
BEGIN
    PRINT 'Mistral 서비스가 이미 존재합니다.';
END
GO
