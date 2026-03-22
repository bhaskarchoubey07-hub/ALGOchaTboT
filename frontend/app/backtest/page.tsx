"use client";

import { useState } from "react";
import { BacktestForm } from "@/components/BacktestForm";
import { MetricCard } from "@/components/MetricCard";
import { PriceChart } from "@/components/PriceChart";
import { BacktestResponse, DataResponse, fetchApi } from "@/services/api";

export default function BacktestPage() {
  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [priceData, setPriceData] = useState<DataResponse | null>(null);

  async function handleResult(backtest: BacktestResponse) {
    setResult(backtest);
    const data = await fetchApi<DataResponse>(`/data/${backtest.symbol}?period=2y&interval=1d`);
    setPriceData(data);
  }

  return (
    <div className="stack">
      <section className="hero">
        <div className="hero-content hero-grid">
          <div className="stack">
            <div className="badge">Backtest and compare</div>
            <h1>Validate signals before they ever reach the blotter.</h1>
            <p>Run historical simulations with transaction costs, position sizing, and risk exits, then inspect the signal path directly on the chart.</p>
          </div>
          <div className="hero-stat-grid">
            <div className="hero-stat">
              <div className="hero-stat-label">Strategies</div>
              <div className="hero-stat-value">4</div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-label">Risk Controls</div>
              <div className="hero-stat-value">SL / TP</div>
            </div>
          </div>
        </div>
      </section>
      <BacktestForm onResult={handleResult} />
      {result ? (
        <>
          <section className="grid metrics">
            <MetricCard label="Total Return" value={`${(result.metrics.total_return * 100).toFixed(2)}%`} />
            <MetricCard label="Sharpe Ratio" value={result.metrics.sharpe_ratio.toFixed(2)} />
            <MetricCard
              label="Max Drawdown"
              value={`${(result.metrics.max_drawdown * 100).toFixed(2)}%`}
              tone="negative"
            />
            <MetricCard label="Win Rate" value={`${(result.metrics.win_rate * 100).toFixed(2)}%`} />
          </section>
          {priceData ? (
            <PriceChart prices={priceData.data} signals={result.signals} title={`${result.symbol} Backtest Signals`} />
          ) : null}
          <div className="panel">
            <div className="panel-content">
              <div className="section-header">
                <div>
                  <div className="section-title">Recent Trades</div>
                  <div className="section-subtitle">Execution tape from the current simulation run</div>
                </div>
              </div>
              <div className="table-shell">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Side</th>
                      <th>Qty</th>
                      <th>Price</th>
                      <th>Fee</th>
                      <th>P&amp;L</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.trades.slice(-12).map((trade, index) => (
                      <tr key={`${trade.timestamp}-${index}`}>
                        <td>{new Date(trade.timestamp).toLocaleDateString()}</td>
                        <td className={trade.side === "BUY" ? "positive" : "negative"}>{trade.side}</td>
                        <td>{trade.quantity.toFixed(4)}</td>
                        <td>{trade.price.toFixed(2)}</td>
                        <td>{trade.fee.toFixed(2)}</td>
                        <td className={trade.pnl >= 0 ? "positive" : "negative"}>{trade.pnl.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
