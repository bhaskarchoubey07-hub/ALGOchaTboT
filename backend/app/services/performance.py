import itertools
from math import sqrt

import numpy as np
import pandas as pd

from app.models.domain import OptimizationRequest, OptimizationResult, PerformanceMetrics
from app.utils.indicators import compute_drawdown


def calculate_metrics(equity_curve: pd.Series, trade_pnls: list[float], risk_free_rate: float) -> PerformanceMetrics:
    returns = equity_curve.pct_change().fillna(0.0)
    total_return = float((equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1) if len(equity_curve) > 1 else 0.0
    annualized_return = float((1 + total_return) ** (252 / max(len(equity_curve), 1)) - 1) if len(equity_curve) > 1 else 0.0
    excess_returns = returns - (risk_free_rate / 252)
    volatility = excess_returns.std()
    sharpe_ratio = float((excess_returns.mean() / volatility) * sqrt(252)) if volatility and not np.isnan(volatility) else 0.0
    drawdown = compute_drawdown(equity_curve).min()
    wins = [pnl for pnl in trade_pnls if pnl > 0]
    losses = [abs(pnl) for pnl in trade_pnls if pnl < 0]
    closed_trades = len([pnl for pnl in trade_pnls if pnl != 0])
    win_rate = float(len(wins) / closed_trades) if closed_trades else 0.0
    profit_factor = float(sum(wins) / sum(losses)) if losses else (None if wins else 0.0)

    return PerformanceMetrics(
        total_return=total_return,
        annualized_return=annualized_return,
        sharpe_ratio=sharpe_ratio,
        max_drawdown=float(drawdown if not np.isnan(drawdown) else 0.0),
        win_rate=win_rate,
        total_trades=closed_trades,
        profit_factor=profit_factor,
    )


class ParameterOptimizer:
    def __init__(self, backtester):
        self.backtester = backtester

    def optimize(self, request: OptimizationRequest, strategy_factory) -> OptimizationResult:
        param_names = list(request.search_space.keys())
        combinations = list(itertools.product(*(request.search_space[name] for name in param_names)))
        leaderboard: list[dict] = []

        for combination in combinations:
            parameters = dict(zip(param_names, combination, strict=True))
            strategy = strategy_factory(request.strategy, parameters=parameters)
            result = self.backtester.run(
                symbol=request.symbol,
                strategy_name=request.strategy,
                strategy=strategy,
                period=request.period,
                interval=request.interval,
                provider=request.provider,
                initial_cash=request.initial_cash,
                fee_rate=request.fee_rate,
                position_size=request.position_size,
            )
            score = getattr(result.metrics, request.metric)
            leaderboard.append({"parameters": parameters, "score": score, "metrics": result.metrics.model_dump()})

        reverse = request.metric != "max_drawdown"
        leaderboard.sort(key=lambda entry: entry["score"], reverse=reverse)
        best = leaderboard[0]
        return OptimizationResult(
            best_parameters=best["parameters"],
            best_score=best["score"],
            metric=request.metric,
            leaderboard=leaderboard[:10],
        )
