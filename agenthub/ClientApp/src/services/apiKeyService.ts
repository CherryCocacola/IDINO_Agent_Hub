/**
 * apiKeyService — 외부 LLM 키 풀(KeyType='Provider') 도메인 래퍼.
 *
 * 트랙 #91 (2026-05-13) 신설.
 *
 * 호출 흐름:
 *   Vue View (ApiKeys.vue 탭 3 — 운영자 전용)
 *     -> apiKeyService (본 파일)
 *     -> services/api.ts (axios 인터셉터: JWT 자동 부착, 401 갱신)
 *     -> AgentHub `[Authorize(Roles="Admin,SuperAdmin")] /api/apikeys/*`
 *     -> ApiKeyService.CreateProviderApiKeyAsync / TestApiKeyAsync / GetPoolStats
 *
 * 설계 원칙:
 *   - anti-pattern #11 (Vue 컴포넌트의 axios 직접 import 금지) 명시 준수.
 *     services/api 인스턴스만 사용 — JWT 자동 부착 + 401 자동 갱신 인터셉터 활용.
 *   - anti-pattern #4 (하드코딩 API URL 금지) 준수 — baseURL='/api' 는 api.ts 에 집중.
 *
 * KeyType 격리:
 *   - 'External': 사용자가 외부에서 AgentHub 를 호출할 때 쓰는 ak-... 키 (기존 자산).
 *   - 'Provider': 운영자가 등록하는 외부 LLM 제공사 키. ApiKeyPoolService 가 풀에 로드.
 *   - listProviderKeys() 는 클라이언트에서 keyType==='Provider' 로 필터 — 백엔드에서
 *     별도 endpoint 분기 없이 기존 GET /apikeys 응답을 재사용 (KeyType 필드 활용).
 */

import api from '@/services/api'
import type {
  ApiKeyDto,
  CreateProviderApiKeyRequestDto,
  TestApiKeyResponseDto,
  PoolStatsResponseDto,
} from '@/types'

/**
 * 외부 LLM 키 풀(KeyType='Provider') 도메인 래퍼.
 *
 * 모든 메서드는 Admin/SuperAdmin 권한이 필요한 백엔드 endpoint 를 호출한다.
 * 권한 부족 시 백엔드가 403 을 반환하며, 인터셉터는 별도 처리하지 않으므로
 * 호출자(View) 가 toast 로 안내한다.
 */
export const apiKeyService = {
  /**
   * 외부 LLM 키 등록 (운영자 전용).
   *
   * 백엔드 POST /api/apikeys/provider:
   *   - ServiceCode 화이트리스트 검사 (NormalizeServiceCode)
   *   - KeyType="Provider" 강제 (DTO 의 KeyType 필드 무시)
   *   - KeyHash UNIQUE 검사 (중복 키 등록 차단)
   *   - validateOnCreate=true 면 등록 직후 제공사 ping → 실패 시 등록 자체를 거부
   *   - 등록 성공 → ApiKeyPoolService.RefreshAsync() 즉시 트리거 → 풀 반영
   *
   * 응답: 마스킹된 ApiKeyDto. apiKey 평문은 응답에 포함되지 않으며 호출자가
   *       request 의 apiKey 필드를 직후 폐기해야 한다.
   */
  async createProviderKey(req: CreateProviderApiKeyRequestDto): Promise<ApiKeyDto> {
    const { data } = await api.post<ApiKeyDto>('/apikeys/provider', req)
    return data
  },

  /**
   * API 키 즉시 유효성 검증 — 제공사별 가벼운 ping 호출.
   *
   * 백엔드 POST /api/apikeys/{id}/test:
   *   - Gemini → /v1beta/models (ListModels)
   *   - OpenAI → /v1/models
   *   - Claude → /v1/messages dry-run
   *   - Perplexity / Mistral → 각자 가벼운 GET
   *   - 타임아웃 10s. 실패 시 success=false + 한국어 message.
   *
   * 호출 시점: 운영자가 [테스트] 버튼 클릭 / validateOnCreate=true 등록 직후 자동.
   */
  async testKey(apiKeyId: number): Promise<TestApiKeyResponseDto> {
    const { data } = await api.post<TestApiKeyResponseDto>(`/apikeys/${apiKeyId}/test`)
    return data
  },

  /**
   * 풀 통계 조회 — 프로바이더별 DB/appsettings 출처 분리 + 냉각 상태.
   *
   * 백엔드 GET /api/apikeys/pool-stats:
   *   - ApiKeyPoolService.GetPoolStatsWithSource() 의 in-memory 스냅샷
   *   - lastRefreshedAt 은 마지막 RefreshAsync 완료 시각 (UTC)
   *   - DB 조회 없이 즉시 반환 — Admin UI 폴링에 안전
   */
  async getPoolStats(): Promise<PoolStatsResponseDto> {
    const { data } = await api.get<PoolStatsResponseDto>('/apikeys/pool-stats')
    return data
  },

  /**
   * 외부 LLM 키 목록 조회 (KeyType='Provider' 만 필터).
   *
   * 기존 GET /api/apikeys 응답에서 클라이언트 사이드로 필터 — 백엔드 endpoint
   * 분기를 늘리지 않기 위함. 응답 ApiKeyDto.keyType 필드를 활용.
   *
   * 구버전 응답 호환: keyType 이 undefined 면 'External' 로 간주 (백엔드 DEFAULT 일치).
   */
  async listProviderKeys(): Promise<ApiKeyDto[]> {
    const { data } = await api.get<ApiKeyDto[]>('/apikeys')
    return (data ?? []).filter((k) => k.keyType === 'Provider')
  },

  /**
   * 외부 LLM 키 삭제. 기존 DELETE /api/apikeys/{id} 재사용.
   *
   * 운영자 콘솔 트랙 #91 에서는 KeyType='Provider' 키만 본 메서드로 삭제하지만,
   * 백엔드는 KeyType 무관하게 동일 endpoint 로 처리한다 — 호출자(View) 가 탭 격리.
   */
  async deleteKey(apiKeyId: number): Promise<void> {
    await api.delete(`/apikeys/${apiKeyId}`)
  },
}
