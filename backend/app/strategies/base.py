from abc import ABC, abstractmethod

import pandas as pd

from app.models.domain import SignalRecord, StrategyOption


class BaseStrategy(ABC):
    key: str
    name: str
    description: str
    default_parameters: dict[str, float | int | bool]

    def __init__(self, parameters: dict[str, float | int | bool] | None = None):
        merged = dict(self.default_parameters)
        if parameters:
            merged.update(parameters)
        self.parameters = merged

    @abstractmethod
    def enrich(self, data: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> list[SignalRecord]:
        raise NotImplementedError

    def option(self) -> StrategyOption:
        return StrategyOption(
            key=self.key,  # type: ignore[arg-type]
            name=self.name,
            description=self.description,
            default_parameters=self.default_parameters,
        )
