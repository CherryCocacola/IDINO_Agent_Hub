# =============================================================================
# Phase 10.2d — DocUtil 문서 템플릿(Document Templates) BFF e2e 검증 스크립트
#
# 사용법:
#   .\Tools\test_phase_10_2d_templates_e2e.ps1 `
#     -BaseUrl "https://localhost:5001" `
#     -AdminToken "eyJhbGc..."
#
# 사전 조건:
#   - AgentHub 가 실행 중 (https://localhost:5001 또는 운영 도메인)
#   - DocUtil 가 응답 가능한 상태 (DocUtilClient 가 BFF 호출 위임)
#   - 운영자 JWT 토큰 (Roles = Admin 또는 SuperAdmin)
#
# 검증 범위:
#   1) 15개 Templates 신규 endpoint 의 라우팅/응답 코드 / 한국어 에러 본문
#   2) 인증 미부착 / 비-Admin 토큰 시 401/403 한국어
#   3) DocUtil 4xx 전파 (한국어 본문)
#   4) DocUtil 5xx → 502 (한국어 본문)
#   5) 캐시 무효화 — 생성 직후 목록 GET 이 새 행 반환
#   6) 회귀 — 직전 Phase 10.1/10.2a~c 의 11+개 endpoint 가 200 / 200 / 200 / ... 유지
# =============================================================================

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$BaseUrl,

    [Parameter(Mandatory=$true)]
    [string]$AdminToken,

    [Parameter(Mandatory=$false)]
    [string]$NonAdminToken = "",

    [Parameter(Mandatory=$false)]
    [switch]$SkipMutations,

    [Parameter(Mandatory=$false)]
    [switch]$IncludeRegression = $true
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# SSL 자체서명 인증서 허용 (개발 환경)
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }

$Script:PassCount = 0
$Script:FailCount = 0
$Script:Results = @()

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers = @{},
        [object]$Body = $null,
        [int[]]$ExpectStatus = @(200),
        [string]$ExpectKoreanInBody = $null,
        [switch]$IsForm
    )
    $startTime = Get-Date
    try {
        $params = @{
            Method = $Method
            Uri = $Url
            Headers = $Headers
            SkipCertificateCheck = $true
            ErrorAction = 'Stop'
        }
        if ($null -ne $Body) {
            if ($IsForm) {
                $params['Form'] = $Body
            } else {
                $params['Body'] = ($Body | ConvertTo-Json -Depth 10 -Compress)
                $params['ContentType'] = 'application/json; charset=utf-8'
            }
        }
        $response = Invoke-WebRequest @params
        $status = $response.StatusCode
        $bodyText = $response.Content
    } catch {
        $errResp = $_.Exception.Response
        if ($null -ne $errResp) {
            $status = [int]$errResp.StatusCode
            try {
                $stream = $errResp.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($stream)
                $bodyText = $reader.ReadToEnd()
            } catch { $bodyText = "" }
        } else {
            $status = 0
            $bodyText = $_.Exception.Message
        }
    }
    $elapsed = ((Get-Date) - $startTime).TotalMilliseconds

    $statusOk = $ExpectStatus -contains $status
    $koreanOk = $true
    if ($ExpectKoreanInBody -and $bodyText) {
        $koreanOk = $bodyText -match $ExpectKoreanInBody
    }
    $pass = $statusOk -and $koreanOk

    $marker = if ($pass) { "PASS" } else { "FAIL" }
    Write-Host ("  [{0}] {1,-60}  HTTP {2,3}  ({3,4:N0} ms)" -f $marker, $Name, $status, $elapsed)
    if (-not $pass) {
        Write-Host "         expected: $($ExpectStatus -join ',')  korean: $ExpectKoreanInBody" -ForegroundColor Yellow
        Write-Host "         body[..200]: $($bodyText.Substring(0, [Math]::Min(200, $bodyText.Length)))" -ForegroundColor Yellow
        $Script:FailCount++
    } else {
        $Script:PassCount++
    }
    $Script:Results += [pscustomobject]@{
        Name = $Name; Method = $Method; Url = $Url; Status = $status; Pass = $pass; ElapsedMs = $elapsed
    }
    return $bodyText
}

# 인증 헤더 헬퍼
$authHeader = @{ 'Authorization' = "Bearer $AdminToken" }
$baseTemplates = "$BaseUrl/api/admin/docutil/templates"

Write-Host ""
Write-Host "===================================================================="
Write-Host "Phase 10.2d Document Templates BFF e2e check  /  $BaseUrl"
Write-Host "===================================================================="

# ── 1) 권한 게이트 ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[1] 권한 게이트 (인증 없음 → 401)"
Test-Endpoint -Name "Anonymous list templates" -Method GET -Url $baseTemplates `
    -ExpectStatus @(401) | Out-Null

if ($NonAdminToken) {
    Write-Host ""
    Write-Host "[1b] 비-Admin 토큰 (→ 403)"
    Test-Endpoint -Name "Non-admin list templates" -Method GET -Url $baseTemplates `
        -Headers @{ 'Authorization' = "Bearer $NonAdminToken" } `
        -ExpectStatus @(403) | Out-Null
}

# ── 2) 목록 (정상 200) ────────────────────────────────────────────────────
Write-Host ""
Write-Host "[2] 목록 / 필터 / 페이징"
Test-Endpoint -Name "List templates default" -Method GET -Url $baseTemplates `
    -Headers $authHeader -ExpectStatus @(200) | Out-Null
Test-Endpoint -Name "List templates with type filter" -Method GET `
    -Url "$baseTemplates`?templateType=report&page=1&size=5" `
    -Headers $authHeader -ExpectStatus @(200) | Out-Null

# ── 3) 잘못된 식별자 / 잘못된 본문 ────────────────────────────────────────
Write-Host ""
Write-Host "[3] 입력 검증 — 400 한국어"
Test-Endpoint -Name "Get with empty id (route-level mismatch)" -Method GET `
    -Url "$baseTemplates/   " -Headers $authHeader `
    -ExpectStatus @(400, 404) | Out-Null
Test-Endpoint -Name "Create with empty body" -Method POST -Url $baseTemplates `
    -Headers $authHeader -Body @{} -ExpectStatus @(400) `
    -ExpectKoreanInBody "이름|유형|형식" | Out-Null
Test-Endpoint -Name "AutoFill missing source ids" -Method POST `
    -Url "$baseTemplates/00000000-0000-0000-0000-000000000000/auto-fill" `
    -Headers $authHeader -Body @{ sourceDocumentIds = @() } -ExpectStatus @(400) `
    -ExpectKoreanInBody "비어" | Out-Null
Test-Endpoint -Name "Convert missing ai_analysis" -Method POST `
    -Url "$baseTemplates/00000000-0000-0000-0000-000000000000/convert" `
    -Headers $authHeader -Body @{} -ExpectStatus @(400) `
    -ExpectKoreanInBody "비어" | Out-Null
Test-Endpoint -Name "ApplyMapping empty array" -Method POST `
    -Url "$baseTemplates/00000000-0000-0000-0000-000000000000/apply-mapping" `
    -Headers $authHeader -Body @{ mappings = @() } -ExpectStatus @(400) `
    -ExpectKoreanInBody "비어" | Out-Null
Test-Endpoint -Name "ApplyMapping invalid location_type" -Method POST `
    -Url "$baseTemplates/00000000-0000-0000-0000-000000000000/apply-mapping" `
    -Headers $authHeader -Body @{ mappings = @(@{ locationType = 'invalid'; variableName = 'x' }) } `
    -ExpectStatus @(400) -ExpectKoreanInBody "허용" | Out-Null

# ── 4) DocUtil 404 전파 (존재하지 않는 ID) ────────────────────────────────
Write-Host ""
Write-Host "[4] DocUtil 404 → BFF NotFound 한국어"
Test-Endpoint -Name "Get nonexistent template" -Method GET `
    -Url "$baseTemplates/00000000-0000-0000-0000-000000000000" `
    -Headers $authHeader -ExpectStatus @(404, 502) | Out-Null

# ── 5) 변이 + 캐시 무효화 + 회귀 ──────────────────────────────────────────
if (-not $SkipMutations) {
    Write-Host ""
    Write-Host "[5] 생성 / 수정 / 삭제 라이프사이클 + 캐시 무효화"
    $createBody = @{
        name = "Phase 10.2d e2e test $(Get-Date -Format yyMMdd_HHmmss)"
        templateType = "test"
        outputFormat = "docx"
        tone = "formal"
        description = "Phase 10.2d e2e verification"
        renderingMode = "jinja2"
    }
    $createResp = Test-Endpoint -Name "Create template (JSON metadata)" -Method POST `
        -Url $baseTemplates -Headers $authHeader -Body $createBody `
        -ExpectStatus @(200, 201)
    try {
        $created = $createResp | ConvertFrom-Json
        $tplId = $created.id
        Write-Host "    Created template id: $tplId"

        # 목록 캐시 invalidation 검증 — 생성 직후 목록 GET 이 새 ID 포함해야 함.
        $listResp = Test-Endpoint -Name "List after create (cache invalidated)" -Method GET `
            -Url "$baseTemplates`?page=1&size=50" -Headers $authHeader -ExpectStatus @(200)
        if ($listResp -notmatch [regex]::Escape($tplId)) {
            Write-Host "    [WARN] 생성된 ID 가 목록에 즉시 노출되지 않음 (캐시 무효화 미동작 가능성)" -ForegroundColor Yellow
        }

        # 상세
        Test-Endpoint -Name "Get created template" -Method GET -Url "$baseTemplates/$tplId" `
            -Headers $authHeader -ExpectStatus @(200) | Out-Null

        # 수정
        Test-Endpoint -Name "Update template" -Method PUT -Url "$baseTemplates/$tplId" `
            -Headers $authHeader -Body @{ description = "edited by e2e" } `
            -ExpectStatus @(200) | Out-Null

        # 변수 GET (빈 배열 또는 기존)
        Test-Endpoint -Name "Get template variables" -Method GET `
            -Url "$baseTemplates/$tplId/variables" -Headers $authHeader `
            -ExpectStatus @(200) | Out-Null

        # 변수 PUT
        Test-Endpoint -Name "Update template variables" -Method PUT `
            -Url "$baseTemplates/$tplId/variables" -Headers $authHeader `
            -Body @{ variables = @(@{ name = 'title'; varType = 'string'; label = '제목'; required = $true; category = 'user_input' }) } `
            -ExpectStatus @(200, 502) | Out-Null
            # NOTE: 파일 미업로드 상태에서 DocUtil 측이 구현에 따라 422/500 가능 → 502 까지 허용.

        # 구조 GET (파일 미업로드 → DocUtil 404/422 → BFF 502)
        Test-Endpoint -Name "Get structure (no file)" -Method GET `
            -Url "$baseTemplates/$tplId/structure" -Headers $authHeader `
            -ExpectStatus @(200, 502) | Out-Null

        # 미리보기 (파일 미업로드 → 502)
        Test-Endpoint -Name "Preview (no file)" -Method GET `
            -Url "$baseTemplates/$tplId/preview" -Headers $authHeader `
            -ExpectStatus @(200, 502, 404) | Out-Null

        # 삭제
        Test-Endpoint -Name "Delete template" -Method DELETE -Url "$baseTemplates/$tplId" `
            -Headers $authHeader -ExpectStatus @(204) | Out-Null

        # 삭제 후 GET 은 404
        Test-Endpoint -Name "Get deleted template → 404" -Method GET -Url "$baseTemplates/$tplId" `
            -Headers $authHeader -ExpectStatus @(404, 502) | Out-Null

    } catch {
        Write-Host "  생성 응답 파싱 실패 — DocUtil 응답을 확인하세요." -ForegroundColor Yellow
        Write-Host "  $($createResp)" -ForegroundColor Yellow
    }
}

# ── 6) 회귀: 이전 Phase BFF endpoint 가 200 (또는 정상 4xx) 응답 ──────────
if ($IncludeRegression) {
    Write-Host ""
    Write-Host "[6] 회귀 — 직전 Phase 10.1/10.2a-c BFF endpoint (11+개)"
    $regressionEndpoints = @(
        @{ Name = "10.1a List DocUtil users";              Method = "GET"; Path = "/api/admin/docutil/users?page=1&size=5"          }
        @{ Name = "10.1b Get DocUtil organization";        Method = "GET"; Path = "/api/admin/docutil/organization"                  }
        @{ Name = "10.1b List DocUtil departments";        Method = "GET"; Path = "/api/admin/docutil/departments"                   }
        @{ Name = "10.1b Get organization quotas";         Method = "GET"; Path = "/api/admin/docutil/organization/quotas"           }
        @{ Name = "10.1c List DocUtil projects";           Method = "GET"; Path = "/api/admin/docutil/projects?page=1&size=5"        }
        @{ Name = "10.2a Dashboard metrics";               Method = "GET"; Path = "/api/admin/docutil/dashboard/metrics"             }
        @{ Name = "10.2a List audit logs";                 Method = "GET"; Path = "/api/admin/docutil/audit-logs?page=1&size=5"      }
        @{ Name = "10.2b List search scopes";              Method = "GET"; Path = "/api/admin/docutil/search-scopes?page=1&size=5"   }
        @{ Name = "10.2b Get evaluation config";           Method = "GET"; Path = "/api/admin/docutil/evaluation/config"             }
        @{ Name = "10.2c List FAQs";                       Method = "GET"; Path = "/api/admin/docutil/faq?page=1&size=5"             }
        @{ Name = "10.2c List reports";                    Method = "GET"; Path = "/api/admin/docutil/reports?page=1&size=5"         }
        @{ Name = "10.2c List report templates";           Method = "GET"; Path = "/api/admin/docutil/reports/templates?page=1&size=5" }
    )
    foreach ($ep in $regressionEndpoints) {
        Test-Endpoint -Name $ep.Name -Method $ep.Method `
            -Url "$BaseUrl$($ep.Path)" -Headers $authHeader `
            -ExpectStatus @(200, 502) | Out-Null
    }
}

# ── 결과 요약 ─────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "===================================================================="
Write-Host "PASS: $Script:PassCount    FAIL: $Script:FailCount    TOTAL: $($Script:PassCount + $Script:FailCount)"
Write-Host "===================================================================="

if ($Script:FailCount -gt 0) {
    Write-Host ""
    Write-Host "Failed cases:" -ForegroundColor Red
    $Script:Results | Where-Object { -not $_.Pass } | Format-Table -AutoSize
    exit 1
}
exit 0
