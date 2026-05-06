using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

/// <summary>
/// Tenant — 통합 멀티테넌시 단일 권위(ADR-8) 엔티티.
/// AgentHub 의 AIAgentManagement schema 에 정의되며 4개 서브프로젝트
/// (agenthub / docutil / career / nexus) 의 모든 Tenant 식별의 단일 진입점이 된다.
/// 본 엔티티는 Phase 4.3 에 도입되었고, 향후 Agent / ApiKey / Department 의
/// TenantId FK 가 본 PK 를 참조하게 된다 (Phase 4.5 또는 7+ 별도 트랙에서 결정).
/// </summary>
/// <remarks>
/// 운영자 콘솔(AgentHub UI) 에서 Tenant 를 생성하고, 외부 노출용 식별자는 TenantCode 를 사용한다.
/// 한국어 표시명은 TenantName 에 보관 — UI 다국어화 시 i18n 리소스 참조 형태로 전환 가능.
/// </remarks>
[Table("Tenants")]
public class Tenant
{
    /// <summary>내부 PK (IDENTITY).</summary>
    [Key]
    public int TenantId { get; set; }

    /// <summary>외부 노출용 고유 식별자. 예: "idino-default", "univ-anam".</summary>
    [Required]
    [MaxLength(50)]
    public string TenantCode { get; set; } = string.Empty;

    /// <summary>운영자 콘솔에 표시할 한국어 명칭.</summary>
    [Required]
    [MaxLength(200)]
    public string TenantName { get; set; } = string.Empty;

    /// <summary>운영 메모용 설명 (선택).</summary>
    [MaxLength(1000)]
    public string? Description { get; set; }

    /// <summary>활성 여부. false 인 Tenant 는 신규 호출에서 거부 대상.</summary>
    [Required]
    public bool IsActive { get; set; } = true;

    /// <summary>레코드 생성 시각 (UTC).</summary>
    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    /// <summary>마지막 수정 시각 (UTC). 신규 생성 시 NULL.</summary>
    public DateTime? UpdatedAt { get; set; }

    /// <summary>생성한 운영자 UserId (선택, FK Users.UserId). 시스템 시드 시 NULL.</summary>
    public int? CreatedBy { get; set; }

    // ── Navigation properties ───────────────────────────────────────────────
    /// <summary>본 Tenant 가 보유한 Department 목록 (1:N).</summary>
    public virtual ICollection<Department> Departments { get; set; } = new List<Department>();

    /// <summary>본 Tenant 를 생성한 운영자 (선택).</summary>
    [ForeignKey("CreatedBy")]
    public virtual User? Creator { get; set; }
}
