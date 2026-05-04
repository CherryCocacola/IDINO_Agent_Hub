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
]
