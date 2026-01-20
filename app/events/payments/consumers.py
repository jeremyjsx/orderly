import asyncio
import json
import logging
import signal
import uuid
from datetime import UTC, datetime
from typing import Set

import aio_pika
from aio_pika.abc import AbstractExchange, AbstractIncomingMessage

from app.core.config import settings
from app.events.orders.events import OrderCreatedEvent
from app.events.payments.events import PaymentProcessedEvent, PaymentProcessedPayload

logger = logging.getLogger(__name__)

_processed_events: Set[uuid.UUID] = set()

MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_BASE = 1.0


async def process_payment(order_event: OrderCreatedEvent) -> PaymentProcessedEvent:
    """
    Process payment for an order.
    
    Args:
        order_event: The order created event
        
    Returns:
        PaymentProcessedEvent with payment details
        
    Raises:
        ValueError: If order data is invalid
    """
    if not order_event.payload.order_id:
        raise ValueError("Order ID is required")
    if order_event.payload.total <= 0:
        raise ValueError(f"Invalid order total: {order_event.payload.total}")

    await asyncio.sleep(0.5)

    transaction_id = str(uuid.uuid4())
    payment_status = "success"

    logger.info(
        f"Processing payment for order {order_event.payload.order_id}, "
        f"amount: {order_event.payload.total}"
    )

    payload = PaymentProcessedPayload(
        order_id=order_event.payload.order_id,
        user_id=order_event.payload.user_id,
        amount=order_event.payload.total,
        payment_method="credit_card",
        transaction_id=transaction_id,
        status=payment_status,
    )

    return PaymentProcessedEvent(
        event_id=uuid.uuid4(),
        event_type="payment.processed",
        event_version=1,
        occurred_at=datetime.now(UTC),
        producer="payment-service",
        payload=payload,
    )


async def publish_payment_event(
    exchange: AbstractExchange, payment_event: PaymentProcessedEvent
) -> None:
    """
    Publish payment processed event to RabbitMQ.
    
    Args:
        exchange: RabbitMQ exchange
        payment_event: The payment event to publish
        
    Raises:
        Exception: If publishing fails
    """
    try:
        message_body = payment_event.model_dump_json()
        message = aio_pika.Message(
            message_body.encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            message_id=str(payment_event.event_id),
            correlation_id=str(payment_event.payload.order_id),
            timestamp=payment_event.occurred_at,
            headers={
                "event_type": payment_event.event_type,
                "event_version": str(payment_event.event_version),
                "producer": payment_event.producer,
            },
        )
        routing_key = "payment.processed"
        logger.debug(
            f"Publishing to exchange '{exchange.name}' with routing_key '{routing_key}'"
        )
        await exchange.publish(message, routing_key=routing_key, mandatory=True)
        logger.info(
            f"Published payment event {payment_event.event_id} "
            f"for order {payment_event.payload.order_id} "
            f"to routing_key '{routing_key}'"
        )
    except Exception as e:
        logger.error(
            f"Failed to publish payment event {payment_event.event_id}: {e}",
            exc_info=True,
        )
        raise


def is_event_processed(event_id: uuid.UUID) -> bool:
    """Check if an event has already been processed (idempotency check)."""
    return event_id in _processed_events


def mark_event_processed(event_id: uuid.UUID) -> None:
    """Mark an event as processed."""
    _processed_events.add(event_id)


async def handle_order_created(
    message: AbstractIncomingMessage, exchange: AbstractExchange
) -> None:
    """
    Handle order.created event with retry logic and idempotency.
    
    Args:
        message: The incoming RabbitMQ message
        exchange: RabbitMQ exchange for publishing responses
    """
    event_id: uuid.UUID | None = None
    retry_count = 0
    
    try:
        body = json.loads(message.body.decode())
        order_event = OrderCreatedEvent(**body)
        event_id = order_event.event_id

        logger.info(
            f"Received order.created event: {event_id}, "
            f"order: {order_event.payload.order_id}"
        )

        if is_event_processed(event_id):
            logger.warning(
                f"Event {event_id} already processed, skipping (idempotency)"
            )
            await message.ack()
            return

        retry_count = int(message.headers.get("x-retry-count", 0)) if message.headers else 0

        payment_event = await process_payment(order_event)
        await publish_payment_event(exchange, payment_event)

        mark_event_processed(event_id)

        logger.info(
            f"Payment processed for order {order_event.payload.order_id}, "
            f"transaction: {payment_event.payload.transaction_id}"
        )

        await message.ack()

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in message: {e}", exc_info=True)
        await message.reject(requeue=False)
    except ValueError as e:
        logger.error(f"Invalid event data: {e}", exc_info=True)
        await message.reject(requeue=False)
    except Exception as e:
        logger.error(
            f"Error processing payment for event {event_id}: {e}",
            exc_info=True,
        )

        if retry_count < MAX_RETRY_ATTEMPTS:
            retry_count += 1
            delay = RETRY_DELAY_BASE * (2 ** (retry_count - 1))
            
            logger.info(
                f"Retrying event {event_id} (attempt {retry_count}/{MAX_RETRY_ATTEMPTS}) "
                f"after {delay}s"
            )

            if message.headers is None:
                message.headers = {}
            message.headers["x-retry-count"] = retry_count

            await message.reject(requeue=True)
            await asyncio.sleep(delay)
        else:
            logger.error(
                f"Max retries exceeded for event {event_id}, sending to DLQ"
            )
            await message.reject(requeue=False)


async def start_payment_consumer() -> None:
    """
    Start the payment event consumer with graceful shutdown support.
    """
    connection = None
    channel = None
    shutdown_event = asyncio.Event()

    def signal_handler():
        """Handle shutdown signals."""
        logger.info("Shutdown signal received, stopping consumer...")
        shutdown_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    try:
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        channel = await connection.channel()

        exchange = await channel.declare_exchange(
            "orderly_events", aio_pika.ExchangeType.TOPIC, durable=True
        )

        order_queue = await channel.declare_queue(
            "order_created",
            durable=True,
            arguments={
                "x-dead-letter-exchange": "orderly_events_dlx",
                "x-dead-letter-routing-key": "order.created.dlq",
            },
        )
        await order_queue.bind(exchange, routing_key="order.created")

        dlx = await channel.declare_exchange(
            "orderly_events_dlx", aio_pika.ExchangeType.TOPIC, durable=True
        )
        dlq = await channel.declare_queue("order_created_dlq", durable=True)
        await dlq.bind(dlx, routing_key="order.created.dlq")

        logger.info(
            f"Created queue 'order_created' and bound to exchange '{exchange.name}' "
            f"with routing_key 'order.created'"
        )

        await channel.set_qos(prefetch_count=5)

        logger.info("Starting payment consumer...")

        async def message_handler(message: AbstractIncomingMessage) -> None:
            """Handle incoming messages."""
            if shutdown_event.is_set():
                await message.nack(requeue=True)
                return
            await handle_order_created(message, exchange)

        await order_queue.consume(message_handler)

        logger.info("Payment consumer started and waiting for messages...")

        await shutdown_event.wait()

        logger.info("Stopping payment consumer...")

    except asyncio.CancelledError:
        logger.info("Consumer cancelled")
    except Exception as e:
        logger.error(f"Error in payment consumer: {e}", exc_info=True)
        raise
    finally:
        if channel and not channel.is_closed:
            await channel.close()
        if connection and not connection.is_closed:
            await connection.close()
        logger.info("Payment consumer stopped")
