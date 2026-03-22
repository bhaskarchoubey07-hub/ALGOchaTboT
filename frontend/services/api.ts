const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

export async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || "Request failed");
  }

  return response.json() as Promise<T>;
}

export function buildWebSocketUrl(path: string): string {
  const normalized = API_BASE_URL.replace(/\/api$/, "");
  if (normalized.startsWith("https://")) {
    return `${normalized.replace("https://", "wss://")}${path}`;
  }
  return `${normalized.replace("http://", "ws://")}${path}`;
}

export type StrategyType = "rsi" | "ma_crossover" | "macd" | "ml_predictor";

export interface PerformanceResponse {
  equity: number;
  cash: number;
  realized_pnl: number;
  unrealized_pnl: number;
  holdings_count: number;
  as_of: string;
}

export interface PortfolioHolding {
  symbol: string;
  quantity: number;
  average_cost: number;
  market_price: number;
  market_value: number;
  unrealized_pnl: number;
}

export interface PortfolioResponse {
  as_of: string;
  cash: number;
  equity: number;
  realized_pnl: number;
  unrealized_pnl: number;
  holdings: PortfolioHolding[];
}

export interface TradeResponse {
  timestamp: string;
  symbol: string;
  side: "BUY" | "SELL";
  quantity: number;
  price: number;
  fee: number;
  pnl: number;
  reason?: string | null;
}

export interface LivePaperTradingStatus {
  active: boolean;
  symbol: string | null;
  provider: "yahoo" | "alpha_vantage" | null;
  poll_interval_seconds: number | null;
  latest_price: number | null;
  last_update: string | null;
  portfolio: PortfolioResponse;
  recent_trades: TradeResponse[];
}

export interface DataResponse {
  symbol: string;
  rows: number;
  data: Array<{
    timestamp: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>;
}

export interface SignalRecord {
  timestamp: string;
  close: number;
  signal: "BUY" | "SELL" | "HOLD";
  metadata: Record<string, number | string>;
}

export interface BacktestResponse {
  symbol: string;
  strategy: StrategyType;
  parameters: Record<string, number | string | boolean>;
  metrics: {
    total_return: number;
    annualized_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    total_trades: number;
    profit_factor: number;
  };
  trades: Array<{
    timestamp: string;
    symbol: string;
    side: "BUY" | "SELL";
    quantity: number;
    price: number;
    fee: number;
    pnl: number;
    reason?: string | null;
  }>;
  equity_curve: Array<{
    timestamp: string;
    equity: number;
    cash: number;
    holdings_value: number;
  }>;
  signals: SignalRecord[];
}
