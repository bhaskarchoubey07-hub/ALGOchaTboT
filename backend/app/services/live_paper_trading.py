import asyncio
from datetime import datetime, timezone

from fastapi import WebSocket

from app.config import get_settings
from app.models.domain import LivePaperTradingStatus, PaperTradeRequest, PortfolioSnapshot
from app.services.market_data import MarketDataService
from app.services.portfolio_service import PortfolioService
from app.services.trading_engine import TradingEngine


class WebSocketConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_json(self, payload: dict) -> None:
        stale_connections: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_json(payload)
            except Exception:
                stale_connections.append(connection)
        for connection in stale_connections:
            self.disconnect(connection)


class LivePaperTradingService:
    def __init__(self, market_data_service: MarketDataService, portfolio_service: PortfolioService):
        settings = get_settings()
        self.settings = settings
        self.market_data_service = market_data_service
        self.portfolio_service = portfolio_service
        self.engine = TradingEngine(initial_cash=settings.initial_cash, fee_rate=settings.transaction_cost)
        self.manager = WebSocketConnectionManager()
        self.symbol: str | None = None
        self.provider: str | None = None
        self.poll_interval_seconds = settings.live_poll_interval_seconds
        self.latest_price: float | None = None
        self.last_update: datetime | None = None
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    def _empty_snapshot(self) -> PortfolioSnapshot:
        return PortfolioSnapshot(
            as_of=datetime.now(timezone.utc),
            cash=self.engine.state.cash,
            equity=self.engine.state.cash,
            realized_pnl=self.engine.state.realized_pnl,
            unrealized_pnl=0.0,
            holdings=[],
        )

    def _build_snapshot(self) -> PortfolioSnapshot:
        timestamp = self.last_update or datetime.now(timezone.utc)
        if self.symbol and self.latest_price is not None:
            prices = {self.symbol: self.latest_price}
        else:
            prices = {}
        return self.engine.snapshot(prices, timestamp)

    def status(self) -> LivePaperTradingStatus:
        snapshot = self._build_snapshot() if (self.symbol or self.engine.state.positions) else self._empty_snapshot()
        return LivePaperTradingStatus(
            active=self._task is not None and not self._task.done(),
            symbol=self.symbol,
            provider=self.provider,  # type: ignore[arg-type]
            poll_interval_seconds=self.poll_interval_seconds if self.symbol else None,
            latest_price=self.latest_price,
            last_update=self.last_update,
            portfolio=snapshot,
            recent_trades=self.engine.state.trades[-10:],
        )

    async def start(self, symbol: str, provider: str, poll_interval_seconds: int) -> LivePaperTradingStatus:
        async with self._lock:
            await self.stop()
            self.engine = TradingEngine(initial_cash=self.settings.initial_cash, fee_rate=self.settings.transaction_cost)
            self.symbol = symbol.upper()
            self.provider = provider
            self.poll_interval_seconds = poll_interval_seconds
            self.latest_price = None
            self.last_update = None
            await self._refresh_price()
            self._task = asyncio.create_task(self._poll_prices(), name=f"live-paper-{self.symbol}")
        return self.status()

    async def stop(self) -> None:
        task = self._task
        self._task = None
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def execute_trade(self, request: PaperTradeRequest):
        if self.symbol is None or self.latest_price is None:
            raise ValueError("Start a live paper-trading session before placing trades.")
        if request.symbol.upper() != self.symbol:
            raise ValueError(f"Active live session is running for {self.symbol}.")

        timestamp = datetime.now(timezone.utc)
        if request.side == "BUY":
            allocation_cash = self.engine.state.cash * request.allocation_pct
            trade = self.engine.execute_buy(
                symbol=self.symbol,
                timestamp=timestamp,
                price=self.latest_price,
                allocation_cash=allocation_cash,
                reason="live_paper_trade_buy",
            )
        else:
            trade = self.engine.execute_sell(
                symbol=self.symbol,
                timestamp=timestamp,
                price=self.latest_price,
                quantity=request.quantity,
                reason="live_paper_trade_sell",
            )

        if trade is None:
            raise ValueError("Trade could not be executed with the current live portfolio state.")

        snapshot = self._build_snapshot()
        self.portfolio_service.update_snapshot(snapshot)
        await self.manager.broadcast_json(
            {
                "type": "trade",
                "trade": trade.model_dump(mode="json"),
                "portfolio": snapshot.model_dump(mode="json"),
                "status": self.status().model_dump(mode="json"),
            }
        )
        return trade, snapshot

    async def _poll_prices(self) -> None:
        assert self.symbol is not None
        assert self.provider is not None
        while True:
            try:
                await self._refresh_price()
                snapshot = self._build_snapshot()
                await self.manager.broadcast_json(
                    {
                        "type": "price_tick",
                        "symbol": self.symbol,
                        "price": self.latest_price,
                        "timestamp": self.last_update.isoformat() if self.last_update else None,
                        "portfolio": snapshot.model_dump(mode="json"),
                        "status": self.status().model_dump(mode="json"),
                    }
                )
            except Exception as exc:
                await self.manager.broadcast_json({"type": "error", "message": str(exc)})
            await asyncio.sleep(self.poll_interval_seconds)

    async def _refresh_price(self) -> None:
        assert self.symbol is not None
        assert self.provider is not None
        price, timestamp = await asyncio.to_thread(
            self.market_data_service.get_live_price,
            self.symbol,
            self.provider,
        )
        self.latest_price = price
        self.last_update = timestamp
        snapshot = self._build_snapshot()
        self.portfolio_service.update_snapshot(snapshot)
