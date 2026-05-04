"""
Evaluation module constants — metric definitions, judge prompts, and defaults.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Metric names (used as keys in DB, Prometheus, and API responses)
# ---------------------------------------------------------------------------

METRIC_CONTEXT_RELEVANCY = "context_relevancy"
METRIC_ANSWER_FAITHFULNESS = "answer_faithfulness"
METRIC_ANSWER_RELEVANCY = "answer_relevancy"
METRIC_HALLUCINATION = "hallucination"

ALL_METRICS = [
    METRIC_CONTEXT_RELEVANCY,
    METRIC_ANSWER_FAITHFULNESS,
    METRIC_ANSWER_RELEVANCY,
    METRIC_HALLUCINATION,
]

# ---------------------------------------------------------------------------
# Default metric weights (per-org overridable)
# ---------------------------------------------------------------------------

DEFAULT_METRIC_WEIGHTS: dict[str, float] = {
    METRIC_CONTEXT_RELEVANCY: 0.25,
    METRIC_ANSWER_FAITHFULNESS: 0.30,
    METRIC_ANSWER_RELEVANCY: 0.25,
    METRIC_HALLUCINATION: 0.20,
}

# ---------------------------------------------------------------------------
# LLM-as-judge prompts
# ---------------------------------------------------------------------------

CONTEXT_RELEVANCY_PROMPT = """\
You are an expert evaluator. Given a user question and a list of retrieved \
document contexts, rate how relevant the retrieved contexts are to answering \
the question.

Score from 0.0 (completely irrelevant) to 1.0 (perfectly relevant).

QUESTION:
{question}

RETRIEVED CONTEXTS:
{contexts}

Respond with ONLY a JSON object:
{{"score": <float 0.0-1.0>, "reasoning": "<brief explanation>"}}"""

ANSWER_FAITHFULNESS_PROMPT = """\
You are an expert evaluator. Given a list of source documents and an AI-generated \
answer, evaluate whether every claim in the answer is supported by the source \
documents.

Score from 0.0 (entirely unsupported) to 1.0 (fully grounded in sources).

SOURCE DOCUMENTS:
{contexts}

AI ANSWER:
{answer}

Respond with ONLY a JSON object:
{{"score": <float 0.0-1.0>, "reasoning": "<brief explanation>"}}"""

ANSWER_RELEVANCY_PROMPT = """\
You are an expert evaluator. Given a user question and an AI-generated answer, \
rate how well the answer addresses the question.

Score from 0.0 (does not answer at all) to 1.0 (perfectly answers the question).

QUESTION:
{question}

AI ANSWER:
{answer}

Respond with ONLY a JSON object:
{{"score": <float 0.0-1.0>, "reasoning": "<brief explanation>"}}"""

HALLUCINATION_DETECTION_PROMPT = """\
You are an expert evaluator. Given source documents and an AI-generated answer, \
identify any claims in the answer that are NOT supported by the source documents.

SOURCE DOCUMENTS:
{contexts}

AI ANSWER:
{answer}

Respond with ONLY a JSON object:
{{"has_hallucination": <true/false>, "evidence": ["<unsupported claim 1>", ...], \
"score": <float 0.0-1.0 where 1.0 means no hallucination>}}"""

# Map metric name → prompt template
METRIC_PROMPTS: dict[str, str] = {
    METRIC_CONTEXT_RELEVANCY: CONTEXT_RELEVANCY_PROMPT,
    METRIC_ANSWER_FAITHFULNESS: ANSWER_FAITHFULNESS_PROMPT,
    METRIC_ANSWER_RELEVANCY: ANSWER_RELEVANCY_PROMPT,
    METRIC_HALLUCINATION: HALLUCINATION_DETECTION_PROMPT,
}
