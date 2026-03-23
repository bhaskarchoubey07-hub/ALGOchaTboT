def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_strategy_options_include_ml_predictor(client):
    response = client.get("/api/strategy/options")

    assert response.status_code == 200
    keys = {item["key"] for item in response.json()["strategies"]}
    assert {"rsi", "ma_crossover", "macd", "ml_predictor"}.issubset(keys)


def test_data_endpoint_returns_mocked_rows(client):
    response = client.get("/api/data/AAPL?period=1mo&interval=1d")

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "AAPL"
    assert payload["rows"] == 90
    assert len(payload["data"]) == 90


def test_strategy_run_returns_signals(client):
    response = client.post(
        "/api/strategy/run",
        json={
            "symbol": "AAPL",
            "strategy": "rsi",
            "period": "6mo",
            "interval": "1d",
            "provider": "yahoo",
            "parameters": {},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["strategy"] == "rsi"
    assert len(payload["signals"]) > 0


def test_backtest_endpoint_returns_metrics_and_trades(client):
    response = client.post(
        "/api/backtest",
        json={
            "symbol": "AAPL",
            "strategy": "rsi",
            "period": "6mo",
            "interval": "1d",
            "provider": "yahoo",
            "initial_cash": 100000,
            "fee_rate": 0.001,
            "position_size": 0.95,
            "stop_loss": 0.05,
            "take_profit": 0.12,
            "parameters": {},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["metrics"]["total_trades"] >= 0
    assert len(payload["equity_curve"]) == 90
    assert "profit_factor" in payload["metrics"]


def test_strategy_optimization_returns_leaderboard(client):
    response = client.post(
        "/api/strategy/optimize",
        json={
            "symbol": "AAPL",
            "strategy": "rsi",
            "period": "6mo",
            "interval": "1d",
            "provider": "yahoo",
            "metric": "sharpe_ratio",
            "search_space": {"period": [10, 14], "oversold": [25, 30], "overbought": [70, 75]},
            "initial_cash": 100000,
            "fee_rate": 0.001,
            "position_size": 0.95,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["leaderboard"]
    assert payload["metric"] == "sharpe_ratio"


def test_live_paper_trading_flow(client):
    start_response = client.post(
        "/api/portfolio/live/start",
        json={"symbol": "AAPL", "provider": "yahoo", "poll_interval_seconds": 2},
    )
    assert start_response.status_code == 200
    start_payload = start_response.json()
    assert start_payload["active"] is True
    assert start_payload["latest_price"] is not None

    trade_response = client.post(
        "/api/portfolio/paper-trade",
        json={"symbol": "AAPL", "side": "BUY", "allocation_pct": 0.1, "provider": "yahoo", "period": "5d", "interval": "1d"},
    )
    assert trade_response.status_code == 200
    trade_payload = trade_response.json()
    assert trade_payload["live"] is True
    assert trade_payload["portfolio"]["holdings"]

    status_response = client.get("/api/portfolio/live/status")
    assert status_response.status_code == 200
    assert status_response.json()["recent_trades"]

    stop_response = client.post("/api/portfolio/live/stop")
    assert stop_response.status_code == 200
    assert stop_response.json()["stopped"] is True
