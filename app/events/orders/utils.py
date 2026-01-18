import uuid
from datetime import UTC, datetime

from app.events.orders.events import OrderCreatedEvent, OrderCreatedPayload
from app.modules.orders.models import Order
from app.modules.orders.schemas import OrderItemPublic
from app.modules.products.schemas import ProductPublic


def order_to_created_event(order: Order) -> OrderCreatedEvent:
    items = []

    for item in order.items or []:
        product_public = None
        if item.product:
            product_public = ProductPublic(
                id=item.product.id,
                name=item.product.name,
                description=item.product.description,
                price=float(item.product.price),
                stock=item.product.stock,
                category_id=item.product.category_id,
                image_url=item.product.image_url,
                is_active=item.product.is_active,
            )

        items.append(
            OrderItemPublic(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=float(item.price),
                subtotal=float(item.subtotal),
                product=product_public,
            )
        )

    payload = OrderCreatedPayload(
        order_id=order.id,
        user_id=order.user_id,
        total=float(order.total),
        items=items,
    )

    return OrderCreatedEvent(
        event_id=uuid.uuid4(),
        occurred_at=datetime.now(UTC),
        producer="orders-service",
        payload=payload,
    )
