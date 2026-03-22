from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models.database import init_db
from app.routes.backtest import router as backtest_router
from app.routes.data import router as data_router
from app.routes.performance import router as performance_router
from app.routes.portfolio import live_paper_trading_service, router as portfolio_router
from app.routes.strategy import router as strategy_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield
    await live_paper_trading_service.stop()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Production-ready algorithmic trading bot and backtesting engine.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_router, prefix=settings.api_prefix)
app.include_router(strategy_router, prefix=settings.api_prefix)
app.include_router(backtest_router, prefix=settings.api_prefix)
app.include_router(portfolio_router, prefix=settings.api_prefix)
app.include_router(performance_router, prefix=settings.api_prefix)


@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.app_env}
