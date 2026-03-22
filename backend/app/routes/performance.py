from fastapi import APIRouter

from app.routes.backtest import portfolio_service

router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("")
def get_performance():
    snapshot = portfolio_service.get_snapshot()
    return {
        "equity": snapshot.equity,
        "cash": snapshot.cash,
        "realized_pnl": snapshot.realized_pnl,
        "unrealized_pnl": snapshot.unrealized_pnl,
        "holdings_count": len(snapshot.holdings),
        "as_of": snapshot.as_of,
    }
