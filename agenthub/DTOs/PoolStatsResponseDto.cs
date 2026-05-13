namespace AIAgentManagement.DTOs;

/// <summary>
/// 외부 LLM 키 풀 통계 응답 — 트랙 #91.
/// 운영자가 콘솔에서 "외부 LLM 키 풀" 탭을 열 때 호출하는 <c>GET /api/apikeys/pool-stats</c> 응답.
/// </summary>
public class PoolStatsResponseDto
{
    /// <summary>제공사별 통계 목록.</summary>
    public List<ProviderPoolStatDto> Providers { get; set; } = new();

    /// <summary>본 통계가 산출된 시점 (UTC).</summary>
    public DateTime LastRefreshedAt { get; set; } = DateTime.UtcNow;
}

/// <summary>
/// 제공사 1개에 대한 풀 통계.
/// </summary>
public class ProviderPoolStatDto
{
    /// <summary>정규화된 제공사 코드 (소문자, 예: openai/claude/gemini/...).</summary>
    public string ServiceCode { get; set; } = string.Empty;

    /// <summary>풀에 등재된 총 키 개수 (appsettings + DB 합산).</summary>
    public int TotalCount { get; set; }

    /// <summary><c>appsettings.json</c> 로부터 적재된 키 개수 (회귀 차단용 폴백).</summary>
    public int FromAppsettings { get; set; }

    /// <summary>DB 의 `ApiKeys` 테이블(`KeyType="Provider"`)에서 적재된 키 개수.</summary>
    public int FromDb { get; set; }

    /// <summary>현재 냉각 상태(429 이후 일시 제외)인 키 개수.</summary>
    public int CoolingDownCount { get; set; }
}
