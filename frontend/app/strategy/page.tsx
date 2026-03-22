import { StrategyRunner } from "@/components/StrategyRunner";

export default function StrategyPage() {
  return (
    <div className="stack">
      <section className="hero">
        <div className="hero-content hero-grid">
          <div className="stack">
            <div className="badge">Signal generation</div>
            <h1>Compose and inspect alpha modules with fast feedback.</h1>
            <p>Select a strategy, run it over cached market data, and inspect the latest trading recommendations before moving into backtesting.</p>
          </div>
          <div className="hero-stat-grid">
            <div className="hero-stat">
              <div className="hero-stat-label">Strategy Families</div>
              <div className="hero-stat-value">Rule + ML</div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-label">Signal Output</div>
              <div className="hero-stat-value">Buy / Sell / Hold</div>
            </div>
          </div>
        </div>
      </section>
      <StrategyRunner />
    </div>
  );
}
