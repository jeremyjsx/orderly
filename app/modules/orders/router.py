import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from app.api.deps import (
    SessionDep,
    get_current_user,
    get_current_user_websocket,
    require_admin,
    require_driver,
)
from app.core.schemas import PaginatedResponse
from app.events.orders.websocket_manager import get_websocket_manager
from app.modules.cart.repo import get_cart_by_user_id
from app.modules.orders.models import OrderStatus
from app.modules.orders.repo import (
    assign_driver_to_order,
    cancel_order,
    create_order_from_cart,
    get_order_by_id,
    get_user_orders,
    list_all_orders,
    list_available_orders,
    list_my_deliveries,
    update_order_status,
)
from app.modules.orders.schemas import (
    OrderCreate,
    OrderItemPublic,
    OrderPublic,
    OrderStatusUpdate,
)
from app.modules.products.schemas import ProductPublic
from app.modules.users.models import Role, User

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


@router.get("/", response_model=PaginatedResponse[OrderPublic])
async def list_orders(
    session: SessionDep,
    admin_user: User = Depends(require_admin),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        default=10, ge=1, le=100, description="Maximum number of records"
    ),
    order_status: OrderStatus | None = Query(
        default=None,
        alias="status",
        description="Filter by order status",
    ),
) -> PaginatedResponse[OrderPublic]:
    """List all orders with pagination and optional filters (admin only)."""
    status_value = order_status.value if order_status else None
    orders, total = await list_all_orders(
        session, offset=offset, limit=limit, status=status_value
    )

    items = [_order_to_public(order) for order in orders]

    return PaginatedResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get("/me", response_model=PaginatedResponse[OrderPublic])
async def get_my_orders(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        default=10, ge=1, le=100, description="Maximum number of records"
    ),
    order_status: OrderStatus | None = Query(
        default=None,
        alias="status",
        description="Filter by order status",
    ),
) -> PaginatedResponse[OrderPublic]:
    """List authenticated user orders with pagination and optional filters."""
    status_value = order_status.value if order_status else None
    orders, total = await get_user_orders(
        session, current_user.id, offset=offset, limit=limit, status=status_value
    )

    items = [_order_to_public(order) for order in orders]

    return PaginatedResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get("/available", response_model=PaginatedResponse[OrderPublic])
async def get_available_orders(
    session: SessionDep,
    driver_user: User = Depends(require_driver),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        default=10, ge=1, le=100, description="Maximum number of records"
    ),
) -> PaginatedResponse[OrderPublic]:
    orders, total = await list_available_orders(session, offset=offset, limit=limit)

    items = [_order_to_public(order) for order in orders]

    return PaginatedResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get("/my-deliveries", response_model=PaginatedResponse[OrderPublic])
async def get_my_deliveries(
    session: SessionDep,
    driver_user: User = Depends(require_driver),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        default=10, ge=1, le=100, description="Maximum number of records"
    ),
) -> PaginatedResponse[OrderPublic]:
    orders, total = await list_my_deliveries(
        session, driver_user.id, offset=offset, limit=limit
    )

    items = [_order_to_public(order) for order in orders]

    return PaginatedResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.websocket("/ws/{order_id}")
async def track_order(
    websocket: WebSocket,
    order_id: uuid.UUID,
    session: SessionDep,
):
    current_user = await get_current_user_websocket(websocket, session)

    order = await get_order_by_id(session, order_id)
    if not order:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketDisconnect("Order not found")

    match current_user.role:
        case Role.ADMIN.value:
            has_permission = True
        case Role.USER.value:
            has_permission = order.user_id == current_user.id
        case Role.DRIVER.value:
            has_permission = order.driver_id == current_user.id
        case _:
            has_permission = False

    if not has_permission:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketDisconnect("You don't have permission to view this order")

    manager = get_websocket_manager()
    await manager.connect(websocket, current_user.id)
    await manager.subscribe_to_order(websocket, order_id)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)


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
            product_price = float(item.product.price)
            product_public = ProductPublic(
                id=item.product.id,
                name=item.product.name,
                description=item.product.description,
                price=product_price,
                stock=item.product.stock,
                category_id=item.product.category_id,
                image_url=item.product.image_url,
                is_active=item.product.is_active,
            )

        item_price = float(item.price)
        item_subtotal = float(item.subtotal)
        items.append(
            OrderItemPublic(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item_price,
                subtotal=item_subtotal,
                product=product_public,
            )
        )

    order_total = float(order.total)
    return OrderPublic(
        id=order.id,
        user_id=order.user_id,
        status=OrderStatus(order.status),
        total=order_total,
        items=items,
        created_at=order.created_at,
        updated_at=order.updated_at,
        driver_id=order.driver_id,
    )


@router.patch("/{order_id}/assign", response_model=OrderPublic)
async def assign_driver_to_order_handler(
    order_id: uuid.UUID,
    session: SessionDep,
    driver_user: User = Depends(require_driver),
) -> OrderPublic:
    try:
        assigned_order = await assign_driver_to_order(session, order_id, driver_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return _order_to_public(assigned_order)
