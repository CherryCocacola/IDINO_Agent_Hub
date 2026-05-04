"""Integration Service Routers."""
from .worknet import router as worknet_router
from .university import router as university_router
from .hrd import router as hrd_router
from .sync import router as sync_router

__all__ = ["worknet_router", "university_router", "hrd_router", "sync_router"]
