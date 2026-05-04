"""
Standalone evaluation runner — runs the full evaluation pipeline once
against the remote server's DB, Qdrant, and OpenAI, then prints results.

Usage:
    python scripts/run_evaluation_once.py
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from pathlib import Path

import httpx
import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# Config (server)
# ---------------------------------------------------------------------------

DB_HOST = "192.168.10.39"
DB_PORT = 5440
DB_USER = "docutil"
DB_PASS = "docutil_pg_2024"
DB_NAME = "docutil"

API_BASE = "http://192.168.10.39:8040/api/v1"
QDRANT_URL = "http://192.168.10.39:6341"

# Will be loaded from server .env
OPENAI_API_KEY = ""

# ---------------------------------------------------------------------------
# Load OpenAI API key
# ---------------------------------------------------------------------------


def load_openai_key() -> str:
    """Load OpenAI API key from server .env via paramiko."""
    import paramiko

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(DB_HOST, username="idino", password="dkdlelsh@12")
    _, stdout, _ = ssh.exec_command(
        'grep "^OPENAI_API_KEY=" /home/idino/docutil/.env'
    )
    line = stdout.read().decode().strip()
    ssh.close()
    return line.split("=", 1)[1] if "=" in line else ""


# ---------------------------------------------------------------------------
# Test questions (subset for quick eval)
# ---------------------------------------------------------------------------

TEST_QUESTIONS = [
    "이 프로젝트의 주요 기술 스택은 무엇인가요?",
    "문서 업로드 후 처리 과정을 설명해주세요.",
    "검색 기능은 어떤 방식으로 동작하나요?",
    "사용자 권한 체계는 어떻게 구성되어 있나요?",
    "보고서 생성 기능에 대해 설명해주세요.",
]

# ---------------------------------------------------------------------------
# LLM calls
# ---------------------------------------------------------------------------

TIMEOUT = 120.0


def llm_generate(
    api_key: str,
    messages: list[dict],
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> str:
    """Call OpenAI Chat Completions API (sync)."""
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Search via API (uses existing deployed API)
# ---------------------------------------------------------------------------


def get_auth_token() -> str:
    """Login as admin to get JWT token."""
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{API_BASE}/auth/login",
            json={"username": "admin", "password": "admin123!"},
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


def search_and_answer(
    token: str, api_key: str, question: str
) -> dict:
    """Search via API, then generate RAG answer."""
    # Call hybrid search (POST endpoint)
    with httpx.Client(timeout=60) as client:
        resp = client.post(
            f"{API_BASE}/search",
            json={"query": question, "max_results": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code != 200:
            return {"answer": "(검색 실패)", "contexts": []}
        data = resp.json()

    results = data.get("results", [])
    contexts = [r.get("content", "") for r in results if r.get("content")]

    if not contexts:
        return {"answer": "(관련 문서를 찾을 수 없습니다)", "contexts": []}

    # Build RAG prompt
    context_text = "\n\n---\n\n".join(
        f"[Source {i + 1}]: {c}" for i, c in enumerate(contexts)
    )
    prompt = f"""You are an expert document analyst. Answer the user's question based ONLY on the provided context. Cite sources using [Source N].

CONTEXT:
{context_text}

QUESTION:
{question}

Provide a thorough, well-cited answer in Korean:"""

    answer = llm_generate(
        api_key,
        [{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2048,
    )
    return {"answer": answer, "contexts": contexts}


# ---------------------------------------------------------------------------
# Judge prompts
# ---------------------------------------------------------------------------

JUDGE_PROMPTS = {
    "context_relevancy": """You are an expert evaluator. Given a user question and retrieved document contexts, rate how relevant the retrieved contexts are to answering the question.
Score from 0.0 (completely irrelevant) to 1.0 (perfectly relevant).

QUESTION:
{question}

RETRIEVED CONTEXTS:
{contexts}

Respond with ONLY a JSON object: {{"score": <float 0.0-1.0>, "reasoning": "<brief explanation>"}}""",
    "answer_faithfulness": """You are an expert evaluator. Given source documents and an AI-generated answer, evaluate whether every claim in the answer is supported by the source documents.
Score from 0.0 (entirely unsupported) to 1.0 (fully grounded in sources).

SOURCE DOCUMENTS:
{contexts}

AI ANSWER:
{answer}

Respond with ONLY a JSON object: {{"score": <float 0.0-1.0>, "reasoning": "<brief explanation>"}}""",
    "answer_relevancy": """You are an expert evaluator. Given a user question and an AI-generated answer, rate how well the answer addresses the question.
Score from 0.0 (does not answer at all) to 1.0 (perfectly answers the question).

QUESTION:
{question}

AI ANSWER:
{answer}

Respond with ONLY a JSON object: {{"score": <float 0.0-1.0>, "reasoning": "<brief explanation>"}}""",
    "hallucination": """You are an expert evaluator. Given source documents and an AI-generated answer, identify any claims in the answer that are NOT supported by the source documents.

SOURCE DOCUMENTS:
{contexts}

AI ANSWER:
{answer}

Respond with ONLY a JSON object: {{"has_hallucination": <true/false>, "evidence": ["<unsupported claim 1>", ...], "score": <float 0.0-1.0 where 1.0 means no hallucination>}}""",
}


def judge_metric(
    api_key: str,
    metric: str,
    question: str,
    answer: str,
    contexts_text: str,
) -> dict:
    """Run a single metric evaluation using LLM-as-judge."""
    prompt = JUDGE_PROMPTS[metric].format(
        question=question, answer=answer, contexts=contexts_text
    )
    messages = [
        {
            "role": "system",
            "content": "You are an AI evaluation judge. Respond only with valid JSON.",
        },
        {"role": "user", "content": prompt},
    ]
    try:
        raw = llm_generate(api_key, messages, temperature=0.0, max_tokens=512)
        # Clean markdown wrapping if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw
            raw = raw.rsplit("```", 1)[0]
            raw = raw.strip()
        return json.loads(raw)
    except Exception as exc:
        print(f"  [WARN] Judge parse error ({metric}): {exc}")
        if metric == "hallucination":
            return {"has_hallucination": False, "evidence": [], "score": 0.5}
        return {"score": 0.5, "reasoning": f"Judge error: {str(exc)[:200]}"}


# ---------------------------------------------------------------------------
# DB operations
# ---------------------------------------------------------------------------


def ensure_eval_tables(conn):
    """Create evaluation tables if they don't exist (for standalone run)."""
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tb_evaluation_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id UUID NOT NULL,
            run_id VARCHAR(64) NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            contexts JSONB,
            context_relevancy FLOAT NOT NULL DEFAULT 0.0,
            answer_faithfulness FLOAT NOT NULL DEFAULT 0.0,
            answer_relevancy FLOAT NOT NULL DEFAULT 0.0,
            hallucination_score FLOAT NOT NULL DEFAULT 0.0,
            has_hallucination BOOLEAN NOT NULL DEFAULT FALSE,
            hallucination_evidence JSONB,
            composite_score FLOAT NOT NULL DEFAULT 0.0,
            judge_details JSONB,
            run_type VARCHAR(20) NOT NULL DEFAULT 'scheduled',
            question_index INTEGER NOT NULL DEFAULT 0,
            ins_dt TIMESTAMPTZ NOT NULL DEFAULT now(),
            ins_user UUID,
            ins_ip VARCHAR(45),
            upd_dt TIMESTAMPTZ NOT NULL DEFAULT now(),
            upd_user UUID,
            upd_ip VARCHAR(45)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tb_evaluation_configs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id UUID NOT NULL UNIQUE,
            context_relevancy_weight FLOAT NOT NULL DEFAULT 0.25,
            answer_faithfulness_weight FLOAT NOT NULL DEFAULT 0.30,
            answer_relevancy_weight FLOAT NOT NULL DEFAULT 0.25,
            hallucination_weight FLOAT NOT NULL DEFAULT 0.20,
            ins_dt TIMESTAMPTZ NOT NULL DEFAULT now(),
            ins_user UUID,
            ins_ip VARCHAR(45),
            upd_dt TIMESTAMPTZ NOT NULL DEFAULT now(),
            upd_user UUID,
            upd_ip VARCHAR(45)
        )
    """)
    conn.commit()
    cur.close()


def get_org_id(conn) -> str:
    """Get first organization ID."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM tb_organizations LIMIT 1")
    row = cur.fetchone()
    cur.close()
    return str(row[0]) if row else ""


def save_eval_log(conn, org_id: str, run_id: str, question: str, answer: str,
                  contexts: list, metrics: dict, question_index: int):
    """Insert evaluation log into DB."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tb_evaluation_logs
            (organization_id, run_id, question, answer, contexts,
             context_relevancy, answer_faithfulness, answer_relevancy,
             hallucination_score, has_hallucination, hallucination_evidence,
             composite_score, judge_details, run_type, question_index)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        org_id, run_id, question, answer,
        json.dumps({"sources": contexts}),
        metrics["context_relevancy"],
        metrics["answer_faithfulness"],
        metrics["answer_relevancy"],
        metrics["hallucination_score"],
        metrics["has_hallucination"],
        json.dumps(metrics.get("hallucination_evidence", [])),
        metrics["composite_score"],
        json.dumps(metrics.get("judge_details", {})),
        "manual",
        question_index,
    ))
    conn.commit()
    cur.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DEFAULT_WEIGHTS = {
    "context_relevancy": 0.25,
    "answer_faithfulness": 0.30,
    "answer_relevancy": 0.25,
    "hallucination": 0.20,
}


def main():
    print("=" * 70)
    print("  AI 응답 품질 평가 (수동 실행)")
    print("=" * 70)

    # Load API key
    print("\n[1/5] OpenAI API 키 로딩...")
    global OPENAI_API_KEY
    OPENAI_API_KEY = load_openai_key()
    if not OPENAI_API_KEY:
        print("ERROR: OpenAI API key not found")
        sys.exit(1)
    print(f"  API Key: {OPENAI_API_KEY[:12]}...")

    # Connect DB
    print("\n[2/5] DB 연결 및 테이블 준비...")
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASS, dbname=DB_NAME,
    )
    ensure_eval_tables(conn)
    org_id = get_org_id(conn)
    print(f"  Organization: {org_id}")

    # Get auth token
    print("\n[3/5] API 인증...")
    try:
        token = get_auth_token()
        print(f"  Token: {token[:20]}...")
    except Exception as exc:
        print(f"  AUTH FAILED: {exc}")
        print("  Falling back to direct LLM evaluation (no search)")
        token = None

    run_id = uuid.uuid4().hex[:16]
    print(f"\n[4/5] 평가 실행 (run_id: {run_id})")
    print(f"  질문 수: {len(TEST_QUESTIONS)}")
    print("-" * 70)

    all_results = []
    totals = {
        "context_relevancy": 0.0,
        "answer_faithfulness": 0.0,
        "answer_relevancy": 0.0,
        "hallucination_score": 0.0,
        "composite_score": 0.0,
    }

    for idx, question in enumerate(TEST_QUESTIONS):
        print(f"\n  Q{idx + 1}. {question}")
        start = time.time()

        # Search & answer
        if token:
            result = search_and_answer(token, OPENAI_API_KEY, question)
        else:
            result = {"answer": "(인증 실패로 검색 불가)", "contexts": []}

        answer = result["answer"]
        contexts = result["contexts"]
        elapsed_search = time.time() - start

        print(f"     검색+응답: {elapsed_search:.1f}s | 컨텍스트 {len(contexts)}건")
        print(f"     답변: {answer[:100]}...")

        # Judge
        contexts_text = "\n\n---\n\n".join(
            f"[Source {i + 1}]: {c}" for i, c in enumerate(contexts)
        )

        start_judge = time.time()

        cr = judge_metric(OPENAI_API_KEY, "context_relevancy", question, answer, contexts_text)
        af = judge_metric(OPENAI_API_KEY, "answer_faithfulness", question, answer, contexts_text)
        ar = judge_metric(OPENAI_API_KEY, "answer_relevancy", question, answer, contexts_text)
        hd = judge_metric(OPENAI_API_KEY, "hallucination", question, answer, contexts_text)

        elapsed_judge = time.time() - start_judge

        cr_score = float(cr.get("score", 0.0))
        af_score = float(af.get("score", 0.0))
        ar_score = float(ar.get("score", 0.0))
        hd_score = float(hd.get("score", 0.0))
        has_hall = bool(hd.get("has_hallucination", False))
        hall_evidence = hd.get("evidence", [])

        composite = (
            cr_score * DEFAULT_WEIGHTS["context_relevancy"]
            + af_score * DEFAULT_WEIGHTS["answer_faithfulness"]
            + ar_score * DEFAULT_WEIGHTS["answer_relevancy"]
            + hd_score * DEFAULT_WEIGHTS["hallucination"]
        )

        metrics = {
            "context_relevancy": cr_score,
            "answer_faithfulness": af_score,
            "answer_relevancy": ar_score,
            "hallucination_score": hd_score,
            "has_hallucination": has_hall,
            "hallucination_evidence": hall_evidence,
            "composite_score": round(composite, 4),
            "judge_details": {
                "context_relevancy": cr,
                "answer_faithfulness": af,
                "answer_relevancy": ar,
                "hallucination": hd,
            },
        }

        print(f"     평가: {elapsed_judge:.1f}s")
        print(f"     컨텍스트 관련성: {cr_score:.2f} | 답변 충실도: {af_score:.2f}")
        print(f"     답변 관련성:     {ar_score:.2f} | 환각 점수:   {hd_score:.2f}")
        print(f"     환각 여부: {'있음' if has_hall else '없음'} | 종합: {composite:.3f}")
        if has_hall and hall_evidence:
            for ev in hall_evidence[:3]:
                print(f"       - {ev[:80]}")

        # Persist
        save_eval_log(
            conn, org_id, run_id, question, answer, contexts,
            metrics, idx,
        )

        for key in totals:
            totals[key] += metrics.get(key, 0.0)
        all_results.append(metrics)

    # Summary
    n = len(all_results)
    print("\n" + "=" * 70)
    print("  [5/5] 평가 결과 요약")
    print("=" * 70)
    print(f"  실행 ID:         {run_id}")
    print(f"  평가 질문 수:    {n}/{len(TEST_QUESTIONS)}")
    print()

    if n > 0:
        avgs = {k: round(v / n, 4) for k, v in totals.items()}
        hall_count = sum(1 for r in all_results if r["has_hallucination"])

        print(f"  {'메트릭':<25} {'평균 점수':>10}")
        print(f"  {'-' * 37}")
        print(f"  {'컨텍스트 관련성':<23} {avgs['context_relevancy']:>10.4f}")
        print(f"  {'답변 충실도':<25} {avgs['answer_faithfulness']:>10.4f}")
        print(f"  {'답변 관련성':<25} {avgs['answer_relevancy']:>10.4f}")
        print(f"  {'환각 점수':<26} {avgs['hallucination_score']:>10.4f}")
        print(f"  {'-' * 37}")
        print(f"  {'종합 점수':<26} {avgs['composite_score']:>10.4f}")
        print(f"  {'환각 발생 건수':<23} {hall_count:>10}")
        print()

        # Quality assessment
        score = avgs["composite_score"]
        if score >= 0.8:
            grade = "우수 (A)"
        elif score >= 0.6:
            grade = "양호 (B)"
        elif score >= 0.4:
            grade = "보통 (C)"
        else:
            grade = "개선 필요 (D)"
        print(f"  종합 등급: {grade}")
    else:
        print("  평가된 질문이 없습니다.")

    conn.close()
    print(f"\n  결과가 DB에 저장되었습니다. (tb_evaluation_logs)")
    print("=" * 70)


if __name__ == "__main__":
    main()
