import { marked } from 'marked'
import DOMPurify from 'dompurify'
import Prism from 'prismjs'
import 'prismjs/themes/prism-tomorrow.css'
// Prism 언어 지원
import 'prismjs/components/prism-python'
import 'prismjs/components/prism-java'
import 'prismjs/components/prism-csharp'
import 'prismjs/components/prism-javascript'
import 'prismjs/components/prism-typescript'
import 'prismjs/components/prism-css'
import 'prismjs/components/prism-markup'

// HTML 엔티티 디코딩 헬퍼 함수
const decodeHtmlEntities = (text: string): string => {
  const textarea = document.createElement('textarea')
  textarea.innerHTML = text
  return textarea.value
}

// 코드 블록 내 연속 공백을 &nbsp;로 변환하는 함수
const preserveSpacesInCode = (code: string): string => {
  // 연속된 공백(2개 이상)을 &nbsp;로 변환
  // 첫 번째 공백은 일반 공백으로 유지하고, 나머지는 &nbsp;로 변환
  return code.replace(/([^\S\n])([^\S\n]+)/g, (match, firstSpace, spaces) => {
    return firstSpace + '&nbsp;'.repeat(spaces.length)
  })
}

// HTML 이스케이프 헬퍼 함수
const escapeHtml = (text: string): string => {
  if (typeof document === 'undefined') {
    // SSR 환경에서도 작동하도록
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;')
  }
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

// Marked 설정 및 커스텀 렌더러
const renderer = new marked.Renderer()

// 코드 블록 렌더러 커스터마이징
renderer.code = (code: string, language?: string) => {
  // HTML 엔티티가 포함되어 있을 수 있으므로 디코딩
  let decodedCode = code
  if (code.includes('&lt;') || code.includes('&gt;') || code.includes('&quot;') || code.includes('&amp;')) {
    try {
      decodedCode = decodeHtmlEntities(code)
    } catch (e) {
      // 디코딩 실패 시 원본 사용
      decodedCode = code
    }
  }
  
  // HTML 코드 블록은 Prism.js를 사용하지 않고 직접 처리 (왜곡 방지)
  if (language && language.toLowerCase() === 'html') {
    // HTML 코드 블록: 이미 디코딩된 코드를 안전하게 이스케이프하여 표시
    // 만약 여전히 HTML 엔티티가 있다면 추가 디코딩
    let finalCode = decodedCode
    if (decodedCode.includes('&lt;') || decodedCode.includes('&gt;')) {
      // 아직 HTML 엔티티가 남아있다면 디코딩
      finalCode = decodeHtmlEntities(decodedCode)
    }
    
    // 최종적으로 안전하게 이스케이프
    let escapedCode = finalCode
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
    
    // 연속 공백을 &nbsp;로 변환
    escapedCode = preserveSpacesInCode(escapedCode)
    
    return `<pre class="language-html"><code class="language-html">${escapedCode}</code></pre>`
  }
  
  if (typeof window !== 'undefined' && Prism && language) {
    const prismLang = language.toLowerCase()
    
    // Prism이 지원하는 언어인지 확인 (HTML 제외)
    if (Prism.languages[prismLang]) {
      try {
        // Prism.highlight는 원본 문자열을 받아야 하므로 디코딩된 코드 사용
        let highlightedCode = Prism.highlight(decodedCode, Prism.languages[prismLang], prismLang)
        // Prism이 생성한 HTML에서 code 태그 내부의 공백 변환
        highlightedCode = highlightedCode.replace(/([^\S\n])([^\S\n]+)/g, (match, firstSpace, spaces) => {
          return firstSpace + '&nbsp;'.repeat(spaces.length)
        })
        return `<pre class="language-${prismLang}"><code class="language-${prismLang}">${highlightedCode}</code></pre>`
      } catch (e) {
        console.error('Prism highlighting error:', e)
        // 에러 발생 시 기본 렌더링
        let escapedCode = decodedCode.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        escapedCode = preserveSpacesInCode(escapedCode)
        return `<pre class="language-${prismLang}"><code class="language-${prismLang}">${escapedCode}</code></pre>`
      }
    } else {
      // 지원하지 않는 언어는 기본 렌더링
      let escapedCode = decodedCode.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      escapedCode = preserveSpacesInCode(escapedCode)
      return `<pre class="language-${prismLang}"><code class="language-${prismLang}">${escapedCode}</code></pre>`
    }
  }
  
  // Prism이 없거나 언어가 없으면 기본 렌더링
  let escapedCode = decodedCode.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  escapedCode = preserveSpacesInCode(escapedCode)
  const langClass = language ? ` class="language-${language}"` : ''
  return `<pre><code${langClass}>${escapedCode}</code></pre>`
}

// 인라인 코드 렌더러 커스터마이징
renderer.codespan = (code: string) => {
  // HTML 엔티티가 이미 인코딩되어 있을 수 있으므로 먼저 디코딩
  let decodedCode = code
  if (code.includes('&lt;') || code.includes('&gt;') || code.includes('&quot;') || code.includes('&amp;')) {
    try {
      decodedCode = decodeHtmlEntities(code)
    } catch (e) {
      decodedCode = code
    }
  }
  // 디코딩된 코드를 다시 안전하게 이스케이프
  const escapedCode = decodedCode
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
  return `<code>${escapedCode}</code>`
}

// marked v11+ 부터 mangle/headerIds 옵션은 default false 로 변경되어 MarkedOptions 에서 제거됨.
// (Phase 3 vue-tsc 2.x 부채 정리 — TS2353 해소, 동작 변화 없음)
marked.setOptions({
  breaks: true, // 줄바꿈을 <br>로 변환
  gfm: true, // GitHub Flavored Markdown 지원
  renderer: renderer
})

/**
 * 메시지 내용을 마크다운에서 HTML로 변환하는 composable 함수
 */
export function useMessageFormatting() {
  const formatMessage = (content: string, messageId: string | number, citations?: string[]): string => {
    if (!content) return ''
    
    try {
      // AI 응답에서 코드 블록 내부의 HTML 엔티티를 먼저 디코딩
      // 마크다운 코드 블록 (```language\ncode\n```) 패턴 찾기
      // HTML 코드 블록은 별도 처리 (language가 html인 경우)
      let processedContent = content.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, codeBlock) => {
        const language = lang ? lang.toLowerCase().trim() : ''
        
        // HTML 코드 블록의 경우: HTML 엔티티 디코딩하지 않고 그대로 유지 (렌더러에서 처리)
        if (language === 'html') {
          return match // 원본 그대로 반환 (렌더러에서 처리)
        }
        
        // 다른 언어 코드 블록: HTML 엔티티 디코딩
        const decodedCode = codeBlock
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&quot;/g, '"')
          .replace(/&#39;/g, "'")
          .replace(/&#x27;/g, "'")
          .replace(/&#x2F;/g, '/')
          .replace(/&amp;/g, '&')
          .replace(/&nbsp;/g, ' ')
        
        // 코드 블록을 원래 형태로 복원
        return lang ? `\`\`\`${lang}\n${decodedCode}\n\`\`\`` : `\`\`\`\n${decodedCode}\n\`\`\``
      })
      
      // 인라인 코드 블록 (`code`) 패턴 찾기 - HTML 엔티티 디코딩 (렌더러에서 다시 이스케이프)
      processedContent = processedContent.replace(/`([^`]+)`/g, (match, code) => {
        // 인라인 코드 내부의 HTML 엔티티 디코딩 (렌더러에서 다시 안전하게 이스케이프됨)
        const decodedCode = code
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&quot;/g, '"')
          .replace(/&#39;/g, "'")
          .replace(/&#x27;/g, "'")
          .replace(/&#x2F;/g, '/')
          .replace(/&amp;/g, '&')
        return `\`${decodedCode}\``
      })
      
      // marked의 커스텀 렌더러가 이미 Prism 구문 강조를 적용
      let html = marked.parse(processedContent) as string
      
      // HTML 코드 블록은 이미 커스텀 렌더러에서 올바르게 이스케이프되었으므로 추가 처리 불필요
      // 다른 언어 코드 블록에 대해서만 추가 처리 (필요시)
      
      // Perplexity citation 번호 [1], [2] 등을 클릭 가능한 링크로 변환
      if (citations && citations.length > 0) {
        // [1], [2], [10] 등의 패턴을 찾아서 클릭 가능한 링크로 변환
        html = html.replace(/\[(\d+)\]/g, (match, num) => {
          const index = parseInt(num) - 1
          if (index >= 0 && index < citations.length) {
            // citation 번호를 클릭하면 해당 출처로 스크롤
            const citationUrl = citations[index].replace(/"/g, '&quot;')
            return `<a href="#citation-${messageId}-${num}" class="citation-number" data-citation-id="citation-${messageId}-${num}" title="${citationUrl}">[${num}]</a>`
          }
          return match
        })
      }
      
      // 테이블에 Bootstrap 클래스 추가
      html = html.replace(/<table>/g, '<table class="markdown-table table table-bordered table-striped table-hover">')
      html = html.replace(/<thead>/g, '<thead class="table-light">')
      
      // 코드 블록에 클래스 추가 및 스타일 개선 (Prism이 처리하지 않은 경우)
      html = html.replace(/<pre><code(?!\s+class="language-)/g, '<pre class="markdown-code-block"><code class="markdown-code"')
      html = html.replace(/<code(?!\s+class="language-)(?!\s+class="markdown-)/g, '<code class="markdown-inline-code"')
      
      // 헤딩에 클래스 추가
      html = html.replace(/<h1>/g, '<h1 class="markdown-heading markdown-h1">')
      html = html.replace(/<h2>/g, '<h2 class="markdown-heading markdown-h2">')
      html = html.replace(/<h3>/g, '<h3 class="markdown-heading markdown-h3">')
      html = html.replace(/<h4>/g, '<h4 class="markdown-heading markdown-h4">')
      html = html.replace(/<h5>/g, '<h5 class="markdown-heading markdown-h5">')
      html = html.replace(/<h6>/g, '<h6 class="markdown-heading markdown-h6">')
      
      // 리스트에 클래스 추가
      html = html.replace(/<ul>/g, '<ul class="markdown-list markdown-ul">')
      html = html.replace(/<ol>/g, '<ol class="markdown-list markdown-ol">')
      html = html.replace(/<li>/g, '<li class="markdown-list-item">')
      
      // 단락에 클래스 추가 및 간격 개선
      html = html.replace(/<p>/g, '<p class="markdown-paragraph">')
      
      // blockquote 스타일 개선
      html = html.replace(/<blockquote>/g, '<blockquote class="markdown-blockquote">')
      
      // 링크에 클래스 추가
      html = html.replace(/<a href=/g, '<a class="markdown-link" href=')
      
      // 강조 텍스트 개선
      html = html.replace(/<strong>/g, '<strong class="markdown-strong">')
      html = html.replace(/<em>/g, '<em class="markdown-em">')
      
      // hr 스타일 개선
      html = html.replace(/<hr>/g, '<hr class="markdown-hr">')
      
      // DOMPurify로 XSS 방지 (안전한 HTML만 허용)
      if (typeof window !== 'undefined') {
        // 코드 블록을 임시로 마스킹하여 DOMPurify가 건드리지 않도록 함
        const codeBlockPlaceholders: string[] = []
        html = html.replace(/<pre[^>]*><code[^>]*>[\s\S]*?<\/code><\/pre>/gi, (match) => {
          const placeholder = `__CODE_BLOCK_${codeBlockPlaceholders.length}__`
          codeBlockPlaceholders.push(match)
          return placeholder
        })
        html = DOMPurify.sanitize(html, {
          ALLOWED_TAGS: [
            'p', 'br', 'strong', 'em', 'u', 's', 'code', 'pre',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'blockquote',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'a', 'img',
            'hr', 'div', 'span'
          ],
          ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'class', 'target', 'rel', 'id', 'data-citation-id'],
          ALLOW_DATA_ATTR: true,
          KEEP_CONTENT: true,
          FORBID_TAGS: [],
          FORBID_ATTR: []
        })
        
        // 코드 블록을 원래대로 복원하고, code 태그 내부의 공백 변환
        codeBlockPlaceholders.forEach((codeBlock, index) => {
          // code 태그 내부의 연속 공백을 &nbsp;로 변환
          const processedCodeBlock = codeBlock.replace(/<code[^>]*>([\s\S]*?)<\/code>/gi, (codeMatch: string, codeContent: string) => {
            // 연속된 공백(2개 이상)을 &nbsp;로 변환
            const processed = codeContent.replace(/([^\S\n])([^\S\n]+)/g, (_spaceMatch: string, firstSpace: string, spaces: string) => {
              return firstSpace + '&nbsp;'.repeat(spaces.length)
            })
            return codeMatch.replace(codeContent, processed)
          })
          html = html.replace(`__CODE_BLOCK_${index}__`, processedCodeBlock)
        })
        
        // 인라인 code 태그 내부의 공백도 변환 (pre로 감싸진 code는 이미 처리되었으므로 제외)
        html = html.replace(/<code[^>]*>([\s\S]*?)<\/code>/gi, (codeMatch: string, codeContent: string) => {
          // pre 태그로 감싸진 code는 이미 처리되었으므로 제외
          if (codeMatch.includes('<pre') || codeMatch.includes('</pre>')) {
            return codeMatch
          }
          // 인라인 code 태그 내부의 연속 공백 변환
          const processed = codeContent.replace(/([^\S\n])([^\S\n]+)/g, (_spaceMatch: string, firstSpace: string, spaces: string) => {
            return firstSpace + '&nbsp;'.repeat(spaces.length)
          })
          return codeMatch.replace(codeContent, processed)
        })
      } else {
        // DOMPurify를 사용하지 않는 경우에도 code 태그 내부 공백 변환
        html = html.replace(/<code[^>]*>([\s\S]*?)<\/code>/gi, (codeMatch: string, codeContent: string) => {
          const processed = codeContent.replace(/([^\S\n])([^\S\n]+)/g, (_spaceMatch: string, firstSpace: string, spaces: string) => {
            return firstSpace + '&nbsp;'.repeat(spaces.length)
          })
          return codeMatch.replace(codeContent, processed)
        })
      }
      
      return html
    } catch (error) {
      console.error('Error parsing markdown:', error)
      // 에러 발생 시 기본 텍스트 반환
      return escapeHtml(content)
    }
  }

  return {
    formatMessage
  }
}