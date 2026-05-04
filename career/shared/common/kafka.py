"""
Kafka Producer/Consumer utilities for event-driven communication.
"""
import json
import os
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError

from .logging import get_logger

logger = get_logger(__name__)


class KafkaProducer:
    """Async Kafka producer for publishing events."""

    def __init__(self, bootstrap_servers: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        self._producer: Optional[AIOKafkaProducer] = None

    async def start(self) -> None:
        """Start the Kafka producer."""
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
            )
            await self._producer.start()
            logger.info(f"Kafka producer started: {self.bootstrap_servers}")

    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self._producer:
            await self._producer.stop()
            self._producer = None
            logger.info("Kafka producer stopped")

    async def send(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[List[tuple]] = None
    ) -> None:
        """
        Send a message to a Kafka topic.

        Args:
            topic: Topic name
            value: Message payload (dict)
            key: Message key for partitioning
            headers: Optional message headers
        """
        if not self._producer:
            await self.start()

        # Add metadata to the event
        event = {
            "event_id": f"{topic}_{datetime.utcnow().timestamp()}",
            "event_type": topic,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": value,
        }

        try:
            await self._producer.send_and_wait(
                topic=topic,
                value=event,
                key=key,
                headers=headers,
            )
            logger.debug(f"Event sent to {topic}: {event['event_id']}")
        except KafkaError as e:
            logger.error(f"Failed to send event to {topic}: {e}")
            raise

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


class KafkaConsumer:
    """Async Kafka consumer for subscribing to events."""

    def __init__(
        self,
        topics: List[str],
        group_id: str,
        bootstrap_servers: Optional[str] = None
    ):
        self.topics = topics
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._handlers: Dict[str, List[Callable]] = {}
        self._running = False

    def on(self, topic: str):
        """Decorator to register event handlers."""

        def decorator(func: Callable):
            if topic not in self._handlers:
                self._handlers[topic] = []
            self._handlers[topic].append(func)
            return func

        return decorator

    def add_handler(self, topic: str, handler: Callable) -> None:
        """Add an event handler for a topic."""
        if topic not in self._handlers:
            self._handlers[topic] = []
        self._handlers[topic].append(handler)

    async def start(self) -> None:
        """Start the Kafka consumer."""
        if self._consumer is None:
            self._consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="latest",
            )
            await self._consumer.start()
            logger.info(
                f"Kafka consumer started for topics {self.topics} "
                f"with group {self.group_id}"
            )

    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        self._running = False
        if self._consumer:
            await self._consumer.stop()
            self._consumer = None
            logger.info("Kafka consumer stopped")

    async def consume(self) -> None:
        """Start consuming messages and dispatching to handlers."""
        if not self._consumer:
            await self.start()

        self._running = True

        try:
            async for message in self._consumer:
                if not self._running:
                    break

                topic = message.topic
                value = message.value

                logger.debug(
                    f"Received event from {topic}: "
                    f"{value.get('event_id', 'unknown')}"
                )

                # Dispatch to registered handlers
                handlers = self._handlers.get(topic, [])
                for handler in handlers:
                    try:
                        await handler(value)
                    except Exception as e:
                        logger.error(
                            f"Error in handler for {topic}: {e}",
                            exc_info=True
                        )

        except Exception as e:
            logger.error(f"Consumer error: {e}", exc_info=True)
            raise

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


# Event Topics
class Topics:
    """Standard event topic names."""

    # Student events
    STUDENT_CREATED = "student.created"
    STUDENT_UPDATED = "student.updated"
    STUDENT_DELETED = "student.deleted"

    # Course events
    COURSE_ENROLLED = "course.enrolled"
    COURSE_COMPLETED = "course.completed"
    COURSE_DROPPED = "course.dropped"

    # Activity events
    ACTIVITY_STARTED = "activity.started"
    ACTIVITY_COMPLETED = "activity.completed"

    # Competency events
    COMPETENCY_CALCULATED = "competency.calculated"
    COMPETENCY_UPDATED = "competency.updated"

    # Roadmap events
    ROADMAP_GENERATED = "roadmap.generated"
    ROADMAP_UPDATED = "roadmap.updated"

    # AI events
    AI_ANALYSIS_COMPLETED = "ai.analysis.completed"
    AI_RECOMMENDATION_GENERATED = "ai.recommendation.generated"
