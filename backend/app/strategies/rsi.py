import pandas as pd

from app.models.domain import SignalRecord
from app.strategies.base import BaseStrategy
from app.utils.indicators import compute_rsi


class RSIStrategy(BaseStrategy):
    key = "rsi"
    name = "RSI Reversion"
    description = "Buys when RSI is oversold and sells when RSI is overbought."
    default_parameters = {"period": 14, "oversold": 30, "overbought": 70}

    def enrich(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df["rsi"] = compute_rsi(df["close"], int(self.parameters["period"]))
        return df

    def generate_signals(self, data: pd.DataFrame) -> list[SignalRecord]:
        df = self.enrich(data)
        signals: list[SignalRecord] = []
        for timestamp, row in df.iterrows():
            signal = "HOLD"
            if row["rsi"] < float(self.parameters["oversold"]):
                signal = "BUY"
            elif row["rsi"] > float(self.parameters["overbought"]):
                signal = "SELL"
            signals.append(
                SignalRecord(
                    timestamp=timestamp.to_pydatetime(),
                    close=float(row["close"]),
                    signal=signal,  # type: ignore[arg-type]
                    metadata={"rsi": round(float(row["rsi"]), 2)},
                )
            )
        return signals
