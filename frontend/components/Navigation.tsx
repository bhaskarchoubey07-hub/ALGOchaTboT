import Link from "next/link";

export function Navigation() {
  return (
    <div className="topbar">
      <div className="brand">
        <div className="brand-title">Atlas Trade OS</div>
        <div className="brand-subtitle">Quant research, signal execution, and live paper monitoring</div>
      </div>
      <nav className="nav">
        <Link href="/">Dashboard</Link>
        <Link href="/strategy">Strategies</Link>
        <Link href="/backtest">Backtests</Link>
        <Link href="/portfolio">Portfolio</Link>
      </nav>
    </div>
  );
}
