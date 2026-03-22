from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

from app.config import get_settings


class MarketDataService:
    def __init__(self):
        self.settings = get_settings()

    def _cache_path(self, symbol: str, period: str, interval: str, provider: str) -> Path:
        safe_symbol = symbol.replace("/", "_").upper()
        return self.settings.cache_dir / f"{provider}_{safe_symbol}_{period}_{interval}.csv"

    def fetch_ohlcv(
        self,
        symbol: str,
        period: str | None = None,
        interval: str | None = None,
        provider: str = "yahoo",
        refresh: bool = False,
    ) -> pd.DataFrame:
        period = period or self.settings.default_period
        interval = interval or self.settings.default_interval
        cache_path = self._cache_path(symbol, period, interval, provider)

        if cache_path.exists() and not refresh:
            cached = pd.read_csv(cache_path, parse_dates=["timestamp"], index_col="timestamp")
            if not cached.empty:
                return cached

        if provider == "alpha_vantage":
            raise NotImplementedError("Alpha Vantage adapter can be added with an API key; Yahoo Finance is enabled by default.")

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=False)
        if df.empty:
            raise ValueError(f"No data returned for {symbol}. Check the symbol or interval.")

        df = df.rename(
            columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}
        )[["open", "high", "low", "close", "volume"]]
        df.index.name = "timestamp"
        df.to_csv(cache_path)
        return df

    def to_records(self, data: pd.DataFrame) -> list[dict]:
        records = data.reset_index().to_dict(orient="records")
        for record in records:
            if hasattr(record["timestamp"], "isoformat"):
                record["timestamp"] = record["timestamp"].isoformat()
        return records

    def get_live_price(self, symbol: str, provider: str = "yahoo") -> tuple[float, datetime]:
        if provider == "alpha_vantage":
            raise NotImplementedError("Alpha Vantage live quotes are not implemented yet.")

        ticker = yf.Ticker(symbol)
        fast_info = getattr(ticker, "fast_info", None)
        last_price = None
        if fast_info:
            last_price = fast_info.get("lastPrice") or fast_info.get("regularMarketPrice")

        if last_price is None:
            intraday = ticker.history(period="1d", interval="1m", auto_adjust=False)
            if intraday.empty:
                raise ValueError(f"No live quote returned for {symbol}.")
            last_row = intraday.iloc[-1]
            return float(last_row["Close"]), datetime.now(timezone.utc)

        return float(last_price), datetime.now(timezone.utc)
