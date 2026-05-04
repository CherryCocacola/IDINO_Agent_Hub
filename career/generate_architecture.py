"""
IDINO Career 시스템 플로우 다이어그램 - 사용자 관점 간단 플로우
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# 한글 + 이모지 폰트 설정
matplotlib.rcParams['font.family'] = ['Segoe UI Emoji', 'Malgun Gothic', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(1, 1, figsize=(20, 14))
ax.set_xlim(0, 20)
ax.set_ylim(0, 14)
ax.axis('off')
fig.patch.set_facecolor('#FAFBFF')

# === 파스텔 색상 ===
BG_BLUE = '#E3F2FD'
BG_GREEN = '#E8F5E9'
BG_PURPLE = '#F3E5F5'
BG_ORANGE = '#FFF3E0'
BG_PINK = '#FCE4EC'
BG_YELLOW = '#FFFDE7'
BG_TEAL = '#E0F2F1'

BORDER_BLUE = '#90CAF9'
BORDER_GREEN = '#A5D6A7'
BORDER_PURPLE = '#CE93D8'
BORDER_ORANGE = '#FFCC80'
BORDER_PINK = '#F48FB1'
BORDER_YELLOW = '#FFF176'
BORDER_TEAL = '#80CBC4'

TEXT_DARK = '#37474F'
TEXT_SUB = '#78909C'


def draw_rounded_box(x, y, w, h, bg, border, icon, title, subtitle='', icon_size=28):
    """부드러운 라운드 박스 + 아이콘 + 제목 + 부제목"""
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                          facecolor=bg, edgecolor=border, linewidth=2, alpha=0.95)
    ax.add_patch(box)
    # 그림자 효과
    shadow = FancyBboxPatch((x + 0.05, y - 0.05), w, h, boxstyle="round,pad=0.15",
                             facecolor='#00000008', edgecolor='none', linewidth=0)
    ax.add_patch(shadow)

    cx = x + w / 2
    if subtitle:
        ax.text(cx, y + h * 0.62, icon, ha='center', va='center', fontsize=icon_size)
        ax.text(cx, y + h * 0.32, title, ha='center', va='center',
                fontsize=11, fontweight='bold', color=TEXT_DARK)
        ax.text(cx, y + h * 0.12, subtitle, ha='center', va='center',
                fontsize=8, color=TEXT_SUB)
    else:
        ax.text(cx, y + h * 0.58, icon, ha='center', va='center', fontsize=icon_size)
        ax.text(cx, y + h * 0.2, title, ha='center', va='center',
                fontsize=11, fontweight='bold', color=TEXT_DARK)


def draw_flow_arrow(x1, y1, x2, y2, label='', color='#B0BEC5'):
    """부드러운 플로우 화살표"""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=2.5,
                                connectionstyle='arc3,rad=0'))
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.3, my, label, fontsize=8, color=TEXT_SUB, va='center')


def draw_curved_arrow(x1, y1, x2, y2, label='', color='#B0BEC5', rad=0.3):
    """곡선 화살표"""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=2,
                                connectionstyle=f'arc3,rad={rad}'))
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.3, label, fontsize=8, color=TEXT_SUB, ha='center')


# =============================================
# 제목
# =============================================
ax.text(10, 13.5, 'IDINO Career', ha='center', va='center',
        fontsize=26, fontweight='bold', color='#1565C0')
ax.text(10, 13.0, 'AI 핵심역량 커리어 로드맵 시스템  |  인제대학교',
        ha='center', va='center', fontsize=11, color=TEXT_SUB)

# =============================================
# Row 1: 사용자
# =============================================
draw_rounded_box(8, 10.8, 4, 1.8, BG_BLUE, BORDER_BLUE,
                 '\U0001F468\u200D\U0001F393', '학생 (사용자)', '웹 브라우저 접속')

# =============================================
# Row 2: 프론트엔드 대시보드
# =============================================
draw_flow_arrow(10, 10.8, 10, 10.0, '', '#64B5F6')

draw_rounded_box(5.5, 8.2, 9, 1.8, BG_TEAL, BORDER_TEAL,
                 '\U0001F4CA', '역량 대시보드', '한눈에 보는 나의 역량 현황')

# =============================================
# Row 3: 주요 기능 6개 (2행 3열)
# =============================================
draw_flow_arrow(10, 8.2, 10, 7.6, '', '#80CBC4')

features_row1 = [
    (1,   5.5, BG_GREEN,  BORDER_GREEN,  '\U0001F4C8', '역량 분석',    '핵심역량 점수 측정'),
    (7.5, 5.5, BG_PURPLE, BORDER_PURPLE, '\U0001F9ED', '커리어 로드맵', 'AI 맞춤 진로 설계'),
    (14,  5.5, BG_ORANGE, BORDER_ORANGE, '\U0001F465', '졸업생 비교',  '선배와 역량 비교'),
]
features_row2 = [
    (1,   3.3, BG_PINK,   BORDER_PINK,   '\U0001F6A8', '위험 알림',    '학업 위기 조기 경보'),
    (7.5, 3.3, BG_YELLOW, BORDER_YELLOW, '\U0001F3AE', '시뮬레이션',   '진로 변경 시뮬레이션'),
    (14,  3.3, BG_BLUE,   BORDER_BLUE,   '\U0001F4AC', 'AI 코칭',     'AI 맞춤 학습 조언'),
]

for x, y, bg, border, icon, title, sub in features_row1 + features_row2:
    draw_rounded_box(x, y, 5, 1.8, bg, border, icon, title, sub, icon_size=24)

# 대시보드 -> 기능 화살표 (3개씩)
for x in [3.5, 10, 16.5]:
    draw_flow_arrow(x, 7.6, x, 7.3, '', '#B0BEC5')

# Row1 -> Row2 연결
for x in [3.5, 10, 16.5]:
    ax.plot([x, x], [5.5, 5.2], color='#CFD8DC', lw=1.5, ls='--')

# =============================================
# Row 4: 하단 인프라 (간략)
# =============================================
infra_y = 1.2
# 배경 바
infra_bg = FancyBboxPatch((1, infra_y - 0.1), 18, 1.6, boxstyle="round,pad=0.2",
                           facecolor='#ECEFF1', edgecolor='#CFD8DC', linewidth=1.5, alpha=0.6)
ax.add_patch(infra_bg)

ax.text(2, infra_y + 1.15, '\u2699\uFE0F  시스템 기반', fontsize=10,
        fontweight='bold', color=TEXT_SUB, va='center')

infra_items = [
    (2.5, '\U0001F5C4', 'PostgreSQL\n학생 데이터 저장'),
    (7,   '\u26A1',     'Redis\n빠른 캐싱'),
    (11,  '\U0001F4E8', 'Kafka\n실시간 이벤트'),
    (15,  '\U0001F916', 'OpenAI GPT\nAI 분석 엔진'),
]
for x, icon, label in infra_items:
    ax.text(x, infra_y + 0.55, icon, fontsize=18, va='center')
    ax.text(x + 0.8, infra_y + 0.55, label, fontsize=8, color=TEXT_SUB, va='center')

# 기능 -> 인프라 점선
for x in [3.5, 10, 16.5]:
    ax.plot([x, x], [3.3, infra_y + 1.5], color='#CFD8DC', lw=1, ls=':')

# =============================================
# 좌측/우측 부가 설명
# =============================================
ax.text(0.3, 9.1, '\U0001F310 Next.js 14\n     웹 프론트엔드',
        fontsize=8, color=TEXT_SUB, va='center')
ax.text(19.7, 9.1, '\U0001F6E1 Kong Gateway\n     API 보안/라우팅',
        fontsize=8, color=TEXT_SUB, va='center', ha='right')

# 18개 서비스 표시
ax.text(19.7, 4.4, '18개 마이크로서비스\nFastAPI 기반',
        fontsize=8, color=TEXT_SUB, va='center', ha='right',
        style='italic')

plt.tight_layout()
plt.savefig('D:/workspace/idino_career/idino_career_architecture.png',
            dpi=200, bbox_inches='tight', facecolor='#FAFBFF')
print("Done: idino_career_architecture.png")
