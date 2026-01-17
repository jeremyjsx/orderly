import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import SessionDep, get_current_user
from app.modules.cart.repo import (
    add_item_to_cart,
    clear_cart,
    get_cart_by_user_id,
    get_cart_item_by_id,
    get_or_create_active_cart,
    remove_cart_item,
    update_cart_item_quantity,
)
from app.modules.cart.schemas import (
    CartItemCreate,
    CartItemUpdate,
    CartItemWithProduct,
    CartPublic,
    CartTotals,
    ProductInfo,
)
from app.modules.users.models import User

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/me", response_model=CartPublic)
async def get_my_cart(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> CartPublic:
    cart = await get_or_create_active_cart(session, current_user.id)

    items = []
    subtotal = 0.0
    total_quantity = 0

    for item in cart.items or []:
        if not item.product:
            continue
        item_subtotal = item.quantity * item.product.price
        subtotal += item_subtotal
        total_quantity += item.quantity

        items.append(
            CartItemWithProduct(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                product=ProductInfo(
                    id=item.product.id,
                    name=item.product.name,
                    price=item.product.price,
                    image_url=item.product.image_url,
                ),
                subtotal=item_subtotal,
            )
        )

    totals = CartTotals(
        subtotal=subtotal,
        total_items=len(items),
        total_quantity=total_quantity,
        grand_total=subtotal,
    )

    return CartPublic(
        id=cart.id,
        user_id=cart.user_id,
        items=items,
        totals=totals,
    )


@router.post(
    "/items", response_model=CartItemWithProduct, status_code=status.HTTP_201_CREATED
)
async def add_item_to_my_cart(
    payload: CartItemCreate,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> CartItemWithProduct:
    cart = await get_or_create_active_cart(session, current_user.id)

    try:
        cart_item = await add_item_to_cart(session, cart.id, payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    if not cart_item.product:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Product information not available",
        )

    return CartItemWithProduct(
        id=cart_item.id,
        product_id=cart_item.product_id,
        quantity=cart_item.quantity,
        product=ProductInfo(
            id=cart_item.product.id,
            name=cart_item.product.name,
            price=cart_item.product.price,
            image_url=cart_item.product.image_url,
        ),
        subtotal=cart_item.quantity * cart_item.product.price,
    )


@router.put("/items/{item_id}", response_model=CartItemWithProduct)
async def update_cart_item(
    item_id: uuid.UUID,
    payload: CartItemUpdate,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> CartItemWithProduct:
    cart_item = await get_cart_item_by_id(session, item_id)
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    if cart_item.cart.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this cart item",
        )

    try:
        updated_item = await update_cart_item_quantity(
            session, item_id, payload.quantity
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    if not updated_item.product:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Product information not available",
        )

    return CartItemWithProduct(
        id=updated_item.id,
        product_id=updated_item.product_id,
        quantity=updated_item.quantity,
        product=ProductInfo(
            id=updated_item.product.id,
            name=updated_item.product.name,
            price=updated_item.product.price,
            image_url=updated_item.product.image_url,
        ),
        subtotal=updated_item.quantity * updated_item.product.price,
    )


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_cart(
    item_id: uuid.UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> None:
    cart_item = await get_cart_item_by_id(session, item_id)
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    if cart_item.cart.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this cart item",
        )

    try:
        await remove_cart_item(session, item_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_my_cart(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> None:
    cart = await get_cart_by_user_id(session, current_user.id)

    if not cart:
        return

    try:
        await clear_cart(session, cart.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
