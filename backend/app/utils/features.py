import pandas as pd
import numpy as np

from app.utils.indicators import compute_macd, compute_rsi


def build_ml_feature_frame(data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy()
    df["return_1"] = df["close"].pct_change(1)
    df["return_5"] = df["close"].pct_change(5)
    df["return_10"] = df["close"].pct_change(10)
    df["volatility_10"] = df["close"].pct_change().rolling(10).std()
    df["sma_10"] = df["close"].rolling(10).mean()
    df["sma_20"] = df["close"].rolling(20).mean()
    df["sma_gap"] = df["sma_10"] / df["sma_20"] - 1
    df["rsi_14"] = compute_rsi(df["close"], 14)
    macd_line, signal_line, histogram = compute_macd(df["close"])
    df["macd"] = macd_line
    df["macd_signal"] = signal_line
    df["macd_hist"] = histogram
    df["volume_change"] = df["volume"].pct_change().replace([np.inf, -np.inf], pd.NA)
    df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)
    return df.dropna()
