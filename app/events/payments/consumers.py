import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime

import aio_pika
from aio_pika.abc import AbstractExchange, AbstractIncomingMessage

from app.core.config import settings
from app.events.orders.events import OrderCreatedEvent
from app.events.payments.events import PaymentProcessedEvent, PaymentProcessedPayload

logger = logging.getLogger(__name__)


async def process_payment(order_event: OrderCreatedEvent) -> PaymentProcessedEvent:
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
    try:
        message_body = payment_event.model_dump_json()
        message = aio_pika.Message(
            message_body.encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        routing_key = "payment.processed"
        logger.debug(
            f"Publishing to exchange '{exchange.name}' with routing_key '{routing_key}'"
        )
        await exchange.publish(message, routing_key=routing_key)
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


async def handle_order_created(
    message: AbstractIncomingMessage, exchange: AbstractExchange
) -> None:
    async with message.process():
        try:
            body = json.loads(message.body.decode())
            order_event = OrderCreatedEvent(**body)

            logger.info(
                f"Received order.created event: {order_event.event_id}, "
                f"order: {order_event.payload.order_id}"
            )

            payment_event = await process_payment(order_event)
            await publish_payment_event(exchange, payment_event)

            logger.info(
                f"Payment processed for order {order_event.payload.order_id}, "
                f"transaction: {payment_event.payload.transaction_id}"
            )

        except Exception as e:
            logger.error(f"Error processing payment: {e}", exc_info=True)
            raise


async def start_payment_consumer() -> None:
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()

    exchange = await channel.declare_exchange(
        "orderly_events", aio_pika.ExchangeType.TOPIC, durable=True
    )

    order_queue = await channel.declare_queue("order_created", durable=True)
    await order_queue.bind(exchange, routing_key="order.created")

    payment_queue = await channel.declare_queue("payment_processed", durable=True)
    await payment_queue.bind(exchange, routing_key="payment.processed")

    logger.info(
        f"Created queue 'payment_processed' and bound to exchange '{exchange.name}' "
        f"with routing_key 'payment.processed'"
    )

    await channel.set_qos(prefetch_count=5)

    logger.info("Starting payment consumer...")

    async def message_handler(message: AbstractIncomingMessage) -> None:
        await handle_order_created(message, exchange)

    await order_queue.consume(message_handler)

    try:
        await asyncio.Future()
    finally:
        await connection.close()
