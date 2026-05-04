"""Synthetic training data generation pipeline.

Generates high-quality QA pairs from document chunks using:
1. GPT-4o for question-answer pair generation
2. GPT-4o-as-Judge for quality scoring
3. Korean-specific reasoning data augmentation
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.core.config import get_settings
from app.integrations.llm.client import OpenAIClient

from .config import DataGenerationConfig

logger = logging.getLogger(__name__)
settings = get_settings()

QA_GENERATION_PROMPT = """당신은 학습 데이터를 생성하는 전문가입니다.
주어진 문서 내용을 바탕으로 다양한 유형의 질문-답변 쌍을 생성해주세요.

문서 내용:
{content}

다음 유형의 질문을 각각 {qa_count}개씩 생성하세요:
1. 사실 확인 (Factual): 문서에서 직접 찾을 수 있는 정보
2. 추론 (Reasoning): 문서 정보를 바탕으로 논리적으로 추론해야 하는 질문
3. 요약 (Summary): 문서의 핵심 내용을 요약하는 질문

각 쌍은 다음 JSON 형식으로 출력:
[
  {{
    "question": "질문 내용",
    "answer": "상세한 답변 (반드시 문서 내용을 근거로)",
    "type": "factual|reasoning|summary",
    "difficulty": "easy|medium|hard"
  }}
]

중요: 답변에는 반드시 문서의 구체적인 내용을 인용하세요."""

JUDGE_PROMPT = """You are evaluating the quality of a QA pair for training data.
Score each criterion from 1-5:

Question: {question}
Answer: {answer}
Source Document: {source}

Criteria:
1. Relevance: Is the question relevant to the source document?
2. Accuracy: Is the answer factually correct based on the source?
3. Completeness: Does the answer fully address the question?
4. Clarity: Are both question and answer clear and well-written?
5. Usefulness: Would this QA pair be useful for training a domain-specific model?

Output as JSON: {{"relevance": N, "accuracy": N, "completeness": N, "clarity": N, "usefulness": N, "overall": N, "reasoning": "brief explanation"}}"""


class TrainingDataGenerator:
    """Generates synthetic QA training data from document chunks."""

    def __init__(self, config: DataGenerationConfig | None = None):
        self.config = config or DataGenerationConfig()
        self._source_llm = OpenAIClient()
        self._judge_llm = OpenAIClient()

    async def generate_from_chunks(
        self,
        chunks: list[dict],
        output_path: str | None = None,
    ) -> list[dict]:
        """Generate QA pairs from document chunks with quality filtering."""
        output_path = output_path or self.config.output_path
        all_samples = []

        for i, chunk in enumerate(chunks):
            content = chunk.get("content", "")
            if len(content) < 100:
                continue

            try:
                # Generate QA pairs
                qa_pairs = await self._generate_qa_pairs(content)

                # Judge each pair
                for qa in qa_pairs:
                    score = await self._judge_quality(
                        qa["question"],
                        qa["answer"],
                        content,
                    )

                    if score >= self.config.min_judge_score:
                        sample = self._format_training_sample(
                            qa["question"],
                            qa["answer"],
                            qa.get("type", "factual"),
                            chunk.get("document_name", ""),
                        )
                        all_samples.append(sample)

                if (i + 1) % 100 == 0:
                    logger.info("Processed %d/%d chunks, %d samples generated", i + 1, len(chunks), len(all_samples))

                if len(all_samples) >= self.config.target_samples:
                    break

            except Exception as exc:
                logger.warning("Failed to generate QA for chunk %d: %s", i, exc)
                continue

        # Save to JSONL
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for sample in all_samples:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")

        logger.info("Generated %d training samples -> %s", len(all_samples), output_path)
        return all_samples

    async def _generate_qa_pairs(self, content: str) -> list[dict]:
        """Generate QA pairs from a single chunk."""
        prompt = QA_GENERATION_PROMPT.format(
            content=content[:3000],
            qa_count=self.config.qa_per_chunk,
        )

        response = await self._source_llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.qa_temperature,
            max_tokens=self.config.qa_max_tokens,
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return []

    async def _judge_quality(self, question: str, answer: str, source: str) -> float:
        """Score QA pair quality using LLM-as-judge."""
        prompt = JUDGE_PROMPT.format(
            question=question,
            answer=answer,
            source=source[:2000],
        )

        response = await self._judge_llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.judge_model == "gpt-4o" and 0.0 or 0.1,
            max_tokens=300,
        )

        try:
            scores = json.loads(response)
            return scores.get("overall", 0) / 5.0
        except (json.JSONDecodeError, KeyError):
            return 0.0

    def _format_training_sample(
        self,
        question: str,
        answer: str,
        qa_type: str,
        doc_name: str,
    ) -> dict:
        """Format as Qwen3 chat template training sample."""
        return {
            "messages": [
                {
                    "role": "system",
                    "content": "당신은 문서 기반 질문에 정확하게 답변하는 전문 AI 어시스턴트입니다. "
                    "항상 근거를 들어 답변하고, 모르는 것은 모른다고 말합니다.",
                },
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer},
            ],
            "metadata": {
                "type": qa_type,
                "source_document": doc_name,
            },
        }
