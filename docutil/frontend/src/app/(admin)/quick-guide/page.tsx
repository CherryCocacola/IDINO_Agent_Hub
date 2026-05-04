"use client";

import { BookOpen, FileText, Search, MessageSquare, Settings } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function QuickGuidePage() {
  const guides = [
    {
      icon: FileText,
      title: "문서 업로드",
      description: "PDF, DOCX, TXT 등 다양한 형식의 문서를 업로드하고 관리합니다.",
      steps: [
        "문서 관리 메뉴로 이동",
        "프로젝트/보드/폴더 선택",
        "'문서 업로드' 버튼 클릭",
        "파일 선택 후 업로드",
      ],
    },
    {
      icon: Search,
      title: "검색 범위 설정",
      description: "검색할 문서의 범위를 지정하여 정확한 검색 결과를 얻습니다.",
      steps: [
        "검색 범위 설정 메뉴로 이동",
        "'새 검색 범위' 버튼 클릭",
        "포함할 문서/폴더 선택",
        "검색 방식 설정 후 저장",
      ],
    },
    {
      icon: MessageSquare,
      title: "AI 채팅",
      description: "업로드된 문서를 기반으로 AI와 대화하며 정보를 검색합니다.",
      steps: [
        "채팅 메뉴로 이동",
        "검색 범위 선택 (선택사항)",
        "질문 입력",
        "AI 응답 확인 및 출처 검토",
      ],
    },
    {
      icon: Settings,
      title: "API 키 관리",
      description: "LLM API 키를 등록하고 관리합니다.",
      steps: [
        "API 키 메뉴로 이동",
        "'키 등록' 버튼 클릭",
        "LLM 제공자 선택",
        "API 키 입력 후 등록",
      ],
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-foreground text-2xl font-bold">퀵 가이드</h1>
        <p className="text-muted-foreground mt-1 text-sm">시스템 사용 방법을 빠르게 익혀보세요</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {guides.map((guide) => (
          <Card key={guide.title}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <guide.icon className="text-primary h-5 w-5" />
                {guide.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground mb-4 text-sm">{guide.description}</p>
              <ol className="space-y-2 text-sm">
                {guide.steps.map((step, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="bg-primary/10 text-primary flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-medium">
                      {index + 1}
                    </span>
                    {step}
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="text-primary h-5 w-5" />
            추가 도움말
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">
            더 자세한 사용 방법은{" "}
            <a href="/help" className="text-primary hover:underline">
              도움말
            </a>{" "}
            페이지를 참조하세요. 문제가 발생한 경우 시스템 관리자에게 문의하세요.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
