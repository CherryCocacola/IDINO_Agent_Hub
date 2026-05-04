/**
 * 이미지 생성 로직 체크 composable 함수
 */
export function useImageGeneration() {
  /**
   * 서비스/모델이 이미지 생성용인지 확인
   */
  const checkImageGeneration = (
    serviceType: string | undefined,
    serviceCode: string,
    modelName: string
  ): { isImageGenerationService: boolean; isImageGenerationModel: boolean } => {
    const serviceCodeLower = serviceCode.toLowerCase()
    const modelNameLower = modelName.toLowerCase()
    
    const isImageGenerationService = 
      serviceType === 'ImageGeneration' || 
      serviceType === 'Both' ||
      serviceCodeLower.includes('dalle') ||
      (serviceCodeLower.includes('gemini') && modelNameLower.includes('image'))
    
    const isImageGenerationModel = 
      modelNameLower.includes('dall-e') ||
      modelNameLower.includes('dalle') ||
      modelNameLower.includes('imagen') ||
      modelNameLower.includes('flux') ||
      modelNameLower.includes('gen4-image') ||
      (modelNameLower.includes('gemini') && (modelNameLower.includes('image') || modelNameLower.includes('pro-image')))
    
    return {
      isImageGenerationService,
      isImageGenerationModel
    }
  }

  /**
   * 서비스/모델이 비디오 생성용인지 확인
   */
  const checkVideoGeneration = (
    serviceType: string | undefined,
    serviceCode: string,
    modelName: string
  ): { isVideoGenerationService: boolean; isVideoGenerationModel: boolean } => {
    const serviceCodeLower = serviceCode.toLowerCase()
    const modelNameLower = modelName.toLowerCase()
    
    const isVideoGenerationService = 
      serviceType === 'VideoGeneration' || 
      serviceType === 'Both'
    
    const isVideoGenerationModel = 
      modelNameLower.includes('videogeneration') ||
      modelNameLower.includes('video-generation') ||
      modelNameLower.includes('veo') ||
      modelNameLower.includes('sora') ||
      serviceCodeLower.includes('gen4-video') ||
      serviceCodeLower.includes('veo') ||
      serviceCodeLower.includes('sora')
    
    return {
      isVideoGenerationService,
      isVideoGenerationModel
    }
  }

  return {
    checkImageGeneration,
    checkVideoGeneration
  }
}