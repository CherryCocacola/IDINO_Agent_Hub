using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

/// <summary>
/// Department — Tenant 내부의 부서/학과 단위(Q1 옵션 B 채택).
/// career 의 tb_department(30 학과) 를 통합 매핑하는 베이스가 되며,
/// Tenants 1 → N Departments 의 단순 계층을 가진다.
/// 학부 ↔ 학과 의 2단계 트리는 ParentDepartmentId self-FK 로 표현한다.
/// </summary>
/// <remarks>
/// Q1 옵션 B 결정 사유:
/// - 옵션 A (Tenants sub-org JSON 컬럼) 는 indexing/조인 비효율 + 검색 가시성 부족
/// - 옵션 C (career 자체 tb_department 유지) 는 R3(스키마 격리) 위반 위험 +
///   AgentHub 운영자 콘솔에서 부서 단위 정책(라우팅/할당량) 부여가 어려움
/// - 옵션 B 는 단일 권위 + RBAC/스코프 확장 용이. 통합 도메인 모델 P2 에 부합.
/// 본 Phase 4.3 에서는 빈 엔티티(스키마 + 시드 1건) 만 도입하고, career.tb_department 데이터
/// 매핑은 Phase 4.5 통합 검증 시점 또는 별도 트랙에서 진행한다.
/// </remarks>
[Table("Departments")]
public class Department
{
    /// <summary>내부 PK (IDENTITY).</summary>
    [Key]
    public int DepartmentId { get; set; }

    /// <summary>외부 노출용 고유 식별자. 예: "computer-science", "AI-ML".</summary>
    [Required]
    [MaxLength(50)]
    public string DepartmentCode { get; set; } = string.Empty;

    /// <summary>운영자 콘솔에 표시할 한국어 명칭.</summary>
    [Required]
    [MaxLength(200)]
    public string DepartmentName { get; set; } = string.Empty;

    /// <summary>소속 Tenant FK (NOT NULL). DELETE 시 RESTRICT — 명시적 정리 후 삭제.</summary>
    [Required]
    public int TenantId { get; set; }

    /// <summary>
    /// 상위 부서 self-FK (학부 ↔ 학과 계층 표현). 최상위 부서면 NULL.
    /// 순환 참조 방지는 application 단에서 검증.
    /// </summary>
    public int? ParentDepartmentId { get; set; }

    /// <summary>운영 메모용 설명 (선택).</summary>
    [MaxLength(1000)]
    public string? Description { get; set; }

    /// <summary>활성 여부. false 인 Department 는 신규 매핑 거부.</summary>
    [Required]
    public bool IsActive { get; set; } = true;

    /// <summary>
    /// 트랙 A1 Phase D (2026-05-26) — DocUtil tb_departments.id (uuid) 와의 매핑.
    /// NULL 허용 (DocUtil 미사용 부서). UNIQUE 제약 — 한 AgentHub Department 는
    /// 한 DocUtil 부서에만 매핑. tb_departments 가 VIEW 화 되면서 alias 의 id 컬럼이
    /// 이 값을 그대로 반환한다 (DocUtil ORM 호환 보장).
    /// </summary>
    public Guid? OriginalDocutilUuid { get; set; }

    /// <summary>레코드 생성 시각 (UTC).</summary>
    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    /// <summary>마지막 수정 시각 (UTC). 신규 생성 시 NULL.</summary>
    public DateTime? UpdatedAt { get; set; }

    // ── Navigation properties ───────────────────────────────────────────────
    /// <summary>소속 Tenant.</summary>
    [ForeignKey("TenantId")]
    public virtual Tenant Tenant { get; set; } = null!;

    /// <summary>상위 Department (선택).</summary>
    [ForeignKey("ParentDepartmentId")]
    public virtual Department? ParentDepartment { get; set; }

    /// <summary>하위 Department 목록 (1:N self-relation).</summary>
    public virtual ICollection<Department> ChildDepartments { get; set; } = new List<Department>();
}
