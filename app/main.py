import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.interfaces.http.routes.market_data import router as market_data_router
from app.interfaces.http.routes.auth import router as auth_router
from app.interfaces.http.routes.portfolios import router as portfolios_router
from app.interfaces.http.routes.holdings import router as holdings_router
from app.interfaces.http.routes.performance import router as performance_router
from app.infrastructure.database import init_db, close_db
from app.infrastructure.cache import RedisCache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()
    await RedisCache.close()


app = FastAPI(
    title="Maravilla Smart Portfolio Backend",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS middleware
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
        frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Include routers
app.include_router(market_data_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(portfolios_router, prefix="/api/v1")
app.include_router(holdings_router, prefix="/api/v1")
app.include_router(performance_router, prefix="/api/v1")