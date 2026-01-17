from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for queries."""

    offset: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(
        default=10, ge=1, le=100, description="Maximum number of records to return"
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    items: list[T] = Field(description="List of items in the current page")
    total: int = Field(description="Total number of available records")
    offset: int = Field(description="Number of records skipped")
    limit: int = Field(description="Limit of records per page")
    has_more: bool = Field(description="Indicates if there are more pages available")
