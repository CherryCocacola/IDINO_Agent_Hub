"use client";

import { Search, HelpCircle, Mail, Phone } from "lucide-react";
import { useState } from "react";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface FAQItem {
  question: string;
  answer: string;
  category: string;
}

const faqData: FAQItem[] = [
  {
    category: "문서 관리",
    question: "지원되는 문서 형식은 무엇인가요?",
    answer: "PDF, DOCX, DOC, TXT, MD, HTML 형식의 문서를 지원합니다. 최대 파일 크기는 50MB입니다.",
  },
  {
    category: "문서 관리",
    question: "문서 업로드 후 처리 시간은 얼마나 걸리나요?",
    answer:
      "문서 크기와 복잡도에 따라 다르지만, 일반적으로 10페이지 문서 기준 1-2분 내에 처리됩니다.",
  },
  {
    category: "문서 관리",
    question: "업로드한 문서를 삭제하면 어떻게 되나요?",
    answer:
      "문서를 삭제하면 관련된 모든 벡터 데이터도 함께 삭제됩니다. 삭제된 문서는 복구할 수 없습니다.",
  },
  {
    category: "검색",
    question: "검색 범위란 무엇인가요?",
    answer:
      "검색 범위는 AI가 답변을 생성할 때 참조할 문서의 집합입니다. 특정 프로젝트나 폴더의 문서만 검색하도록 설정할 수 있습니다.",
  },
  {
    category: "검색",
    question: "검색 결과가 정확하지 않은 경우 어떻게 해야 하나요?",
    answer:
      "검색 범위를 좁히거나, 질문을 더 구체적으로 작성해 보세요. 또한 관련 문서가 올바르게 업로드되었는지 확인하세요.",
  },
  {
    category: "AI 채팅",
    question: "AI 응답의 출처는 어떻게 확인하나요?",
    answer: "AI 응답 하단에 '출처' 섹션에서 참조된 문서와 해당 페이지를 확인할 수 있습니다.",
  },
  {
    category: "AI 채팅",
    question: "대화 내용은 저장되나요?",
    answer:
      "네, 모든 대화 내용은 자동으로 저장됩니다. 채팅 세션 목록에서 이전 대화를 다시 확인할 수 있습니다.",
  },
  {
    category: "계정",
    question: "비밀번호를 잊어버렸어요.",
    answer:
      "로그인 페이지에서 '비밀번호 찾기'를 클릭하여 등록된 이메일로 비밀번호 재설정 링크를 받을 수 있습니다.",
  },
  {
    category: "계정",
    question: "API 키는 어떻게 관리하나요?",
    answer:
      "시스템 설정 > API 키 메뉴에서 LLM API 키를 등록하고 관리할 수 있습니다. 키는 등록 후 마스킹되어 표시됩니다.",
  },
];

export default function HelpPage() {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredFAQ = faqData.filter(
    (item) =>
      item.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.answer.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const categories = [...new Set(faqData.map((item) => item.category))];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-foreground text-2xl font-bold">도움말</h1>
        <p className="text-muted-foreground mt-1 text-sm">자주 묻는 질문과 시스템 사용 가이드</p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
        <Input
          placeholder="질문 검색..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* FAQ */}
      <div className="space-y-6">
        {categories.map((category) => {
          const categoryItems = filteredFAQ.filter((item) => item.category === category);
          if (categoryItems.length === 0) return null;

          return (
            <Card key={category}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <HelpCircle className="text-primary h-5 w-5" />
                  {category}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Accordion type="single" collapsible className="w-full">
                  {categoryItems.map((item, index) => (
                    <AccordionItem key={index} value={`item-${index}`}>
                      <AccordionTrigger className="text-left">{item.question}</AccordionTrigger>
                      <AccordionContent className="text-muted-foreground">
                        {item.answer}
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Contact */}
      <Card>
        <CardHeader>
          <CardTitle>문의하기</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground mb-4 text-sm">
            원하시는 답변을 찾지 못하셨나요? 아래 연락처로 문의해 주세요.
          </p>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <Mail className="text-muted-foreground h-4 w-4" />
              <span>support@example.com</span>
            </div>
            <div className="flex items-center gap-2">
              <Phone className="text-muted-foreground h-4 w-4" />
              <span>02-1234-5678</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
