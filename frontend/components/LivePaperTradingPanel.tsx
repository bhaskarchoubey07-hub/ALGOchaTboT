"use client";

import { useEffect, useRef, useState } from "react";
import { buildWebSocketUrl, fetchApi, LivePaperTradingStatus, PortfolioResponse } from "@/services/api";
import { PortfolioSnapshot } from "@/components/PortfolioSnapshot";

interface LivePaperTradingPanelProps {
  initialPortfolio: PortfolioResponse;
  initialStatus: LivePaperTradingStatus;
}

export function LivePaperTradingPanel({ initialPortfolio, initialStatus }: LivePaperTradingPanelProps) {
  const [portfolio, setPortfolio] = useState(initialPortfolio);
  const [status, setStatus] = useState(initialStatus);
  const [symbol, setSymbol] = useState(initialStatus.symbol || "AAPL");
  const [pollIntervalSeconds, setPollIntervalSeconds] = useState(initialStatus.poll_interval_seconds || 5);
  const [allocationPct, setAllocationPct] = useState(0.25);
  const [quantity, setQuantity] = useState("");
  const [connectionState, setConnectionState] = useState("disconnected");
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const readyForOrders = status.active && status.latest_price !== null;

  useEffect(() => {
    const socket = new WebSocket(buildWebSocketUrl("/api/portfolio/ws/paper-trading"));
    socketRef.current = socket;

    socket.onopen = () => {
      setConnectionState("connected");
      setError(null);
    };

    socket.onclose = () => {
      setConnectionState("disconnected");
    };

    socket.onerror = () => {
      setError("WebSocket connection failed.");
      setConnectionState("error");
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data) as {
        type: string;
        message?: string;
        status?: LivePaperTradingStatus;
        portfolio?: PortfolioResponse;
      };
      if (message.type === "error" && message.message) {
        setError(message.message);
      }
      if (message.status) {
        setStatus(message.status);
        setPortfolio(message.status.portfolio);
      }
      if (message.portfolio) {
        setPortfolio(message.portfolio);
      }
    };

    return () => {
      socket.close();
    };
  }, []);

  async function startSession() {
    setError(null);
    try {
      const nextStatus = await fetchApi<LivePaperTradingStatus>("/portfolio/live/start", {
        method: "POST",
        body: JSON.stringify({
          symbol,
          provider: "yahoo",
          poll_interval_seconds: pollIntervalSeconds
        })
      });
      setStatus(nextStatus);
      setPortfolio(nextStatus.portfolio);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to start live session");
    }
  }

  async function stopSession() {
    setError(null);
    try {
      const response = await fetchApi<{ stopped: boolean; status: LivePaperTradingStatus }>("/portfolio/live/stop", {
        method: "POST"
      });
      setStatus(response.status);
      setPortfolio(response.status.portfolio);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to stop live session");
    }
  }

  async function placeTrade(side: "BUY" | "SELL") {
    setError(null);
    try {
      const response = await fetchApi<{ portfolio: PortfolioResponse }>("/portfolio/paper-trade", {
        method: "POST",
        body: JSON.stringify({
          symbol,
          side,
          quantity: side === "SELL" && quantity ? Number(quantity) : null,
          allocation_pct: allocationPct,
          provider: "yahoo",
          period: "5d",
          interval: "1d"
        })
      });
      setPortfolio(response.portfolio);
      const refreshedStatus = await fetchApi<LivePaperTradingStatus>("/portfolio/live/status");
      setStatus(refreshedStatus);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to place trade");
    }
  }

  return (
    <div className="stack">
      <div className="panel">
        <div className="panel-content stack">
          <div className="section-header">
            <div>
              <div className="section-title">Real-Time Paper Trading</div>
              <div className="section-subtitle">Live quote monitoring, manual order entry, and continuous portfolio repricing</div>
            </div>
            <div className="inline-list">
              <span className={`pill ${status.active ? "positive" : "warning"}`}>{status.active ? "Session active" : "Session idle"}</span>
              <span className={`pill ${connectionState === "connected" ? "positive" : "negative"}`}>{connectionState}</span>
            </div>
          </div>
          <div className="dashboard-strip">
            <div className="metric-card">
              <div className="metric-label">Latest Price</div>
              <div className="metric-value">{status.latest_price ? status.latest_price.toFixed(2) : "--"}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Last Update</div>
              <div className="metric-value" style={{ fontSize: "1.2rem" }}>
                {status.last_update ? new Date(status.last_update).toLocaleTimeString() : "--"}
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Tracked Symbol</div>
              <div className="metric-value">{status.symbol || symbol}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Poll Interval</div>
              <div className="metric-value">{pollIntervalSeconds}s</div>
            </div>
          </div>
          <div className="form-grid">
            <label>
              Symbol
              <input value={symbol} onChange={(event) => setSymbol(event.target.value.toUpperCase())} />
            </label>
            <label>
              Poll Interval (sec)
              <input
                type="number"
                min={1}
                max={60}
                value={pollIntervalSeconds}
                onChange={(event) => setPollIntervalSeconds(Number(event.target.value))}
              />
            </label>
            <label>
              Buy Allocation
              <input
                type="number"
                min={0.05}
                max={1}
                step={0.05}
                value={allocationPct}
                onChange={(event) => setAllocationPct(Number(event.target.value))}
              />
            </label>
            <label>
              Sell Quantity
              <input value={quantity} onChange={(event) => setQuantity(event.target.value)} placeholder="Optional for full exit" />
            </label>
          </div>
          <div className="button-row">
            <button onClick={startSession}>Start Live Session</button>
            <button className="button-secondary" onClick={stopSession}>
              Stop Session
            </button>
            <button className="button-buy" onClick={() => placeTrade("BUY")} disabled={!readyForOrders}>
              Paper Buy
            </button>
            <button className="button-sell" onClick={() => placeTrade("SELL")} disabled={!readyForOrders}>
              Paper Sell
            </button>
          </div>
          {!readyForOrders && status.active ? (
            <div className="warning">Waiting for the first live quote before enabling order entry.</div>
          ) : null}
          {error ? <div className="negative">{error}</div> : null}
        </div>
      </div>

      <PortfolioSnapshot portfolio={portfolio} />

      <div className="panel">
        <div className="panel-content">
          <div className="section-header">
            <div>
              <div className="section-title">Recent Live Trades</div>
              <div className="section-subtitle">Manual executions recorded against the most recent streamed quote</div>
            </div>
          </div>
          {status.recent_trades.length ? (
            <div className="table-shell">
              <table className="table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Side</th>
                    <th>Qty</th>
                    <th>Price</th>
                    <th>P&amp;L</th>
                  </tr>
                </thead>
                <tbody>
                  {status.recent_trades.map((trade, index) => (
                    <tr key={`${trade.timestamp}-${index}`}>
                      <td>{new Date(trade.timestamp).toLocaleString()}</td>
                      <td className={trade.side === "BUY" ? "positive" : "negative"}>{trade.side}</td>
                      <td>{trade.quantity.toFixed(4)}</td>
                      <td>{trade.price.toFixed(2)}</td>
                      <td className={trade.pnl >= 0 ? "positive" : "negative"}>{trade.pnl.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">No live trades yet. Start a session and submit a paper order to populate the trade tape.</div>
          )}
        </div>
      </div>
    </div>
  );
}
