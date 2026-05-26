import type { NextConfig } from 'next'

const API_URL = process.env.API_URL || 'http://localhost:8040'

/**
 * AgentHub 운영자 콘솔 절대 URL (환경별 주입).
 * 트랙 A1 Phase E (2026-05-26): DocUtil 운영자 페이지 15개를 AgentHub 통합 콘솔로
 * 302 redirect. 빌드 타임에 인라인되므로 next.config.ts 단계에서 결정.
 */
const AGENTHUB_URL =
  process.env.NEXT_PUBLIC_AGENTHUB_URL || 'http://192.168.10.39:64005'

/**
 * DocUtil 운영자 페이지 → AgentHub 콘솔 매핑 (15 항목).
 * AgentHub 의 `/admin/docutil-*` 라우트가 동일 기능 흡수 완료(Phase A~B 검증).
 */
const ADMIN_REDIRECTS: { source: string; destination: string }[] = [
  { source: '/admin-accounts', destination: `${AGENTHUB_URL}/admin/docutil-users` },
  { source: '/departments', destination: `${AGENTHUB_URL}/admin/docutil-departments` },
  { source: '/projects', destination: `${AGENTHUB_URL}/admin/docutil-projects` },
  { source: '/dashboard', destination: `${AGENTHUB_URL}/admin/docutil-dashboard` },
  { source: '/api-keys', destination: `${AGENTHUB_URL}/admin/docutil-api-keys` },
  { source: '/agents', destination: `${AGENTHUB_URL}/admin/docutil-doc-agents` },
  { source: '/documents', destination: `${AGENTHUB_URL}/admin/docutil-documents-v2` },
  { source: '/templates', destination: `${AGENTHUB_URL}/admin/docutil-templates` },
  { source: '/search-scopes', destination: `${AGENTHUB_URL}/admin/docutil-search-scopes` },
  { source: '/evaluation', destination: `${AGENTHUB_URL}/admin/docutil-evaluation` },
  { source: '/help', destination: `${AGENTHUB_URL}/admin/docutil-faq` },
  { source: '/settings', destination: `${AGENTHUB_URL}/admin/docutil-settings` },
  { source: '/quick-guide', destination: `${AGENTHUB_URL}/admin/docutil-quick-guide` },
  { source: '/search-test', destination: `${AGENTHUB_URL}/admin/docutil-search-test` },
  // quotas 는 AgentHub 의 departments 화면에 통합됨
  { source: '/quotas', destination: `${AGENTHUB_URL}/admin/docutil-departments` },
]

const nextConfig: NextConfig = {
  output: 'standalone',
  serverExternalPackages: [],
  experimental: {
    serverActions: {
      bodySizeLimit: '100mb',
    },
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${API_URL}/api/:path*`,
      },
      {
        source: '/ws/:path*',
        destination: `${API_URL}/ws/:path*`,
      },
    ]
  },
  async redirects() {
    // permanent=false 인 이유: 향후 SSO/도메인 통합 시 변경 가능성 보존 (302).
    return ADMIN_REDIRECTS.map((r) => ({
      source: r.source,
      destination: r.destination,
      permanent: false,
    }))
  },
}

export default nextConfig
