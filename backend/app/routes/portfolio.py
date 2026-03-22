from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.models.domain import LivePaperTradingStartRequest, PaperTradeRequest
from app.routes.backtest import portfolio_service
from app.services.live_paper_trading import LivePaperTradingService
from app.services.market_data import MarketDataService
from app.services.trading_engine import TradingEngine

router = APIRouter(prefix="/portfolio", tags=["portfolio"])
market_data_service = MarketDataService()
paper_engine = TradingEngine(initial_cash=100000.0)
live_paper_trading_service = LivePaperTradingService(market_data_service, portfolio_service)


@router.get("")
def get_portfolio():
    return portfolio_service.get_snapshot()


@router.post("/paper-trade")
async def paper_trade(request: PaperTradeRequest):
    try:
        live_status = live_paper_trading_service.status()
        if live_status.active and live_status.symbol == request.symbol.upper():
            trade, snapshot = await live_paper_trading_service.execute_trade(request)
            return {"trade": trade, "portfolio": snapshot, "live": True}

        latest_price, timestamp = market_data_service.get_live_price(symbol=request.symbol, provider=request.provider)
        if request.side == "BUY":
            allocation_cash = paper_engine.state.cash * request.allocation_pct
            trade = paper_engine.execute_buy(
                symbol=request.symbol,
                timestamp=timestamp,
                price=latest_price,
                allocation_cash=allocation_cash,
                reason="paper_trade_buy",
            )
        else:
            trade = paper_engine.execute_sell(
                symbol=request.symbol,
                timestamp=timestamp,
                price=latest_price,
                quantity=request.quantity,
                reason="paper_trade_sell",
            )
        if trade is None:
            raise ValueError("Trade could not be executed with the provided portfolio state.")
        snapshot = paper_engine.snapshot({request.symbol: latest_price}, timestamp)
        portfolio_service.update_snapshot(snapshot)
        return {"trade": trade, "portfolio": snapshot, "live": False}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/live/status")
def get_live_status():
    return live_paper_trading_service.status()


@router.post("/live/start")
async def start_live_paper_trading(request: LivePaperTradingStartRequest):
    try:
        return await live_paper_trading_service.start(
            symbol=request.symbol,
            provider=request.provider,
            poll_interval_seconds=request.poll_interval_seconds,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/live/stop")
async def stop_live_paper_trading():
    await live_paper_trading_service.stop()
    return {"stopped": True, "status": live_paper_trading_service.status()}


@router.websocket("/ws/paper-trading")
async def paper_trading_websocket(websocket: WebSocket):
    await live_paper_trading_service.manager.connect(websocket)
    try:
        await websocket.send_json(
            {
                "type": "snapshot",
                "status": live_paper_trading_service.status().model_dump(mode="json"),
            }
        )
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        live_paper_trading_service.manager.disconnect(websocket)
    finally:
        live_paper_trading_service.manager.disconnect(websocket)
