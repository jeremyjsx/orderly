from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.cart.router import router as cart_router
from app.modules.products.router import router as products_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(products_router)
router.include_router(cart_router)
