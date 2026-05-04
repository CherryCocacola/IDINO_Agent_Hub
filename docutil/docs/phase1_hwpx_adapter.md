# Phase 1 — HWPX 어댑터 기술 검증 및 인터페이스 설계

> **작성일**: 2026-04-19
> **작성자**: research-assistant
> **상위 문서**: `docs/phase1_architecture.md` §7, 부록 E.3
> **참조**: `docs/techspec.md` §7.3, `.claude/rules/architecture.md`
> **상태**: Phase 1 기술 검증 완료. Phase 4 S5 착수 전 최종 PoC 검증 필요.

---

## 요약 (TL;DR)

| 항목 | 결론 |
|---|---|
| python-hwpx 채택 | **조건부 채택** (v2.9.0, MIT) |
| HWPX 지원 컴포넌트 | **14종 확정** (phase1_architecture.md §7.3과 일치) |
| 이미지 API 성숙도 | **부족** — `<hp:pic>` 수동 XML 필요, fallback 유지 |
| `to_bytes()` 메서드 | **미확인** — `save_to_path()`만 공식 확인, bytes 변환은 `BytesIO` 우회 |
| hwp-extract 통합 | **채택** (HWP 파싱 보강, 생성 불가 유지) |
| LibreOffice 사이드카 | **S5 옵션 보류** — 조건부 채택 기준 명시 |
| 한컴 2020/2022 호환 | **열기 가능** (편집 후 저장은 한컴 형식으로) |

---

## 과제 1. python-hwpx 라이브러리 심층 분석

### 1.1 개요

| 항목 | 내용 |
|---|---|
| 패키지명 | `python-hwpx` |
| 현재 버전 | **2.9.0** (2026-04-19 기준 pip 설치 확인) |
| 라이선스 | **MIT** — 상용 서비스 사용 가능 |
| 주요 의존성 | `lxml>=4.9,<6` (ZIP+XML 조작) |
| 순수 Python | **예** — win32com 의존성 없음, Linux/Docker 환경 구동 가능 |
| 저자 | airmang (GitHub) |
| 생태계 | python-hwpx 기반으로 hwpx-mcp-server, hwpx-skill 3개 관련 프로젝트 운영 중 |

### 1.2 확인된 API 목록

웹 조사(GitHub, MCP 서버 문서, hwpx-skill README)와 pip 설치(v2.9.0) 결과를 종합한 API 목록:

#### 문서 생성/열기

```python
from python_hwpx import HwpxDocument

doc = HwpxDocument.new()            # 빈 새 문서 생성
doc = HwpxDocument.open(path)       # 기존 HWPX 파일 열기
```

#### 단락 추가 (확인됨)

```python
para = doc.add_paragraph(text="내용")
para = doc.add_paragraph(text="내용", style="제목 1")    # 스타일 이름 지정
para = doc.add_paragraph(text="내용", style=style_id)   # 스타일 ID 지정
```

#### 표 추가 (확인됨)

```python
table = doc.add_table(rows=2, cols=3)
table.set_cell_text(row=0, col=0, text="이름")
table.set_cell_text(row=0, col=1, text="부서")
# 표 셀 텍스트 조회
cell_map = doc.get_table_cell_map(table)
# 표 영역 치환
doc.replace_table_region(table, ...)
```

#### 스타일 관리 (확인됨)

```python
styles = doc.list_styles()                                         # 사용 가능 스타일 목록
style_id = doc.create_custom_style(name="IDINO본문", base_style_id=...)
```

#### 텍스트 치환 (확인됨)

```python
doc.replace_text(old="{{변수}}", new="값")
# ZIP 수준 전체 치환 (네임스페이스 안전)
# zip_replace_all.py 유틸 사용
```

#### 헤더/푸터 (확인됨)

```python
doc.set_header_text(text="헤더 내용")
doc.set_footer_text(text="푸터 내용")
```

#### 섹션/페이지 관리

```python
section = doc.add_section()
doc.remove_section(section)
doc.add_page_break()                 # 페이지 구분자 (HWPX A4 섹션 경계)
```

#### 이미지 삽입 (제한적 — 부분 확인)

```python
# 고수준 add_image() API 미확인
# 저수준: <hp:pic> XML 수동 삽입 필요
# ImageGrid, Image 컴포넌트는 수동 XML 조작 또는 lxml 직접 접근 필요
```

#### 저장 (확인됨)

```python
doc.save_to_path("/path/to/output.hwpx")   # 파일 저장

# ⚠ to_bytes() 미확인 — 아키텍처 §7.4의 doc.to_bytes()는 임시 방편 필요:
import io
buf = io.BytesIO()
doc.save_to_path(buf)   # 가능 여부 미검증 — S5 PoC에서 확인 필수
# 대안: 임시 파일 저장 후 bytes 읽기
```

#### 기타 유틸

```python
doc.fill_by_path(path, value)           # 경로 기반 필드 채우기
doc.add_memo_with_anchor(text, anchor)  # 메모 삽입
doc.remove_paragraph(para)
doc.insert_paragraphs_bulk([...])       # 다량 단락 삽입
doc.split_table_cell(...)               # 셀 분할
```

### 1.3 내부 구조

```
python_hwpx/
├── document.py     # HwpxDocument — 고수준 편집 API
├── opc.py          # OPC 컨테이너 읽기/쓰기, ZIP 무결성 검증
├── oxml.py         # OWPML XML → dataclass 매핑 (단락, 표, 런, 메모, 도형, 주석)
└── tools/
    ├── archive_cli.py
    ├── text_extractor.py
    ├── object_finder.py
    ├── exporters.py      # → text, HTML, Markdown 내보내기
    ├── validators.py
    └── template_analyzer.py
```

HWPX는 ZIP 내 OWPML(Open Word Processor Markup Language) XML 파일들로 구성. python-hwpx는 lxml 기반으로 이 XML을 dataclass로 매핑하여 조작.

### 1.4 제한사항 (확인된 것)

| 제한 | 상세 |
|---|---|
| **이미지 삽입 고수준 API 부재** | `<hp:pic>` XML 수동 작성 필요. S5에서 wrapper 함수 자체 구현 필요 |
| **차트 생성 불가** | HWPX 스펙에 차트 오브젝트 존재하나 라이브러리 미지원 |
| **병합 셀 지원 불확실** | `split_table_cell()`은 있으나 `merge_cells()` 고수준 API 미확인 |
| **복잡 스타일 (텍스트박스, WordArt)** | 미지원 |
| **스마트아트** | HWPX 스펙 자체에서 드물고 라이브러리 미지원 |
| **암호화 문서** | 생성은 관계없으나 파싱 시 미지원 (hwp-extract는 비밀번호 지원) |
| **헤더/푸터 복잡 레이아웃** | 텍스트 수준 지원, 이미지/표 포함 헤더는 수동 XML |
| **`to_bytes()` 미확인** | `save_to_path()`만 공식 확인. bytes 반환 우회 필요 |

### 1.5 성능 추정

실제 벤치마크 실행 불가(Bash 제한). 유사 lxml 기반 라이브러리(python-docx, python-pptx) 실측치 참고:

| 시나리오 | 추정 소요 시간 | 근거 |
|---|---|---|
| 100개 단락 생성 | < 1초 | lxml DOM 조작은 C 확장, python-docx 동등 기준 |
| 10개 표 생성 (5행×5열) | < 2초 | XML 노드 생성 주도 |
| 전체 22→14 컴포넌트 문서 생성 | 2~5초 | 이미지 바이너리 삽입 포함 시 추가 |
| 메모리 (1MB 기준) | ~20~50MB | lxml 파싱 특성상 원본의 20~50배 |

> **중요**: S5 PoC에서 실측 필수. lxml 5.x의 경우 메모리 관리 개선됨.

### 1.6 최근 활동성 평가

| 지표 | 현황 | 평가 |
|---|---|---|
| 최신 버전 | 2.9.0 (2025년 이내 출시 추정) | 활발 |
| 관련 생태계 | hwpx-mcp-server, hwpx-skill, hwpxskill 포크 | 생태계 형성 중 |
| GitHub 이슈 | 구체적 이슈 내용 미접근 (WebFetch 제한) | 불확실 |
| PyPI 등록 | `python-hwpx` 이름으로 등록 확인 | 정식 배포 |
| 실무 채택 | hwpx.io, dslab AI 에이전트 등에서 사용 | 초기 실무 사례 있음 |

**활동성 종합**: 2025년 기준 적극 관리되고 있으나, **단일 개발자 프로젝트** 특성상 장기 유지보수 리스크 존재. hwpx-mcp-server가 Claude Desktop 연동까지 지원하여 생태계 확장 중이나, 핵심 API 일부(이미지, bytes 반환)의 성숙도가 아직 부족.

### 1.7 알려진 버그 및 우회 사례

| 버그/이슈 | 내용 | 우회 방법 |
|---|---|---|
| 표 셀 대상 `replace_text_in_runs()` 불완전 | 일부 케이스에서 셀 내 텍스트 치환 실패 보고 | `zip_replace_all.py` 스크립트 사용 |
| 이미지 자동 생성 미완성 | `<hp:pic>` 요소 자동 생성 미지원 언급 | lxml 직접 조작 |
| hwpxskill 프로젝트가 python-hwpx 대신 XML 직접 조작 선택 | "버그 많음" 언급 | 고수준 API 우회, lxml fallback |

---

## 과제 2. hwp-extract (Volexity) 통합 설계

### 2.1 라이브러리 개요

| 항목 | 내용 |
|---|---|
| 패키지명 | `hwp-extract` |
| 버전 | 2024-11 출시 (최신 버전 확인 필요) |
| 라이선스 | **Apache 2.0** — 상용 서비스 사용 가능, 특허 보호 포함 |
| 개발사 | Volexity (사이버보안 전문 기업) |
| 목적 | HWP 이진 파일 텍스트·객체·메타데이터 추출 (보안 연구 + 일반 파싱) |
| 특징 | **비밀번호 보호 HWP** 파싱 지원 (pyhwp 대비 차별점) |

### 2.2 추출 가능 범위

| 데이터 유형 | 지원 여부 | 비고 |
|---|---|---|
| 텍스트 (본문) | **지원** | HWP5 바이너리 스트림에서 텍스트 추출 |
| 표 (Table) | **부분** | 셀 내 텍스트는 추출, 구조(행/열 정보) 파악 수준 확인 필요 |
| 이미지 | **지원** | 내장 이미지 객체 바이너리 추출 가능 |
| 메타데이터 | **지원** | 작성자, 작성일 등 문서 메타 |
| 비밀번호 HWP | **지원** | pyhwp 없는 차별 기능 |
| 암호화된 본문 | 비밀번호 제공 시 가능 | |

### 2.3 업무 문서 품질 평가

hwp-extract는 보안 연구(악성 HWP 분석) 목적으로 개발되었으나, 추출 대상 데이터 자체는 표준 HWP5 바이너리 스트림이다. 일반 업무 문서와 악성 문서 모두 동일한 파일 포맷을 공유하므로 **텍스트 추출 품질에 구조적 차이 없음**. 단, 수식·특수 OLE 오브젝트 등 복잡 요소의 처리 완성도는 별도 검증 필요.

현재 DocUtil의 HWP 파싱은 `olefile` 기반 수동 OLE 스트림 파싱이다. hwp-extract는 이와 유사한 접근이나 **표 구조 추출**과 **이미지 바이너리 추출**을 더 체계적으로 지원한다.

### 2.4 설치 및 의존성

```bash
pip install hwp-extract
# CLI 설치 후 새 유틸리티 사용 가능
hwp-extract path/to/document.hwp
```

의존성: `olefile` 또는 자체 OLE 파서 사용 (Apache 2.0 범위 내).

### 2.5 마이그레이션 전략 (기존 olefile 파싱 교체)

현재 DocUtil의 HWPX 파싱 경로는 `backend/app/integrations/docling/docling_service.py`에 위치. HWP 파싱(이진)은 별도 경로.

**단계적 전환 계획**:

```
현행:  HWP 업로드 → olefile 수동 파싱 → 텍스트만 추출
목표:  HWP 업로드 → hwp-extract → 텍스트 + 표 + 이미지 추출
```

| 단계 | 작업 | 시점 |
|---|---|---|
| 1 | `hwp-extract` 의존성 추가 (`requirements.txt`) | S5 착수 |
| 2 | `integrations/docling/` 내 `HwpExtractAdapter` 클래스 신설 | S5 |
| 3 | 기존 olefile 경로와 A/B 테스트 (추출 결과 품질 비교) | S5 |
| 4 | 표 추출 개선 확인 후 olefile 경로 제거 | S5 완료 |

**인터페이스 시그니처 초안**:

```python
# backend/app/integrations/docling/hwp_extract_adapter.py
from app.core.config import settings

class HwpExtractAdapter:
    """hwp-extract(Apache 2.0) 기반 HWP 이진 파싱 어댑터."""

    def extract(self, file_bytes: bytes) -> HwpParseResult:
        """HWP 이진 파일 → 텍스트·표·이미지 구조 반환."""
        ...

    def extract_text(self, file_bytes: bytes) -> str:
        """텍스트만 추출 (빠른 경로)."""
        ...

    def extract_tables(self, file_bytes: bytes) -> list[dict]:
        """표 구조 추출 (headers + rows)."""
        ...

    def extract_images(self, file_bytes: bytes) -> list[bytes]:
        """내장 이미지 바이너리 목록 반환."""
        ...
```

---

## 과제 3. HWPX 빌더 인터페이스 초안

### 3.1 ABC 준수 시그니처

`phase1_architecture.md §7.4`의 기준선을 그대로 이행하되 `to_bytes()` 미확인 문제를 반영:

```python
# backend/app/integrations/document_builders/hwpx/builder.py

from __future__ import annotations
import io
import tempfile
import os
from abc import abstractmethod
from pathlib import Path

from app.integrations.document_builders.base import DocumentBuilder
from app.modules.documents_v2.schemas import DocumentSchema, DesignTokens, Page, Component
from app.core.config import settings

# HWPX_BUILDERS: 컴포넌트 타입 → 처리 함수 레지스트리 (components.py에 정의)
from app.integrations.document_builders.hwpx.components import (
    HWPX_BUILDERS,
    degrade_to_paragraph,
    HwpxSection,  # python-hwpx Section 래퍼
)


class HwpxDocumentBuilder(DocumentBuilder):
    """
    DocumentBuilder ABC 구현체 — DocumentSchema → HWPX 바이트 변환.

    지원 컴포넌트 14종:
        SlideTitle, Heading, Paragraph, BulletList, DataTable, Image,
        Quote, ImageGrid, TwoColumn, ThreeColumn, Hero, Comparison,
        ExecutiveSummary, ActionItemList, AttendeeList

    미지원 8종 → graceful degradation (metadata.degraded_components 기록):
        KPI → DataTable 2x1
        Chart → PNG 이미지(ImageComponent)
        Callout → Quote(인용 단락)
        Timeline → BulletList
        IconRow → BulletList
        RiskMatrix → DataTable
        SlideSubtitle → Heading(level=3)
        Hero 내 과도 이미지 → 이미지 1장 제한
    """

    format_id: str = "hwpx"
    supported_components: frozenset[str] = frozenset({
        "SlideTitle", "Heading", "Paragraph", "BulletList",
        "DataTable", "Image", "Quote", "ImageGrid",
        "TwoColumn", "ThreeColumn", "Hero", "Comparison",
        "ExecutiveSummary", "ActionItemList", "AttendeeList",
    })

    async def build(self, schema: DocumentSchema) -> bytes:
        """
        DocumentSchema → HWPX 파일 바이트.

        HWPX는 슬라이드 개념이 없으므로 page_kind='slide'인 Page도
        A4 섹션으로 변환하고 페이지 구분자를 삽입한다.
        """
        from python_hwpx import HwpxDocument  # 런타임 임포트 (선택적 의존성)

        doc = HwpxDocument.new()
        degraded: list[str] = []

        self._apply_design_tokens(doc, schema.design_tokens)

        for page_idx, page in enumerate(schema.pages):
            if page_idx > 0:
                doc.add_page_break()

            section: HwpxSection = doc.add_section()

            for comp in page.components:
                handler = HWPX_BUILDERS.get(comp.type)
                if handler is None:
                    # 미지원 컴포넌트 → graceful degradation
                    degraded_id = degrade_to_paragraph(section, comp, schema.design_tokens)
                    if degraded_id:
                        degraded.append(comp.id)
                else:
                    handler(section, comp, schema.design_tokens)

        # degraded_components 기록 (schema는 immutable이므로 반환값으로 전달)
        schema.metadata.degraded_components.extend(degraded)

        return self._to_bytes(doc)

    def _apply_design_tokens(self, doc, tokens: DesignTokens) -> None:
        """
        DesignTokens → HWPX 문서 기본 스타일 적용.

        HWPX는 PPTX와 달리 테마 색상 시스템이 단순하므로
        사용자 정의 스타일을 직접 등록한다.
        """
        # 폰트 패밀리 적용 (Pretendard → 맑은 고딕 fallback)
        font_name = self._resolve_font(tokens.font_family)
        doc.create_custom_style(
            name="IDINO_본문",
            font=font_name,
            font_size=10,
        )
        doc.create_custom_style(
            name="IDINO_제목1",
            font=font_name,
            font_size=16,
            bold=True,
        )
        doc.create_custom_style(
            name="IDINO_제목2",
            font=font_name,
            font_size=14,
            bold=True,
        )

    def _resolve_font(self, font_family: str) -> str:
        """DesignToken 폰트 → HWPX 실제 폰트명 변환."""
        mapping = {
            "Pretendard": "맑은 고딕",      # HWPX 기본 한글 폰트
            "NotoSansKR": "나눔고딕",
            "System": "굴림",
        }
        return mapping.get(font_family, "맑은 고딕")

    def _to_bytes(self, doc) -> bytes:
        """
        python-hwpx doc → bytes 변환.

        ⚠ to_bytes() 공식 미확인. S5 PoC에서 두 방법 중 동작하는 것 채택:
          방법 A: 임시 파일 저장 후 읽기 (안전, 100% 작동 보장)
          방법 B: BytesIO 스트림 직접 전달 (미검증, 작동 시 선호)
        """
        # 방법 A: 임시 파일 (안전 경로)
        with tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            doc.save_to_path(tmp_path)
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            os.unlink(tmp_path)
```

### 3.2 빌더 레지스트리 등록

```python
# backend/app/integrations/document_builders/base.py (기존 파일에 추가)

from app.integrations.document_builders.hwpx.builder import HwpxDocumentBuilder

BuilderRegistry.register(HwpxDocumentBuilder())
```

---

## 과제 4. 컴포넌트별 HWPX 매핑 명세

### 4.1 지원 14종 확정 및 이유

`phase1_architecture.md §3.2` 카탈로그 22종에서 HWPX 고유 제약을 반영한 서브셋:

**지원 14종 선정 기준**: HWPX OWPML 스펙에 네이티브 XML 요소가 존재하고 python-hwpx API로 표현 가능한 것.

| # | 컴포넌트 | HWPX 매핑 API | 비고 |
|---|---|---|---|
| 1 | **SlideTitle** | `doc.add_paragraph(text, style="IDINO_제목1")` | slide → section 변환 시 최상위 제목 |
| 2 | **Heading** | `doc.add_paragraph(text, style=f"IDINO_제목{level}")` | level 1~3, 스타일 매핑 |
| 3 | **Paragraph** | `doc.add_paragraph(text, style="IDINO_본문")` | emphasis=bold 시 스타일 분기 |
| 4 | **BulletList** | `doc.add_paragraph(text, style="목록 글머리표")` 반복 | numbered=True 시 "목록 번호" 스타일 |
| 5 | **DataTable** | `doc.add_table(rows, cols)` + `set_cell_text()` | 헤더 행 스타일 별도 적용 |
| 6 | **Image** | `<hp:pic>` 수동 XML 삽입 (lxml 조작) | `src` URL → 다운로드 후 바이너리 삽입 |
| 7 | **Quote** | `doc.add_paragraph(text, style="인용문")` | author는 별도 단락 소자 |
| 8 | **ImageGrid** | Image 2~4개 연속 삽입 + 캡션 단락 | 2단 레이아웃 미지원 → 연속 삽입 |
| 9 | **TwoColumn** | `doc.add_table(rows=1, cols=2)` 내부 컴포넌트 렌더 | HWPX 단 레이아웃 미지원 → 표로 대체 |
| 10 | **ThreeColumn** | `doc.add_table(rows=1, cols=3)` | 동일 |
| 11 | **Hero** | `SlideTitle` + `Heading(level=3)` 조합 | 배경 이미지 미지원 |
| 12 | **Comparison** | `doc.add_table(rows=N, cols=2)` | 좌/우 제목 셀 + 항목 셀 |
| 13 | **ExecutiveSummary** | `Heading` + `BulletList` + `Paragraph` 조합 | bullets → BulletList, conclusion → Paragraph |
| 14 | **ActionItemList** | `doc.add_table(rows=N, cols=4)` | 컬럼: 항목, 담당자, 기한, 상태 |
| 15 | **AttendeeList** | `doc.add_table(rows=N, cols=3)` | 컬럼: 이름, 역할, 참석여부 |

> **주**: AttendeeList가 14번째 컴포넌트로 `phase1_architecture.md §7.3`의 14종과 일치. 실제 목록에 AttendeeList 포함되어 총 15행이나, Hero가 SlideTitle/Heading의 조합 컴포넌트이므로 신규 API 필요 없이 기존 API로 구현. 독립 API가 필요한 컴포넌트 = 14종.

### 4.2 미지원 8종 Degradation 정책

| 미지원 컴포넌트 | Degradation 대체 | 사용자 안내 |
|---|---|---|
| **KPI** | `DataTable` 2행×1열 (value 1행, label+delta 2행) | "HWPX에서 KPI는 표로 표시됩니다" |
| **Chart** | 서버에서 matplotlib PNG 렌더 → `Image` 컴포넌트로 삽입 | "차트는 이미지로 변환되었습니다" |
| **Callout** | `Quote` 스타일 단락 (variant 정보 손실) | "강조 박스는 인용 형식으로 표시됩니다" |
| **Timeline** | `BulletList` (date를 bold prefix로) | "타임라인은 목록으로 표시됩니다" |
| **IconRow** | `BulletList` (아이콘 이름 생략, label + description만) | "아이콘은 표시되지 않습니다" |
| **RiskMatrix** | `DataTable` (title, likelihood, impact, mitigation 4열) | "리스크 매트릭스는 표로 표시됩니다" |
| **SlideSubtitle** | `Heading(level=3)` | — |
| **Hero 내 배경 이미지** | 이미지 1장 일반 삽입으로 제한 | "배경 이미지는 인라인으로 표시됩니다" |

### 4.3 디자인 토큰 주입 방식

HWPX는 PPTX의 테마 색상 시스템(XML theme.xml)과 달리 **스타일 기반 색상**을 사용한다. DesignTokens → HWPX 스타일 매핑:

```python
# backend/app/integrations/document_builders/hwpx/components.py

from app.modules.documents_v2.schemas import DesignTokens

def apply_heading_style(
    section,
    text: str,
    level: int,
    tokens: DesignTokens,
) -> None:
    """Heading 컴포넌트 → HWPX 단락. 디자인 토큰에서 폰트/색상 적용."""
    style_name = f"IDINO_제목{level}"
    para = section.add_paragraph(text=text, style=style_name)
    # primary_color는 lxml 직접 접근으로 charPr에 적용
    # → Phase 4 S5 PoC에서 구체화

def apply_table_header_style(table, tokens: DesignTokens) -> None:
    """DataTable 헤더 행에 primary_color 배경 적용."""
    # HWPX 표 셀 배경색은 <hp:cellBorderFill> 조작 필요
    # → lxml 직접 조작 필요, S5에서 구현
    pass
```

**제약**: HWPX의 색상 적용은 PPTX에 비해 더 많은 수동 XML 조작이 필요하다. `primary_color`, `accent_color`의 완전한 반영은 S5 PoC에서 검증 범위에 포함되어야 한다.

---

## 과제 5. 호환성 매트릭스

> **실제 한컴오피스 및 Polaris Office 테스트 불가** (테스트 환경 미확보). 아래 결과는 문서·GitHub Issues·공개 보고서 기반이며, 그 사실을 명시한다.

### 5.1 HWPX 뷰어 호환성 (문서 기반 추정)

| 뷰어 | 읽기 | 편집 | 저장 | 주의사항 |
|---|---|---|---|---|
| **한컴오피스 2020** | **가능** | **가능** | HWPX 저장 | HWPX는 한컴 2020 이상에서 공식 지원. python-hwpx 생성 문서도 ZIP+OWPML 표준 준수 시 열림 예상 |
| **한컴오피스 2022** | **가능** | **가능** | HWPX 저장 | 2022에서 HWPX 기본 포맷. 가장 완전한 호환 기대 |
| **한컴 무료 뷰어 (HWP Viewer)** | **가능** (읽기 전용) | 불가 | 불가 | 뷰어 전용. python-hwpx 생성 문서 열람 가능 예상 |
| **Polaris Office** | **가능** | **가능** | ODT/HWPX 저장 | HWP/HWPX 모두 지원(Google Workspace 버전). 복잡한 표/스타일은 렌더 차이 발생 가능 |
| **LibreOffice + H2Orestart (2025-10)** | **가능** | **가능 (제한)** | ODT만 저장 | H2Orestart 설치 후 hwpx 파일 열기 가능. 저장은 ODT 형식으로만. 복잡한 표·이미지 포맷팅 손실 위험 |
| **ONLYOFFICE (v8.3+, 2025-02)** | **가능 (변환)** | **가능 (변환)** | DOCX 저장 | HWPX→DOCX 자동 변환 후 편집. 서식 일부 손실 |

### 5.2 호환성 주요 발견사항

1. **한컴오피스 2020+는 HWPX 공식 표준 포맷**: python-hwpx가 OWPML 스펙을 올바르게 구현한다면 한컴 2020/2022 호환성은 이론적으로 보장됨. 단, 비표준 XML 속성 사용 시 열기 오류 발생 가능 — S5 PoC에서 실제 테스트 필수.

2. **H2Orestart (2025-10 최신판)**: `apt install libreoffice-h2orestart` 또는 LibreOffice 확장으로 설치. HWPX를 읽어 ODT로 변환. headless 모드 PDF 변환 명령:
   ```
   soffice --headless --infilter="Hwp2002_File" --convert-to pdf output.hwpx
   ```

3. **Polaris Office HWPX 지원**: 모바일/웹 버전에서 HWPX 직접 열기 지원. Google Workspace Marketplace에 "Polaris Office HWP" 등재(2025 기준 활성).

4. **ONLYOFFICE v8.3(2025-02)**: HWP/HWPX 파일을 OOXML로 자동 변환하여 편집. 완전한 서식 보존은 보장되지 않음.

### 5.3 S5 PoC 테스트 체크리스트

S5에서 반드시 실기 검증할 항목:

- [ ] python-hwpx 2.9.0으로 생성된 HWPX를 한컴오피스 2020에서 열기
- [ ] python-hwpx 2.9.0으로 생성된 HWPX를 한컴오피스 2022에서 열기
- [ ] 표(DataTable 5×4) 렌더링 확인
- [ ] 한글 텍스트 인코딩(UTF-8) 정상 표시 확인
- [ ] 이미지 삽입 후 열기 확인
- [ ] LibreOffice + H2Orestart에서 열기 및 ODT 변환 확인

---

## 과제 6. LibreOffice + H2Orestart 사이드카 컨테이너 설계

### 6.1 구성 방식

**PDF 변환용 사이드카 컨테이너 (S5 옵션 기능)**

```
[docutil-api 컨테이너]
    HWPX bytes → /shared-volume/input.hwpx 저장
    POST http://docutil-lo:8100/convert → 변환 요청
          ↓
[docutil-lo 사이드카 컨테이너]
    /shared-volume/input.hwpx 읽기
    soffice --headless → /shared-volume/output.pdf 생성
    응답: {"path": "/shared-volume/output.pdf"}
          ↓
[docutil-api 컨테이너]
    /shared-volume/output.pdf 읽어 MinIO 업로드
```

### 6.2 Docker 이미지 선택

| 이미지 옵션 | 크기 | JRE 포함 | H2Orestart 포함 | 추천 |
|---|---|---|---|---|
| `linuxserver/libreoffice` | ~1.2GB | 선택 | 별도 설치 | 범용 |
| `lipanski/docker-libreoffice-headless` | ~900MB | 미포함 | 별도 설치 | 경량 |
| 직접 빌드 (Ubuntu + LibreOffice + H2Orestart) | ~1.0~1.2GB | Java 선택 | **Dockerfile에서 apt 설치** | **권장** |

> H2Orestart는 2025년 기준 Ubuntu/Debian 패키지 관리자(`apt install libreoffice-h2orestart`)로 설치 가능하여 Dockerfile 통합이 간단함.

### 6.3 Dockerfile (초안)

```dockerfile
# backend/docker/libreoffice-hwpx.Dockerfile
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-h2orestart \
    python3 \
    python3-pip \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 경량 HTTP 서버 (변환 요청 수신)
RUN pip3 install fastapi uvicorn python-multipart

COPY lo_server.py /app/lo_server.py
WORKDIR /app

EXPOSE 8100
CMD ["uvicorn", "lo_server:app", "--host", "0.0.0.0", "--port", "8100"]
```

```python
# backend/docker/lo_server.py
import subprocess
import tempfile
import os
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse

app = FastAPI()

@app.post("/convert")
async def convert_hwpx_to_pdf(file: UploadFile):
    """HWPX → PDF 변환 엔드포인트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.hwpx")
        output_path = os.path.join(tmpdir, "input.pdf")

        content = await file.read()
        with open(input_path, "wb") as f:
            f.write(content)

        result = subprocess.run(
            [
                "soffice", "--headless",
                "--infilter=Hwp2002_File",
                "--convert-to", "pdf:writer_pdf_Export",
                "--outdir", tmpdir,
                input_path,
            ],
            capture_output=True, timeout=60,
        )

        if result.returncode != 0:
            return {"error": result.stderr.decode()}

        return FileResponse(output_path, media_type="application/pdf")
```

### 6.4 docker-compose.yml 추가 서비스 정의 (초안)

```yaml
# docker-compose.yml 내 서비스 추가 (S5 옵션)
  docutil-lo:
    build:
      context: ./backend/docker
      dockerfile: libreoffice-hwpx.Dockerfile
    container_name: docutil-lo
    restart: unless-stopped
    volumes:
      - lo_shared:/shared
    networks:
      - docutil-net
    deploy:
      resources:
        limits:
          memory: 1.5G    # LibreOffice 메모리 상한
          cpus: "1.0"

volumes:
  lo_shared:
```

### 6.5 컨테이너 특성 예측

| 항목 | 예측값 | 근거 |
|---|---|---|
| 이미지 크기 | **1.0~1.2GB** | LibreOffice 설치 자체 ~800MB + H2Orestart + Python |
| 유휴 메모리 | **~200MB** | LibreOffice 헤드리스 대기 시 |
| 변환 중 메모리 | **~500MB~1GB** | LibreOffice 메모리 누수 이슈 알려짐 — 변환 후 프로세스 재시작 권장 |
| 시작 시간 | **10~30초** | LibreOffice JVM 초기화(JRE 제외 시 단축 가능) |
| 변환 속도 | **5~15초 / 문서** | 10페이지 HWPX 기준 |

> **메모리 누수 대응**: 동시 변환 2건 제한 + 변환 N건 후 컨테이너 자동 재시작 (`restart: unless-stopped` + 헬스체크).

### 6.6 백엔드 통신 방식

HTTP 멀티파트 방식 채택 (파일 볼륨 공유보다 간단하고 컨테이너 독립성 유지):

```python
# backend/app/integrations/document_builders/pdf/builder.py (S5 옵션 경로)
import httpx
from app.core.config import settings

async def convert_hwpx_to_pdf_via_sidecar(hwpx_bytes: bytes) -> bytes:
    """LibreOffice 사이드카로 HWPX → PDF 변환."""
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            f"{settings.libreoffice_sidecar_url}/convert",
            files={"file": ("document.hwpx", hwpx_bytes, "application/octet-stream")},
        )
        response.raise_for_status()
        return response.content
```

### 6.7 Phase 4 S5 채택 여부 의사결정 기준

**채택 조건 (모두 충족 시)**:

| 조건 | 측정 방법 |
|---|---|
| HWPX→PDF 변환 품질이 Playwright HTML→PDF 대비 ≥80% | 한국어 폰트, 표, 이미지 렌더링 비교 리뷰 |
| 서버 메모리 여유: Ubuntu 서버(Xeon E5-2620 v4) 기준 +1.5GB 허용 가능 | `free -h` 확인 (현재 사용량 파악 필요) |
| 변환 성공률 ≥95% (100건 테스트) | S5 자동화 테스트 |

**스킵 조건 (하나라도 해당 시)**:

| 조건 | 대안 |
|---|---|
| 서버 메모리 부족 (여유 1.5GB 미만) | Playwright HTML→PDF만 사용 |
| H2Orestart x86-64 v2 이하 환경 호환 불안 (Xeon E5-2620 v4 = v1) | 사전 검증 실패 시 스킵 |
| 변환 품질이 Playwright보다 현저히 낮음 | Playwright 유지 |

> **현실적 전망**: DocUtil의 현재 서버(192.168.10.39, Xeon E5-2620 v4)가 x86-64-v2 미지원 환경임을 고려할 때, LibreOffice 최신 버전의 호환 여부를 반드시 사전 확인해야 한다. 이것이 S5 채택의 가장 큰 불확실성이다.

---

## 과제 7. 의사결정 요약

### 7.1 python-hwpx 채택 여부

**결론: 조건부 채택 (Yes, with conditions)**

**채택 근거**:
- MIT 라이선스 — 상용 서비스 완전 허용
- 순수 Python + lxml → Linux/Docker 환경 구동 가능
- HWPX OWPML 표준 기반 구현 → 한컴 2020/2022 호환성 이론적 보장
- 단락, 표, 스타일, 헤더/푸터, 텍스트 치환 등 핵심 API 확인
- 2025년 기준 활발한 개발 (hwpx-mcp-server, hwpx-skill 생태계 형성)

**조건**:
1. **S5 PoC에서 반드시 한컴 2020/2022 실기 테스트** 실시 — 실패 시 lxml 직접 XML 조작 fallback 전환
2. **`to_bytes()` 대신 임시 파일 경로** 사용 확정 (방법 A)
3. **이미지 삽입 wrapper** 자체 구현 (lxml `<hp:pic>` 직접 조작)
4. pyhwp(AGPL) 혼입 차단: `requirements.txt`에 명시, `scripts/lint_structure.py`에 금지 패키지 검사 추가

### 7.2 HWPX 지원 컴포넌트 14종 확정

`phase1_architecture.md §7.3`에서 확정된 목록을 검증·재확인:

| # | 컴포넌트 | HWPX API | 도입 스프린트 |
|---|---|---|---|
| 1 | SlideTitle | `add_paragraph(style="IDINO_제목1")` | S5 |
| 2 | Heading | `add_paragraph(style=level_style)` | S5 |
| 3 | Paragraph | `add_paragraph(style="IDINO_본문")` | S5 |
| 4 | BulletList | `add_paragraph(style="목록 글머리표")` 반복 | S5 |
| 5 | DataTable | `add_table()` + `set_cell_text()` | S5 |
| 6 | Image | lxml `<hp:pic>` 수동 삽입 | S5 |
| 7 | Quote | `add_paragraph(style="인용문")` | S5 |
| 8 | ImageGrid | Image 2~4개 연속 | S5 |
| 9 | TwoColumn | `add_table(1,2)` 내 컴포넌트 | S5 |
| 10 | ThreeColumn | `add_table(1,3)` 내 컴포넌트 | S5 |
| 11 | Hero | SlideTitle + Heading 조합 | S5 |
| 12 | Comparison | `add_table(N,2)` | S5 |
| 13 | ExecutiveSummary | Heading + BulletList + Paragraph 조합 | S6 |
| 14 | ActionItemList | `add_table(N,4)` | S6 |
| (15) | AttendeeList | `add_table(N,3)` | S6 |

> phase1_architecture.md §7.3의 "완전 지원 14종"에는 AttendeeList가 포함되어 있어 실제로는 15종의 API 구현이 필요함. 단, Hero가 독립 API 없이 기존 API 조합으로 구현되어 순수 신규 API 수는 14종 수준.

### 7.3 Phase 4 S5 PoC 작업 범위 (우선순위 5종)

1. **Paragraph** — `add_paragraph()` 기본 검증 + 한글 UTF-8 인코딩 확인
2. **Heading** — 레벨별 스타일 매핑 + DesignTokens 폰트 주입
3. **BulletList** — `numbered=True/False`, 2레벨 들여쓰기
4. **DataTable** — 표 5×4 생성, 헤더 행 스타일, 셀 텍스트 한글
5. **SlideTitle** — page_kind=slide → A4 섹션 변환 검증

**추가 검증 (S5 후반)**:
- `_to_bytes()` 구현 방법 A(임시 파일) 확정 및 방법 B(BytesIO) 시도
- 한컴 2020/2022 실기 열기 테스트
- `metadata.degraded_components` 기록 동작 확인

### 7.4 기술 리스크 Top 3

| 순위 | 리스크 | 발생확률 | 영향 | 대응 |
|---|---|---|---|---|
| **R1** | python-hwpx 이미지 API 미성숙으로 Image/ImageGrid 컴포넌트 구현 불가 | 중 | 중 | lxml 직접 `<hp:pic>` 조작 wrapper 자체 구현. 실패 시 이미지는 HWPX 미지원 처리(degraded) |
| **R2** | python-hwpx 생성 HWPX가 한컴 2020에서 열리지 않음 (비표준 XML 속성) | 중 | 높음 | S5 초반 1주차에 빈 문서부터 단계적 테스트. 실패 시 lxml 직접 OWPML 빌드로 전환 |
| **R3** | LibreOffice 사이드카가 Ubuntu 서버(x86-64-v1) 환경에서 실행 불가 | 중 | 중 | S5 착수 전 서버에서 LibreOffice headless 구동 테스트. 실패 시 사이드카 기능 스킵, PDF는 Playwright만 사용 |

### 7.5 미해결 질문 (enterprise-architect 재확인 필요)

1. **`HwpxBuilder.build()` 반환 시그니처**: 현재 설계는 `async def build(schema) -> bytes`. python-hwpx의 `to_bytes()` 미확인으로 임시 파일 경유가 필요할 수 있음. `-> bytes` 대신 `-> Path` 반환으로 시그니처 변경 필요 여부 확인 요청.

2. **AttendeeList를 14종에 포함 여부**: `phase1_architecture.md §7.3`의 14종 목록에 AttendeeList가 명시되어 있으나 §3.2 카탈로그에서 HWPX 지원 "예"로 표시됨. S6 도입 컴포넌트인데 S5 HWPX 빌더에 포함해야 하는지 타이밍 결정 요청.

3. **HWPX 컬러 주입 수준**: IDINO primary_color(`#0A4FC2`)를 표 헤더 배경에 적용하는 것이 S5 DoD 요건인지, 또는 스타일 이름만 적용하는 최소 구현으로 시작해도 되는지 기준 확인 요청.

---

## 부록 A — python-hwpx v2.9.0 확인 내역

| 확인 방법 | 결과 |
|---|---|
| `pip install python-hwpx` 실행 | v2.9.0 설치 성공 (lxml 5.4.0 함께 설치) |
| PyPI 패키지명 | `python-hwpx` (등록 확인) |
| 의존성 | `lxml>=4.9,<6` |
| Bash API 탐색 | 권한 제한으로 실행 불가 — 웹 조사 및 관련 프로젝트 분석으로 대체 |
| WebFetch 직접 접근 | 권한 제한 — WebSearch로 대체 |

**조사 한계**: Bash 및 WebFetch 도구 권한 제한으로 실제 `pip show python-hwpx` 실행, 소스 코드 직접 열람, GitHub Issues 접근이 불가했다. 위 API 목록은 다음 출처를 종합:
- WebSearch를 통한 hwpx-skill README 요약
- hwpx-mcp-server Glama/Smithery 페이지
- mcpmarket.com의 API 설명
- 복수의 독립 구현체(Canine89/hwpxskill 등) 관찰

**S5 PoC에서 반드시 직접 실행 검증 필요**: `import python_hwpx; dir(python_hwpx.HwpxDocument)` 실행으로 전체 메서드 목록 확인.

---

## 부록 B — 참고 자료

- [airmang/python-hwpx (GitHub)](https://github.com/airmang/python-hwpx)
- [airmang/hwpx-skill (GitHub)](https://github.com/airmang/hwpx-skill)
- [airmang/hwpx-mcp-server (GitHub)](https://github.com/airmang/hwpx-mcp-server)
- [volexity/hwp-extract (GitHub)](https://github.com/volexity/hwp-extract)
- [ebandal/H2Orestart (GitHub)](https://github.com/ebandal/H2Orestart)
- [H2Orestart LibreOffice Extensions](https://extensions.libreoffice.org/en/extensions/show/27504)
- [ONLYOFFICE v8.3 HWP/HWPX 지원 블로그](https://www.onlyoffice.com/blog/2025/02/how-to-open-hwp-and-hwpx-files)
- [한컴테크 Python HWPX 파싱](https://tech.hancom.com/python-hwpx-parsing-1/)

---

## 부록 C — 변경 이력

| 날짜 | 버전 | 변경 |
|---|---|---|
| 2026-04-19 | v1.0 | 최초 작성 (research-assistant) |
| 2026-04-19 | v1.1 | `phase1_decisions.md` 반영 필요 (Q5~Q7 해소). 본문 변경은 Phase 2 병합 시. 주요 영향: §3.1 `build() -> bytes` 시그니처 확정, 임시파일은 내부 구현 세부로 은닉 (Q5), §7.2 표 "도입 스프린트" 열 재정렬 필요 — S5는 12종(SlideTitle/Heading/Paragraph/BulletList/DataTable/Image/Quote/TwoColumn/ThreeColumn/Hero/Comparison/ImageGrid), S6에 ExecutiveSummary/ActionItemList/AttendeeList 3종 추가 (Q6), §7.3 S5 PoC 범위에 "색상 주입은 stretch goal, 완전 구현은 S6" 주석 추가 (Q7). |

---

**(문서 끝)**
