import logging
import uuid
from datetime import UTC, datetime

from app.events.orders.events import OrderCreatedEvent, OrderCreatedPayload
from app.modules.orders.models import Order
from app.modules.orders.schemas import OrderItemPublic
from app.modules.products.schemas import ProductPublic

logger = logging.getLogger(__name__)


def order_to_created_event(order: Order) -> OrderCreatedEvent:
    """
    Convert an Order model to an OrderCreatedEvent.
    
    Args:
        order: The order model to convert
        
    Returns:
        OrderCreatedEvent with order data
        
    Raises:
        ValueError: If order data is invalid
    """
    if not order.id:
        raise ValueError("Order ID is required")
    
    if not order.user_id:
        raise ValueError("User ID is required")
    
    if order.total is None or float(order.total) <= 0:
        raise ValueError(f"Invalid order total: {order.total}")
    
    items = []
    if not order.items:
        logger.warning(f"Order {order.id} has no items, creating event anyway")

        for item in order.items:
            if not item.product_id:
                logger.warning(
                    f"Order item {item.id} has no product_id, skipping"
                )
                continue
                
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

            if item.quantity <= 0:
                logger.warning(
                    f"Order item {item.id} has invalid quantity: {item.quantity}"
                )
                continue

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
