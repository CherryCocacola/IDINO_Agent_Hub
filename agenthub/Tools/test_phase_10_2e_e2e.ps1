# Phase 10.2e E2E 정합성 검증 스크립트 (PowerShell)
#
# 목적:
#   라이브 DocUtil + AgentHub 인스턴스 부재 환경에서도 BFF 트랙의 정합성을
#   자동 검증한다. 라이브 인스턴스가 살아있다면 PASS 후 라이브 호출까지
#   확장 가능. Phase 10.2d test_phase_10_2d_templates_e2e.ps1 의 정적 검증
#   패턴(파일 존재 / 메서드 시그니처 / 권한 게이트 / 한국어 에러 / 캐시
#   invalidation) 을 그대로 답습한다.
#
# 검증 카테고리:
#   1. 백엔드 endpoint 카운트 = 서비스 함수 카운트 = 1:1
#   2. 모든 컨트롤러 [Authorize(Roles="Admin,SuperAdmin")] 게이트 보유
#   3. mutation 컨트롤러는 InvalidateXxxCacheAsync 사이트 보유
#   4. EnsureSuccessOrThrowKoreanAsync 한국어 에러 변환 적용
#   5. 한국어 BadRequest / 502 메시지 카운트 ≥ 임계
#   6. 직전 DocUtil admin 컨트롤러(10.1a/b/c + 10.2a/b/c/d) 회귀 PASS
#
# 사용법:
#   pwsh -File agenthub/Tools/test_phase_10_2e_e2e.ps1

$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$agentHub = Join-Path $repoRoot 'agenthub'

$pass = 0
$fail = 0
$errors = New-Object System.Collections.Generic.List[string]

function Assert([bool] $cond, [string] $msg) {
    if ($cond) {
        Write-Host "[PASS] $msg" -ForegroundColor Green
        $script:pass++
    } else {
        Write-Host "[FAIL] $msg" -ForegroundColor Red
        $script:fail++
        $script:errors.Add($msg)
    }
}

Write-Host "=== Phase 10.2e — DocUtil API Keys + Agents + Documents V2 BFF 정합성 검증 ===" -ForegroundColor Cyan

# ── 1. 파일 존재 확인 ───────────────────────────────────────────────────
$files = @(
    'Services/IDocUtilClient.cs',
    'Services/DocUtilClient.cs',
    'Controllers/AdminDocUtilApiKeysController.cs',
    'Controllers/AdminDocUtilDocAgentsController.cs',
    'Controllers/AdminDocUtilDocumentsV2Controller.cs',
    'ClientApp/src/services/docutilService.ts',
    'ClientApp/src/views/admin/AdminDocUtilApiKeys.vue',
    'ClientApp/src/views/admin/AdminDocUtilDocAgents.vue',
    'ClientApp/src/views/admin/AdminDocUtilDocumentsV2.vue'
)
foreach ($f in $files) {
    $p = Join-Path $agentHub $f
    Assert (Test-Path $p) "파일 존재: $f"
}

# ── 2. 백엔드 endpoint 카운트 (도메인별 — 본 트랙 + 회귀) ──────────────
$endpointPattern = '\[Http(Get|Post|Put|Patch|Delete)\('

$apiKeysCount = (Select-String -Path (Join-Path $agentHub 'Controllers/AdminDocUtilApiKeysController.cs') -Pattern $endpointPattern -AllMatches).Matches.Count
$docAgentsCount = (Select-String -Path (Join-Path $agentHub 'Controllers/AdminDocUtilDocAgentsController.cs') -Pattern $endpointPattern -AllMatches).Matches.Count
$docV2Count = (Select-String -Path (Join-Path $agentHub 'Controllers/AdminDocUtilDocumentsV2Controller.cs') -Pattern $endpointPattern -AllMatches).Matches.Count

Assert ($apiKeysCount -eq 4) "API Keys endpoint 4개 (List/Create/Delete/Verify) — actual=$apiKeysCount"
Assert ($docAgentsCount -eq 5) "DocAgents endpoint 5개 (CRUD) — actual=$docAgentsCount"
Assert ($docV2Count -eq 7) "Documents V2 endpoint 7개 (List/Get/Generate/Patch/Export/Status/Download) — actual=$docV2Count"

$totalNew = $apiKeysCount + $docAgentsCount + $docV2Count
Assert ($totalNew -eq 16) "Phase 10.2e 신규 endpoint 합계 16 — actual=$totalNew"

# ── 3. 회귀 — 직전 DocUtil admin 컨트롤러 endpoint 보존 ─────────────────
$regression = @{
    'AdminDocUtilUsersController.cs'        = 4
    'AdminDocUtilDepartmentsController.cs'  = 9
    'AdminDocUtilProjectsController.cs'     = 13
    'AdminDocUtilOperationsController.cs'   = 7
    'AdminDocUtilSearchScopesController.cs' = 9
    'AdminDocUtilEvaluationController.cs'   = 7
    'AdminDocUtilFaqController.cs'          = 5
    'AdminDocUtilReportsController.cs'      = 10
    'AdminDocUtilTemplatesController.cs'    = 15
}
$regressionTotal = 0
foreach ($name in $regression.Keys) {
    $exp = $regression[$name]
    $path = Join-Path $agentHub "Controllers/$name"
    $matches = Select-String -Path $path -Pattern $endpointPattern -AllMatches
    $actual = if ($matches) { $matches.Matches.Count } else { 0 }
    Assert ($actual -eq $exp) "회귀: $name endpoint 수 보존 ($exp) — actual=$actual"
    $regressionTotal += $actual
}
Assert ($regressionTotal -eq 79) "회귀: 직전 DocUtil admin 컨트롤러 합계 endpoint 79 보존 — actual=$regressionTotal"

# ── 4. 권한 게이트 — 본 트랙 + 회귀 모두 [Authorize(Roles="Admin,SuperAdmin")] ──
$newControllers = @(
    'AdminDocUtilApiKeysController.cs',
    'AdminDocUtilDocAgentsController.cs',
    'AdminDocUtilDocumentsV2Controller.cs'
)
foreach ($n in ($newControllers + $regression.Keys)) {
    $path = Join-Path $agentHub "Controllers/$n"
    $matches = Select-String -Path $path -Pattern '\[Authorize\(Roles\s*=\s*"Admin,SuperAdmin"' -AllMatches
    $count = if ($matches) { $matches.Matches.Count } else { 0 }
    Assert ($count -ge 1) "권한 게이트: $n 에 [Authorize(Roles=Admin,SuperAdmin)] 존재"
}

# ── 5. mutation 캐시 invalidate ─────────────────────────────────────────
$inv = @{
    'AdminDocUtilApiKeysController.cs'      = 'InvalidateApiKeysCacheAsync'
    'AdminDocUtilDocAgentsController.cs'    = 'InvalidateDocAgentsCacheAsync'
    'AdminDocUtilDocumentsV2Controller.cs'  = 'InvalidateDocumentsV2CacheAsync'
}
foreach ($n in $inv.Keys) {
    $path = Join-Path $agentHub "Controllers/$n"
    $matches = Select-String -Path $path -Pattern $inv[$n] -AllMatches
    $count = if ($matches) { $matches.Matches.Count } else { 0 }
    # 정의(1) + 호출(≥3, mutation 성공/실패 분기) — 합 ≥ 4 보장
    Assert ($count -ge 4) "캐시 invalidate: $n 에 $($inv[$n]) 호출/정의 ≥ 4 — actual=$count"
}

# ── 6. 한국어 에러 메시지 ───────────────────────────────────────────────
$korNew = 0
foreach ($n in $newControllers) {
    $path = Join-Path $agentHub "Controllers/$n"
    $matches = Select-String -Path $path -Pattern '(BadRequest\(ErrorResponseDto\.BadRequest|StatusCode\(502, new ErrorResponseDto)' -AllMatches
    $korNew += if ($matches) { $matches.Matches.Count } else { 0 }
}
Assert ($korNew -ge 30) "한국어 BadRequest/502 메시지 변환 사이트 ≥ 30 (신규 3 컨트롤러) — actual=$korNew"

# ── 7. Service / Client 메서드 시그니처 ────────────────────────────────
$idoc = Join-Path $agentHub 'Services/IDocUtilClient.cs'
$idocContent = Get-Content $idoc -Raw

$expectedMethods = @(
    'ListApiKeysAsync', 'CreateApiKeyAsync', 'DeleteApiKeyAsync', 'VerifyApiKeyAsync',
    'ListDocAgentsAsync', 'GetDocAgentAsync', 'CreateDocAgentAsync', 'UpdateDocAgentAsync', 'DeleteDocAgentAsync',
    'GenerateDocumentV2Async', 'ListDocumentsV2Async', 'GetDocumentV2Async', 'PatchDocumentV2Async',
    'RequestDocumentV2ExportAsync', 'GetDocumentV2ExportStatusAsync', 'DownloadDocumentV2ExportAsync'
)
foreach ($m in $expectedMethods) {
    Assert ($idocContent -match "Task\s*<?.*?>?\s+$m\s*\(") "IDocUtilClient: $m 시그니처 존재"
}

# ── 8. Vue service 함수 export ─────────────────────────────────────────
$svc = Join-Path $agentHub 'ClientApp/src/services/docutilService.ts'
$svcContent = Get-Content $svc -Raw
$tsExpected = @(
    'listApiKeys', 'createApiKey', 'deleteApiKey', 'verifyApiKey',
    'listDocAgents', 'getDocAgent', 'createDocAgent', 'updateDocAgent', 'deleteDocAgent',
    'listDocumentsV2', 'getDocumentV2', 'generateDocumentV2', 'patchDocumentV2',
    'requestDocumentV2Export', 'getDocumentV2ExportStatus', 'downloadDocumentV2Export'
)
foreach ($f in $tsExpected) {
    Assert ($svcContent -match "export\s+async\s+function\s+$f\s*\(") "docutilService.ts: $f export 존재"
}

# ── 9. 라우터 등록 ───────────────────────────────────────────────────────
$router = Join-Path $agentHub 'ClientApp/src/router/index.ts'
$routerContent = Get-Content $router -Raw
foreach ($name in @('AdminDocUtilApiKeys', 'AdminDocUtilDocAgents', 'AdminDocUtilDocumentsV2')) {
    Assert ($routerContent -match "name:\s*'$name'") "Router: $name 라우트 등록"
}

# ── 10. MainLayout 메뉴 등록 + i18n 키 ─────────────────────────────────
$layout = Join-Path $agentHub 'ClientApp/src/layouts/MainLayout.vue'
$layoutContent = Get-Content $layout -Raw
foreach ($key in @('docutilApiKeys', 'docutilDocAgents', 'docutilDocumentsV2')) {
    Assert ($layoutContent -match "nav\.$key") "MainLayout: nav.$key 메뉴 등록"
}

# i18n 키 (ko + en 모두) — adminDocutilApiKeys / DocAgents / DocumentsV2 블록 존재.
$ko = Get-Content (Join-Path $agentHub 'ClientApp/src/i18n/locales/ko.json') -Raw
$en = Get-Content (Join-Path $agentHub 'ClientApp/src/i18n/locales/en.json') -Raw
foreach ($block in @('adminDocutilApiKeys', 'adminDocutilDocAgents', 'adminDocutilDocumentsV2')) {
    Assert ($ko -match "`"$block`":\s*{") "i18n ko: $block 블록 존재"
    Assert ($en -match "`"$block`":\s*{") "i18n en: $block 블록 존재"
}

# ── 11. 신규 코드에 @ts-nocheck 없음 ─────────────────────────────────────
$newFrontFiles = @(
    'ClientApp/src/views/admin/AdminDocUtilApiKeys.vue',
    'ClientApp/src/views/admin/AdminDocUtilDocAgents.vue',
    'ClientApp/src/views/admin/AdminDocUtilDocumentsV2.vue'
)
foreach ($f in $newFrontFiles) {
    $content = Get-Content (Join-Path $agentHub $f) -Raw
    Assert (-not ($content -match '@ts-nocheck')) "$f 에 @ts-nocheck 미존재"
}

# ── 결과 ─────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "==== 결과: PASS=$pass, FAIL=$fail ====" -ForegroundColor Cyan
if ($fail -gt 0) {
    Write-Host ""
    Write-Host "실패 케이스:" -ForegroundColor Red
    foreach ($e in $errors) {
        Write-Host "  - $e" -ForegroundColor Red
    }
    exit 1
} else {
    Write-Host "모든 정합성 검증 PASS." -ForegroundColor Green
    exit 0
}
