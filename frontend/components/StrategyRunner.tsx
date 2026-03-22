"use client";

import { useEffect, useState } from "react";
import { fetchApi, SignalRecord, StrategyType } from "@/services/api";

interface StrategyRunnerProps {
  defaultSymbol?: string;
}

interface StrategyOption {
  key: StrategyType;
  name: string;
  description: string;
  default_parameters: Record<string, number | boolean>;
}

export function StrategyRunner({ defaultSymbol = "AAPL" }: StrategyRunnerProps) {
  const [symbol, setSymbol] = useState(defaultSymbol);
  const [strategy, setStrategy] = useState<StrategyType>("rsi");
  const [options, setOptions] = useState<StrategyOption[]>([]);
  const [signals, setSignals] = useState<SignalRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchApi<{ strategies: StrategyOption[] }>("/strategy/options")
      .then((data) => setOptions(data.strategies))
      .catch((err: Error) => setError(err.message));
  }, []);

  async function runStrategy() {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchApi<{ signals: SignalRecord[] }>("/strategy/run", {
        method: "POST",
        body: JSON.stringify({
          symbol,
          strategy,
          period: "1y",
          interval: "1d",
          provider: "yahoo",
          parameters: {}
        })
      });
      setSignals(result.signals.slice(-12));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to run strategy");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel">
      <div className="panel-content stack">
        <div className="section-header">
          <div>
            <div className="section-title">Strategy Builder</div>
            <p className="section-subtitle">Run modular RSI, MACD, moving-average, and ML strategies against recent history.</p>
          </div>
          <div className="inline-list">
            <span className="pill">{options.length || 0} strategies loaded</span>
            <span className="pill">{symbol}</span>
          </div>
        </div>
        <div className="form-grid">
          <label>
            Symbol
            <input value={symbol} onChange={(event) => setSymbol(event.target.value.toUpperCase())} />
          </label>
          <label>
            Strategy
            <select value={strategy} onChange={(event) => setStrategy(event.target.value as StrategyType)}>
              {options.map((option) => (
                <option key={option.key} value={option.key}>
                  {option.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="button-row">
          <button onClick={runStrategy} disabled={loading}>
            {loading ? "Running..." : "Run Strategy"}
          </button>
        </div>
        {error ? <div className="negative">{error}</div> : null}
        {signals.length ? (
          <div>
            <div className="section-header">
              <div className="section-title">Latest Signals</div>
            </div>
            <div className="table-shell">
              <table className="table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Signal</th>
                    <th>Close</th>
                  </tr>
                </thead>
                <tbody>
                  {signals.map((signal) => (
                    <tr key={`${signal.timestamp}-${signal.signal}`}>
                      <td>{new Date(signal.timestamp).toLocaleDateString()}</td>
                      <td className={signal.signal === "BUY" ? "positive" : signal.signal === "SELL" ? "negative" : ""}>
                        {signal.signal}
                      </td>
                      <td>{signal.close.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="empty-state">Run a strategy to inspect the latest generated signals and validate the setup.</div>
        )}
      </div>
    </div>
  );
}
