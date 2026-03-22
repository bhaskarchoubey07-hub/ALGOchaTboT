from collections.abc import Generator
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def get_engine():
    settings = get_settings()
    if not settings.database_url:
        return None
    connect_args = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(settings.database_url, future=True, pool_pre_ping=True, connect_args=connect_args)


ENGINE = get_engine()
SessionLocal: Optional[sessionmaker[Session]] = (
    sessionmaker(autocommit=False, autoflush=False, bind=ENGINE) if ENGINE is not None else None
)


def init_db() -> None:
    if ENGINE is None:
        return
    from app.models.orm import BacktestResultORM, PortfolioSnapshotORM, StrategyRunORM, TradeORM  # noqa: F401

    Base.metadata.create_all(bind=ENGINE)


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise RuntimeError("Database is not configured. Set DATABASE_URL to enable persistence.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
