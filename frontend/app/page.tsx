import { MetricCard } from "@/components/MetricCard";
import { PriceChart } from "@/components/PriceChart";
import { StrategyRunner } from "@/components/StrategyRunner";
import { DataResponse, PerformanceResponse, fetchApi } from "@/services/api";

export default async function DashboardPage() {
  let performance: PerformanceResponse | null = null;
  let data: DataResponse | null = null;

  try {
    [performance, data] = await Promise.all([
      fetchApi<PerformanceResponse>("/performance"),
      fetchApi<DataResponse>("/data/AAPL?period=6mo&interval=1d")
    ]);
  } catch {
    performance = {
      equity: 100000,
      cash: 100000,
      realized_pnl: 0,
      unrealized_pnl: 0,
      holdings_count: 0,
      as_of: new Date().toISOString()
    };
    data = { symbol: "AAPL", rows: 0, data: [] };
  }

  return (
    <div className="stack">
      <section className="hero">
        <div className="hero-content hero-grid">
          <div className="stack">
            <div className="badge">Professional Trading Dashboard</div>
            <h1>Systematic research, execution, and paper trading in one view.</h1>
            <p>
              Monitor portfolio state, inspect price action, run rule-based and ML strategies, and shift directly into
              live paper execution from a dark trading workstation designed for dense signal review.
            </p>
            <div className="inline-list">
              <span className="pill">FastAPI backend</span>
              <span className="pill">Next.js frontend</span>
              <span className="pill">Live paper trading</span>
              <span className="pill">ML strategy support</span>
            </div>
          </div>
          <div className="hero-stat-grid">
            <div className="hero-stat">
              <div className="hero-stat-label">Net Liquidation</div>
              <div className="hero-stat-value">{performance.equity.toFixed(2)}</div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-label">Realized P&amp;L</div>
              <div className={`hero-stat-value ${performance.realized_pnl >= 0 ? "positive" : "negative"}`}>
                {performance.realized_pnl.toFixed(2)}
              </div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-label">Unrealized P&amp;L</div>
              <div className={`hero-stat-value ${performance.unrealized_pnl >= 0 ? "positive" : "negative"}`}>
                {performance.unrealized_pnl.toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      </section>
      <section className="grid metrics">
        <MetricCard label="Equity" value={performance.equity.toFixed(2)} footnote="Marked-to-market account value" />
        <MetricCard label="Cash" value={performance.cash.toFixed(2)} footnote="Available buying power in simulation" />
        <MetricCard
          label="Realized P&L"
          value={performance.realized_pnl.toFixed(2)}
          tone={performance.realized_pnl >= 0 ? "positive" : "negative"}
          footnote="Closed trade contribution"
        />
        <MetricCard
          label="Unrealized P&L"
          value={performance.unrealized_pnl.toFixed(2)}
          tone={performance.unrealized_pnl >= 0 ? "positive" : "negative"}
          footnote="Open position mark-to-market"
        />
      </section>
      <section className="grid two">
        <PriceChart prices={data.data} title="AAPL Market Data" />
        <StrategyRunner />
      </section>
    </div>
  );
}
