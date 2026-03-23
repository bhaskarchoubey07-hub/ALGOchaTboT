import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


def request_json(method: str, url: str, payload: dict | None = None) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the running trading bot API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Base URL for the FastAPI server.")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    checks: list[tuple[str, callable]] = []

    def check_health():
        payload = request_json("GET", f"{base_url}/health")
        assert_true(payload["status"] == "ok", "Health endpoint did not return ok.")

    def check_strategy_options():
        payload = request_json("GET", f"{base_url}/api/strategy/options")
        keys = {item["key"] for item in payload["strategies"]}
        assert_true("ml_predictor" in keys, "ML strategy missing from options.")

    def check_data():
        payload = request_json("GET", f"{base_url}/api/data/AAPL?period=1mo&interval=1d")
        assert_true(payload["rows"] > 0, "Data endpoint returned no rows.")

    def check_strategy_run():
        payload = request_json(
            "POST",
            f"{base_url}/api/strategy/run",
            {
                "symbol": "AAPL",
                "strategy": "rsi",
                "period": "6mo",
                "interval": "1d",
                "provider": "yahoo",
                "parameters": {},
            },
        )
        assert_true(len(payload["signals"]) > 0, "Strategy run returned no signals.")

    def check_backtest():
        payload = request_json(
            "POST",
            f"{base_url}/api/backtest",
            {
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
        assert_true("metrics" in payload and "equity_curve" in payload, "Backtest payload missing core fields.")

    def check_live_paper():
        start = request_json(
            "POST",
            f"{base_url}/api/portfolio/live/start",
            {"symbol": "AAPL", "provider": "yahoo", "poll_interval_seconds": 2},
        )
        assert_true(start["active"] is True, "Live paper session did not activate.")
        assert_true(start["latest_price"] is not None, "Live paper session did not fetch an initial quote.")

        trade = request_json(
            "POST",
            f"{base_url}/api/portfolio/paper-trade",
            {"symbol": "AAPL", "side": "BUY", "allocation_pct": 0.1, "provider": "yahoo", "period": "5d", "interval": "1d"},
        )
        assert_true(trade["portfolio"]["holdings"], "Paper trade did not open a holding.")

        stop = request_json("POST", f"{base_url}/api/portfolio/live/stop")
        assert_true(stop["stopped"] is True, "Live paper session did not stop.")

    checks.extend(
        [
            ("health", check_health),
            ("strategy options", check_strategy_options),
            ("data", check_data),
            ("strategy run", check_strategy_run),
            ("backtest", check_backtest),
            ("live paper trading", check_live_paper),
        ]
    )

    try:
        for label, func in checks:
            print(f"[smoke] running {label}...")
            func()
        print("[smoke] all checks passed")
        return 0
    except (AssertionError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        print(f"[smoke] failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
