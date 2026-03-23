# Algorithmic Trading Bot with Backtesting Engine

Full-stack algorithmic trading system built with FastAPI and Next.js. It includes market data ingestion, modular strategies, a backtesting engine, a simulated trading engine, optional PostgreSQL persistence, and a dashboard for visualization.

## Features

- Market data fetching with local CSV caching
- RSI, MACD, moving-average crossover, and ML predictor strategies
- Backtesting with transaction fees, position sizing, stop loss, and take profit
- Parameter optimization for strategy tuning
- Simulated paper trading portfolio state
- FastAPI endpoints with Swagger docs at `/docs`
- Next.js dashboard with candlestick charts and trade markers
- Render deployment config for backend and frontend

## Project Structure

```text
backend/
  app/
    main.py
    routes/
    services/
    strategies/
    models/
    utils/

frontend/
  app/
  components/
  services/
```

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Automated Tests

```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest
```

The tests mock market data and live quotes so they remain stable and do not depend on external APIs.

## Smoke Test

Run the API locally first, then execute:

```bash
python scripts/smoke_test.py --base-url http://127.0.0.1:8000
```

This validates health, market data, strategy execution, backtesting, and live paper-trading endpoints against a running server.

Optional environment variables:

```env
APP_ENV=development
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/trading
ALPHA_VANTAGE_API_KEY=your_key
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Optional environment variable:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

## API Endpoints

- `GET /api/data/{symbol}`
- `POST /api/strategy/run`
- `POST /api/strategy/optimize`
- `POST /api/backtest`
- `POST /api/backtest/compare`
- `GET /api/portfolio`
- `POST /api/portfolio/paper-trade`
- `GET /api/portfolio/live/status`
- `POST /api/portfolio/live/start`
- `POST /api/portfolio/live/stop`
- `GET /api/performance`

WebSocket:

- `WS /api/portfolio/ws/paper-trading`

## Example RSI Backtest Request

```json
{
  "symbol": "AAPL",
  "strategy": "rsi",
  "period": "2y",
  "interval": "1d",
  "provider": "yahoo",
  "initial_cash": 100000,
  "fee_rate": 0.001,
  "position_size": 0.95,
  "stop_loss": 0.05,
  "take_profit": 0.12,
  "parameters": {
    "period": 14,
    "oversold": 30,
    "overbought": 70
  }
}
```

## Sample Output Metrics

Illustrative example from a sample run:

```text
Total Return: 18.42%
Sharpe Ratio: 1.21
Max Drawdown: -8.64%
Win Rate: 57.14%
Profit Factor: 1.73
```

## ML Strategy Notes

- Strategy key: `ml_predictor`
- Historical features include lagged returns, rolling volatility, SMA spread, RSI, MACD, and volume change
- The model trains on the first segment of the dataset and produces signals on the out-of-sample segment
- Default model: `RandomForestClassifier`

## Render Deployment

- Deploy backend from `backend/`
- Deploy frontend from `frontend/`
- Use the provided `render.yaml` as a blueprint
- Set `NEXT_PUBLIC_API_BASE_URL` to the public backend `/api` URL

## Real-Time Paper Trading

- Starts a live paper session for one symbol using Yahoo Finance quotes
- Polls the live price API on a configurable interval
- Broadcasts `price_tick`, `trade`, and `snapshot` events over WebSocket
- Lets the frontend place simulated buy and sell orders against the latest live quote

## Caveats

- Yahoo Finance is enabled by default. Alpha Vantage is left as an adapter extension point.
- This project is for education and simulation, not financial advice or live brokerage execution.
