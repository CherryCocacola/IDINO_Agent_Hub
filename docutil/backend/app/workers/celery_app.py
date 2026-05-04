"""
Celery application configuration for the Document Utilization System.

Defines the Celery instance, serialization settings, task routing,
retry policies, and periodic beat schedule.
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "document_utilization",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
)

# 워커 모듈에서 정의된 태스크를 자동으로 발견하여 등록한다
celery_app.autodiscover_tasks(
    [
        "app.workers.document_processor",
        "app.workers.embedding_generator",
        "app.workers.report_generator",
        "app.workers.evaluation_runner",
        # Phase 4 S2 D4: DocumentV2 → 파일 포맷 비동기 export.
        "app.workers.export_worker",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "workers.document_processor.*": {"queue": "document_processing"},
        "workers.embedding_generator.*": {"queue": "embedding"},
        "workers.report_generator.*": {"queue": "report_generation"},
        "workers.evaluation_runner.*": {"queue": "evaluation"},
        # Phase 4 S2 D4: export_worker 전용 큐.
        "workers.export_worker.*": {"queue": "document_export"},
    },
    task_default_retry_delay=60,
    task_max_retries=3,
    beat_schedule={
        "aggregate-metrics": {
            "task": "workers.document_processor.aggregate_metrics",
            "schedule": 300.0,  # every 5 minutes
        },
        "daily-evaluation": {
            "task": "workers.evaluation_runner.run_scheduled_evaluation",
            "schedule": crontab(hour=3, minute=0),
        },
    },
)
