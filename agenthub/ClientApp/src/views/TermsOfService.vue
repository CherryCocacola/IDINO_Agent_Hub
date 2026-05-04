<template>
  <div class="legal-page">
    <div class="legal-container">
      <div class="legal-header">
        <a href="/" class="legal-logo">
          <i class="bi bi-robot"></i> AIAgent Management
        </a>
      </div>

      <div class="legal-content">
        <h1>이용약관</h1>
        <p class="legal-updated">최종 업데이트: 2026년 3월 17일</p>

        <section>
          <h2>제1조 (목적)</h2>
          <p>본 약관은 IDINO(이하 "회사")가 제공하는 AIAgent Management 서비스(이하 "서비스")의 이용에 관한 조건 및 절차, 회사와 이용자의 권리·의무 및 책임사항을 규정함을 목적으로 합니다.</p>
        </section>

        <section>
          <h2>제2조 (정의)</h2>
          <ul>
            <li><strong>"서비스"</strong>란 회사가 제공하는 AI 에이전트 관리 플랫폼 및 관련 제반 서비스를 의미합니다.</li>
            <li><strong>"이용자"</strong>란 본 약관에 동의하고 회사가 제공하는 서비스를 이용하는 자를 의미합니다.</li>
            <li><strong>"에이전트"</strong>란 이용자가 서비스 내에서 생성하거나 관리하는 AI 챗봇 또는 자동화 워크플로우를 의미합니다.</li>
          </ul>
        </section>

        <section>
          <h2>제3조 (약관의 효력 및 변경)</h2>
          <p>본 약관은 서비스 화면에 게시하거나 기타 방법으로 이용자에게 공지함으로써 효력이 발생합니다. 회사는 필요한 경우 관련 법령을 위배하지 않는 범위 내에서 본 약관을 변경할 수 있으며, 변경된 약관은 공지 후 7일 이후부터 효력이 발생합니다.</p>
        </section>

        <section>
          <h2>제4조 (서비스의 제공)</h2>
          <p>회사는 다음과 같은 서비스를 제공합니다.</p>
          <ul>
            <li>AI 에이전트 생성 및 관리</li>
            <li>대화 이력 저장 및 조회</li>
            <li>지식 베이스(RAG) 구축 및 활용</li>
            <li>워크플로우 자동화</li>
            <li>사용량 통계 및 분석</li>
            <li>기타 회사가 추가 개발하거나 제휴를 통해 제공하는 서비스</li>
          </ul>
        </section>

        <section>
          <h2>제5조 (이용자의 의무)</h2>
          <p>이용자는 다음 행위를 해서는 안 됩니다.</p>
          <ul>
            <li>타인의 정보를 도용하거나 허위 정보를 등록하는 행위</li>
            <li>서비스를 이용하여 법령 또는 본 약관이 금지하는 행위</li>
            <li>서비스의 정상적인 운영을 방해하는 행위</li>
            <li>서비스를 이용하여 음란물, 폭력물 등 불법 콘텐츠를 생성하는 행위</li>
            <li>회사의 지적재산권을 침해하는 행위</li>
          </ul>
        </section>

        <section>
          <h2>제6조 (서비스 이용 제한)</h2>
          <p>회사는 이용자가 본 약관의 의무를 위반하거나 서비스의 정상적인 운영을 방해하는 경우, 경고, 일시 정지, 영구 이용 정지 등의 조치를 취할 수 있습니다.</p>
        </section>

        <section>
          <h2>제7조 (책임의 한계)</h2>
          <p>회사는 이용자가 서비스를 이용하여 기대하는 수익을 얻지 못하거나 AI 생성 결과물의 정확성에 대해 책임을 지지 않습니다. AI 응답은 참고용이며, 중요한 의사결정에 단독으로 활용하지 않도록 권장합니다.</p>
        </section>

        <section>
          <h2>제8조 (준거법 및 관할)</h2>
          <p>본 약관은 대한민국 법률에 따라 해석되며, 서비스 이용과 관련한 분쟁은 회사 소재지를 관할하는 법원을 전속 관할로 합니다.</p>
        </section>
      </div>

      <div class="legal-footer">
        <router-link to="/privacy" class="legal-link">개인정보처리방침</router-link>
        <span class="legal-sep">|</span>
        <a href="/" class="legal-link">서비스 홈</a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 정적 페이지 — 추가 로직 없음
</script>

<style scoped>
.legal-page {
  min-height: 100vh;
  background: var(--ai-bg, #f8f9fa);
  padding: 2rem 1rem;
}

.legal-container {
  max-width: 800px;
  margin: 0 auto;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,.08);
  padding: 2.5rem;
}

.legal-header {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--ai-border, #e5e7eb);
}

.legal-logo {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--ai-primary, #4f46e5);
  text-decoration: none;
}

.legal-content h1 {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
  color: var(--ai-text, #111827);
}

.legal-updated {
  color: var(--ai-text-muted, #6b7280);
  font-size: 0.875rem;
  margin-bottom: 2rem;
}

.legal-content section {
  margin-bottom: 2rem;
}

.legal-content h2 {
  font-size: 1.1rem !important;
  font-weight: 700 !important;
  color: var(--ai-text, #111827);
  margin-bottom: 0.75rem;
}

.legal-content p,
.legal-content li {
  font-size: 0.9375rem;
  line-height: 1.7;
  color: var(--ai-text-secondary, #374151);
}

.legal-content ul {
  padding-left: 1.5rem;
}

.legal-content li {
  margin-bottom: 0.4rem;
}

.legal-footer {
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--ai-border, #e5e7eb);
  text-align: center;
  color: var(--ai-text-muted, #6b7280);
  font-size: 0.875rem;
}

.legal-link {
  color: var(--ai-primary, #4f46e5);
  text-decoration: none;
}

.legal-link:hover {
  text-decoration: underline;
}

.legal-sep {
  margin: 0 0.75rem;
}
</style>
