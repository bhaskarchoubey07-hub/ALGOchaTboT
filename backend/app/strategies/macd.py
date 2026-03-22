import pandas as pd

from app.models.domain import SignalRecord
from app.strategies.base import BaseStrategy
from app.utils.indicators import compute_macd


class MACDStrategy(BaseStrategy):
    key = "macd"
    name = "MACD Crossover"
    description = "Buys when MACD crosses above the signal line and sells on downward crossover."
    default_parameters = {"fast_period": 12, "slow_period": 26, "signal_period": 9}

    def enrich(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        macd_line, signal_line, histogram = compute_macd(
            df["close"],
            int(self.parameters["fast_period"]),
            int(self.parameters["slow_period"]),
            int(self.parameters["signal_period"]),
        )
        df["macd"] = macd_line
        df["signal_line"] = signal_line
        df["histogram"] = histogram
        return df.dropna()

    def generate_signals(self, data: pd.DataFrame) -> list[SignalRecord]:
        df = self.enrich(data)
        signals: list[SignalRecord] = []
        previous_state = 0
        for timestamp, row in df.iterrows():
            current_state = 1 if row["macd"] > row["signal_line"] else -1
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
                        "macd": round(float(row["macd"]), 4),
                        "signal_line": round(float(row["signal_line"]), 4),
                    },
                )
            )
        return signals
