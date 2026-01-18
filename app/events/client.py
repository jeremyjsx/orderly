import logging

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
    global _connection, _channel, _exchange, _queues

    try:
        _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        _channel = await _connection.channel()
        _exchange = await _channel.declare_exchange(
            "orderly_events", aio_pika.ExchangeType.TOPIC, durable=True
        )

        order_created_queue = await _channel.declare_queue(
            "order_created", durable=True
        )

        await order_created_queue.bind(_exchange, routing_key="order.created")
        _queues["order_created"] = order_created_queue

        payment_processed_queue = await _channel.declare_queue(
            "payment_processed", durable=True
        )
        await payment_processed_queue.bind(_exchange, routing_key="payment.processed")
        _queues["payment_processed"] = payment_processed_queue

        logger.info(
            "Connected to RabbitMQ. Exchange 'orderly_events' and queues created"
        )
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        raise


async def disconnect() -> None:
    global _connection, _channel, _exchange, _queues

    if _channel:
        await _channel.close()
    if _connection:
        await _connection.close()

    _channel = None
    _connection = None
    _exchange = None
    _queues = {}

    logger.info("Disconnected from RabbitMQ")


async def publish_event(event: Event, routing_key: str | None = None) -> None:
    if not _exchange:
        logger.warning("RabbitMQ not connected, skipping event publication")
        return

    try:
        routing_key = routing_key or event.event_type
        message_body = event.model_dump_json()

        message = aio_pika.Message(
            message_body.encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await _exchange.publish(message, routing_key=routing_key)
        logger.info(f"Published event {event.event_id} with type '{event.event_type}'")
    except Exception as e:
        logger.error(f"Failed to publish event {event.event_id}: {e}", exc_info=True)
        raise


async def is_connected() -> bool:
    return _connection is not None and not _connection.is_closed
