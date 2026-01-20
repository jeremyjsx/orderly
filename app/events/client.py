import logging
from typing import Any

import aio_pika
from aio_pika.abc import (
    AbstractChannel,
    AbstractConnection,
    AbstractExchange,
    AbstractQueue,
)

from app.core.config import settings
from app.events.base import Event

logger = logging.getLogger(__name__)

_connection: AbstractConnection | None = None
_channel: AbstractChannel | None = None
_exchange: AbstractExchange | None = None
_queues: dict[str, AbstractQueue] = {}


async def connect() -> None:
    """Initialize RabbitMQ connection with exchange and queues."""
    global _connection, _channel, _exchange, _queues

    try:
        _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        _channel = await _connection.channel()
        await _channel.set_publisher_confirms(True)
        
        _exchange = await _channel.declare_exchange(
            "orderly_events", aio_pika.ExchangeType.TOPIC, durable=True
        )

        order_created_queue = await _channel.declare_queue(
            "order_created",
            durable=True,
            arguments={
                "x-dead-letter-exchange": "orderly_events_dlx",
                "x-dead-letter-routing-key": "order.created.dlq",
            },
        )
        await order_created_queue.bind(_exchange, routing_key="order.created")
        _queues["order_created"] = order_created_queue

        payment_processed_queue = await _channel.declare_queue(
            "payment_processed",
            durable=True,
            arguments={
                "x-dead-letter-exchange": "orderly_events_dlx",
                "x-dead-letter-routing-key": "payment.processed.dlq",
            },
        )
        await payment_processed_queue.bind(_exchange, routing_key="payment.processed")
        _queues["payment_processed"] = payment_processed_queue

        dlx = await _channel.declare_exchange(
            "orderly_events_dlx", aio_pika.ExchangeType.TOPIC, durable=True
        )

        await _channel.declare_queue("order_created_dlq", durable=True)
        await _channel.declare_queue("payment_processed_dlq", durable=True)

        logger.info(
            "Connected to RabbitMQ. Exchange 'orderly_events', DLX, and queues created"
        )
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}", exc_info=True)
        raise


async def disconnect() -> None:
    """Close RabbitMQ connection gracefully."""
    global _connection, _channel, _exchange, _queues

    try:
        if _channel and not _channel.is_closed:
            await _channel.close()
    except Exception as e:
        logger.warning(f"Error closing channel: {e}")

    try:
        if _connection and not _connection.is_closed:
            await _connection.close()
    except Exception as e:
        logger.warning(f"Error closing connection: {e}")

    _channel = None
    _connection = None
    _exchange = None
    _queues = {}

    logger.info("Disconnected from RabbitMQ")


async def publish_event(
    event: Event,
    routing_key: str | None = None,
    correlation_id: str | None = None,
) -> bool:
    if not _exchange:
        logger.warning("RabbitMQ not connected, skipping event publication")
        return False

    if not _channel or _channel.is_closed:
        logger.warning("RabbitMQ channel not available, skipping event publication")
        return False

    try:
        routing_key = routing_key or event.event_type
        message_body = event.model_dump_json()
        correlation_id = correlation_id or str(event.event_id)

        message = aio_pika.Message(
            message_body.encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            message_id=str(event.event_id),
            correlation_id=correlation_id,
            timestamp=event.occurred_at,
            headers={
                "event_type": event.event_type,
                "event_version": str(event.event_version),
                "producer": event.producer,
            },
        )

        await _exchange.publish(
            message,
            routing_key=routing_key,
            mandatory=True,
        )

        logger.info(
            f"Published event {event.event_id} (type: '{event.event_type}', "
            f"routing_key: '{routing_key}')"
        )
        return True
    except (aio_pika.exceptions.MessageProcessError, ConnectionError) as e:
        logger.error(
            f"Message not routable or connection error for event {event.event_id}: {e}",
            exc_info=True,
        )
        return False
    except Exception as e:
        logger.error(
            f"Failed to publish event {event.event_id}: {e}",
            exc_info=True,
        )
        return False


async def is_connected() -> bool:
    """Check if RabbitMQ connection is active."""
    return (
        _connection is not None
        and not _connection.is_closed
        and _channel is not None
        and not _channel.is_closed
        and _exchange is not None
    )
