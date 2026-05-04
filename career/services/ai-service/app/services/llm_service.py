from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from typing import List, Dict, Any, Optional
import json
import logging

from openai import AsyncOpenAI

from ..config import get_settings
from ..tools.tool_definitions import TOOLS, SYSTEM_PROMPT, JSON_SCHEMA_ACTIONBOARD
from ..tools.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.settings = get_settings()
        # LangChain client (existing)
        self.llm = ChatOpenAI(
            model=self.settings.OPENAI_MODEL,
            temperature=self.settings.TEMPERATURE,
            max_tokens=self.settings.MAX_TOKENS,
            api_key=self.settings.OPENAI_API_KEY,
        )
        # OpenAI direct client for Tool Calling
        self.openai_client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.tool_executor = ToolExecutor(self.settings)

    async def generate_action_recommendations(
        self,
        student_data: Dict[str, Any],
        competency_scores: List[Dict[str, Any]],
        career_goal: str,
    ) -> List[Dict[str, Any]]:
        """Generate AI-powered action recommendations for a student."""

        # Return empty if no competency data available
        if not competency_scores:
            logger.info("No competency data available, returning empty recommendations")
            return []

        # Return empty if student data is incomplete
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

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content

            # Parse JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            actions = json.loads(content.strip())
            return actions
        except json.JSONDecodeError:
            # Return default recommendations if parsing fails
            return self._get_default_recommendations()
        except Exception as e:
            print(f"LLM Error: {e}")
            return self._get_default_recommendations()

    async def analyze_competencies(
        self,
        competency_scores: List[Dict[str, Any]],
        career_goal: str,
    ) -> Dict[str, Any]:
        """Analyze competency scores and provide insights."""

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

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except Exception as e:
            print(f"Analysis Error: {e}")
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
        """Handle chatbot conversation."""

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

        messages = [SystemMessage(content=system_prompt)]

        # Add context if available
        if context:
            context_msg = f"학생 정보: {json.dumps(context, ensure_ascii=False)}"
            messages.append(SystemMessage(content=context_msg))

        # Add conversation history
        for msg in history[-10:]:  # Last 10 messages
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=message))

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content

            # Try to parse as JSON
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                return json.loads(content.strip())
            except json.JSONDecodeError:
                # Return as plain text response
                return {
                    "response": content,
                    "suggestions": [],
                }
        except Exception as e:
            logger.error(f"Chat Error: {e}")
            raise

    async def generate_semester_goals(
        self,
        student_data: Dict[str, Any],
        competency_scores: List[Dict[str, Any]],
        current_goals: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate semester sprint goals."""

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

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except Exception as e:
            print(f"Goals Error: {e}")
            return {
                "goals": [],
                "ai_suggestions": ["목표 생성 중 오류가 발생했습니다."],
            }

    def _get_default_recommendations(self) -> List[Dict[str, Any]]:
        """Return empty recommendations when AI fails or no data available."""
        # Return empty list instead of mock data to avoid misleading recommendations
        return []

    # ==================== Tool Calling Methods ====================

    async def generate_with_tools(
        self,
        student_id: str,
        task: str,
        max_tool_calls: int = 5,
    ) -> Dict[str, Any]:
        """
        Generate recommendations using OpenAI Tool Calling.

        This method autonomously calls tools to gather student data,
        competency scores, and alumni patterns before generating recommendations.

        Args:
            student_id: The student ID to analyze
            task: The task description (e.g., "career recommendations", "competency analysis")
            max_tool_calls: Maximum number of tool calls to prevent infinite loops

        Returns:
            Structured recommendation response
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"학생 ID: {student_id}\n\n요청: {task}\n\n"
                "사용 가능한 도구를 활용하여 학생 정보를 수집하고 분석해주세요."
            }
        ]

        call_count = 0
        tool_results = []

        while call_count < max_tool_calls:
            try:
                response = await self.openai_client.chat.completions.create(
                    model=self.settings.OPENAI_MODEL,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    temperature=self.settings.TEMPERATURE,
                )

                choice = response.choices[0]
                assistant_message = choice.message

                # No more tool calls - generate final response with Structured Output
                if not assistant_message.tool_calls:
                    logger.info(f"Tool calling completed after {call_count} calls")

                    # Phase 2-2: Apply JSON Schema for structured output
                    try:
                        structured_response = await self.openai_client.chat.completions.create(
                            model=self.settings.OPENAI_MODEL,
                            messages=messages,
                            response_format={
                                "type": "json_schema",
                                "json_schema": JSON_SCHEMA_ACTIONBOARD
                            },
                            temperature=self.settings.TEMPERATURE,
                        )
                        result = json.loads(structured_response.choices[0].message.content)
                    except Exception as schema_error:
                        logger.warning(f"Structured output failed, falling back: {schema_error}")
                        # Fallback: Try to parse the original response as JSON
                        content = assistant_message.content or ""
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

                # Process tool calls
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ]
                })

                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)

                    logger.info(f"Executing tool: {tool_name} with args: {arguments}")

                    # Execute the tool
                    result = await self.tool_executor.execute(tool_name, arguments)

                    tool_results.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "result_summary": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                    })

                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "content": json.dumps(result, ensure_ascii=False),
                        "tool_call_id": tool_call.id,
                    })

                call_count += 1

            except Exception as e:
                logger.error(f"Tool calling error: {e}")
                return {
                    "error": str(e),
                    "tool_calls_made": call_count,
                    "tool_results": tool_results,
                }

        # Max calls reached
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
        Generate recommendations using Tool Calling + RAG + Structured Outputs.

        This method combines all Phase 2 features:
        - Phase 2-1: Tool Calling for data gathering
        - Phase 2-2: Structured Outputs for consistent response format
        - Phase 2-3: RAG for evidence-based recommendations

        Args:
            student_id: The student ID to analyze
            task: The task description
            db: Database session for RAG queries
            use_rag: Whether to use RAG for evidence retrieval
            max_tool_calls: Maximum number of tool calls

        Returns:
            Structured recommendation response with evidence
        """
        import time
        start_time = time.time()

        evidence = []
        evidence_context = ""

        # Phase 2-3: RAG - Retrieve relevant evidence
        if use_rag and db is not None:
            try:
                from .embedding_service import EmbeddingService
                from .retrieval_service import RetrievalService

                embedding_service = EmbeddingService(self.settings)
                retrieval_service = RetrievalService(db, embedding_service)

                # Search for relevant evidence
                evidence = await retrieval_service.hybrid_search(
                    query=task,
                    student_id=student_id,
                    top_k=5
                )

                # Format evidence for prompt
                evidence_context = retrieval_service.format_evidence_for_prompt(evidence)
                logger.info(f"Retrieved {len(evidence)} evidence items for RAG")

            except Exception as e:
                logger.warning(f"RAG retrieval failed, continuing without evidence: {e}")

        # Build enhanced system prompt with evidence
        enhanced_prompt = SYSTEM_PROMPT
        if evidence_context:
            enhanced_prompt = f"""{SYSTEM_PROMPT}

{evidence_context}

위 Evidence를 참고하여 학생에게 구체적이고 근거 있는 추천을 제공하세요.
추천의 reasoning 필드에 관련 Evidence를 언급해주세요.
"""

        messages = [
            {"role": "system", "content": enhanced_prompt},
            {
                "role": "user",
                "content": f"학생 ID: {student_id}\n\n요청: {task}\n\n"
                "사용 가능한 도구를 활용하여 학생 정보를 수집하고 분석해주세요."
            }
        ]

        call_count = 0
        tool_results = []

        # Phase 2-1: Tool Calling loop
        while call_count < max_tool_calls:
            try:
                response = await self.openai_client.chat.completions.create(
                    model=self.settings.OPENAI_MODEL,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    temperature=self.settings.TEMPERATURE,
                )

                choice = response.choices[0]
                assistant_message = choice.message

                # No more tool calls - generate final response with Structured Output
                if not assistant_message.tool_calls:
                    logger.info(f"Tool calling completed after {call_count} calls")

                    # Phase 2-2: Apply JSON Schema for structured output
                    try:
                        structured_response = await self.openai_client.chat.completions.create(
                            model=self.settings.OPENAI_MODEL,
                            messages=messages,
                            response_format={
                                "type": "json_schema",
                                "json_schema": JSON_SCHEMA_ACTIONBOARD
                            },
                            temperature=self.settings.TEMPERATURE,
                        )
                        result = json.loads(structured_response.choices[0].message.content)
                    except Exception as schema_error:
                        logger.warning(f"Structured output failed: {schema_error}")
                        content = assistant_message.content or ""
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

                    # Add metadata
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

                # Process tool calls
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ]
                })

                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)

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
                        "tool_call_id": tool_call.id,
                    })

                call_count += 1

            except Exception as e:
                logger.error(f"Tool calling with RAG error: {e}")
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

        # Max calls reached
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
