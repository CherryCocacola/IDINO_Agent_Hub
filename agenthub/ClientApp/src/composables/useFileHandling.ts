import api from '@/services/api'
import { useI18n } from 'vue-i18n'

/**
 * 파일/이미지 다운로드 및 처리 composable 함수
 */
export function useFileHandling() {
  const { t } = useI18n()

  // URL 안전하게 가져오기 (window.location 접근 보호)
  const getFileUrl = (url: string): string => {
    if (!url) return ''
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url
    }
    if (typeof window !== 'undefined' && window.location && window.location.origin) {
      return `${window.location.origin}${url}`
    }
    // window가 없는 경우 (SSR 등) 원본 URL 반환
    return url
  }

  const getAttachmentUrl = (url: string): string => {
    return getFileUrl(url)
  }

  // 파일 다운로드 URL 생성 (API 엔드포인트 사용)
  const getFileDownloadUrl = (url: string): string => {
    if (!url) return ''
    
    // 이미 전체 URL인 경우 API 엔드포인트로 변환
    if (url.startsWith('http://') || url.startsWith('https://')) {
      // URL에서 경로 부분만 추출
      try {
        const urlObj = new URL(url)
        const filePath = urlObj.pathname
        // /uploads/로 시작하는 경우 /api/files/download로 변환
        if (filePath.startsWith('/uploads/')) {
          return `/api/files/download${filePath}`
        }
      } catch {
        // URL 파싱 실패 시 그대로 반환
      }
    }
    
    // 상대 경로인 경우 API 엔드포인트로 변환
    if (url.startsWith('/uploads/')) {
      return `/api/files/download${url}`
    }
    
    // 경로가 없는 경우 원본 URL 반환
    return url
  }

  // 이미지 소스 가져오기 (preview 우선, 없으면 URL 사용)
  const getImageSource = (attachment: { type: string; url: string; name: string; preview?: string }): string => {
    // Base64 preview가 있으면 우선 사용 (서버 URL 문제 방지)
    if (attachment.preview) {
      return attachment.preview
    }
    // preview가 없으면 URL 사용
    if (attachment.url) {
      // data URL인 경우 그대로 반환 (Base64 이미지)
      if (attachment.url.startsWith('data:')) {
        return attachment.url
      }
      // 일반 URL인 경우 getAttachmentUrl 사용
      return getAttachmentUrl(attachment.url)
    }
    // 둘 다 없으면 빈 문자열 (에러 처리됨)
    return ''
  }

  // 파일 다운로드 핸들러
  const downloadFile = async (attachment: { type: string; url: string; name: string }) => {
    try {
      const downloadUrl = getFileDownloadUrl(attachment.url)
      console.log('[downloadFile] Downloading file:', { name: attachment.name, url: attachment.url, downloadUrl })
      
      // API를 통해 다운로드 (인증 토큰 포함)
      const response = await api.get(downloadUrl, {
        responseType: 'blob'
      })
      
      // Blob을 다운로드 링크로 변환
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = attachment.name || 'download'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error: any) {
      console.error('Error downloading file:', error)
      const errorMessage = t('agentChat.fileDownloadFailed', { defaultValue: '파일 다운로드에 실패했습니다' })
      alert(`${errorMessage}: ${error.response?.data?.message || error.message}`)
      
      // 실패 시 직접 링크로 시도 (fallback)
      const downloadUrl = getFileDownloadUrl(attachment.url)
      if (downloadUrl.startsWith('/api/files/download')) {
        window.open(downloadUrl, '_blank')
      }
    }
  }

  // 이미지 다운로드 핸들러
  const downloadImage = async (imageUrl: string, filename: string) => {
    try {
      const downloadFilename = filename || `image-${Date.now()}.png`
      
      // data URL인 경우 (Base64 이미지) 직접 다운로드
      if (imageUrl.startsWith('data:')) {
        // data URL에서 Base64 데이터 추출
        const base64Match = imageUrl.match(/^data:([^;]+);base64,(.+)$/)
        if (base64Match) {
          const mimeType = base64Match[1] || 'image/png'
          const base64Data = base64Match[2]
          
          // Base64를 Blob으로 변환
          const byteCharacters = atob(base64Data)
          const byteNumbers = new Array(byteCharacters.length)
          for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i)
          }
          const byteArray = new Uint8Array(byteNumbers)
          const blob = new Blob([byteArray], { type: mimeType })
          
          // Blob을 다운로드 링크로 변환
          const url = window.URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = downloadFilename
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          window.URL.revokeObjectURL(url)
          return
        }
      }
      
      // 이미지 URL이 외부 URL인 경우 백엔드 프록시를 통해 다운로드 (CORS 문제 해결, 인증 포함)
      if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
        const downloadUrl = `/api/image-generation/download?imageUrl=${encodeURIComponent(imageUrl)}&filename=${encodeURIComponent(downloadFilename)}`
        
        // api 객체를 사용하여 인증 토큰이 포함된 요청으로 이미지 다운로드
        const response = await api.get(downloadUrl, {
          responseType: 'blob'
        })
        
        // Blob을 다운로드 링크로 변환
        const blob = new Blob([response.data])
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = downloadFilename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      } else {
        // 내부 URL인 경우 api 객체를 사용하여 인증 토큰 포함
        const response = await api.get(getAttachmentUrl(imageUrl), {
          responseType: 'blob'
        })
        
        const blob = new Blob([response.data])
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = downloadFilename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      }
    } catch (error: any) {
      console.error('이미지 다운로드 실패:', error)
      alert('이미지 다운로드에 실패했습니다: ' + (error.response?.data?.message || error.message || '알 수 없는 오류'))
    }
  }

  // 이미지 로드 에러 처리
  const handleImageError = (event: Event, attachment: { type: string; url: string; name: string; preview?: string }) => {
    const img = event.target as HTMLImageElement
    // 이미 URL을 사용하고 있었는데 에러가 난 경우, preview로 재시도
    if (attachment.preview && img.src !== attachment.preview) {
      console.warn('[handleImageError] Image URL failed, trying preview:', attachment.url)
      img.src = attachment.preview
      img.onerror = null // 무한 루프 방지
    } else {
      // preview도 실패했거나 없는 경우
      console.error('[handleImageError] Image failed to load:', {
        name: attachment.name,
        url: attachment.url,
        hasPreview: !!attachment.preview
      })
      // 에러 메시지 표시
      img.alt = `이미지를 불러올 수 없습니다: ${attachment.name}`
      img.style.backgroundColor = '#f0f0f0'
      img.style.padding = '20px'
      img.style.display = 'flex'
      img.style.alignItems = 'center'
      img.style.justifyContent = 'center'
    }
  }

  return {
    getFileUrl,
    getAttachmentUrl,
    getFileDownloadUrl,
    getImageSource,
    downloadFile,
    downloadImage,
    handleImageError
  }
}