"""
LLMService — Phase 7.4 (AgentHub 단일 진입점 위임)
====================================================

Phase 7.4 변경 요약:
    - 기존: LangChain `ChatOpenAI` + OpenAI SDK `AsyncOpenAI` 직접 호출
    - 변경: `shared.common.agenthub_client.AgentHubClient` 위임
    - 사유: 통합 R2 단일 진입점 원칙. AgentHub 가 LLM 라우팅(External/Internal) +
      ApiKeyPool + PII 정책 + 사용량 추적 + Tool Calling 정책을 일괄 관리한다.

매핑 (AI_INVENTORY 기준):
    - generate_action_recommendations    → AgentCode "career-action-recommender"   (CA-3)
    - analyze_competencies               → AgentCode "career-competency-analyzer"  (CA-4)
    - chat                               → AgentCode "career-chatbot"              (CA-5, Internal/Nexus)
    - generate_semester_goals            → AgentCode "career-semester-planner"     (CA-6)
    - generate_with_tools                → AgentCode "career-actionboard-orchestrator" (CA-7, CA-8)
    - generate_with_tools_and_rag        → AgentCode "career-rag-actionboard"      (CA-9, CA-10)

호출 변경 패턴 (BEFORE / AFTER):
    BEFORE: response = await self.openai_client.chat.completions.create(model=..., messages=..., ...)
    AFTER:  response = await self._agenthub.chat(agent_code="career-...", messages=..., extra={...})
    - response 는 OpenAI ChatCompletion 형식 dict — 기존 파싱 로직 그대로 호환.

Tool Calling 처리:
    AgentHub Phase 7.1 시드된 Agent 정의에 `tools` / `tool_choice` / `response_format`
    이 사전 등록되어 있다 (`JSON_SCHEMA_ACTIONBOARD` 자동 적용). 클라이언트 코드는
    `messages` 만 보내고 AgentHub 가 OpenAI provider 로 라우팅 시 자동 적용한다.

    단, Phase 7.4 시점에 AgentHub 가 아직 도구 정의를 메시지에 동봉하지 않으므로
    호환을 위해 본 클라이언트는 `extra={"tools": TOOLS, "tool_choice": "auto"}` 를
    임시로 함께 전송한다. (Phase 5+ 에서 Agent 등록 정의로 자동 주입되면 제거.)

비-스트리밍만 사용:
    Phase 7.4 범위에서는 ai-service 내부 호출이 단발성 응답이므로 chat() 만 사용.
    스트리밍은 Phase 7.5 의 frontend → AgentHub 직결 시 도입 (AgentHubClient.chat_stream).
"""
from typing import List, Dict, Any, Optional
import json
import logging

from shared.common.agenthub_client import AgentHubClient, AgentHubError, get_agenthub_client

from ..config import get_settings
from ..tools.tool_definitions import TOOLS, SYSTEM_PROMPT, JSON_SCHEMA_ACTIONBOARD
from ..tools.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


class LLMService:
    """
    학생 커리어 도메인의 LLM 호출을 모두 AgentHub Agent 로 위임하는 서비스.

    초보자 가이드:
        - 기존에는 OpenAI 키를 들고 직접 OpenAI/Anthropic 으로 호출했지만,
          이제는 *AgentHub 라는 게이트웨이* 의 OpenAI 호환 엔드포인트로 위임한다.
        - "model" 파라미터에 OpenAI 모델명(`gpt-4o-mini`) 대신 `AgentCode`(`career-...`)
          를 넣는다. AgentHub 가 Agent 정의를 보고 실제 모델/프로바이더 로 분기.
    """

    def __init__(self, agenthub_client: Optional[AgentHubClient] = None):
        # 환경설정은 여전히 필요(OPENAI_MODEL 은 fallback 용 메타정보로만 보존,
        # temperature 같은 호출 단위 override 값 참조)
        self.settings = get_settings()
        # AgentHub 단일 진입점 — 환경변수 AGENTHUB_URL/AGENTHUB_API_KEY 로 자동 구성.
        # 테스트에서는 mock 클라이언트를 주입할 수 있도록 인자로도 받는다.
        self._agenthub = agenthub_client or get_agenthub_client()
        # Tool Calling 의 *실행* (학생/역량/동문 데이터 fetch) 은 여전히 본 서비스 내부
        self.tool_executor = ToolExecutor(self.settings)

    # ── public API ──────────────────────────────────────────────────────────

    async def generate_action_recommendations(
        self,
        student_data: Dict[str, Any],
        competency_scores: List[Dict[str, Any]],
        career_goal: str,
    ) -> List[Dict[str, Any]]:
        """학생 맞춤 액션 4건을 AgentHub `career-action-recommender` 로 생성한다."""

        # 빈 데이터 가드 — 토큰/비용 절감
        if not competency_scores:
            logger.info("No competency data available, returning empty recommendations")
            return []

        if not student_data.get('name') and not student_data.get('department_name'):
            logger.info("Incomplete student data, returning empty recommendations")
            return []

        system_prompt = """당신은 대학생 커리어 개발 전문 AI 상담사입니다.
학생의 현재 역량 점수, 이수 교과목, 비교과 활동, 목표 직업을 분석하여
가장 효과적인 액션 추천을 제공합니다.

다음 형식으로 정확히 4개의 액션을 JSON 배열로 응답하세요:
[
  {
    "id": 1,
    "title": "액션 제목",
    "description": "구체적인 설명",
    "priority": "high|medium|low",
    "deadline": "기한 (예: 2주 이내, 1개월)",
    "competency": "관련 역량명",
    "reasoning": "이 액션을 추천하는 이유",
    "icon_type": "book|users|award|briefcase"
  }
]

우선순위 기준:
- high: 역량 갭이 크고 목표 직업에 필수적인 경우
- medium: 개선이 필요하지만 시급하지 않은 경우
- low: 추가적인 성장을 위한 선택적 활동"""

        user_prompt = f"""학생 정보:
- 이름: {student_data.get('name', '학생')}
- 학과: {student_data.get('department_name', '미정')}
- 학년: {student_data.get('grade', 3)}학년
- 학점: {student_data.get('gpa', 0.0)}
- 목표 직업: {career_goal}

현재 역량 점수:
{json.dumps(competency_scores, ensure_ascii=False, indent=2)}

위 정보를 바탕으로 가장 효과적인 4개의 액션을 추천해주세요."""

        try:
            # AgentHub `career-action-recommender` Agent 호출 — Hybrid 라우팅
            response = await self._agenthub.chat(
                agent_code="career-action-recommender",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.settings.TEMPERATURE,
                max_tokens=self.settings.MAX_TOKENS,
            )

            content = response["choices"][0]["message"]["content"]

            # 코드펜스 제거 (LLM 이 ```json ... ``` 으로 감쌀 수 있음)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            actions = json.loads(content.strip())
            return actions
        except (json.JSONDecodeError, KeyError, IndexError) as ex:
            logger.warning(f"Action recommendation 응답 파싱 실패: {ex}")
            return self._get_default_recommendations()
        except AgentHubError as ex:
            logger.error(f"AgentHub action recommendation 호출 실패: {ex}")
            return self._get_default_recommendations()
        except Exception as e:
            logger.exception(f"Unexpected LLM Error: {e}")
            return self._get_default_recommendations()

    async def analyze_competencies(
        self,
        competency_scores: List[Dict[str, Any]],
        career_goal: str,
    ) -> Dict[str, Any]:
        """5대 역량 분석을 AgentHub `career-competency-analyzer` 로 수행한다."""

        system_prompt = """당신은 대학생 역량 분석 전문가입니다.
학생의 5대 핵심역량(창의역량, 융복합역량, 소통역량, 협력역량, 도전역량) 점수를 분석하고
목표 직업과의 적합성을 평가합니다.

다음 JSON 형식으로 응답하세요:
{
  "analysis": "전반적인 역량 분석 요약 (2-3문장)",
  "strengths": ["강점 1", "강점 2"],
  "weaknesses": ["약점 1", "약점 2"],
  "improvement_suggestions": ["구체적인 교과목명, 비교과 활동, 자격증을 포함한 개선 제안 1", "개선 제안 2", "개선 제안 3"]
}

improvement_suggestions 작성 시 반드시 다음을 포함하세요:
- 수강 추천 교과목명 (예: 캡스톤디자인, 데이터분석실습 등)
- 참여 추천 비교과 활동 (예: 창업동아리, 해외봉사, 학술대회 등)
- 취득 추천 자격증 (예: 컴퓨터활용능력, SQLD, TOEIC 등)
각 제안은 학생의 부족한 역량과 직접 연관된 구체적 행동 계획이어야 합니다."""

        user_prompt = f"""목표 직업: {career_goal}

역량 점수:
{json.dumps(competency_scores, ensure_ascii=False, indent=2)}

위 역량을 분석해주세요."""

        try:
            response = await self._agenthub.chat(
                agent_code="career-competency-analyzer",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.settings.TEMPERATURE,
                max_tokens=self.settings.MAX_TOKENS,
            )

            content = response["choices"][0]["message"]["content"]

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except (AgentHubError, json.JSONDecodeError, KeyError, IndexError) as ex:
            logger.error(f"AgentHub competency analyze 실패: {ex}")
            return {
                "analysis": "역량 분석 중 오류가 발생했습니다.",
                "strengths": [],
                "weaknesses": [],
                "improvement_suggestions": [],
            }
        except Exception as e:
            logger.exception(f"Analysis Error: {e}")
            return {
                "analysis": "역량 분석 중 오류가 발생했습니다.",
                "strengths": [],
                "weaknesses": [],
                "improvement_suggestions": [],
            }

    async def chat(
        self,
        message: str,
        history: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        커리어봇 챗봇 응답을 AgentHub `career-chatbot` 으로 위임한다.

        주의 (PII):
            `career-chatbot` Agent 정의는 LlmRouting=Internal — Nexus 강제. 학생 발화에
            이름/성적 등 PII 가 포함될 수 있어 외부 LLM 으로 새지 않도록 경계되어 있다.
        """

        system_prompt = """당신은 대학생 커리어 개발을 돕는 AI 상담사 '커리어봇'입니다.

역할:
- 친근하고 전문적인 어조로 상담
- 학생의 역량 개발과 진로 설정 지원
- 구체적이고 실행 가능한 조언 제공
- 필요시 관련 비교과 활동이나 자격증 추천

응답 형식:
{
  "response": "상담 응답 내용",
  "suggestions": ["추가 질문이나 액션 제안 1", "제안 2"]
}"""

        # AgentHub 메시지 구성 — system / context / 최근 10턴 히스토리 / 현재 발화
        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

        if context:
            context_msg = f"학생 정보: {json.dumps(context, ensure_ascii=False)}"
            messages.append({"role": "system", "content": context_msg})

        for msg in history[-10:]:
            role = "user" if msg.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("content", "")})

        messages.append({"role": "user", "content": message})

        try:
            response = await self._agenthub.chat(
                agent_code="career-chatbot",
                messages=messages,
                temperature=self.settings.TEMPERATURE,
                max_tokens=self.settings.MAX_TOKENS,
            )
            content = response["choices"][0]["message"]["content"]

            try:
                # JSON 응답 시도
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                return json.loads(content.strip())
            except json.JSONDecodeError:
                # JSON 이 아니면 평문으로 감싸 반환 — 기존 응답 형식 호환
                return {
                    "response": content,
                    "suggestions": [],
                }
        except (AgentHubError, KeyError, IndexError) as e:
            logger.error(f"AgentHub chat 실패: {e}")
            raise

    async def generate_semester_goals(
        self,
        student_data: Dict[str, Any],
        competency_scores: List[Dict[str, Any]],
        current_goals: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """학기 스프린트 목표 생성을 AgentHub `career-semester-planner` 로 위임한다."""

        system_prompt = """당신은 대학생 학기 목표 설정 전문가입니다.
학생의 현재 상황과 역량을 분석하여 이번 학기에 달성해야 할 목표를 제안합니다.

다음 JSON 형식으로 응답하세요:
{
  "goals": [
    {"label": "목표 1", "completed": false, "priority": "high"},
    {"label": "목표 2", "completed": false, "priority": "medium"}
  ],
  "ai_suggestions": ["AI 조언 1", "AI 조언 2"]
}"""

        user_prompt = f"""학생 정보:
{json.dumps(student_data, ensure_ascii=False, indent=2)}

역량 점수:
{json.dumps(competency_scores, ensure_ascii=False, indent=2)}

현재 설정된 목표:
{json.dumps(current_goals, ensure_ascii=False, indent=2)}

이번 학기 목표와 조언을 생성해주세요."""

        try:
            response = await self._agenthub.chat(
                agent_code="career-semester-planner",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.settings.TEMPERATURE,
                max_tokens=self.settings.MAX_TOKENS,
            )
            content = response["choices"][0]["message"]["content"]

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except (AgentHubError, json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"AgentHub semester goal 생성 실패: {e}")
            return {
                "goals": [],
                "ai_suggestions": ["목표 생성 중 오류가 발생했습니다."],
            }
        except Exception as e:
            logger.exception(f"Goals Error: {e}")
            return {
                "goals": [],
                "ai_suggestions": ["목표 생성 중 오류가 발생했습니다."],
            }

    def _get_default_recommendations(self) -> List[Dict[str, Any]]:
        """AI 실패/데이터 부재 시 빈 추천 — mock 데이터로 사용자 오도 방지."""
        return []

    # ==================== Tool Calling Methods ====================

    async def generate_with_tools(
        self,
        student_id: str,
        task: str,
        max_tool_calls: int = 5,
    ) -> Dict[str, Any]:
        """
        Tool Calling 기반 ActionBoard 추천을 AgentHub `career-actionboard-orchestrator`
        Agent 로 위임한다.

        OpenAI Tool Calling 루프 (학생 데이터 fetch 등) 는 본 함수가 직접 관리하고,
        실제 LLM 호출은 모두 AgentHub 를 거친다. AgentHub 는 OpenAI Structured Outputs
        (`response_format=json_schema`) 를 OpenAI provider 로 라우팅한다.

        주의 (TECHSPEC W2):
            Tool Calling 의 strict JSON Schema 는 OpenAI 전용. AgentHub 가 Hybrid 라우팅
            중 Internal(Nexus) 로 분기하면 schema 호환이 깨질 수 있어, 본 Agent 정의는
            ServiceCode="openai" 강제 권장 (Phase 7.5 점검 항목).
        """
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"학생 ID: {student_id}\n\n요청: {task}\n\n"
                "사용 가능한 도구를 활용하여 학생 정보를 수집하고 분석해주세요."
            }
        ]

        call_count = 0
        tool_results: List[Dict[str, Any]] = []

        while call_count < max_tool_calls:
            try:
                # 1차 호출 — Tool Calling 루프 (AgentHub 가 OpenAI provider 로 라우팅)
                response = await self._agenthub.chat(
                    agent_code="career-actionboard-orchestrator",
                    messages=messages,
                    temperature=self.settings.TEMPERATURE,
                    extra={
                        "tools": TOOLS,
                        "tool_choice": "auto",
                    },
                )
                # AgentHub 는 OpenAI ChatCompletion 형식 dict 그대로 반환
                choice = response["choices"][0]
                assistant_message = choice["message"]
                tool_calls = assistant_message.get("tool_calls")

                # 더 이상 도구 호출 없음 → Structured Outputs 로 최종 응답 생성
                if not tool_calls:
                    logger.info(f"Tool calling completed after {call_count} calls")

                    try:
                        # 최종 호출 — JSON Schema strict (response_format)
                        structured_response = await self._agenthub.chat(
                            agent_code="career-actionboard-orchestrator",
                            messages=messages,
                            temperature=self.settings.TEMPERATURE,
                            extra={
                                "response_format": {
                                    "type": "json_schema",
                                    "json_schema": JSON_SCHEMA_ACTIONBOARD,
                                },
                            },
                        )
                        result = json.loads(
                            structured_response["choices"][0]["message"]["content"]
                        )
                    except Exception as schema_error:
                        logger.warning(f"Structured output failed, falling back: {schema_error}")
                        content = assistant_message.get("content") or ""
                        try:
                            if "```json" in content:
                                content = content.split("```json")[1].split("```")[0]
                            elif "```" in content:
                                content = content.split("```")[1].split("```")[0]
                            result = json.loads(content.strip())
                        except json.JSONDecodeError:
                            result = {
                                "summary": content,
                                "strengths": [],
                                "improvements": [],
                                "recommendations": [],
                                "alumni_insights": [],
                            }

                    result["tool_calls_made"] = call_count
                    result["tool_results"] = tool_results
                    return result

                # 도구 호출 처리 — assistant 메시지를 messages 에 누적
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.get("content"),
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"],
                            }
                        }
                        for tc in tool_calls
                    ],
                })

                # 각 도구 실행 — career 의 student/competency/alumni MS 호출
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    arguments = json.loads(tool_call["function"]["arguments"])

                    logger.info(f"Executing tool: {tool_name} with args: {arguments}")

                    result = await self.tool_executor.execute(tool_name, arguments)

                    tool_results.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "result_summary": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                    })

                    messages.append({
                        "role": "tool",
                        "content": json.dumps(result, ensure_ascii=False),
                        "tool_call_id": tool_call["id"],
                    })

                call_count += 1

            except AgentHubError as e:
                logger.error(f"AgentHub Tool calling error: {e}")
                return {
                    "error": str(e),
                    "tool_calls_made": call_count,
                    "tool_results": tool_results,
                }
            except Exception as e:
                logger.exception(f"Tool calling unexpected error: {e}")
                return {
                    "error": str(e),
                    "tool_calls_made": call_count,
                    "tool_results": tool_results,
                }

        logger.warning(f"Max tool calls ({max_tool_calls}) reached")
        return {
            "error": "Maximum tool calls reached",
            "tool_calls_made": call_count,
            "tool_results": tool_results,
        }

    # ==================== Phase 2-3: RAG Integration ====================

    async def generate_with_tools_and_rag(
        self,
        student_id: str,
        task: str,
        db=None,
        use_rag: bool = True,
        max_tool_calls: int = 5,
    ) -> Dict[str, Any]:
        """
        Tool Calling + RAG + Structured Outputs 를 AgentHub `career-rag-actionboard`
        Agent 로 위임한다.

        본 함수는 RAG 컨텍스트(evidence) 를 시스템 프롬프트에 prepend 한 뒤
        `generate_with_tools` 와 동일한 Tool Calling 루프를 수행한다.
        """
        import time
        start_time = time.time()

        evidence: List[Dict[str, Any]] = []
        evidence_context = ""

        # Phase 2-3: RAG — Evidence 검색
        if use_rag and db is not None:
            try:
                from .embedding_service import EmbeddingService
                from .retrieval_service import RetrievalService

                embedding_service = EmbeddingService(self.settings)
                retrieval_service = RetrievalService(db, embedding_service)

                evidence = await retrieval_service.hybrid_search(
                    query=task,
                    student_id=student_id,
                    top_k=5
                )

                evidence_context = retrieval_service.format_evidence_for_prompt(evidence)
                logger.info(f"Retrieved {len(evidence)} evidence items for RAG")

            except Exception as e:
                logger.warning(f"RAG retrieval failed, continuing without evidence: {e}")

        enhanced_prompt = SYSTEM_PROMPT
        if evidence_context:
            enhanced_prompt = f"""{SYSTEM_PROMPT}

{evidence_context}

위 Evidence를 참고하여 학생에게 구체적이고 근거 있는 추천을 제공하세요.
추천의 reasoning 필드에 관련 Evidence를 언급해주세요.
"""

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": enhanced_prompt},
            {
                "role": "user",
                "content": f"학생 ID: {student_id}\n\n요청: {task}\n\n"
                "사용 가능한 도구를 활용하여 학생 정보를 수집하고 분석해주세요."
            }
        ]

        call_count = 0
        tool_results: List[Dict[str, Any]] = []

        # Tool Calling loop — AgentHub 위임
        while call_count < max_tool_calls:
            try:
                response = await self._agenthub.chat(
                    agent_code="career-rag-actionboard",
                    messages=messages,
                    temperature=self.settings.TEMPERATURE,
                    extra={
                        "tools": TOOLS,
                        "tool_choice": "auto",
                    },
                )

                choice = response["choices"][0]
                assistant_message = choice["message"]
                tool_calls = assistant_message.get("tool_calls")

                if not tool_calls:
                    logger.info(f"Tool calling completed after {call_count} calls")

                    try:
                        structured_response = await self._agenthub.chat(
                            agent_code="career-rag-actionboard",
                            messages=messages,
                            temperature=self.settings.TEMPERATURE,
                            extra={
                                "response_format": {
                                    "type": "json_schema",
                                    "json_schema": JSON_SCHEMA_ACTIONBOARD,
                                },
                            },
                        )
                        result = json.loads(
                            structured_response["choices"][0]["message"]["content"]
                        )
                    except Exception as schema_error:
                        logger.warning(f"Structured output failed: {schema_error}")
                        content = assistant_message.get("content") or ""
                        try:
                            if "```json" in content:
                                content = content.split("```json")[1].split("```")[0]
                            elif "```" in content:
                                content = content.split("```")[1].split("```")[0]
                            result = json.loads(content.strip())
                        except json.JSONDecodeError:
                            result = {
                                "summary": content,
                                "strengths": [],
                                "improvements": [],
                                "recommendations": [],
                                "alumni_insights": [],
                            }

                    latency_ms = int((time.time() - start_time) * 1000)
                    result["metadata"] = {
                        "tool_calls_made": call_count,
                        "evidence_count": len(evidence),
                        "latency_ms": latency_ms,
                        "rag_enabled": use_rag,
                    }
                    result["tool_results"] = tool_results
                    result["evidence"] = [
                        {
                            "source_type": e.get("source_type"),
                            "title": e.get("title"),
                            "score": e.get("score"),
                        }
                        for e in evidence
                    ]

                    return result

                messages.append({
                    "role": "assistant",
                    "content": assistant_message.get("content"),
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"],
                            }
                        }
                        for tc in tool_calls
                    ],
                })

                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    arguments = json.loads(tool_call["function"]["arguments"])

                    logger.info(f"Executing tool: {tool_name} with args: {arguments}")

                    result = await self.tool_executor.execute(tool_name, arguments)

                    tool_results.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "result_summary": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                    })

                    messages.append({
                        "role": "tool",
                        "content": json.dumps(result, ensure_ascii=False),
                        "tool_call_id": tool_call["id"],
                    })

                call_count += 1

            except AgentHubError as e:
                logger.error(f"AgentHub Tool+RAG error: {e}")
                latency_ms = int((time.time() - start_time) * 1000)
                return {
                    "error": str(e),
                    "metadata": {
                        "tool_calls_made": call_count,
                        "evidence_count": len(evidence),
                        "latency_ms": latency_ms,
                        "rag_enabled": use_rag,
                    },
                    "tool_results": tool_results,
                }
            except Exception as e:
                logger.exception(f"Tool+RAG unexpected error: {e}")
                latency_ms = int((time.time() - start_time) * 1000)
                return {
                    "error": str(e),
                    "metadata": {
                        "tool_calls_made": call_count,
                        "evidence_count": len(evidence),
                        "latency_ms": latency_ms,
                        "rag_enabled": use_rag,
                    },
                    "tool_results": tool_results,
                }

        latency_ms = int((time.time() - start_time) * 1000)
        logger.warning(f"Max tool calls ({max_tool_calls}) reached with RAG")
        return {
            "error": "Maximum tool calls reached",
            "metadata": {
                "tool_calls_made": call_count,
                "evidence_count": len(evidence),
                "latency_ms": latency_ms,
                "rag_enabled": use_rag,
            },
            "tool_results": tool_results,
        }
