from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.models.domain import PortfolioPosition, PortfolioSnapshot, Trade


@dataclass
class PositionState:
    quantity: float = 0.0
    average_cost: float = 0.0


@dataclass
class PortfolioState:
    cash: float
    realized_pnl: float = 0.0
    positions: dict[str, PositionState] = field(default_factory=dict)
    trades: list[Trade] = field(default_factory=list)


class TradingEngine:
    def __init__(self, initial_cash: float, fee_rate: float = 0.001):
        self.state = PortfolioState(cash=initial_cash)
        self.fee_rate = fee_rate

    def execute_buy(self, symbol: str, timestamp: datetime, price: float, allocation_cash: float, reason: str) -> Trade | None:
        if allocation_cash <= 0 or self.state.cash <= 0:
            return None
        spend = min(allocation_cash, self.state.cash)
        fee = spend * self.fee_rate
        quantity = max((spend - fee) / price, 0.0)
        if quantity <= 0:
            return None
        position = self.state.positions.setdefault(symbol, PositionState())
        new_cost_basis = position.average_cost * position.quantity + price * quantity
        position.quantity += quantity
        position.average_cost = new_cost_basis / position.quantity
        self.state.cash -= spend
        trade = Trade(timestamp=timestamp, symbol=symbol, side="BUY", quantity=quantity, price=price, fee=fee, reason=reason)
        self.state.trades.append(trade)
        return trade

    def execute_sell(self, symbol: str, timestamp: datetime, price: float, quantity: float | None = None, reason: str = "") -> Trade | None:
        position = self.state.positions.get(symbol)
        if position is None or position.quantity <= 0:
            return None
        quantity = position.quantity if quantity is None else min(quantity, position.quantity)
        if quantity <= 0:
            return None
        gross = quantity * price
        fee = gross * self.fee_rate
        pnl = (price - position.average_cost) * quantity - fee
        position.quantity -= quantity
        self.state.cash += gross - fee
        self.state.realized_pnl += pnl
        if position.quantity <= 1e-8:
            position.quantity = 0.0
            position.average_cost = 0.0
        trade = Trade(
            timestamp=timestamp,
            symbol=symbol,
            side="SELL",
            quantity=quantity,
            price=price,
            fee=fee,
            pnl=pnl,
            reason=reason,
        )
        self.state.trades.append(trade)
        return trade

    def snapshot(self, symbol_to_price: dict[str, float], as_of: datetime) -> PortfolioSnapshot:
        holdings: list[PortfolioPosition] = []
        unrealized_total = 0.0
        for symbol, position in self.state.positions.items():
            if position.quantity <= 0:
                continue
            market_price = symbol_to_price.get(symbol, position.average_cost)
            market_value = market_price * position.quantity
            unrealized = (market_price - position.average_cost) * position.quantity
            unrealized_total += unrealized
            holdings.append(
                PortfolioPosition(
                    symbol=symbol,
                    quantity=position.quantity,
                    average_cost=position.average_cost,
                    market_price=market_price,
                    market_value=market_value,
                    unrealized_pnl=unrealized,
                )
            )

        equity = self.state.cash + sum(position.market_value for position in holdings)
        return PortfolioSnapshot(
            as_of=as_of,
            cash=self.state.cash,
            equity=equity,
            realized_pnl=self.state.realized_pnl,
            unrealized_pnl=unrealized_total,
            holdings=holdings,
        )
