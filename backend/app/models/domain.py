from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


SignalType = Literal["BUY", "SELL", "HOLD"]
StrategyType = Literal["rsi", "ma_crossover", "macd", "ml_predictor"]
DataProvider = Literal["yahoo", "alpha_vantage"]


class StrategyRunRequest(BaseModel):
    symbol: str = "AAPL"
    strategy: StrategyType
    period: str = "1y"
    interval: str = "1d"
    provider: DataProvider = "yahoo"
    parameters: dict[str, float | int | bool] = Field(default_factory=dict)


class BacktestRequest(BaseModel):
    symbol: str = "AAPL"
    strategy: StrategyType
    period: str = "2y"
    interval: str = "1d"
    provider: DataProvider = "yahoo"
    initial_cash: float = 100000.0
    fee_rate: float = 0.001
    position_size: float = Field(default=0.95, ge=0.01, le=1.0)
    stop_loss: float | None = Field(default=None, ge=0.0, le=1.0)
    take_profit: float | None = Field(default=None, ge=0.0, le=5.0)
    parameters: dict[str, float | int | bool] = Field(default_factory=dict)


class SignalRecord(BaseModel):
    timestamp: datetime
    close: float
    signal: SignalType
    metadata: dict[str, Any] = Field(default_factory=dict)


class Trade(BaseModel):
    timestamp: datetime
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: float
    price: float
    fee: float
    pnl: float = 0.0
    reason: str | None = None


class EquityPoint(BaseModel):
    timestamp: datetime
    equity: float
    cash: float
    holdings_value: float


class PerformanceMetrics(BaseModel):
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profit_factor: float | None


class BacktestResponse(BaseModel):
    symbol: str
    strategy: StrategyType
    parameters: dict[str, float | int | bool]
    metrics: PerformanceMetrics
    trades: list[Trade]
    equity_curve: list[EquityPoint]
    signals: list[SignalRecord]


class PortfolioPosition(BaseModel):
    symbol: str
    quantity: float
    average_cost: float
    market_price: float
    market_value: float
    unrealized_pnl: float


class PortfolioSnapshot(BaseModel):
    as_of: datetime
    cash: float
    equity: float
    realized_pnl: float
    unrealized_pnl: float
    holdings: list[PortfolioPosition]


class StrategyOption(BaseModel):
    key: StrategyType
    name: str
    description: str
    default_parameters: dict[str, float | int | bool]


class OptimizationRequest(BaseModel):
    symbol: str = "AAPL"
    strategy: StrategyType
    period: str = "2y"
    interval: str = "1d"
    provider: DataProvider = "yahoo"
    metric: Literal["total_return", "sharpe_ratio", "max_drawdown"] = "sharpe_ratio"
    search_space: dict[str, list[float | int]]
    initial_cash: float = 100000.0
    fee_rate: float = 0.001
    position_size: float = Field(default=0.95, ge=0.01, le=1.0)

    @field_validator("search_space")
    @classmethod
    def ensure_search_space(cls, value: dict[str, list[float | int]]) -> dict[str, list[float | int]]:
        if not value:
            raise ValueError("search_space must contain at least one parameter.")
        return value


class OptimizationResult(BaseModel):
    best_parameters: dict[str, float | int]
    best_score: float
    metric: str
    leaderboard: list[dict[str, Any]]


class StrategyComparisonRequest(BaseModel):
    symbol: str = "AAPL"
    strategies: list[StrategyType]
    period: str = "2y"
    interval: str = "1d"
    provider: DataProvider = "yahoo"
    initial_cash: float = 100000.0
    fee_rate: float = 0.001
    position_size: float = Field(default=0.95, ge=0.01, le=1.0)
    parameters: dict[str, dict[str, float | int | bool]] = Field(default_factory=dict)


class PaperTradeRequest(BaseModel):
    symbol: str = "AAPL"
    side: Literal["BUY", "SELL"]
    quantity: float | None = Field(default=None, gt=0.0)
    allocation_pct: float = Field(default=0.25, gt=0.0, le=1.0)
    provider: DataProvider = "yahoo"
    period: str = "5d"
    interval: str = "1d"


class LivePaperTradingStartRequest(BaseModel):
    symbol: str = "AAPL"
    provider: DataProvider = "yahoo"
    poll_interval_seconds: int = Field(default=5, ge=1, le=60)


class LivePaperTradingStatus(BaseModel):
    active: bool
    symbol: str | None = None
    provider: DataProvider | None = None
    poll_interval_seconds: int | None = None
    latest_price: float | None = None
    last_update: datetime | None = None
    portfolio: PortfolioSnapshot
    recent_trades: list[Trade] = Field(default_factory=list)
