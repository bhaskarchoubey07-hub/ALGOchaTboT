import { PortfolioResponse } from "@/services/api";

interface PortfolioSnapshotProps {
  portfolio: PortfolioResponse;
}

export function PortfolioSnapshot({ portfolio }: PortfolioSnapshotProps) {
  return (
    <div className="panel">
      <div className="panel-content stack">
        <div className="section-header">
          <div>
            <div className="section-title">Portfolio View</div>
            <div className="section-subtitle">Marked to market using the latest simulated or streamed quote state</div>
          </div>
          <div className="pill">{portfolio.holdings.length} open positions</div>
        </div>
        <div className="grid metrics">
          <div className="metric-card">
            <div className="metric-label">Cash</div>
            <div className="metric-value">{portfolio.cash.toFixed(2)}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Equity</div>
            <div className="metric-value">{portfolio.equity.toFixed(2)}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Realized P&amp;L</div>
            <div className={`metric-value ${portfolio.realized_pnl >= 0 ? "positive" : "negative"}`}>
              {portfolio.realized_pnl.toFixed(2)}
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Unrealized P&amp;L</div>
            <div className={`metric-value ${portfolio.unrealized_pnl >= 0 ? "positive" : "negative"}`}>
              {portfolio.unrealized_pnl.toFixed(2)}
            </div>
          </div>
        </div>
        {portfolio.holdings.length ? (
          <div className="table-shell">
            <table className="table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Qty</th>
                  <th>Avg Cost</th>
                  <th>Market Price</th>
                  <th>Market Value</th>
                  <th>Unrealized P&amp;L</th>
                </tr>
              </thead>
              <tbody>
                {portfolio.holdings.map((holding) => (
                  <tr key={holding.symbol}>
                    <td>{holding.symbol}</td>
                    <td>{holding.quantity.toFixed(4)}</td>
                    <td>{holding.average_cost.toFixed(2)}</td>
                    <td>{holding.market_price.toFixed(2)}</td>
                    <td>{holding.market_value.toFixed(2)}</td>
                    <td className={holding.unrealized_pnl >= 0 ? "positive" : "negative"}>{holding.unrealized_pnl.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">No open holdings yet. Start a live session or place a paper trade to populate the blotter.</div>
        )}
      </div>
    </div>
  );
}
