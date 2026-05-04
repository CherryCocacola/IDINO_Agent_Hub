namespace AIAgentManagement.DTOs;

/// <summary>
/// 사용 내역 통계 집계 결과 (KPI 카드용)
/// </summary>
public class UsageHistorySummaryDto
{
    public int TotalCalls { get; set; }
    public long TotalTokens { get; set; }
    public double TotalCost { get; set; }
    /// <summary>응답 시간 평균 (초 단위)</summary>
    public double AvgResponseTime { get; set; }
}
