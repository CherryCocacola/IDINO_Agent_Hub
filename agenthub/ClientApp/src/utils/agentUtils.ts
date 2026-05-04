/** 흰색 계열 색상 - agent 표시 시 가독성을 위해 대체 */
const WHITE_COLORS = ['#ffffff', '#fff', '#FFFFFF', '#FFF', 'white']

/**
 * agent.colorCode가 흰색이면 대체 색상 반환 (배지/아이콘 가독성)
 * @param defaultColor colorCode가 null이거나 흰색일 때 사용할 기본 색상
 */
export function getAgentDisplayColor(
  colorCode: string | null | undefined,
  defaultColor = '#6c757d'
): string {
  if (!colorCode) return defaultColor
  const normalized = colorCode.trim().toLowerCase()
  if (WHITE_COLORS.includes(colorCode.trim()) || normalized === '#fff' || normalized === '#ffffff') {
    return defaultColor
  }
  return colorCode
}

/**
 * 배경색에 대비되는 글자색 반환 (밝은 배경 → 진한 글자, 어두운 배경 → 흰 글자)
 */
export function getAgentContrastTextColor(backgroundColor: string | null | undefined): string {
  const bg = getAgentDisplayColor(backgroundColor, '#6c757d')
  const hex = bg.replace(/^#/, '')
  if (hex.length !== 6 && hex.length !== 3) return '#212529'
  const r = hex.length === 6 ? parseInt(hex.slice(0, 2), 16) : parseInt(hex[0] + hex[0], 16)
  const g = hex.length === 6 ? parseInt(hex.slice(2, 4), 16) : parseInt(hex[1] + hex[1], 16)
  const b = hex.length === 6 ? parseInt(hex.slice(4, 6), 16) : parseInt(hex[2] + hex[2], 16)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.5 ? '#212529' : '#ffffff'
}
