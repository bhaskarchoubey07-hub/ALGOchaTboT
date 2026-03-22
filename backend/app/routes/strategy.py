from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import SessionLocal
from app.models.domain import OptimizationRequest, StrategyRunRequest
from app.models.orm import StrategyRunORM
from app.services.backtester import Backtester
from app.services.market_data import MarketDataService
from app.services.performance import ParameterOptimizer
from app.strategies.registry import get_strategy, list_strategies

router = APIRouter(prefix="/strategy", tags=["strategies"])
market_data_service = MarketDataService()
backtester = Backtester(market_data_service)
optimizer = ParameterOptimizer(backtester)


def optional_db():
    if SessionLocal is None:
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/options")
def get_strategy_options():
    return {"strategies": [option.model_dump() for option in list_strategies()]}


@router.post("/run")
def run_strategy(request: StrategyRunRequest, db: Session | None = Depends(optional_db)):
    try:
        strategy = get_strategy(request.strategy, request.parameters)
        data = market_data_service.fetch_ohlcv(
            symbol=request.symbol, period=request.period, interval=request.interval, provider=request.provider
        )
        signals = strategy.generate_signals(data)
        if db is not None:
            db.add(
                StrategyRunORM(
                    symbol=request.symbol,
                    strategy=request.strategy,
                    parameters=strategy.parameters,
                    signals=[signal.model_dump(mode="json") for signal in signals],
                )
            )
            db.commit()
        return {
            "symbol": request.symbol.upper(),
            "strategy": request.strategy,
            "parameters": strategy.parameters,
            "signals": [signal.model_dump(mode="json") for signal in signals],
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/optimize")
def optimize_strategy(request: OptimizationRequest):
    try:
        return optimizer.optimize(request, get_strategy)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
