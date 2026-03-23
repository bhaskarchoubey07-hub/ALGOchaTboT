import pandas as pd

from app.config import get_settings
from app.models.domain import BacktestResponse, EquityPoint, SignalRecord
from app.services.market_data import MarketDataService
from app.services.performance import calculate_metrics
from app.services.trading_engine import TradingEngine
from app.strategies.base import BaseStrategy


class Backtester:
    def __init__(self, market_data_service: MarketDataService | None = None):
        self.market_data_service = market_data_service or MarketDataService()
        self.settings = get_settings()

    def run(
        self,
        symbol: str,
        strategy_name: str,
        strategy: BaseStrategy,
        period: str,
        interval: str,
        provider: str,
        initial_cash: float,
        fee_rate: float,
        position_size: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
    ) -> BacktestResponse:
        data = self.market_data_service.fetch_ohlcv(symbol=symbol, period=period, interval=interval, provider=provider)
        signals = strategy.generate_signals(data)
        signal_map = {signal.timestamp: signal for signal in signals}
        trader = TradingEngine(initial_cash=initial_cash, fee_rate=fee_rate)
        equity_curve: list[EquityPoint] = []
        active_entry_price: float | None = None

        for timestamp, row in data.iterrows():
            current_ts = timestamp.to_pydatetime()
            price = float(row["close"])
            signal: SignalRecord | None = signal_map.get(current_ts)
            open_position = trader.state.positions.get(symbol)
            has_position = open_position is not None and open_position.quantity > 0

            if active_entry_price is not None:
                if stop_loss is not None and price <= active_entry_price * (1 - stop_loss):
                    trade = trader.execute_sell(symbol, current_ts, price, reason="stop_loss")
                    if trade:
                        active_entry_price = None
                        has_position = False
                elif take_profit is not None and price >= active_entry_price * (1 + take_profit):
                    trade = trader.execute_sell(symbol, current_ts, price, reason="take_profit")
                    if trade:
                        active_entry_price = None
                        has_position = False

            if signal and signal.signal == "BUY" and not has_position:
                allocation = trader.state.cash * position_size
                trade = trader.execute_buy(symbol, current_ts, price, allocation_cash=allocation, reason="signal_buy")
                if trade:
                    active_entry_price = price
                    has_position = True
            elif signal and signal.signal == "SELL" and has_position:
                trade = trader.execute_sell(symbol, current_ts, price, reason="signal_sell")
                if trade:
                    active_entry_price = None
                    has_position = False

            snapshot = trader.snapshot({symbol: price}, current_ts)
            equity_curve.append(
                EquityPoint(
                    timestamp=current_ts,
                    equity=snapshot.equity,
                    cash=snapshot.cash,
                    holdings_value=snapshot.equity - snapshot.cash,
                )
            )

        if trader.state.positions.get(symbol) and trader.state.positions[symbol].quantity > 0:
            final_price = float(data.iloc[-1]["close"])
            trader.execute_sell(symbol, data.index[-1].to_pydatetime(), final_price, reason="final_close")
            final_snapshot = trader.snapshot({symbol: final_price}, data.index[-1].to_pydatetime())
            equity_curve[-1] = EquityPoint(
                timestamp=data.index[-1].to_pydatetime(),
                equity=final_snapshot.equity,
                cash=final_snapshot.cash,
                holdings_value=final_snapshot.equity - final_snapshot.cash,
            )

        equity_series = pd.Series([point.equity for point in equity_curve], index=[point.timestamp for point in equity_curve])
        trade_pnls = [trade.pnl for trade in trader.state.trades if trade.side == "SELL"]
        metrics = calculate_metrics(equity_series, trade_pnls, self.settings.risk_free_rate)

        return BacktestResponse(
            symbol=symbol,
            strategy=strategy_name,  # type: ignore[arg-type]
            parameters=strategy.parameters,
            metrics=metrics,
            trades=trader.state.trades,
            equity_curve=equity_curve,
            signals=signals,
        )
