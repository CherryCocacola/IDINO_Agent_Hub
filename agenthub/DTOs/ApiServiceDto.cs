namespace AIAgentManagement.DTOs;

public class ApiServiceDto
{
    public int ServiceId { get; set; }
    public string ServiceCode { get; set; } = string.Empty;
    public string ServiceName { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? IconClass { get; set; }
    public string? ColorCode { get; set; }
    public string? DefaultModel { get; set; }
    public decimal CostPerRequest { get; set; }
    public bool IsActive { get; set; }
    public string ServiceType { get; set; } = "Chat";

    // 트랙 #97-post4 (2026-05-18): 외부/내부 LLM 분류 + 실제 사용 가능 여부
    //
    // ServiceCategory: 프론트엔드 탭 분기용
    //   - "external": 외부 인터넷 LLM (OpenAI/Claude/Gemini/Perplexity/Mistral/Azure/Copilot/이미지 생성 등)
    //   - "internal": 내부 LAN-only LLM (Nexus)
    //
    // HasActiveKey: 호출 가능 여부 — ApiKeyPool 카운트 + 환경변수 fallback + Nexus.BaseUrl 검사
    //   - true: 키 등록되어 호출 가능
    //   - false: 키 미설정/만료/INVALID → 멀티채팅 dropdown 에서 숨김 처리
    //
    // 사용자 결정 (2026-05-18): 키 없거나 expired 된 model 은 우선 숨김.
    //   향후 키 추가 시 ApiKeyPool 자동 갱신 → HasActiveKey=true 전환 → UI 자동 노출.
    public string ServiceCategory { get; set; } = "external";
    public bool HasActiveKey { get; set; } = false;
}
