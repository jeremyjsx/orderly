import uuid

from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(ge=1, default=1)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "quantity": 2,
            }
        }
    )


class CartItemPublic(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity: int


class ProductInfo(BaseModel):
    id: uuid.UUID
    name: str
    price: float
    image_url: str


class CartItemWithProduct(CartItemPublic):
    product_id: uuid.UUID = Field(exclude=True)
    product: ProductInfo
    subtotal: float = Field(description="quantity x product.price")


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)

    model_config = ConfigDict(json_schema_extra={"example": {"quantity": 3}})


class CartTotals(BaseModel):
    subtotal: float = Field(description="Sum of all item subtotals")
    total_items: int = Field(description="Number of distinct items in the cart")
    total_quantity: int = Field(description="Sum of all quantities")
    grand_total: float = Field(description="Total final (equal to subtotal for now)")


class CartPublic(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    items: list[CartItemWithProduct]
    totals: CartTotals
