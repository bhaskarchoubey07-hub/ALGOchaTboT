import { LivePaperTradingPanel } from "@/components/LivePaperTradingPanel";
import { LivePaperTradingStatus, PortfolioResponse, fetchApi } from "@/services/api";

export default async function PortfolioPage() {
  let portfolio: PortfolioResponse;
  let status: LivePaperTradingStatus;
  try {
    [portfolio, status] = await Promise.all([
      fetchApi<PortfolioResponse>("/portfolio"),
      fetchApi<LivePaperTradingStatus>("/portfolio/live/status")
    ]);
  } catch {
    portfolio = {
      as_of: new Date().toISOString(),
      cash: 100000,
      equity: 100000,
      realized_pnl: 0,
      unrealized_pnl: 0,
      holdings: []
    };
    status = {
      active: false,
      symbol: null,
      provider: null,
      poll_interval_seconds: null,
      latest_price: null,
      last_update: null,
      portfolio,
      recent_trades: []
    };
  }

  return (
    <div className="stack">
      <section className="hero">
        <div className="hero-content hero-grid">
          <div className="stack">
            <div className="badge">Paper portfolio</div>
            <h1>Operate a live paper book with streaming quote awareness.</h1>
            <p>Track the active symbol, stream live updates over WebSocket, and manage a simulated portfolio through a more desk-like control surface.</p>
          </div>
          <div className="hero-stat-grid">
            <div className="hero-stat">
              <div className="hero-stat-label">Portfolio Equity</div>
              <div className="hero-stat-value">{portfolio.equity.toFixed(2)}</div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-label">Holdings</div>
              <div className="hero-stat-value">{portfolio.holdings.length}</div>
            </div>
          </div>
        </div>
      </section>
      <LivePaperTradingPanel initialPortfolio={portfolio} initialStatus={status} />
    </div>
  );
}
