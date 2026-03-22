from app.strategies.base import BaseStrategy
from app.strategies.ma_crossover import MovingAverageCrossoverStrategy
from app.strategies.macd import MACDStrategy
from app.strategies.ml_predictor import MLPredictorStrategy
from app.strategies.rsi import RSIStrategy


STRATEGY_REGISTRY: dict[str, type[BaseStrategy]] = {
    RSIStrategy.key: RSIStrategy,
    MovingAverageCrossoverStrategy.key: MovingAverageCrossoverStrategy,
    MACDStrategy.key: MACDStrategy,
    MLPredictorStrategy.key: MLPredictorStrategy,
}


def get_strategy(strategy_name: str, parameters: dict | None = None) -> BaseStrategy:
    strategy_cls = STRATEGY_REGISTRY.get(strategy_name)
    if strategy_cls is None:
        supported = ", ".join(sorted(STRATEGY_REGISTRY))
        raise ValueError(f"Unsupported strategy '{strategy_name}'. Supported strategies: {supported}")
    return strategy_cls(parameters=parameters)


def list_strategies():
    return [strategy_cls().option() for strategy_cls in STRATEGY_REGISTRY.values()]
