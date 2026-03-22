import pandas as pd

from app.models.domain import SignalRecord
from app.strategies.base import BaseStrategy


class MovingAverageCrossoverStrategy(BaseStrategy):
    key = "ma_crossover"
    name = "Moving Average Crossover"
    description = "Buys when short moving average crosses above long moving average."
    default_parameters = {"short_window": 20, "long_window": 50}

    def enrich(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df["short_ma"] = df["close"].rolling(window=int(self.parameters["short_window"])).mean()
        df["long_ma"] = df["close"].rolling(window=int(self.parameters["long_window"])).mean()
        return df.dropna()

    def generate_signals(self, data: pd.DataFrame) -> list[SignalRecord]:
        df = self.enrich(data)
        signals: list[SignalRecord] = []
        previous_state = 0
        for timestamp, row in df.iterrows():
            current_state = 1 if row["short_ma"] > row["long_ma"] else -1
            signal = "HOLD"
            if current_state == 1 and previous_state != 1:
                signal = "BUY"
            elif current_state == -1 and previous_state != -1:
                signal = "SELL"
            previous_state = current_state
            signals.append(
                SignalRecord(
                    timestamp=timestamp.to_pydatetime(),
                    close=float(row["close"]),
                    signal=signal,  # type: ignore[arg-type]
                    metadata={
                        "short_ma": round(float(row["short_ma"]), 4),
                        "long_ma": round(float(row["long_ma"]), 4),
                    },
                )
            )
        return signals
