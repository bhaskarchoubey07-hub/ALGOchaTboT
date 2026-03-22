"use client";

import { useState } from "react";
import { BacktestResponse, fetchApi, StrategyType } from "@/services/api";

interface BacktestFormProps {
  onResult: (result: BacktestResponse) => void;
}

export function BacktestForm({ onResult }: BacktestFormProps) {
  const [symbol, setSymbol] = useState("AAPL");
  const [strategy, setStrategy] = useState<StrategyType>("rsi");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mlParameters = {
    train_split: 0.7,
    buy_threshold: 0.55,
    sell_threshold: 0.45,
    n_estimators: 200,
    max_depth: 5,
    random_state: 42
  };

  async function submit() {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchApi<BacktestResponse>("/backtest", {
        method: "POST",
        body: JSON.stringify({
          symbol,
          strategy,
          period: "2y",
          interval: "1d",
          provider: "yahoo",
          initial_cash: 100000,
          fee_rate: 0.001,
          position_size: 0.95,
          stop_loss: 0.05,
          take_profit: 0.12,
          parameters: strategy === "ml_predictor" ? mlParameters : {}
        })
      });
      onResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Backtest failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel stack">
      <div className="section-title">Backtesting Engine</div>
      <div className="form-grid">
        <label>
          Symbol
          <input value={symbol} onChange={(event) => setSymbol(event.target.value.toUpperCase())} />
        </label>
        <label>
          Strategy
          <select value={strategy} onChange={(event) => setStrategy(event.target.value as StrategyType)}>
            <option value="rsi">RSI</option>
            <option value="ma_crossover">MA Crossover</option>
            <option value="macd">MACD</option>
            <option value="ml_predictor">ML Predictor</option>
          </select>
        </label>
      </div>
      <button onClick={submit} disabled={loading}>
        {loading ? "Running..." : "Run Backtest"}
      </button>
      {error ? <div className="negative">{error}</div> : null}
    </div>
  );
}
