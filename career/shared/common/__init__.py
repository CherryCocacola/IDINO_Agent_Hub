"""
Shared common utilities for all microservices.
"""
from .auth import verify_token, get_current_user, JWTBearer
from .exceptions import (
    ServiceException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from .logging import setup_logging, get_logger
# Phase 7.2 — AgentHub 단일 진입점 클라이언트 (R2)
from .agenthub_client import (
    AgentHubClient,
    AgentHubError,
    get_agenthub_client,
)

# Kafka imports are optional (requires aiokafka)
try:
    from .kafka import KafkaProducer, KafkaConsumer
    _kafka_available = True
except ImportError:
    KafkaProducer = None
    KafkaConsumer = None
    _kafka_available = False

__all__ = [
    "verify_token",
    "get_current_user",
    "JWTBearer",
    "ServiceException",
    "NotFoundException",
    "UnauthorizedException",
    "ValidationException",
    "setup_logging",
    "get_logger",
    "KafkaProducer",
    "KafkaConsumer",
    # Phase 7.2 — AgentHub 클라이언트
    "AgentHubClient",
    "AgentHubError",
    "get_agenthub_client",
]
