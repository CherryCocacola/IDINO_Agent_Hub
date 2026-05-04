namespace AIAgentManagement.DTOs;

public class ApiKeyDto
{
    public int ApiKeyId { get; set; }
    public int UserId { get; set; }
    public string KeyName { get; set; } = string.Empty;
    public string ServiceCode { get; set; } = string.Empty;
    public string? ServiceName { get; set; }
    public int? AgentId { get; set; }
    public string? Description { get; set; }
    public DateTime? ExpiresAt { get; set; }
    public bool IsActive { get; set; }
    public DateTime? LastUsedAt { get; set; }
    public int UsageCount { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public string? MaskedKey { get; set; } // 마스킹된 키 (예: ak-...xxxx)

    // ── 보안 확장 필드 ──
    /// <summary>허용 IP 목록 (쉼표 구분). null이면 모든 IP 허용.</summary>
    public string? AllowedIps { get; set; }

    /// <summary>스코프 목록 (쉼표 구분). null이면 모든 스코프 허용.</summary>
    public string? Scopes { get; set; }

    /// <summary>분당 최대 요청 수. null이면 무제한.</summary>
    public int? RateLimitPerMinute { get; set; }

    /// <summary>일당 최대 요청 수. null이면 무제한.</summary>
    public int? RateLimitPerDay { get; set; }
}

public class CreateApiKeyRequestDto
{
    public string KeyName { get; set; } = string.Empty;
    public string ServiceCode { get; set; } = string.Empty;
    public string ApiKey { get; set; } = string.Empty; // 평문 키
    public string? Description { get; set; }
    public DateTime? ExpiresAt { get; set; }
    public string? AllowedIps { get; set; }
    public string? Scopes { get; set; }
    public int? RateLimitPerMinute { get; set; }
    public int? RateLimitPerDay { get; set; }
}

public class UpdateApiKeyRequestDto
{
    public string? KeyName { get; set; }
    public string? Description { get; set; }
    public bool? IsActive { get; set; }
    public DateTime? ExpiresAt { get; set; }
    public string? AllowedIps { get; set; }
    public string? Scopes { get; set; }
    public int? RateLimitPerMinute { get; set; }
    public int? RateLimitPerDay { get; set; }
}

public class CreateAgentApiKeyRequestDto
{
    public string? KeyName { get; set; }
    public string? Description { get; set; }
    public DateTime? ExpiresAt { get; set; }
    public string? AllowedIps { get; set; }
    public string? Scopes { get; set; }
    public int? RateLimitPerMinute { get; set; }
    public int? RateLimitPerDay { get; set; }
}

public class CreateAgentApiKeyResponseDto
{
    public int ApiKeyId { get; set; }
    public string ApiKey { get; set; } = string.Empty; // 생성 시에만 반환
    public string KeyName { get; set; } = string.Empty;
    public int AgentId { get; set; }
    public DateTime? ExpiresAt { get; set; }
    public string? Scopes { get; set; }
    public string? AllowedIps { get; set; }
    public int? RateLimitPerMinute { get; set; }
    public int? RateLimitPerDay { get; set; }
    public string Warning { get; set; } = "이 키는 이번에만 표시됩니다. 안전한 곳에 저장하세요.";
}

/// <summary>API 키 인증 검증 결과 (기존 int? 대신 사용)</summary>
public class ApiKeyValidationResult
{
    public int UserId { get; set; }
    public int ApiKeyId { get; set; }
    public int? AgentId { get; set; }
    public string? Scopes { get; set; }
    public string? AllowedIps { get; set; }
    public int? RateLimitPerMinute { get; set; }
    public int? RateLimitPerDay { get; set; }

    /// <summary>스코프 배열 (파싱된 값). 비어있으면 전체 허용.</summary>
    public IReadOnlyList<string> ScopeList =>
        string.IsNullOrWhiteSpace(Scopes)
            ? Array.Empty<string>()
            : Scopes.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);

    /// <summary>허용 IP 배열 (파싱된 값). 비어있으면 전체 허용.</summary>
    public IReadOnlyList<string> AllowedIpList =>
        string.IsNullOrWhiteSpace(AllowedIps)
            ? Array.Empty<string>()
            : AllowedIps.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
}

/// <summary>API 사용량 통계 응답 DTO</summary>
public class AgentApiUsageDto
{
    public int AgentId { get; set; }
    public int ApiKeyId { get; set; }
    public string KeyName { get; set; } = string.Empty;
    public int TotalRequests { get; set; }
    public DateTime? LastUsedAt { get; set; }
    public int? RateLimitPerMinute { get; set; }
    public int? RateLimitPerDay { get; set; }
    public string? Scopes { get; set; }
    public DateTime? ExpiresAt { get; set; }
}

/// <summary>Agent 공개 정보 응답 DTO (API Key 인증 및 퍼블릭 페이지용)</summary>
public class AgentPublicInfoDto
{
    public int AgentId { get; set; }
    public string AgentName { get; set; } = string.Empty;
    public string? AgentCode { get; set; }
    public string? Description { get; set; }
    public string? IconClass { get; set; }
    public string? ColorCode { get; set; }
    public bool IsPublic { get; set; }
    public string? DefaultModel { get; set; }
    public bool EnableRag { get; set; }
    // 공유 / 임베드 설정
    public string? WelcomeMessage { get; set; }
    public string? PlaceholderText { get; set; }
    public string? ChatTheme { get; set; }
    public List<string> Capabilities { get; set; } = new();
}

/// <summary>퍼블릭 채팅 요청 DTO (비로그인 게스트용)</summary>
public class PublicChatRequestDto
{
    public string Message { get; set; } = string.Empty;
    public List<PublicChatMessageDto>? Messages { get; set; }
}

/// <summary>퍼블릭 채팅 메시지 항목</summary>
public class PublicChatMessageDto
{
    public string Role { get; set; } = "user";
    public string Content { get; set; } = string.Empty;
}
