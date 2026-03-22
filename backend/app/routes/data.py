from fastapi import APIRouter, HTTPException, Query

from app.services.market_data import MarketDataService

router = APIRouter(prefix="/data", tags=["market-data"])
market_data_service = MarketDataService()


@router.get("/{symbol}")
def get_symbol_data(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    provider: str = Query(default="yahoo"),
    refresh: bool = Query(default=False),
):
    try:
        data = market_data_service.fetch_ohlcv(symbol=symbol, period=period, interval=interval, provider=provider, refresh=refresh)
        return {"symbol": symbol.upper(), "rows": len(data), "data": market_data_service.to_records(data)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
