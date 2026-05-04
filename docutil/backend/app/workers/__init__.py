"""
Workers package for the Document Utilization System.

Contains Celery task definitions for asynchronous background processing:
  - celery_app: Celery application configuration
  - document_processor: Document parsing, chunking, and ingestion pipeline
  - embedding_generator: Dense and sparse vector embedding generation
  - report_generator: Template-based report generation with RAG
"""

from app.workers.celery_app import celery_app

__all__ = ["celery_app"]
