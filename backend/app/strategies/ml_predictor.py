import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.models.domain import SignalRecord
from app.strategies.base import BaseStrategy
from app.utils.features import build_ml_feature_frame


class MLPredictorStrategy(BaseStrategy):
    key = "ml_predictor"
    name = "ML Predictor"
    description = "Uses technical features and a historical classifier to predict next-bar direction."
    default_parameters = {
        "train_split": 0.7,
        "buy_threshold": 0.55,
        "sell_threshold": 0.45,
        "n_estimators": 200,
        "max_depth": 5,
        "random_state": 42,
    }

    feature_columns = [
        "return_1",
        "return_5",
        "return_10",
        "volatility_10",
        "sma_gap",
        "rsi_14",
        "macd",
        "macd_signal",
        "macd_hist",
        "volume_change",
    ]

    def enrich(self, data: pd.DataFrame) -> pd.DataFrame:
        df = build_ml_feature_frame(data)
        if len(df) < 50:
            raise ValueError("Not enough data to train ML strategy. Use a longer period or smaller interval.")

        split_idx = max(int(len(df) * float(self.parameters["train_split"])), 30)
        split_idx = min(split_idx, len(df) - 1)

        train_df = df.iloc[:split_idx]
        predict_df = df.iloc[split_idx:]
        if predict_df.empty:
            raise ValueError("ML strategy has no out-of-sample rows to score. Increase the data period.")

        model = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=int(self.parameters["n_estimators"]),
                        max_depth=int(self.parameters["max_depth"]),
                        random_state=int(self.parameters["random_state"]),
                        min_samples_leaf=5,
                    ),
                ),
            ]
        )
        model.fit(train_df[self.feature_columns], train_df["target"])

        df["prediction_probability"] = model.predict_proba(df[self.feature_columns])[:, 1]
        df["dataset"] = "train"
        df.loc[predict_df.index, "dataset"] = "test"
        return df

    def generate_signals(self, data: pd.DataFrame) -> list[SignalRecord]:
        df = self.enrich(data)
        buy_threshold = float(self.parameters["buy_threshold"])
        sell_threshold = float(self.parameters["sell_threshold"])
        signals: list[SignalRecord] = []

        for timestamp, row in df.iterrows():
            signal = "HOLD"
            if row["dataset"] == "test":
                if row["prediction_probability"] >= buy_threshold:
                    signal = "BUY"
                elif row["prediction_probability"] <= sell_threshold:
                    signal = "SELL"
            signals.append(
                SignalRecord(
                    timestamp=timestamp.to_pydatetime(),
                    close=float(row["close"]),
                    signal=signal,  # type: ignore[arg-type]
                    metadata={
                        "prediction_probability": round(float(row["prediction_probability"]), 4),
                        "dataset": str(row["dataset"]),
                    },
                )
            )
        return signals
