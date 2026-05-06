"""
Integrations package for the Document Utilization System.

Contains client wrappers for external services:
  - llm: LLM clients (OpenAI, vLLM) and prompt templates
    (Phase 7.3 deprecate 예정 — AgentHubClient 단일 진입점으로 교체)
  - vector_store: Qdrant vector database client
  - object_storage: MinIO S3-compatible object storage client
  - ocr: OCR service wrappers (Tesseract, EasyOCR)
  - docling: Granite-Docling VLM for enhanced document parsing
  - agenthub_client: AgentHub OpenAI 호환 엔드포인트 단일 진입점 (Phase 7.2~7.3, R2)
"""
