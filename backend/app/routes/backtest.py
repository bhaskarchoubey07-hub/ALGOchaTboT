from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import SessionLocal
from app.models.domain import BacktestRequest, PortfolioSnapshot, StrategyComparisonRequest
from app.models.orm import BacktestResultORM
from app.services.backtester import Backtester
from app.services.market_data import MarketDataService
from app.services.portfolio_service import PortfolioService
from app.strategies.registry import get_strategy

router = APIRouter(prefix="/backtest", tags=["backtesting"])
market_data_service = MarketDataService()
backtester = Backtester(market_data_service)
portfolio_service = PortfolioService()


def optional_db():
    if SessionLocal is None:
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("")
def run_backtest(request: BacktestRequest, db: Session | None = Depends(optional_db)):
    try:
        strategy = get_strategy(request.strategy, request.parameters)
        result = backtester.run(
            symbol=request.symbol,
            strategy_name=request.strategy,
            strategy=strategy,
            period=request.period,
            interval=request.interval,
            provider=request.provider,
            initial_cash=request.initial_cash,
            fee_rate=request.fee_rate,
            position_size=request.position_size,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
        )
        last_equity_point = result.equity_curve[-1]
        snapshot = PortfolioSnapshot(
            as_of=last_equity_point.timestamp,
            cash=last_equity_point.cash,
            equity=last_equity_point.equity,
            realized_pnl=sum(trade.pnl for trade in result.trades if trade.side == "SELL"),
            unrealized_pnl=0.0,
            holdings=[],
        )
        portfolio_service.update_snapshot(snapshot, db=db)
        portfolio_service.store_trades(result.trades, db=db)
        if db is not None:
            db.add(
                BacktestResultORM(
                    symbol=request.symbol,
                    strategy=request.strategy,
                    parameters=result.parameters,
                    metrics=result.metrics.model_dump(),
                    equity_curve=[point.model_dump(mode="json") for point in result.equity_curve],
                    trades=[trade.model_dump(mode="json") for trade in result.trades],
                )
            )
            db.commit()
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/compare")
def compare_strategies(request: StrategyComparisonRequest):
    try:
        results = []
        for strategy_name in request.strategies:
            strategy = get_strategy(strategy_name, request.parameters.get(strategy_name, {}))
            result = backtester.run(
                symbol=request.symbol,
                strategy_name=strategy_name,
                strategy=strategy,
                period=request.period,
                interval=request.interval,
                provider=request.provider,
                initial_cash=request.initial_cash,
                fee_rate=request.fee_rate,
                position_size=request.position_size,
            )
            results.append(
                {
                    "strategy": strategy_name,
                    "parameters": strategy.parameters,
                    "metrics": result.metrics.model_dump(),
                }
            )
        return {"symbol": request.symbol.upper(), "results": results}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
