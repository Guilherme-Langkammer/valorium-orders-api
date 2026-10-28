from fastapi import FastAPI

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.orders import router as orders_router

app = FastAPI(
    title="Valorium Orders API",
    description="Public backend engineering portfolio project.",
    version="0.3.0",
)


app.include_router(health_router)
app.include_router(orders_router)
app.include_router(auth_router)
