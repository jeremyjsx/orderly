import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.db.session import SessionDep
from app.modules.cart.models import Cart, CartItem
from app.modules.orders.models import Order, OrderItem, OrderStatus
from app.modules.products.models import Product


async def create_order_from_cart(session: SessionDep, cart_id: uuid.UUID) -> Order:
    result = await session.execute(
        select(Cart)
        .where(Cart.id == cart_id)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
    )
    cart = result.scalar_one_or_none()
    if not cart:
        raise ValueError(f"Cart with id {cart_id} not found")

    if not cart.items:
        raise ValueError(f"Cart with id {cart_id} has no items")

    order_total = 0.0
    order_items_data = []

    for cart_item in cart.items:
        if not cart_item.product:
            raise ValueError(f"Cart item with id {cart_item.id} has no product")

        product = cart_item.product

        if not product.is_active:
            raise ValueError(f"Product with id {product.id} is not active")

        if product.stock < cart_item.quantity:
            raise ValueError(f"Product with id {product.id} has insufficient stock")

        item_subtotal = cart_item.quantity * product.price
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

        product = await session.get(Product, item_data["product_id"])
        if product:
            product.stock -= item_data["quantity"]

    for cart_item in cart.items:
        await session.delete(cart_item)

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


async def get_user_orders(session: SessionDep, user_id: uuid.UUID) -> Sequence[Order]:
    result = await session.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )
    return result.scalars().all()


async def update_order_status(
    session: SessionDep, order_id: uuid.UUID, status: OrderStatus
) -> Order:
    order = await session.get(Order, order_id)
    if not order:
        raise ValueError(f"Order with id {order_id} not found")
    order.status = status.value
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise
    await session.refresh(order)
    return order


async def cancel_order(session: SessionDep, order_id: uuid.UUID) -> Order:
    order = await get_order_by_id(session, order_id)
    if not order:
        raise ValueError(f"Order with id {order_id} not found")

    if order.status == OrderStatus.CANCELLED.value:
        raise ValueError(f"Order with id {order_id} is already cancelled")

    if order.status not in [OrderStatus.PENDING.value, OrderStatus.PROCESSING.value]:
        raise ValueError(f"Cannot cancel order with status {order.status}")

    for order_item in order.items:
        product = await session.get(Product, order_item.product_id)
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
