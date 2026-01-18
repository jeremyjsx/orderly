import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from decimal import Decimal

from app.db.session import SessionDep
from app.modules.cart.models import Cart, CartItem
from app.modules.orders.models import Order, OrderItem, OrderStatus
from app.modules.products.models import Product

VALID_TRANSITIONS: dict[str, set[str]] = {
    OrderStatus.PENDING.value: {
        OrderStatus.PROCESSING.value,
        OrderStatus.CANCELLED.value,
    },
    OrderStatus.PROCESSING.value: {
        OrderStatus.SHIPPED.value,
        OrderStatus.CANCELLED.value,
    },
    OrderStatus.SHIPPED.value: {OrderStatus.DELIVERED.value},
    OrderStatus.DELIVERED.value: set(),
    OrderStatus.CANCELLED.value: set(),
}


def validate_status_transition(current_status: str, new_status: str) -> None:
    """Validate if a status transition is allowed."""
    if current_status == new_status:
        raise ValueError(f"Order is already in status {new_status}")

    allowed_transitions = VALID_TRANSITIONS.get(current_status, set())
    if new_status not in allowed_transitions:
        if allowed_transitions:
            transitions_str = ", ".join(allowed_transitions)
        else:
            transitions_str = "none (final state)"
        raise ValueError(
            f"Cannot transition from {current_status} to {new_status}. "
            f"Allowed transitions: {transitions_str}"
        )


async def create_order_from_cart(
    session: SessionDep, cart_id: uuid.UUID, user_id: uuid.UUID
) -> Order:
    result = await session.execute(
        select(Cart)
        .where(Cart.id == cart_id)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
    )
    cart = result.scalar_one_or_none()
    if not cart:
        raise ValueError(f"Cart with id {cart_id} not found")

    if cart.user_id != user_id:
        raise ValueError(
            f"Cart with id {cart_id} does not belong to user with id {user_id}"
        )

    if not cart.items:
        raise ValueError(f"Cart with id {cart_id} has no items")

    order_total = Decimal("0.0")
    order_items_data = []

    for cart_item in cart.items:
        if not cart_item.product:
            raise ValueError(f"Cart item with id {cart_item.id} has no product")

        product = cart_item.product

        if not product.is_active:
            raise ValueError(f"Product with id {product.id} is not active")

        if product.stock < cart_item.quantity:
            raise ValueError(f"Product with id {product.id} has insufficient stock")

        item_subtotal = Decimal(str(cart_item.quantity)) * product.price
        order_total += item_subtotal
        order_items_data.append(
            {
                "product_id": product.id,
                "quantity": cart_item.quantity,
                "price": product.price,
                "subtotal": item_subtotal,
            }
        )

    order = Order(
        id=uuid.uuid4(),
        user_id=cart.user_id,
        status=OrderStatus.PENDING.value,
        total=order_total,
    )
    session.add(order)

    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise

    for item_data in order_items_data:
        order_item = OrderItem(
            id=uuid.uuid4(),
            order_id=order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            price=item_data["price"],
            subtotal=item_data["subtotal"],
        )
        session.add(order_item)

        product_result = await session.execute(
            select(Product)
            .where(Product.id == item_data["product_id"])
            .with_for_update()
        )
        product = product_result.scalar_one_or_none()
        if product:
            if product.stock < item_data["quantity"]:
                await session.rollback()
                raise ValueError(
                    f"Product with id {product.id} has insufficient stock. "
                    f"Available: {product.stock}, Requested: {item_data['quantity']}"
                )
            product.stock -= item_data["quantity"]

    for cart_item in cart.items:
        await session.delete(cart_item)

    await session.delete(cart)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise

    await session.refresh(order, ["items"])
    return order


async def get_order_by_id(session: SessionDep, order_id: uuid.UUID) -> Order | None:
    result = await session.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )
    return result.scalar_one_or_none()


async def get_user_orders(
    session: SessionDep,
    user_id: uuid.UUID,
    offset: int = 0,
    limit: int = 10,
    status: str | None = None,
) -> tuple[Sequence[Order], int]:
    query = select(Order).where(Order.user_id == user_id)

    if status is not None:
        query = query.where(Order.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    query = (
        query.options(selectinload(Order.items).selectinload(OrderItem.product))
        .offset(offset)
        .limit(limit)
        .order_by(Order.created_at.desc())
    )
    result = await session.execute(query)
    orders = result.scalars().all()

    return orders, total


async def list_all_orders(
    session: SessionDep,
    offset: int = 0,
    limit: int = 10,
    status: str | None = None,
) -> tuple[Sequence[Order], int]:
    """List all orders with pagination and optional filters (admin only)."""
    query = select(Order)

    if status is not None:
        query = query.where(Order.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    query = (
        query.options(selectinload(Order.items).selectinload(OrderItem.product))
        .offset(offset)
        .limit(limit)
        .order_by(Order.created_at.desc())
    )
    result = await session.execute(query)
    orders = result.scalars().all()

    return orders, total


async def update_order_status(
    session: SessionDep, order_id: uuid.UUID, status: OrderStatus
) -> Order:
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise ValueError(f"Order with id {order_id} not found")

    validate_status_transition(order.status, status.value)

    order.status = status.value
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise
    
    updated_order = await get_order_by_id(session, order_id)
    if not updated_order:
        raise ValueError(f"Order with id {order_id} not found after update")
    return updated_order


async def cancel_order(session: SessionDep, order_id: uuid.UUID) -> Order:
    order = await get_order_by_id(session, order_id)
    if not order:
        raise ValueError(f"Order with id {order_id} not found")

    validate_status_transition(order.status, OrderStatus.CANCELLED.value)

    for order_item in order.items:
        product_result = await session.execute(
            select(Product).where(Product.id == order_item.product_id).with_for_update()
        )
        product = product_result.scalar_one_or_none()
        if product:
            product.stock += order_item.quantity

    order.status = OrderStatus.CANCELLED.value
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise

    await session.refresh(order)
    return order
