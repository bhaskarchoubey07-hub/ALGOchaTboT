from datetime import datetime

from sqlalchemy.orm import Session

from app.models.domain import PortfolioSnapshot
from app.models.orm import PortfolioSnapshotORM, TradeORM


class PortfolioService:
    def __init__(self):
        self.last_snapshot = PortfolioSnapshot(
            as_of=datetime.utcnow(),
            cash=100000.0,
            equity=100000.0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            holdings=[],
        )

    def update_snapshot(self, snapshot: PortfolioSnapshot, db: Session | None = None) -> None:
        self.last_snapshot = snapshot
        if db is None:
            return
        db.add(
            PortfolioSnapshotORM(
                as_of=snapshot.as_of,
                cash=snapshot.cash,
                equity=snapshot.equity,
                realized_pnl=snapshot.realized_pnl,
                unrealized_pnl=snapshot.unrealized_pnl,
                holdings=snapshot.model_dump()["holdings"],
            )
        )
        db.commit()

    def store_trades(self, trades, db: Session | None = None) -> None:
        if db is None:
            return
        for trade in trades:
            db.add(TradeORM(**trade.model_dump()))
        db.commit()

    def get_snapshot(self) -> PortfolioSnapshot:
        return self.last_snapshot
