import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sys

import pandas as pd
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.routes.backtest import portfolio_service
from app.routes.portfolio import live_paper_trading_service, paper_engine


@pytest.fixture
def sample_market_data() -> pd.DataFrame:
    index = pd.date_range("2025-01-01", periods=90, freq="D", tz="UTC")
    close = pd.Series(
        [100 + i * 0.4 + ((-1) ** i) * 1.5 for i in range(len(index))],
        index=index,
    )
    data = pd.DataFrame(index=index)
    data["open"] = close - 0.8
    data["high"] = close + 1.2
    data["low"] = close - 1.4
    data["close"] = close
    data["volume"] = [1_000_000 + i * 1_000 for i in range(len(index))]
    data.index.name = "timestamp"
    return data


@pytest.fixture(autouse=True)
def mock_market_data(monkeypatch: pytest.MonkeyPatch, sample_market_data: pd.DataFrame) -> None:
    from app.services.market_data import MarketDataService

    def fake_fetch_ohlcv(self, symbol: str, period: str | None = None, interval: str | None = None, provider: str = "yahoo", refresh: bool = False):
        return sample_market_data.copy()

    def fake_live_price(self, symbol: str, provider: str = "yahoo"):
        return float(sample_market_data.iloc[-1]["close"]), datetime.now(timezone.utc)

    monkeypatch.setattr(MarketDataService, "fetch_ohlcv", fake_fetch_ohlcv)
    monkeypatch.setattr(MarketDataService, "get_live_price", fake_live_price)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    paper_engine.state.cash = 100000.0
    paper_engine.state.realized_pnl = 0.0
    paper_engine.state.positions.clear()
    paper_engine.state.trades.clear()

    portfolio_service.last_snapshot.cash = 100000.0
    portfolio_service.last_snapshot.equity = 100000.0
    portfolio_service.last_snapshot.realized_pnl = 0.0
    portfolio_service.last_snapshot.unrealized_pnl = 0.0
    portfolio_service.last_snapshot.holdings = []


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def stop_live_service_after_test():
    yield
    asyncio.run(live_paper_trading_service.stop())
