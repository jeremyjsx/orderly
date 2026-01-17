import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import SessionDep, get_current_user, require_admin
from app.core.schemas import PaginatedResponse
from app.modules.cart.repo import get_cart_by_user_id
from app.modules.orders.models import OrderStatus
from app.modules.orders.repo import (
    cancel_order,
    create_order_from_cart,
    get_order_by_id,
    get_user_orders,
    update_order_status,
)
from app.modules.orders.schemas import (
    OrderCreate,
    OrderItemPublic,
    OrderPublic,
    OrderStatusUpdate,
)
from app.modules.products.schemas import ProductPublic
from app.modules.users.models import User

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderPublic, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> OrderPublic:
    cart = await get_cart_by_user_id(session, current_user.id)
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active cart found",
        )

    try:
        order = await create_order_from_cart(session, cart.id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return _order_to_public(order)


@router.get("/me", response_model=PaginatedResponse[OrderPublic])
async def get_my_orders(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        default=10, ge=1, le=100, description="Maximum number of records"
    ),
    status: str | None = Query(
        default=None,
        description=(
            "Filter by order status "
            "(pending, processing, shipped, delivered, cancelled)"
        ),
    ),
) -> PaginatedResponse[OrderPublic]:
    """List authenticated user orders with pagination and optional filters."""
    orders, total = await get_user_orders(
        session, current_user.id, offset=offset, limit=limit, status=status
    )

    items = [_order_to_public(order) for order in orders]

    return PaginatedResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get("/{order_id}", response_model=OrderPublic)
async def get_order(
    order_id: uuid.UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> OrderPublic:
    order = await get_order_by_id(session, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this order",
        )

    return _order_to_public(order)


@router.patch("/{order_id}/cancel", response_model=OrderPublic)
async def cancel_my_order(
    order_id: uuid.UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> OrderPublic:
    order = await get_order_by_id(session, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to cancel this order",
        )

    try:
        cancelled_order = await cancel_order(session, order_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return _order_to_public(cancelled_order)


@router.patch("/{order_id}/status", response_model=OrderPublic)
async def update_order_status_handler(
    order_id: uuid.UUID,
    payload: OrderStatusUpdate,
    session: SessionDep,
    admin_user: User = Depends(require_admin),
) -> OrderPublic:
    try:
        updated_order = await update_order_status(session, order_id, payload.status)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return _order_to_public(updated_order)


def _order_to_public(order) -> OrderPublic:
    items = []
    for item in order.items or []:
        product_public = None
        if item.product:
            product_public = ProductPublic(
                id=item.product.id,
                name=item.product.name,
                description=item.product.description,
                price=item.product.price,
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
                price=item.price,
                subtotal=item.subtotal,
                product=product_public,
            )
        )

    return OrderPublic(
        id=order.id,
        user_id=order.user_id,
        status=OrderStatus(order.status),
        total=order.total,
        items=items,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
