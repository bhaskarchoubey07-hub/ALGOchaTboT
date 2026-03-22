"use client";

import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface PriceChartProps {
  prices: Array<{
    timestamp: string;
    open: number;
    high: number;
    low: number;
    close: number;
  }>;
  signals?: Array<{
    timestamp: string;
    close: number;
    signal: "BUY" | "SELL" | "HOLD";
  }>;
  title: string;
}

export function PriceChart({ prices, signals = [], title }: PriceChartProps) {
  const buySignals = signals.filter((signal) => signal.signal === "BUY");
  const sellSignals = signals.filter((signal) => signal.signal === "SELL");

  return (
    <div className="panel">
      <div className="panel-content">
        <div className="section-header">
          <div>
            <div className="section-title">{title}</div>
            <div className="section-subtitle">Candlesticks with strategy markers layered onto the active symbol</div>
          </div>
          <div className="inline-list">
            <span className="pill">{prices.length} bars</span>
            <span className="pill positive">{buySignals.length} buy signals</span>
            <span className="pill negative">{sellSignals.length} sell signals</span>
          </div>
        </div>
        <div className="chart-shell">
          <Plot
            data={[
              {
                x: prices.map((point) => point.timestamp),
                open: prices.map((point) => point.open),
                high: prices.map((point) => point.high),
                low: prices.map((point) => point.low),
                close: prices.map((point) => point.close),
                increasing: { line: { color: "#20c997" } },
                decreasing: { line: { color: "#ff6b6b" } },
                type: "candlestick",
                name: "Price"
              },
              {
                x: buySignals.map((signal) => signal.timestamp),
                y: buySignals.map((signal) => signal.close),
                mode: "markers",
                type: "scatter",
                name: "Buy",
                marker: { color: "#20c997", size: 10, symbol: "triangle-up" }
              },
              {
                x: sellSignals.map((signal) => signal.timestamp),
                y: sellSignals.map((signal) => signal.close),
                mode: "markers",
                type: "scatter",
                name: "Sell",
                marker: { color: "#ff6b6b", size: 10, symbol: "triangle-down" }
              }
            ]}
            layout={{
              autosize: true,
              height: 460,
              paper_bgcolor: "rgba(0,0,0,0)",
              plot_bgcolor: "rgba(0,0,0,0)",
              margin: { l: 28, r: 20, t: 10, b: 28 },
              font: { color: "#c5d2e8" },
              legend: { orientation: "h", x: 0, y: 1.1 },
              xaxis: {
                rangeslider: { visible: false },
                gridcolor: "rgba(143, 169, 205, 0.08)",
                zerolinecolor: "rgba(143, 169, 205, 0.08)"
              },
              yaxis: {
                gridcolor: "rgba(143, 169, 205, 0.08)",
                zerolinecolor: "rgba(143, 169, 205, 0.08)"
              }
            }}
            style={{ width: "100%" }}
            config={{ responsive: true, displayModeBar: false }}
          />
        </div>
      </div>
    </div>
  );
}
