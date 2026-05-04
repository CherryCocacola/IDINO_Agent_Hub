"use client";

/**
 * 변수 매핑 에디터 컴포넌트
 *
 * 업로드된 DOCX 템플릿의 문서 구조(문단, 표)를 시각적으로 보여주고,
 * 사용자가 각 셀/문단을 클릭하여 변수를 매핑할 수 있는 풀스크린 에디터입니다.
 *
 * 주요 기능:
 * 1. 서버에서 문서 구조(문단+표)를 조회하여 시각화
 * 2. 셀 클릭 → 우측 패널에서 변수명/타입/카테고리 설정
 * 3. 매핑 결과를 서버에 저장 (POST /templates/{id}/apply-mapping)
 */

import {
  Loader2,
  Sparkles,
  RotateCcw,
  Save,
  Trash2,
  Check,
  TableProperties,
  FileText,
  Info,
} from "lucide-react";
import { useState, useEffect, useCallback, useMemo } from "react";

import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { apiClient } from "@/lib/api/client";
import { useToast } from "@/lib/hooks/use-toast";
import { cn } from "@/lib/utils/cn";

// ─────────────────────────────────────────────
// 타입 정의 — 서버 API 응답과 내부 상태에 사용
// ─────────────────────────────────────────────

/** 문단(paragraph) 하나의 정보 */
interface Paragraph {
  index: number; // 문서 내 문단 순서 (0부터 시작)
  text: string; // 문단 텍스트 내용
  style: string; // 워드 스타일 (예: "제목 1", "본문")
  variable_name: string | null; // 이미 매핑된 변수명 (없으면 null)
}

/** 표(table)의 개별 셀 정보 */
interface TableCell {
  row: number; // 행 번호 (0부터)
  col: number; // 열 번호 (0부터)
  text: string; // 셀 텍스트 내용
  gridSpan: number; // 가로 병합 칸 수 (1이면 병합 없음)
  rowSpan: number; // 세로 병합 칸 수 (1이면 병합 없음)
  is_label: boolean; // 라벨 셀 여부 (회색 배경으로 표시)
  variable_name: string | null; // 이미 매핑된 변수명
}

/** 표의 한 행(row) 정보 */
interface TableRow {
  index: number; // 행 번호
  cells: TableCell[]; // 해당 행의 셀 목록
}

/** 표(table) 전체 정보 */
interface Table {
  index: number; // 문서 내 표 순서
  total_rows: number; // 전체 행 수
  total_cols: number; // 전체 열 수
  rows: TableRow[]; // 행 목록
}

/** 기존에 이미 정의된 변수 정보 */
interface ExistingVariable {
  name: string;
  var_type: string;
  label: string;
  category: string;
  field_type: string;
}

/** GET /templates/{id}/structure API 응답 */
interface StructureResponse {
  paragraphs: Paragraph[];
  tables: Table[];
  existing_variables: ExistingVariable[];
}

/** 사용자가 셀/문단을 클릭했을 때의 선택 정보 */
interface SelectedLocation {
  type: "table_cell" | "paragraph"; // 셀인지 문단인지
  tableIndex?: number; // 표 번호 (셀일 때만)
  row?: number; // 행 번호 (셀일 때만)
  col?: number; // 열 번호 (셀일 때만)
  paragraphIndex?: number; // 문단 번호 (문단일 때만)
  text: string; // 원본 텍스트
  currentVariable: string | null; // 현재 매핑된 변수명
}

/** 하나의 변수 매핑 정보 (로컬 상태 + 서버 전송용) */
interface VariableMapping {
  location_type: "table_cell" | "paragraph";
  table_index?: number;
  row?: number;
  col?: number;
  paragraph_index?: number;
  variable_name: string; // 변수명 (예: "장소", "회의내용")
  var_type: string; // 데이터 타입 (string, text, date 등)
  label: string; // 화면 표시 라벨
  category: string; // user_input / ai_generated / session_auto
  field_type: string; // input / textarea / date / select
}

/** 컴포넌트 Props */
interface VariableMappingEditorProps {
  templateId: string; // 편집할 템플릿 ID
  templateName: string; // 템플릿 이름 (헤더에 표시)
  open: boolean; // 다이얼로그 열림 여부 (dialog 모드에서만 사용)
  onClose: () => void; // 닫기 콜백
  onSaved: () => void; // 저장 완료 콜백 (목록 새로고침용)
  mode?: "dialog" | "inline"; // 표시 모드: dialog(전체화면 팝업) 또는 inline(부모 컴포넌트에 삽입)
}

// ─────────────────────────────────────────────
// 상수 정의 — 드롭다운 선택지
// ─────────────────────────────────────────────

/** 변수 데이터 타입 옵션 */
const VAR_TYPE_OPTIONS = [
  { value: "string", label: "문자열 (짧은 텍스트)" },
  { value: "text", label: "텍스트 (긴 내용)" },
  { value: "date", label: "날짜" },
  { value: "number", label: "숫자" },
  { value: "list", label: "목록" },
] as const;

/** 변수 카테고리 옵션 — 누가 값을 채우는지 결정 */
const CATEGORY_OPTIONS = [
  { value: "user_input", label: "사용자 입력", description: "사용자가 직접 입력" },
  { value: "ai_generated", label: "AI 생성", description: "AI가 자동 생성" },
  { value: "session_auto", label: "세션 자동", description: "로그인 정보에서 자동" },
] as const;

/** 입력 필드 유형 옵션 — 사용자에게 보여줄 입력 UI */
const FIELD_TYPE_OPTIONS = [
  { value: "input", label: "한줄 입력" },
  { value: "textarea", label: "여러줄 입력" },
  { value: "date", label: "날짜 선택" },
  { value: "select", label: "드롭다운" },
] as const;

/** 카테고리별 뱃지 색상 */
const CATEGORY_BADGE_STYLES: Record<string, string> = {
  user_input: "bg-green-100 text-green-800 border-green-200",
  ai_generated: "bg-blue-100 text-blue-900 border-blue-200",
  session_auto: "bg-orange-100 text-orange-800 border-orange-200",
};

/** 카테고리 한글 라벨 */
const CATEGORY_LABELS: Record<string, string> = {
  user_input: "사용자 입력",
  ai_generated: "AI 생성",
  session_auto: "세션 자동",
};

// ─────────────────────────────────────────────
// 유틸리티 함수
// ─────────────────────────────────────────────

/**
 * 매핑 위치를 고유 문자열 키로 변환
 * 예: "table_0_2_1" (표 0의 2행 1열), "para_3" (문단 3)
 * Map의 키로 사용하여 매핑 데이터를 빠르게 조회합니다.
 */
function locationKey(mapping: {
  location_type: string;
  table_index?: number;
  row?: number;
  col?: number;
  paragraph_index?: number;
}): string {
  if (mapping.location_type === "table_cell") {
    return `table_${mapping.table_index}_${mapping.row}_${mapping.col}`;
  }
  return `para_${mapping.paragraph_index}`;
}

// ─────────────────────────────────────────────
// 메인 컴포넌트
// ─────────────────────────────────────────────

export default function VariableMappingEditor({
  templateId,
  templateName,
  open,
  onClose,
  onSaved,
  mode = "dialog",
}: VariableMappingEditorProps) {
  const { addToast } = useToast();

  // --- 데이터 로딩 상태 ---
  const [loading, setLoading] = useState(false); // 구조 로딩 중
  const [saving, setSaving] = useState(false); // 저장 중
  const [structure, setStructure] = useState<StructureResponse | null>(null); // 서버에서 받은 문서 구조

  // --- 매핑 데이터 ---
  // Map 형태로 관리: key = locationKey, value = 매핑 정보
  const [mappings, setMappings] = useState<Map<string, VariableMapping>>(new Map());

  // --- 우측 패널: 셀/문단 선택 상태 ---
  const [selected, setSelected] = useState<SelectedLocation | null>(null);

  // --- 우측 패널: 변수 편집 폼 ---
  const [editVarName, setEditVarName] = useState(""); // 변수명
  const [editVarType, setEditVarType] = useState("string"); // 데이터 타입
  const [editCategory, setEditCategory] = useState("user_input"); // 카테고리
  const [editFieldType, setEditFieldType] = useState("input"); // 필드 유형
  const [editLabel, setEditLabel] = useState(""); // 표시 라벨

  // ─────────────────────────────────────────
  // 문서 구조 로드 — 다이얼로그가 열릴 때 실행
  // ─────────────────────────────────────────

  const loadStructure = useCallback(async () => {
    if (!templateId) return;
    setLoading(true);
    try {
      const data = await apiClient.get<StructureResponse>(`/templates/${templateId}/structure`);
      setStructure(data);

      // 서버에서 이미 매핑된 변수가 있으면 로컬 상태에 반영
      // 문단에 매핑된 변수 처리
      const initialMappings = new Map<string, VariableMapping>();

      data.paragraphs.forEach((p) => {
        if (p.variable_name) {
          // 기존 변수 목록에서 추가 정보 찾기
          const existing = data.existing_variables.find((v) => v.name === p.variable_name);
          const mapping: VariableMapping = {
            location_type: "paragraph",
            paragraph_index: p.index,
            variable_name: p.variable_name,
            var_type: existing?.var_type || "string",
            label: existing?.label || p.variable_name,
            category: existing?.category || "user_input",
            field_type: existing?.field_type || "input",
          };
          initialMappings.set(locationKey(mapping), mapping);
        }
      });

      // 표의 셀에 매핑된 변수 처리
      data.tables.forEach((table) => {
        table.rows.forEach((row) => {
          row.cells.forEach((cell) => {
            if (cell.variable_name) {
              const existing = data.existing_variables.find((v) => v.name === cell.variable_name);
              const mapping: VariableMapping = {
                location_type: "table_cell",
                table_index: table.index,
                row: cell.row,
                col: cell.col,
                variable_name: cell.variable_name,
                var_type: existing?.var_type || "string",
                label: existing?.label || cell.variable_name,
                category: existing?.category || "user_input",
                field_type: existing?.field_type || "input",
              };
              initialMappings.set(locationKey(mapping), mapping);
            }
          });
        });
      });

      setMappings(initialMappings);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "문서 구조를 불러오지 못했습니다", "error");
    } finally {
      setLoading(false);
    }
  }, [templateId, addToast]);

  // 다이얼로그가 열릴 때, 또는 인라인 모드에서 templateId가 설정될 때 구조 로드
  useEffect(() => {
    // dialog 모드: open이 true일 때만 로드
    // inline 모드: templateId가 있으면 바로 로드
    const shouldLoad = mode === "inline" ? !!templateId : open && !!templateId;
    if (shouldLoad) {
      // 상태 초기화
      setSelected(null);
      setMappings(new Map());
      setStructure(null);
      resetEditForm();
      loadStructure();
    }
  }, [open, templateId, loadStructure, mode]);

  // ─────────────────────────────────────────
  // 편집 폼 초기화
  // ─────────────────────────────────────────

  /** 우측 패널의 변수 입력 폼을 기본값으로 되돌립니다 */
  const resetEditForm = () => {
    setEditVarName("");
    setEditVarType("string");
    setEditCategory("user_input");
    setEditFieldType("input");
    setEditLabel("");
  };

  // ─────────────────────────────────────────
  // 셀/문단 클릭 핸들러
  // ─────────────────────────────────────────

  /** 표의 셀을 클릭했을 때 호출 — 우측 패널에 해당 셀 정보를 표시 */
  const handleCellClick = (tableIndex: number, cell: TableCell) => {
    // 라벨 셀은 클릭 불가 (변수를 넣을 수 없는 헤더/라벨 영역)
    if (cell.is_label) return;

    const loc: SelectedLocation = {
      type: "table_cell",
      tableIndex,
      row: cell.row,
      col: cell.col,
      text: cell.text,
      currentVariable: cell.variable_name,
    };
    setSelected(loc);

    // 이미 매핑된 변수가 있으면 해당 정보로 폼 채우기
    const key = locationKey({
      location_type: "table_cell",
      table_index: tableIndex,
      row: cell.row,
      col: cell.col,
    });
    const existing = mappings.get(key);
    if (existing) {
      setEditVarName(existing.variable_name);
      setEditVarType(existing.var_type);
      setEditCategory(existing.category);
      setEditFieldType(existing.field_type);
      setEditLabel(existing.label);
    } else {
      resetEditForm();
    }
  };

  /** 문단을 클릭했을 때 호출 — 우측 패널에 해당 문단 정보를 표시 */
  const handleParagraphClick = (paragraph: Paragraph) => {
    const loc: SelectedLocation = {
      type: "paragraph",
      paragraphIndex: paragraph.index,
      text: paragraph.text,
      currentVariable: paragraph.variable_name,
    };
    setSelected(loc);

    // 이미 매핑된 변수가 있으면 폼 채우기
    const key = locationKey({
      location_type: "paragraph",
      paragraph_index: paragraph.index,
    });
    const existing = mappings.get(key);
    if (existing) {
      setEditVarName(existing.variable_name);
      setEditVarType(existing.var_type);
      setEditCategory(existing.category);
      setEditFieldType(existing.field_type);
      setEditLabel(existing.label);
    } else {
      resetEditForm();
    }
  };

  // ─────────────────────────────────────────
  // 변수 적용/삭제 핸들러
  // ─────────────────────────────────────────

  /** "적용" 버튼 클릭 — 선택된 셀/문단에 변수 매핑을 추가 */
  const handleApplyMapping = () => {
    if (!selected) return;

    // 변수명 필수 검증
    const trimmedName = editVarName.trim();
    if (!trimmedName) {
      addToast("변수명을 입력해주세요", "error");
      return;
    }

    // 변수명에 공백이나 특수문자가 있으면 경고
    if (/[^a-zA-Z0-9가-힣_]/.test(trimmedName)) {
      addToast("변수명은 영문, 한글, 숫자, 밑줄(_)만 사용 가능합니다", "error");
      return;
    }

    // 매핑 정보 생성
    const mapping: VariableMapping = {
      location_type: selected.type,
      variable_name: trimmedName,
      var_type: editVarType,
      label: editLabel.trim() || trimmedName, // 라벨이 비어있으면 변수명 사용
      category: editCategory,
      field_type: editFieldType,
    };

    // 위치 정보 설정 (셀이면 표/행/열, 문단이면 문단 인덱스)
    if (selected.type === "table_cell") {
      mapping.table_index = selected.tableIndex;
      mapping.row = selected.row;
      mapping.col = selected.col;
    } else {
      mapping.paragraph_index = selected.paragraphIndex;
    }

    // 로컬 상태에 매핑 추가 (기존 매핑이 있으면 덮어쓰기)
    const key = locationKey(mapping);
    const newMappings = new Map(mappings);
    newMappings.set(key, mapping);
    setMappings(newMappings);

    addToast(`"${trimmedName}" 변수가 매핑되었습니다`, "success");
  };

  /** "삭제" 버튼 클릭 — 선택된 셀/문단의 매핑을 제거 */
  const handleRemoveMapping = () => {
    if (!selected) return;

    const keyObj =
      selected.type === "table_cell"
        ? {
            location_type: "table_cell" as const,
            table_index: selected.tableIndex,
            row: selected.row,
            col: selected.col,
          }
        : { location_type: "paragraph" as const, paragraph_index: selected.paragraphIndex };

    const key = locationKey(keyObj);
    const newMappings = new Map(mappings);
    newMappings.delete(key);
    setMappings(newMappings);

    // 폼 초기화
    resetEditForm();
    addToast("변수 매핑이 제거되었습니다", "info");
  };

  /** "전체 초기화" 버튼 — 모든 매핑을 지우고 처음 상태로 되돌림 */
  const handleResetAll = () => {
    if (mappings.size === 0) {
      addToast("초기화할 매핑이 없습니다", "info");
      return;
    }
    setMappings(new Map());
    setSelected(null);
    resetEditForm();
    addToast("모든 변수 매핑이 초기화되었습니다", "info");
  };

  // ─────────────────────────────────────────
  // 저장 — 서버에 매핑 전송
  // ─────────────────────────────────────────

  /** "저장" 버튼 클릭 — 매핑 데이터를 서버에 전송 */
  const handleSave = async () => {
    if (mappings.size === 0) {
      addToast("매핑된 변수가 없습니다. 변수를 추가해주세요.", "error");
      return;
    }

    setSaving(true);
    try {
      // Map → 배열로 변환하여 서버에 전송
      const mappingArray = Array.from(mappings.values());
      await apiClient.post(`/templates/${templateId}/apply-mapping`, {
        mappings: mappingArray,
      });
      addToast("변수 매핑이 저장되었습니다", "success");
      onSaved();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "변수 매핑 저장에 실패했습니다", "error");
    } finally {
      setSaving(false);
    }
  };

  // ─────────────────────────────────────────
  // 매핑된 변수 목록 (우측 패널 하단에 표시)
  // ─────────────────────────────────────────

  /** 현재 매핑된 변수를 배열로 변환 (렌더링용) */
  const mappingList = useMemo(() => Array.from(mappings.values()), [mappings]);

  // ─────────────────────────────────────────
  // 선택된 위치에 이미 매핑이 있는지 확인
  // ─────────────────────────────────────────

  /** 현재 선택된 셀/문단에 매핑이 있는지 여부 */
  const selectedHasMapping = useMemo(() => {
    if (!selected) return false;
    const keyObj =
      selected.type === "table_cell"
        ? {
            location_type: "table_cell" as const,
            table_index: selected.tableIndex,
            row: selected.row,
            col: selected.col,
          }
        : { location_type: "paragraph" as const, paragraph_index: selected.paragraphIndex };
    return mappings.has(locationKey(keyObj));
  }, [selected, mappings]);

  // ─────────────────────────────────────────
  // 렌더링
  // ─────────────────────────────────────────

  // ─────────────────────────────────────────────
  // 에디터 본문 내용 (dialog/inline 모드 공통으로 사용)
  // ─────────────────────────────────────────────

  /** 에디터 내부 콘텐츠를 별도 변수로 분리하여 dialog/inline 양쪽에서 재사용 */
  const editorContent = (
    <>
      {/* ======== 본문 영역: 좌측(문서 구조) + 우측(변수 설정) ======== */}
      <div
        className={cn(
          "flex overflow-hidden",
          // inline 모드: 높이 제한, dialog 모드: 부모에서 flex-1로 늘어남
          mode === "inline" ? "max-h-[500px]" : "min-h-0 flex-1",
        )}
      >
        {/* ── 좌측 패널: 문서 구조 시각화 (60%) ── */}
        <div className="flex min-h-0 w-[60%] flex-col border-r">
          <div className="shrink-0 border-b bg-gray-50 px-4 py-2">
            <p className="text-muted-foreground flex items-center gap-1 text-xs">
              <span title="안내">
                <Info className="h-3.5 w-3.5" />
              </span>
              셀을 클릭하면 우측에서 변수를 설정할 수 있습니다.
              <span className="ml-1 inline-block h-3 w-3 rounded border border-blue-400 bg-blue-200" />
              = 변수 매핑됨
            </p>
          </div>

          <ScrollArea className="flex-1">
            <div className="space-y-6 p-4">
              {/* 로딩 스피너 */}
              {loading && (
                <div className="flex items-center justify-center py-20">
                  <Loader2 className="text-muted-foreground h-8 w-8 animate-spin" />
                  <span className="text-muted-foreground ml-3">문서 구조를 불러오는 중...</span>
                </div>
              )}

              {/* 구조가 없는 경우 */}
              {!loading && !structure && (
                <div className="text-muted-foreground flex flex-col items-center justify-center py-20">
                  <span title="문서 없음">
                    <FileText className="mb-3 h-12 w-12 opacity-40" />
                  </span>
                  <p>문서 구조를 불러올 수 없습니다.</p>
                  <p className="mt-1 text-xs">DOCX 파일이 업로드된 템플릿인지 확인해주세요.</p>
                </div>
              )}

              {/* 구조 로드 완료 → 문단과 표를 순서대로 표시 */}
              {!loading && structure && (
                <>
                  {/* ── 문단 렌더링 ── */}
                  {structure.paragraphs.length > 0 && (
                    <section>
                      <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-gray-700">
                        <span title="문단">
                          <FileText className="h-4 w-4" />
                        </span>
                        문단 ({structure.paragraphs.length}개)
                      </h3>
                      <div className="space-y-1">
                        {structure.paragraphs.map((p) => {
                          // 이 문단에 매핑이 있는지 확인
                          const key = locationKey({
                            location_type: "paragraph",
                            paragraph_index: p.index,
                          });
                          const mapped = mappings.get(key);
                          // 현재 선택된 문단인지 확인
                          const isSelected =
                            selected?.type === "paragraph" && selected.paragraphIndex === p.index;

                          return (
                            <div
                              key={`para-${p.index}`}
                              onClick={() => handleParagraphClick(p)}
                              className={cn(
                                "cursor-pointer rounded-md border px-3 py-2 text-sm transition-all",
                                // 선택 상태: 파란 테두리 강조
                                isSelected && "ring-primary ring-2",
                                // 매핑 상태: 파란 배경
                                mapped
                                  ? "border-blue-300 bg-blue-50 hover:bg-blue-100"
                                  : "border-gray-200 bg-white hover:bg-yellow-50",
                              )}
                            >
                              <div className="flex items-center justify-between">
                                <span className="truncate text-gray-600">
                                  {p.text || "(빈 문단)"}
                                </span>
                                {/* 매핑된 변수가 있으면 뱃지 표시 */}
                                {mapped && (
                                  <Badge variant="info" className="ml-2 shrink-0 text-xs">
                                    {"{{ " + mapped.variable_name + " }}"}
                                  </Badge>
                                )}
                              </div>
                              {/* 스타일 정보 표시 */}
                              {p.style && (
                                <span className="mt-0.5 block text-xs text-gray-400">
                                  스타일: {p.style}
                                </span>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </section>
                  )}

                  {/* ── 표 렌더링 ── */}
                  {structure.tables.map((table) => (
                    <section key={`table-${table.index}`}>
                      <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-gray-700">
                        <span title="표">
                          <TableProperties className="h-4 w-4" />
                        </span>
                        표 {table.index} ({table.total_rows}행 x {table.total_cols}열)
                      </h3>
                      <div className="overflow-x-auto rounded-lg border">
                        <table className="w-full border-collapse text-sm">
                          <tbody>
                            {table.rows.map((row) => (
                              <tr key={`row-${table.index}-${row.index}`}>
                                {row.cells.map((cell) => {
                                  // rowSpan이 1보다 큰 셀이 이미 위에서 병합을 시작했다면
                                  // 이 셀은 렌더링하지 않음 (rowSpan "continue")
                                  // → 서버가 이미 continue 셀을 제외하고 보내주는 구조

                                  // 이 셀에 매핑이 있는지 확인
                                  const key = locationKey({
                                    location_type: "table_cell",
                                    table_index: table.index,
                                    row: cell.row,
                                    col: cell.col,
                                  });
                                  const mapped = mappings.get(key);
                                  // 현재 선택된 셀인지 확인
                                  const isSelected =
                                    selected?.type === "table_cell" &&
                                    selected.tableIndex === table.index &&
                                    selected.row === cell.row &&
                                    selected.col === cell.col;

                                  return (
                                    <td
                                      key={`cell-${cell.row}-${cell.col}`}
                                      colSpan={cell.gridSpan > 1 ? cell.gridSpan : undefined}
                                      rowSpan={cell.rowSpan > 1 ? cell.rowSpan : undefined}
                                      onClick={() =>
                                        !cell.is_label && handleCellClick(table.index, cell)
                                      }
                                      className={cn(
                                        "min-w-[60px] border px-2 py-1.5 transition-all",
                                        // 라벨 셀: 회색 배경, 클릭 불가
                                        cell.is_label &&
                                          "cursor-default bg-gray-100 font-medium text-gray-700",
                                        // 일반 셀 (라벨이 아닌): 클릭 가능
                                        !cell.is_label &&
                                          !mapped &&
                                          "cursor-pointer bg-white hover:bg-yellow-50",
                                        // 매핑된 셀: 파란 배경
                                        !cell.is_label &&
                                          mapped &&
                                          "cursor-pointer border-blue-300 bg-blue-50 hover:bg-blue-100",
                                        // 선택된 셀: 테두리 강조
                                        isSelected && "ring-primary ring-2 ring-inset",
                                      )}
                                    >
                                      <div className="flex items-center gap-1">
                                        {/* 셀 텍스트 */}
                                        <span
                                          className={cn(
                                            "truncate",
                                            cell.is_label ? "text-gray-700" : "text-gray-500",
                                          )}
                                        >
                                          {cell.text || (cell.is_label ? "" : "\u00A0")}
                                        </span>
                                        {/* 매핑된 변수 뱃지 */}
                                        {mapped && (
                                          <Badge
                                            variant="info"
                                            className="shrink-0 px-1.5 py-0 text-[10px]"
                                          >
                                            {"{{ " + mapped.variable_name + " }}"}
                                          </Badge>
                                        )}
                                      </div>
                                    </td>
                                  );
                                })}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </section>
                  ))}

                  {/* 문단도 표도 없는 경우 */}
                  {structure.paragraphs.length === 0 && structure.tables.length === 0 && (
                    <div className="text-muted-foreground py-16 text-center">
                      <p>문서에서 분석할 수 있는 구조가 없습니다.</p>
                    </div>
                  )}
                </>
              )}
            </div>
          </ScrollArea>
        </div>

        {/* ── 우측 패널: 변수 설정 (40%) ── */}
        <div className="flex min-h-0 w-[40%] flex-col">
          <ScrollArea className="flex-1">
            <div className="space-y-5 p-4">
              {/* ── 선택된 위치 정보 ── */}
              {selected ? (
                <>
                  {/* 위치 정보 표시 */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-semibold text-gray-800">선택된 위치</h4>
                    <div className="space-y-1 rounded-md bg-gray-50 p-3 text-sm">
                      <p className="text-gray-600">
                        <span className="font-medium text-gray-700">위치: </span>
                        {selected.type === "table_cell"
                          ? `표 ${selected.tableIndex}, ${selected.row}행 ${selected.col}열`
                          : `문단 ${selected.paragraphIndex}`}
                      </p>
                      <p className="text-gray-600">
                        <span className="font-medium text-gray-700">원본 텍스트: </span>
                        {selected.text || "(비어있음)"}
                      </p>
                    </div>
                  </div>

                  <Separator />

                  {/* ── 변수 설정 폼 ── */}
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-gray-800">변수 설정</h4>

                    {/* 변수명 입력 */}
                    <div className="space-y-1">
                      <label htmlFor="var-name" className="text-xs font-medium text-gray-600">
                        변수명 <span className="text-red-500">*</span>
                      </label>
                      <input
                        id="var-name"
                        type="text"
                        value={editVarName}
                        onChange={(e) => setEditVarName(e.target.value)}
                        placeholder="예: 장소, 회의내용, 작성일"
                        className="border-input bg-background placeholder:text-muted-foreground focus-visible:ring-ring flex h-9 w-full rounded-md border px-3 py-1 text-sm shadow-sm transition-colors focus-visible:ring-1 focus-visible:outline-none"
                      />
                    </div>

                    {/* 표시 라벨 입력 (화면에 보여줄 이름) */}
                    <div className="space-y-1">
                      <label htmlFor="var-label" className="text-xs font-medium text-gray-600">
                        표시 라벨
                        <span className="ml-1 text-gray-400">(비우면 변수명 사용)</span>
                      </label>
                      <input
                        id="var-label"
                        type="text"
                        value={editLabel}
                        onChange={(e) => setEditLabel(e.target.value)}
                        placeholder="예: 회의 장소"
                        className="border-input bg-background placeholder:text-muted-foreground focus-visible:ring-ring flex h-9 w-full rounded-md border px-3 py-1 text-sm shadow-sm transition-colors focus-visible:ring-1 focus-visible:outline-none"
                      />
                    </div>

                    {/* 데이터 타입 선택 */}
                    <div className="space-y-1">
                      <label htmlFor="var-type" className="text-xs font-medium text-gray-600">
                        데이터 타입
                      </label>
                      <select
                        id="var-type"
                        value={editVarType}
                        onChange={(e) => {
                          setEditVarType(e.target.value);
                          // 타입에 따라 필드 유형 자동 변경
                          if (e.target.value === "date") {
                            setEditFieldType("date");
                          } else if (e.target.value === "text") {
                            setEditFieldType("textarea");
                          } else {
                            setEditFieldType("input");
                          }
                        }}
                        className="border-input bg-background focus-visible:ring-ring flex h-9 w-full rounded-md border px-3 py-1 text-sm shadow-sm focus-visible:ring-1 focus-visible:outline-none"
                      >
                        {VAR_TYPE_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* 카테고리 선택 — 값을 누가 채우는지 */}
                    <div className="space-y-1">
                      <label htmlFor="var-category" className="text-xs font-medium text-gray-600">
                        카테고리
                      </label>
                      <select
                        id="var-category"
                        value={editCategory}
                        onChange={(e) => setEditCategory(e.target.value)}
                        className="border-input bg-background focus-visible:ring-ring flex h-9 w-full rounded-md border px-3 py-1 text-sm shadow-sm focus-visible:ring-1 focus-visible:outline-none"
                      >
                        {CATEGORY_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label} — {opt.description}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* 입력 필드 유형 — 사용자에게 보여줄 UI */}
                    <div className="space-y-1">
                      <label htmlFor="var-field-type" className="text-xs font-medium text-gray-600">
                        입력 필드 유형
                      </label>
                      <select
                        id="var-field-type"
                        value={editFieldType}
                        onChange={(e) => setEditFieldType(e.target.value)}
                        className="border-input bg-background focus-visible:ring-ring flex h-9 w-full rounded-md border px-3 py-1 text-sm shadow-sm focus-visible:ring-1 focus-visible:outline-none"
                      >
                        {FIELD_TYPE_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* 적용/삭제 버튼 */}
                    <div className="flex items-center gap-2 pt-2">
                      <button
                        onClick={handleApplyMapping}
                        disabled={!editVarName.trim()}
                        className={cn(
                          "inline-flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                          editVarName.trim()
                            ? "bg-blue-600 text-white hover:bg-blue-700"
                            : "cursor-not-allowed bg-gray-200 text-gray-400",
                        )}
                      >
                        <Check className="h-4 w-4" />
                        적용
                      </button>

                      {/* 이미 매핑이 있는 셀에서만 삭제 버튼 표시 */}
                      {selectedHasMapping && (
                        <button
                          onClick={handleRemoveMapping}
                          className="inline-flex items-center gap-1.5 rounded-md border border-red-200 bg-white px-3 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                          삭제
                        </button>
                      )}
                    </div>
                  </div>
                </>
              ) : (
                /* 아무것도 선택하지 않은 상태 */
                <div className="text-muted-foreground flex flex-col items-center justify-center py-12">
                  <span title="셀을 선택하세요">
                    <TableProperties className="mb-3 h-10 w-10 opacity-30" />
                  </span>
                  <p className="text-sm">좌측에서 셀이나 문단을 클릭하세요</p>
                  <p className="mt-1 text-xs">변수를 매핑할 위치를 선택합니다</p>
                </div>
              )}

              <Separator />

              {/* ── 매핑된 변수 목록 ── */}
              <div className="space-y-2">
                <h4 className="flex items-center justify-between text-sm font-semibold text-gray-800">
                  <span>매핑된 변수 ({mappingList.length}개)</span>
                </h4>

                {mappingList.length === 0 ? (
                  <p className="text-muted-foreground py-3 text-center text-xs">
                    아직 매핑된 변수가 없습니다.
                  </p>
                ) : (
                  <div className="space-y-1">
                    {mappingList.map((m) => {
                      // 각 매핑의 고유 키
                      const key = locationKey(m);
                      // 위치 설명 텍스트
                      const locLabel =
                        m.location_type === "table_cell"
                          ? `표${m.table_index} ${m.row}행${m.col}열`
                          : `문단${m.paragraph_index}`;

                      return (
                        <div
                          key={key}
                          onClick={() => {
                            // 목록 항목 클릭 시 해당 위치 선택으로 이동
                            if (m.location_type === "table_cell" && structure) {
                              const table = structure.tables.find((t) => t.index === m.table_index);
                              if (table) {
                                const row = table.rows.find((r) => r.index === m.row);
                                const cell = row?.cells.find((c) => c.col === m.col);
                                if (cell) handleCellClick(m.table_index!, cell);
                              }
                            } else if (m.location_type === "paragraph" && structure) {
                              const para = structure.paragraphs.find(
                                (p) => p.index === m.paragraph_index,
                              );
                              if (para) handleParagraphClick(para);
                            }
                          }}
                          className="flex cursor-pointer items-center justify-between rounded-md border px-2.5 py-1.5 text-sm transition-colors hover:bg-gray-50"
                        >
                          <div className="flex min-w-0 items-center gap-2">
                            <Check className="h-3.5 w-3.5 shrink-0 text-green-600" />
                            <span className="truncate font-medium">{m.variable_name}</span>
                          </div>
                          <div className="flex shrink-0 items-center gap-1.5">
                            <span className="text-xs text-gray-400">{locLabel}</span>
                            <Badge
                              className={cn(
                                "px-1.5 py-0 text-[10px]",
                                CATEGORY_BADGE_STYLES[m.category] || "bg-gray-100 text-gray-600",
                              )}
                            >
                              {CATEGORY_LABELS[m.category] || m.category}
                            </Badge>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </ScrollArea>
        </div>
      </div>

      {/* ======== 하단 액션 바 ======== */}
      <div
        className={cn(
          "flex shrink-0 items-center justify-between border-t bg-gray-50 px-6 py-3",
          // inline 모드에서는 패딩/마진 조정
          mode === "inline" && "px-4 py-2",
        )}
      >
        {/* 좌측 버튼들 */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => addToast("AI 자동 분석 기능은 추후 지원 예정입니다", "info")}
            disabled={loading || saving}
            className="inline-flex items-center gap-1.5 rounded-md border border-blue-200 bg-white px-3 py-2 text-sm font-medium text-blue-800 transition-colors hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Sparkles className="h-4 w-4" />
            AI 자동 분석
          </button>
          <button
            onClick={handleResetAll}
            disabled={loading || saving || mappings.size === 0}
            className="inline-flex items-center gap-1.5 rounded-md border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RotateCcw className="h-4 w-4" />
            전체 초기화
          </button>
        </div>

        {/* 우측: 저장 버튼 */}
        <button
          onClick={handleSave}
          disabled={saving || loading || mappings.size === 0}
          className="bg-primary text-primary-foreground hover:bg-primary/90 inline-flex items-center gap-1.5 rounded-md px-5 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          {saving ? "저장 중..." : "저장"}
        </button>
      </div>
    </>
  );

  // ─────────────────────────────────────────────
  // inline 모드: Dialog 없이 에디터 내용만 렌더링
  // 부모 컴포넌트(예: 생성 다이얼로그)에 직접 삽입됩니다.
  // ─────────────────────────────────────────────
  if (mode === "inline") {
    return (
      <div className="border-border overflow-hidden rounded-lg border">
        {/* 인라인 모드 헤더 */}
        <div className="border-b bg-white px-4 py-3">
          <h4 className="text-foreground flex items-center gap-2 text-sm font-semibold">
            <span title="변수 매핑 에디터">
              <TableProperties className="h-4 w-4 text-blue-600" />
            </span>
            변수 매핑 에디터
          </h4>
          <p className="text-muted-foreground mt-0.5 text-xs">
            문서의 셀이나 문단을 클릭하고, 우측 패널에서 변수를 설정하세요.
          </p>
        </div>
        {editorContent}
      </div>
    );
  }

  // ─────────────────────────────────────────────
  // dialog 모드: 기존 Dialog 래퍼로 감싸서 렌더링
  // ─────────────────────────────────────────────
  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        if (!isOpen) onClose();
      }}
    >
      <DialogContent
        className="flex h-[90vh] max-h-[90vh] w-[95vw] max-w-[95vw] flex-col gap-0 p-0"
        onInteractOutside={(e) => e.preventDefault()}
      >
        {/* ======== 헤더 영역 ======== */}
        <DialogHeader className="shrink-0 border-b px-6 py-4">
          <DialogTitle className="flex items-center gap-2 text-lg">
            <span title="변수 매핑 에디터">
              <TableProperties className="h-5 w-5 text-blue-600" />
            </span>
            <span className="truncate">{templateName}</span>
            <span className="text-muted-foreground font-normal">변수 매핑 에디터</span>
          </DialogTitle>
          <DialogDescription className="text-muted-foreground text-sm">
            문서의 셀이나 문단을 클릭하고, 우측 패널에서 변수를 설정하세요.
          </DialogDescription>
        </DialogHeader>

        {editorContent}
      </DialogContent>
    </Dialog>
  );
}
