import uuid

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.db.session import SessionDep
from app.modules.cart.models import Cart, CartItem, CartStatus
from app.modules.cart.schemas import CartItemCreate
from app.modules.products.models import Product


async def get_or_create_active_cart(session: SessionDep, user_id: uuid.UUID) -> Cart:
    result = await session.execute(
        select(Cart)
        .where(Cart.user_id == user_id, Cart.status == CartStatus.ACTIVE.value)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
    )
    cart = result.scalar_one_or_none()

    if not cart:
        cart = Cart(id=uuid.uuid4(), user_id=user_id, status=CartStatus.ACTIVE.value)
        session.add(cart)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise
        await session.refresh(cart, ["items"])

    return cart


async def get_cart_by_user_id(session: SessionDep, user_id: uuid.UUID) -> Cart | None:
    result = await session.execute(
        select(Cart)
        .where(Cart.user_id == user_id, Cart.status == CartStatus.ACTIVE.value)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
    )
    return result.scalar_one_or_none()


async def get_cart_by_id(session: SessionDep, cart_id: uuid.UUID) -> Cart | None:
    result = await session.execute(select(Cart).where(Cart.id == cart_id))
    return result.scalar_one_or_none()


async def add_item_to_cart(
    session: SessionDep, cart_id: uuid.UUID, item_data: CartItemCreate
) -> CartItem:
    product_result = await session.execute(
        select(Product).where(Product.id == item_data.product_id).with_for_update()
    )
    product = product_result.scalar_one_or_none()

    if not product:
        raise ValueError("Product not found")

    if not product.is_active:
        raise ValueError(f"Product with id {item_data.product_id} is not active")

    if product.stock < item_data.quantity:
        raise ValueError(f"Insufficient stock. Stock: {product.stock}")

    result = await session.execute(
        select(CartItem).where(
            CartItem.cart_id == cart_id, CartItem.product_id == item_data.product_id
        )
    )
    existing_item = result.scalar_one_or_none()
    if existing_item:
        new_quantity = existing_item.quantity + item_data.quantity

        if new_quantity > product.stock:
            raise ValueError(f"Insufficient stock. Stock: {product.stock}")

        existing_item.quantity = new_quantity

        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise

        await session.refresh(existing_item, ["product"])
        return existing_item

    else:
        cart_item = CartItem(
            id=uuid.uuid4(),
            cart_id=cart_id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
        )
        session.add(cart_item)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise
        await session.refresh(cart_item, ["product"])
    return cart_item


async def update_cart_item_quantity(
    session: SessionDep,
    item_id: uuid.UUID,
    quantity: int,
) -> CartItem:
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0")

    cart_item = await session.get(CartItem, item_id)
    if not cart_item:
        raise ValueError(f"Cart item with id {item_id} not found")

    product_result = await session.execute(
        select(Product).where(Product.id == cart_item.product_id).with_for_update()
    )
    product = product_result.scalar_one_or_none()

    if not product:
        raise ValueError(f"Product with id {cart_item.product_id} not found")

    if product.stock < quantity:
        raise ValueError(
            f"Insufficient stock. Available: {product.stock}, Requested: {quantity}"
        )

    cart_item.quantity = quantity
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise
    await session.refresh(cart_item, ["product"])
    return cart_item


async def remove_cart_item(
    session: SessionDep,
    item_id: uuid.UUID,
) -> None:
    cart_item = await session.get(CartItem, item_id)
    if not cart_item:
        raise ValueError(f"Cart item with id {item_id} not found")

    await session.delete(cart_item)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise


async def clear_cart(
    session: SessionDep,
    cart_id: uuid.UUID,
) -> None:
    result = await session.execute(select(CartItem).where(CartItem.cart_id == cart_id))
    items = result.scalars().all()

    for item in items:
        await session.delete(item)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise


async def get_cart_item_by_id(
    session: SessionDep,
    item_id: uuid.UUID,
) -> CartItem | None:
    result = await session.execute(
        select(CartItem)
        .where(CartItem.id == item_id)
        .options(selectinload(CartItem.product), selectinload(CartItem.cart))
    )
    return result.scalar_one_or_none()


async def delete_cart_items_by_product_id(
    session: SessionDep,
    product_id: uuid.UUID,
) -> int:
    """Delete all cart items containing a specific product.

    Returns the number of items deleted.
    """
    result = await session.execute(
        delete(CartItem).where(CartItem.product_id == product_id)
    )
    return result.rowcount


async def delete_cart_by_user_id(
    session: SessionDep,
    user_id: uuid.UUID,
) -> bool:
    """Delete user's active cart and all its items.

    Returns True if a cart was deleted, False if no cart found.
    """
    cart = await get_cart_by_user_id(session, user_id)
    if not cart:
        return False

    await session.execute(delete(CartItem).where(CartItem.cart_id == cart.id))

    await session.delete(cart)

    return True
