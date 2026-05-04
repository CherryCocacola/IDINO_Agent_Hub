<template>
  <div class="lp-root">
    <!-- NAV -->
    <nav class="lp-nav" :class="{ scrolled: navScrolled }">
      <a href="/" class="lp-logo">
        <div class="lp-logo-icon"><i class="bi bi-robot"></i></div>
        AgentHub
      </a>
      <div class="lp-nav-links">
        <a href="#features" @click.prevent="scrollTo('features')">기능</a>
        <a href="#how" @click.prevent="scrollTo('how')">사용방법</a>
        <a href="#demo" @click.prevent="scrollTo('demo')">데모</a>
        <a href="#usecases" @click.prevent="scrollTo('usecases')">활용 사례</a>
      </div>
      <div class="lp-nav-actions">
        <router-link to="/login" class="btn-ghost">로그인</router-link>
        <router-link to="/agents/builder" class="btn-primary-sm">무료 시작하기</router-link>
      </div>
    </nav>

    <!-- HERO -->
    <section class="lp-hero">
      <div class="lp-hero-inner">
        <div class="lp-hero-content fade-in visible">
          <div class="hero-badge">
            <i class="bi bi-stars"></i> 코딩 없이 만드는 AI 에이전트
          </div>
          <h1>
            나만의 AI를<br>
            <span class="highlight">5분 만에 만들고</span><br>
            어디서나 공유하세요
          </h1>
          <p class="hero-desc">
            GPT, Claude, Mistral 등 최고의 AI 모델 위에<br>
            나만의 에이전트를 만들고, 링크로 공유하거나<br>
            웹사이트에 바로 임베드하세요.
          </p>
          <div class="hero-actions">
            <router-link to="/agents/builder" class="btn-hero-primary">
              <i class="bi bi-plus-circle-fill"></i> 에이전트 만들기
            </router-link>
          </div>
          <div class="hero-stats">
            <div class="hero-stat-item">
              <div class="num">3+</div>
              <div class="label">지원 AI 서비스</div>
            </div>
            <div class="hero-stat-item">
              <div class="num">5분</div>
              <div class="label">에이전트 생성 시간</div>
            </div>
            <div class="hero-stat-item">
              <div class="num">무제한</div>
              <div class="label">에이전트 생성 가능</div>
            </div>
          </div>
        </div>

        <div class="lp-hero-visual fade-in visible" style="animation-delay:.2s">
          <div class="floating-badge top-right">
            <i class="bi bi-check-circle-fill"></i> 응답 생성 완료
          </div>
          <div class="floating-badge bottom-left">
            <i class="bi bi-lightning-charge-fill"></i> gpt-4o 연결됨
          </div>
          <div class="floating-badge mid-right" style="font-size:11px">
            <i class="bi bi-bar-chart-fill" style="color:#f59e0b"></i> 토큰: 142
          </div>
          <div class="chat-preview">
            <div class="chat-preview-header">
              <div class="chat-preview-avatar">🤖</div>
              <div class="chat-preview-info">
                <strong>마케팅 분석 Agent</strong>
                <small><span class="online-dot"></span>온라인 · GPT-4o</small>
              </div>
            </div>
            <div class="chat-preview-body">
              <div class="chat-bubble bot">안녕하세요! 마케팅 분석을 도와드릴 준비가 됐습니다. 무엇이 궁금하신가요?</div>
              <div class="chat-bubble user">우리 제품의 SNS 마케팅 전략 좀 짜줄 수 있어?</div>
              <div class="chat-bubble bot">물론이죠! 먼저 타겟 고객층과 예산 규모를 알려주시면 더 정확한 전략을 제안해 드릴게요 😊</div>
              <div class="chat-bubble typing">
                <div class="dot"></div><div class="dot"></div><div class="dot"></div>
              </div>
            </div>
            <div class="chat-preview-input">
              <span>메시지를 입력하세요...</span>
              <button><i class="bi bi-send-fill"></i></button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- AI SERVICES -->
    <section class="lp-services">
      <div class="services-label">다음 AI 서비스와 연동 가능합니다</div>
      <div class="services-logos">
        <div class="service-chip"><i class="bi bi-circle-fill dot-green"></i> OpenAI GPT-4o</div>
        <div class="service-chip"><i class="bi bi-circle-fill dot-blue"></i> Claude 3.5 Sonnet</div>
        <div class="service-chip"><i class="bi bi-circle-fill dot-orange"></i> Mistral Large</div>
        <div class="service-chip"><i class="bi bi-circle-fill dot-purple"></i> GPT-o3</div>
        <div class="service-chip"><i class="bi bi-circle-fill dot-green"></i> Claude Opus</div>
        <div class="service-chip chip-dashed">+ 더 많은 모델 준비 중</div>
      </div>
    </section>

    <!-- FEATURES -->
    <section class="lp-features" id="features">
      <div class="lp-inner">
        <div class="fade-in section-head">
          <div class="section-label"><i class="bi bi-grid-3x3-gap"></i> 핵심 기능</div>
          <div class="section-title">필요한 모든 기능이 한 곳에</div>
          <p class="section-desc">복잡한 설정 없이 AI 에이전트를 만들고, 공유하고, 분석하세요.</p>
        </div>
        <div class="features-grid fade-in">
          <div class="feature-card" v-for="f in features" :key="f.title">
            <div class="feature-icon" :style="{ background: f.bg, color: f.color }">
              <i :class="f.icon"></i>
            </div>
            <h3>{{ f.title }}</h3>
            <p>{{ f.desc }}</p>
            <span class="feature-tag">{{ f.tag }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- HOW IT WORKS -->
    <section class="lp-how" id="how">
      <div class="lp-inner">
        <div class="fade-in section-head" style="text-align:center">
          <div class="section-label"><i class="bi bi-signpost-split"></i> 사용 방법</div>
          <div class="section-title">딱 4단계면 충분합니다</div>
          <p class="section-desc" style="margin:0 auto">처음 사용자도 5분 안에 나만의 AI 에이전트를 만들고 공유할 수 있습니다.</p>
        </div>
        <div class="steps fade-in">
          <div class="step" v-for="s in howSteps" :key="s.num">
            <div class="step-num">{{ s.num }}</div>
            <h4>{{ s.title }}</h4>
            <p v-html="s.desc"></p>
          </div>
        </div>
      </div>
    </section>

    <!-- DEMO -->
    <section class="lp-demo" id="demo">
      <div class="lp-inner">
        <div class="fade-in section-head">
          <div class="section-label"><i class="bi bi-play-circle-fill"></i> 라이브 데모</div>
          <div class="section-title">지금 바로 체험해보세요</div>
          <p class="section-desc">로그인 없이 샘플 에이전트와 대화해볼 수 있습니다.</p>
        </div>
        <div class="demo-inner fade-in">
          <div>
            <div class="demo-text-list">
              <div
                v-for="d in demoItems"
                :key="d.key"
                class="demo-item"
                :class="{ active: currentDemo === d.key }"
                @click="setDemo(d.key)"
              >
                <div class="demo-item-icon" :style="{ background: d.bg }">{{ d.avatar }}</div>
                <div>
                  <h5>{{ d.name }}</h5>
                  <p>{{ d.desc }}</p>
                </div>
              </div>
            </div>
            <p class="demo-note" style="color:#475569; margin-top:16px; font-size:12px;">
              실제 에이전트는 로그인 후 직접 만들 수 있습니다.<br>
              <router-link to="/login" style="color:#818cf8">지금 시작하기 →</router-link>
            </p>
          </div>

          <div>
            <div class="demo-chat-wrap">
              <div class="demo-chat-header">
                <div class="demo-chat-avatar">{{ currentDemoData.avatar }}</div>
                <div class="demo-chat-info">
                  <strong>{{ currentDemoData.name }}</strong>
                  <small><span style="color:#4ade80; font-size:8px">●</span> 온라인 데모</small>
                </div>
              </div>
              <div class="demo-chat-body" ref="demoChatEl">
                <div
                  v-for="(msg, i) in demoMessages"
                  :key="i"
                  class="demo-bubble"
                  :class="msg.role"
                >{{ msg.text }}</div>
              </div>
              <div class="demo-chat-input">
                <input
                  type="text"
                  v-model="demoInput"
                  placeholder="메시지를 입력하세요..."
                  @keydown.enter="sendDemo"
                >
                <button @click="sendDemo"><i class="bi bi-send-fill"></i></button>
              </div>
            </div>
            <p class="demo-note">※ 실제 AI가 아닌 시나리오 기반 데모입니다. <router-link to="/login">실제 버전 체험하기</router-link></p>
          </div>
        </div>
      </div>
    </section>

    <!-- USE CASES -->
    <section class="lp-usecases" id="usecases">
      <div class="lp-inner">
        <div class="fade-in section-head">
          <div class="section-label"><i class="bi bi-lightbulb-fill"></i> 활용 사례</div>
          <div class="section-title">이런 곳에 활용하고 있어요</div>
          <p class="section-desc">업무 자동화부터 고객 서비스까지, 다양한 분야에서 AI 에이전트를 활용해보세요.</p>
        </div>
        <div class="use-cases-grid fade-in">
          <div class="use-case-card" v-for="uc in useCases" :key="uc.title" :class="uc.cls">
            <div>
              <h3>{{ uc.title }}</h3>
              <p>{{ uc.desc }}</p>
            </div>
            <span class="use-case-tag">{{ uc.tag }}</span>
            <div class="uc-bg-icon"><i :class="uc.icon"></i></div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="lp-cta">
      <div class="lp-inner">
        <div class="fade-in" style="text-align:center">
          <h2>지금 바로 첫 번째<br>AI 에이전트를 만들어보세요</h2>
          <p>복잡한 설정도, 개발 지식도 필요 없습니다.<br>5분이면 나만의 AI가 준비됩니다.</p>
          <div class="cta-actions">
            <router-link to="/login" class="btn-cta-ghost">
              <i class="bi bi-box-arrow-in-right"></i> 로그인
            </router-link>
          </div>
        </div>
      </div>
    </section>

    <!-- FOOTER -->
    <footer class="lp-footer">
      <div class="lp-footer-logo"><i class="bi bi-robot"></i> Agent Hub</div>
      <div class="lp-footer-links">
        <router-link to="/terms">이용약관</router-link>
        <router-link to="/privacy">개인정보처리방침</router-link>
        <router-link to="/help">도움말</router-link>
      </div>
      <div class="lp-copy">© 2026 Agent Hub. All rights reserved.</div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'

// ── 네비게이션 스크롤 감지 ──
const navScrolled = ref(false)
const scrollTo = (id: string) => {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

// ── Features ──
const features = [
  { icon: 'bi bi-magic', bg: '#eef2ff', color: '#4F46E5', title: '에이전트 빌더', desc: '5단계 위저드로 시스템 프롬프트, 모델, 동작 방식을 설정하세요. 코딩은 전혀 필요 없습니다.', tag: 'No-code' },
  { icon: 'bi bi-share-fill', bg: '#f0fdf4', color: '#10b981', title: '링크로 공유', desc: '에이전트 URL을 생성해 누구에게나 공유하세요. 로그인 없이도 대화 가능한 챗봇 페이지가 제공됩니다.', tag: 'Public URL' },
  { icon: 'bi bi-code-slash', bg: '#fff7ed', color: '#f59e0b', title: '웹 임베드', desc: '한 줄의 iframe 코드로 어떤 웹사이트에도 챗봇을 심을 수 있습니다. 테마도 커스터마이즈 가능합니다.', tag: 'iframe embed' },
  { icon: 'bi bi-database-fill', bg: '#f0f9ff', color: '#0ea5e9', title: 'RAG 문서 연동', desc: '내부 문서나 Knowledge Base를 연결해 에이전트가 정확한 정보를 바탕으로 답변하도록 만드세요.', tag: 'Knowledge Base' },
  { icon: 'bi bi-graph-up-arrow', bg: '#fdf4ff', color: '#a855f7', title: '사용 분석', desc: '토큰 사용량, 비용, 응답 속도 등을 대시보드에서 실시간으로 확인하세요. 팀별 할당량도 설정 가능합니다.', tag: 'Analytics' },
  { icon: 'bi bi-shield-check-fill', bg: '#fff1f2', color: '#ef4444', title: '보안 & 컴플라이언스', desc: 'PII 보호, 금칙어 필터, 감사 로그 등 기업 환경에 필요한 보안 기능이 기본으로 탑재되어 있습니다.', tag: 'Enterprise' },
]

// ── How It Works ──
const howSteps = [
  { num: '1', title: 'AI 서비스 선택', desc: 'GPT, Claude, Mistral 중<br>원하는 AI 모델을 고르세요' },
  { num: '2', title: '에이전트 설정', desc: '역할, 말투, 지식 범위를<br>시스템 프롬프트로 정의하세요' },
  { num: '3', title: '테스트 & 저장', desc: '바로 대화해보며 동작을<br>확인하고 저장하세요' },
  { num: '4', title: '공유 & 임베드', desc: 'URL을 공유하거나<br>웹에 임베드하세요' },
]

// ── Demo ──
const demoItems = [
  { key: 'platform', avatar: '🤖', name: '플랫폼 안내 에이전트', desc: '이 플랫폼의 기능과 사용 방법에 대해 무엇이든 물어보세요', bg: 'rgba(99,102,241,.2)' },
  { key: 'hr', avatar: '💼', name: 'HR 도우미 에이전트', desc: '사내 규정, 휴가 신청, 복리후생 등 HR 관련 질문 답변', bg: 'rgba(16,185,129,.2)' },
  { key: 'code', avatar: '💻', name: '코딩 도우미 에이전트', desc: '코드 리뷰, 버그 찾기, 코드 설명 등 개발 업무 지원', bg: 'rgba(245,158,11,.2)' },
]

const demoReplies: Record<string, Record<string, string>> = {
  platform: {
    default: '좋은 질문이에요! 이 플랫폼에서는 코딩 없이 나만의 AI 에이전트를 만들 수 있습니다. 에이전트 빌더에서 5단계만 따라하면 됩니다.',
    '기능': 'AI 에이전트 생성, 링크 공유, 웹 임베드, RAG 문서 연동, 사용량 분석, 멀티 AI 지원 등 다양한 기능을 제공합니다!',
    '요금': '기본 기능은 무료로 이용 가능합니다. AI API 비용만 별도로 발생합니다.',
    '임베드': 'iframe 코드 한 줄로 어떤 웹사이트에도 챗봇을 삽입할 수 있습니다. 테마(라이트/다크)도 선택 가능해요!',
  },
  hr: {
    default: '사내 HR 정책과 관련한 문의를 도와드릴게요. 더 자세한 사항은 HR팀에 문의해주세요.',
    '휴가': '연차 휴가는 입사 1년 후 15일이 부여됩니다. 신청은 사내 시스템에서 3일 전에 해주세요.',
  },
  code: {
    default: '코드를 붙여넣어주시면 검토해드리겠습니다! 어떤 언어나 프레임워크든 도움을 드릴 수 있어요.',
    '버그': '버그를 찾으려면 코드와 오류 메시지를 함께 알려주세요. 빠르게 원인을 파악해드릴게요!',
  }
}

const demoWelcomes: Record<string, string> = {
  platform: '안녕하세요! 저는 Agent Hub 안내 에이전트입니다. 플랫폼 사용법, 기능, 요금 등 무엇이든 물어보세요 😊',
  hr: '안녕하세요! HR 도우미 에이전트입니다. 휴가, 복리후생, 사내 규정에 대해 편하게 질문하세요.',
  code: '안녕하세요! 코딩 관련 질문이 있으신가요? 코드 리뷰, 버그 찾기, 설명 등 도와드릴게요.',
}

const currentDemo = ref('platform')
const demoInput = ref('')
const demoMessages = ref<{ role: string; text: string }[]>([
  { role: 'bot', text: demoWelcomes['platform'] }
])
const demoChatEl = ref<HTMLElement | null>(null)

const currentDemoData = computed(() => demoItems.find(d => d.key === currentDemo.value) || demoItems[0])

const setDemo = (key: string) => {
  currentDemo.value = key
  demoMessages.value = [{ role: 'bot', text: demoWelcomes[key] }]
}

const sendDemo = async () => {
  const msg = demoInput.value.trim()
  if (!msg) return
  demoMessages.value.push({ role: 'user', text: msg })
  demoInput.value = ''
  await nextTick()
  if (demoChatEl.value) demoChatEl.value.scrollTop = demoChatEl.value.scrollHeight

  setTimeout(async () => {
    const replies = demoReplies[currentDemo.value]
    let reply = replies.default
    for (const [key, val] of Object.entries(replies)) {
      if (key !== 'default' && msg.includes(key)) { reply = val; break }
    }
    demoMessages.value.push({ role: 'bot', text: reply })
    await nextTick()
    if (demoChatEl.value) demoChatEl.value.scrollTop = demoChatEl.value.scrollHeight
  }, 700)
}

// ── Use Cases ──
const useCases = [
  { cls: 'uc-1', icon: 'bi bi-headset', title: '고객 지원 챗봇', desc: 'FAQ, 주문 조회, 반품 안내 등을 자동화해 24시간 고객 응대를 구현하세요.', tag: '고객 서비스' },
  { cls: 'uc-2', icon: 'bi bi-people-fill', title: '사내 HR 도우미', desc: '사내 정책, 복지, 온보딩 정보를 에이전트에 연결해 직원 질문에 즉시 답변합니다.', tag: 'HR & 총무' },
  { cls: 'uc-3', icon: 'bi bi-box-seam-fill', title: '제품 설명 도우미', desc: '상품 카탈로그, 사용 설명서를 RAG로 연결해 정확한 제품 정보를 제공합니다.', tag: '영업 & 마케팅' },
  { cls: 'uc-4', icon: 'bi bi-mortarboard-fill', title: '교육 & 트레이닝', desc: '학습 자료를 연결해 개인화된 교육 튜터를 만들고 직원 교육에 활용하세요.', tag: '교육' },
  { cls: 'uc-5', icon: 'bi bi-code-square', title: '코드 리뷰 도우미', desc: '개발팀만의 코딩 컨벤션과 규칙을 학습시켜 일관된 코드 리뷰를 자동화합니다.', tag: '개발' },
  { cls: 'uc-6', icon: 'bi bi-graph-up-arrow', title: '리서치 & 분석', desc: '보고서, 데이터를 연결해 빠른 정보 요약 및 인사이트 도출을 지원합니다.', tag: '분석' },
]

// ── Lifecycle ──
onMounted(() => {
  // 네비게이션 스크롤 감지
  const handleScroll = () => { navScrolled.value = window.scrollY > 10 }
  window.addEventListener('scroll', handleScroll)

  // fade-in 애니메이션
  const observer = new IntersectionObserver(
    entries => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible') }),
    { threshold: 0, rootMargin: '0px 0px -40px 0px' }
  )
  setTimeout(() => {
    document.querySelectorAll('.lp-root .fade-in').forEach(el => {
      const rect = el.getBoundingClientRect()
      if (rect.top < window.innerHeight) {
        el.classList.add('visible')
      } else {
        observer.observe(el)
      }
    })
  }, 50)
})
</script>

<style scoped>
*, *::before, *::after { box-sizing: border-box; }

.lp-root {
  font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
  color: #1e293b;
  background: #fff;
  line-height: 1.6;
}

/* ── FADE IN ── */
.fade-in { opacity: 0; transform: translateY(20px); transition: opacity .6s ease, transform .6s ease; }
.fade-in.visible { opacity: 1; transform: translateY(0); }

/* ── NAV ── */
.lp-nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 48px;
  background: rgba(255,255,255,.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(226,232,240,.5);
  transition: box-shadow .2s;
}
.lp-nav.scrolled { box-shadow: 0 2px 12px rgba(0,0,0,.08); }
.lp-logo {
  display: flex; align-items: center; gap: 10px;
  font-weight: 800; font-size: 20px; color: #4F46E5;
  text-decoration: none;
}
.lp-logo-icon {
  width: 36px; height: 36px; border-radius: 10px;
  background: linear-gradient(135deg, #4F46E5, #8b5cf6);
  display: flex; align-items: center; justify-content: center;
  color: white; font-size: 18px;
}
.lp-nav-links { display: flex; align-items: center; gap: 32px; }
.lp-nav-links a { text-decoration: none; color: #64748b; font-size: 14px; font-weight: 500; transition: color .2s; }
.lp-nav-links a:hover { color: #4F46E5; }
.lp-nav-actions { display: flex; align-items: center; gap: 12px; }
.btn-ghost { background: none; border: none; padding: 8px 16px; color: #64748b; font-size: 14px; cursor: pointer; border-radius: 8px; font-weight: 500; text-decoration: none; transition: background .2s; }
.btn-ghost:hover { background: #f8fafc; color: #4F46E5; }
.btn-primary-sm { background: #4F46E5; color: white; border: none; padding: 8px 20px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; text-decoration: none; display: inline-block; transition: opacity .2s; }
.btn-primary-sm:hover { opacity: .88; color: white; }

/* ── HERO ── */
.lp-hero {
  min-height: 100vh;
  display: flex; align-items: center;
  background: linear-gradient(160deg, #f8f9ff 0%, #eef2ff 40%, #f0f9ff 100%);
  padding: 120px 48px 80px;
  position: relative; overflow: hidden;
}
.lp-hero::before {
  content: '';
  position: absolute; top: -200px; right: -200px;
  width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(99,102,241,.12) 0%, transparent 70%);
  border-radius: 50%;
}
.lp-hero-inner {
  max-width: 1200px; margin: 0 auto; width: 100%;
  display: grid; grid-template-columns: 1fr 1fr; gap: 60px; align-items: center;
  position: relative; z-index: 1;
}
.hero-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(79,70,229,.1); color: #4F46E5;
  border: 1px solid rgba(79,70,229,.2); border-radius: 20px;
  padding: 5px 14px; font-size: 12px; font-weight: 600; margin-bottom: 20px;
}
.lp-hero-content h1 { font-size: 52px; font-weight: 800; line-height: 1.15; color: #0f172a; margin-bottom: 20px; word-break: keep-all; }
.highlight { background: linear-gradient(135deg, #4F46E5, #0EA5E9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.hero-desc { font-size: 17px; color: #64748b; margin-bottom: 36px; line-height: 1.8; word-break: keep-all; }
.hero-actions { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; margin-bottom: 40px; }
.btn-hero-primary { display: inline-flex; align-items: center; gap: 8px; background: #4F46E5; color: white; text-decoration: none; padding: 14px 28px; border-radius: 12px; font-size: 15px; font-weight: 700; transition: all .2s; box-shadow: 0 4px 14px rgba(79,70,229,.35); }
.btn-hero-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(79,70,229,.45); color: white; }
.btn-hero-ghost { display: inline-flex; align-items: center; gap: 8px; background: white; color: #4F46E5; text-decoration: none; padding: 14px 28px; border-radius: 12px; font-size: 15px; font-weight: 700; border: 2px solid rgba(79,70,229,.3); transition: all .2s; }
.btn-hero-ghost:hover { border-color: #4F46E5; background: rgba(79,70,229,.05); color: #4F46E5; }
.hero-stats { display: flex; gap: 32px; }
.hero-stat-item .num { font-size: 28px; font-weight: 800; color: #4F46E5; }
.hero-stat-item .label { font-size: 12px; color: #64748b; margin-top: 2px; }

/* ── HERO VISUAL ── */
.lp-hero-visual { position: relative; }
.floating-badge {
  position: absolute; background: white; border-radius: 20px;
  padding: 8px 14px; font-size: 12px; font-weight: 600; color: #1e293b;
  box-shadow: 0 4px 16px rgba(0,0,0,.1); display: flex; align-items: center; gap: 6px;
  animation: float 3s ease-in-out infinite;
}
.floating-badge i { color: #4F46E5; }
.top-right { top: -20px; right: -20px; animation-delay: 0s; }
.bottom-left { bottom: 20px; left: -30px; animation-delay: 1s; }
.mid-right { top: 40%; right: -40px; animation-delay: .5s; }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }

.chat-preview { background: white; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,.12); overflow: hidden; max-width: 420px; margin: 0 auto; }
.chat-preview-header { display: flex; align-items: center; gap: 12px; padding: 16px 20px; border-bottom: 1px solid #f1f5f9; }
.chat-preview-avatar { width: 40px; height: 40px; background: linear-gradient(135deg, #4F46E5, #8b5cf6); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
.chat-preview-info strong { display: block; font-size: 14px; font-weight: 700; }
.chat-preview-info small { color: #64748b; font-size: 11px; display: flex; align-items: center; gap: 4px; }
.online-dot { width: 6px; height: 6px; background: #4ade80; border-radius: 50%; display: inline-block; }
.chat-preview-body { padding: 16px 20px; display: flex; flex-direction: column; gap: 10px; }
.chat-bubble { padding: 10px 14px; border-radius: 12px; font-size: 13px; line-height: 1.5; max-width: 85%; }
.chat-bubble.bot { background: #f1f5f9; color: #1e293b; align-self: flex-start; border-bottom-left-radius: 4px; }
.chat-bubble.user { background: #4F46E5; color: white; align-self: flex-end; border-bottom-right-radius: 4px; }
.chat-bubble.typing { display: flex; gap: 4px; align-items: center; }
.dot { width: 6px; height: 6px; background: #94a3b8; border-radius: 50%; animation: bounce .9s infinite; }
.dot:nth-child(2) { animation-delay: .2s; }
.dot:nth-child(3) { animation-delay: .4s; }
@keyframes bounce { 0%,60%,100% { transform: translateY(0); } 30% { transform: translateY(-4px); } }
.chat-preview-input { display: flex; align-items: center; padding: 12px 16px; border-top: 1px solid #f1f5f9; gap: 8px; }
.chat-preview-input span { flex: 1; color: #94a3b8; font-size: 13px; }
.chat-preview-input button { background: #4F46E5; color: white; border: none; width: 32px; height: 32px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; }

/* ── AI SERVICES ── */
.lp-services { padding: 32px 48px; background: #f8fafc; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; text-align: center; }
.services-label { font-size: 13px; color: #64748b; font-weight: 500; margin-bottom: 16px; }
.services-logos { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }
.service-chip { display: inline-flex; align-items: center; gap: 6px; background: white; border: 1px solid #e2e8f0; border-radius: 20px; padding: 6px 16px; font-size: 13px; font-weight: 500; color: #475569; box-shadow: 0 1px 3px rgba(0,0,0,.05); }
.chip-dashed { color: #94a3b8; border-style: dashed; }
.dot-green { color: #4ade80; font-size: 8px; }
.dot-blue  { color: #60a5fa; font-size: 8px; }
.dot-orange{ color: #fb923c; font-size: 8px; }
.dot-purple{ color: #c084fc; font-size: 8px; }

/* ── COMMON SECTION ── */
.lp-inner { max-width: 1200px; margin: 0 auto; }
.section-head { margin-bottom: 48px; }
.section-label { display: inline-flex; align-items: center; gap: 6px; background: rgba(79,70,229,.08); color: #4F46E5; border-radius: 20px; padding: 5px 14px; font-size: 12px; font-weight: 600; margin-bottom: 16px; }
.section-title { font-size: 36px; font-weight: 800; color: #0f172a; margin-bottom: 12px; }
.section-desc { font-size: 16px; color: #64748b; max-width: 520px; }

/* ── FEATURES ── */
.lp-features { padding: 80px 48px; }
.features-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.feature-card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 28px; transition: all .2s; }
.feature-card:hover { transform: translateY(-4px); box-shadow: 0 8px 32px rgba(0,0,0,.08); border-color: transparent; }
.feature-icon { width: 52px; height: 52px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 22px; margin-bottom: 18px; }
.feature-card h3 { font-size: 17px; font-weight: 700; color: #1e293b; margin-bottom: 8px; }
.feature-card p { font-size: 14px; color: #64748b; line-height: 1.6; margin-bottom: 16px; }
.feature-tag { display: inline-block; background: #f1f5f9; color: #475569; border-radius: 6px; padding: 3px 10px; font-size: 11px; font-weight: 600; }

/* ── HOW IT WORKS ── */
.lp-how { padding: 80px 48px; background: #f8fafc; }
.steps { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; margin-top: 40px; }
.step { background: white; border-radius: 16px; padding: 32px 24px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,.05); }
.step-num { width: 48px; height: 48px; background: linear-gradient(135deg, #4F46E5, #8b5cf6); border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 800; color: white; margin: 0 auto 16px; }
.step h4 { font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 8px; }
.step p { font-size: 13px; color: #64748b; line-height: 1.6; }

/* ── DEMO ── */
.lp-demo { padding: 80px 48px; background: linear-gradient(160deg, #0f172a 0%, #1e1b4b 100%); color: white; }
.lp-demo .section-label { background: rgba(255,255,255,.1); color: #a5b4fc; }
.lp-demo .section-title { color: white; }
.lp-demo .section-desc { color: #94a3b8; }
.demo-inner { display: grid; grid-template-columns: 1fr 1fr; gap: 48px; align-items: start; }
.demo-text-list { display: flex; flex-direction: column; gap: 12px; }
.demo-item { display: flex; align-items: center; gap: 16px; padding: 16px 20px; border-radius: 14px; cursor: pointer; border: 1px solid rgba(255,255,255,.1); transition: all .2s; }
.demo-item:hover { background: rgba(255,255,255,.08); }
.demo-item.active { background: rgba(99,102,241,.25); border-color: rgba(99,102,241,.4); }
.demo-item-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }
.demo-item h5 { font-size: 14px; font-weight: 700; color: white; margin-bottom: 4px; }
.demo-item p  { font-size: 12px; color: #94a3b8; line-height: 1.4; }
.demo-note { font-size: 12px; color: #94a3b8; }
.demo-note a { color: #818cf8; }

.demo-chat-wrap { background: white; border-radius: 20px; overflow: hidden; }
.demo-chat-header { display: flex; align-items: center; gap: 12px; padding: 16px 20px; border-bottom: 1px solid #f1f5f9; }
.demo-chat-avatar { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 22px; }
.demo-chat-info strong { display: block; font-size: 14px; font-weight: 700; color: #1e293b; }
.demo-chat-info small { color: #64748b; font-size: 11px; }
.demo-chat-body { padding: 16px 20px; min-height: 200px; max-height: 300px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; color: #1e293b; }
.demo-bubble { padding: 10px 14px; border-radius: 12px; font-size: 13px; line-height: 1.5; max-width: 85%; }
.demo-bubble.bot  { background: #f1f5f9; color: #1e293b; align-self: flex-start; border-bottom-left-radius: 4px; }
.demo-bubble.user { background: #4F46E5; color: white; align-self: flex-end; border-bottom-right-radius: 4px; }
.demo-chat-input { display: flex; align-items: center; padding: 12px 16px; border-top: 1px solid #f1f5f9; gap: 8px; }
.demo-chat-input input { flex: 1; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 12px; font-size: 13px; outline: none; }
.demo-chat-input input:focus { border-color: #4F46E5; }
.demo-chat-input button { background: #4F46E5; color: white; border: none; width: 36px; height: 36px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; }

/* ── USE CASES ── */
.lp-usecases { padding: 80px 48px; }
.use-cases-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.use-case-card {
  border-radius: 16px; padding: 28px; position: relative; overflow: hidden;
  display: flex; flex-direction: column; justify-content: space-between; gap: 16px;
  min-height: 180px; transition: transform .2s;
}
.use-case-card:hover { transform: translateY(-3px); }
.use-case-card h3 { font-size: 18px; font-weight: 700; margin-bottom: 8px; }
.use-case-card p  { font-size: 13px; line-height: 1.5; }
.use-case-tag { display: inline-block; border-radius: 20px; padding: 3px 12px; font-size: 11px; font-weight: 700; }
.uc-bg-icon { position: absolute; right: 16px; bottom: 16px; font-size: 52px; opacity: .1; }
.uc-1 { background: linear-gradient(135deg, #eef2ff, #e0e7ff); color: #3730a3; }
.uc-1 .use-case-tag { background: rgba(55,48,163,.15); color: #3730a3; }
.uc-2 { background: linear-gradient(135deg, #f0fdf4, #dcfce7); color: #166534; }
.uc-2 .use-case-tag { background: rgba(22,101,52,.15); color: #166534; }
.uc-3 { background: linear-gradient(135deg, #fff7ed, #ffedd5); color: #92400e; }
.uc-3 .use-case-tag { background: rgba(146,64,14,.15); color: #92400e; }
.uc-4 { background: linear-gradient(135deg, #f0f9ff, #e0f2fe); color: #075985; }
.uc-4 .use-case-tag { background: rgba(7,89,133,.15); color: #075985; }
.uc-5 { background: linear-gradient(135deg, #fdf4ff, #fae8ff); color: #6b21a8; }
.uc-5 .use-case-tag { background: rgba(107,33,168,.15); color: #6b21a8; }
.uc-6 { background: linear-gradient(135deg, #fff1f2, #ffe4e6); color: #9f1239; }
.uc-6 .use-case-tag { background: rgba(159,18,57,.15); color: #9f1239; }

/* ── CTA ── */
.lp-cta { padding: 80px 48px; background: linear-gradient(160deg, #4F46E5 0%, #7c3aed 100%); color: white; text-align: center; }
.lp-cta h2 { font-size: 40px; font-weight: 800; line-height: 1.3; margin-bottom: 16px; }
.lp-cta p { font-size: 16px; color: rgba(255,255,255,.8); margin-bottom: 36px; line-height: 1.8; }
.cta-actions { display: flex; justify-content: center; gap: 16px; flex-wrap: wrap; }
.btn-cta-white { display: inline-flex; align-items: center; gap: 8px; background: white; color: #4F46E5; text-decoration: none; padding: 14px 32px; border-radius: 12px; font-size: 15px; font-weight: 700; transition: all .2s; box-shadow: 0 4px 14px rgba(0,0,0,.2); }
.btn-cta-white:hover { transform: translateY(-2px); color: #4F46E5; }
.btn-cta-ghost { display: inline-flex; align-items: center; gap: 8px; background: transparent; color: white; text-decoration: none; padding: 14px 32px; border-radius: 12px; font-size: 15px; font-weight: 700; border: 2px solid rgba(255,255,255,.5); transition: all .2s; }
.btn-cta-ghost:hover { background: rgba(255,255,255,.1); color: white; }

/* ── FOOTER ── */
.lp-footer { background: #0f172a; color: #94a3b8; padding: 40px 48px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; }
.lp-footer-logo { font-size: 18px; font-weight: 800; color: white; display: flex; align-items: center; gap: 8px; }
.lp-footer-links { display: flex; gap: 24px; }
.lp-footer-links a { color: #94a3b8; text-decoration: none; font-size: 13px; transition: color .2s; }
.lp-footer-links a:hover { color: white; }
.lp-copy { font-size: 12px; }

/* ── 반응형 ── */
@media (max-width: 900px) {
  .lp-nav { padding: 14px 24px; }
  .lp-nav-links { display: none; }
  .lp-hero { padding: 100px 24px 60px; }
  .lp-hero-inner { grid-template-columns: 1fr; }
  .lp-hero-visual { display: none; }
  .lp-hero-content h1 { font-size: 36px; }
  .lp-features, .lp-how, .lp-demo, .lp-usecases, .lp-cta { padding: 60px 24px; }
  .features-grid, .use-cases-grid { grid-template-columns: 1fr 1fr; }
  .steps { grid-template-columns: 1fr 1fr; }
  .demo-inner { grid-template-columns: 1fr; }
  .section-title { font-size: 28px; }
}

@media (max-width: 600px) {
  .features-grid, .use-cases-grid { grid-template-columns: 1fr; }
  .steps { grid-template-columns: 1fr; }
  .lp-footer { flex-direction: column; text-align: center; }
  .hero-stats { gap: 20px; }
}
</style>
