import json
import logging
from typing import Any
from aiokafka import AIOKafkaProducer
from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level singleton — one producer shared across all requests
# AIOKafkaProducer is async, works natively with FastAPI's event loop
_producer: AIOKafkaProducer | None = None


async def get_kafka_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        raise RuntimeError("Kafka producer not started. Call start_kafka_producer() first.")
    return _producer


async def start_kafka_producer():
    """Called on FastAPI startup. Creates the persistent TCP connection to Kafka broker."""
    global _producer
    _producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        # key_serializer ensures messages with same key go to same partition
        # (e.g., same account_id = same partition = ordered delivery)
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        acks="all",             # Wait for all replicas to acknowledge (durability)
        retry_backoff_ms=500,   # Retry delay on transient failures
        request_timeout_ms=30000,
    )
    await _producer.start()
    logger.info("Kafka producer started.")


async def stop_kafka_producer():
    """Called on FastAPI shutdown. Flushes pending messages then closes connection."""
    global _producer
    if _producer:
        await _producer.stop()
        logger.info("Kafka producer stopped.")


async def publish_event(topic: str, event: dict[str, Any], key: str | None = None):
    """
    Generic publish function. All services call this.
    key = partition key (use account_id or customer_id for ordering guarantees)
    """
    producer = await get_kafka_producer()
    try:
        await producer.send_and_wait(topic, value=event, key=key)
        logger.debug(f"Published to {topic}: {event.get('event_type', 'unknown')}")
    except Exception as e:
        # Don't crash the main transaction — log and continue
        # In production: send to a dead-letter queue or retry via Celery
        logger.error(f"Failed to publish Kafka event to {topic}: {e}")