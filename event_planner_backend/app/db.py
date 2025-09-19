"""Database initialization and session management."""
from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from .config import Config

Base = declarative_base()
_engine = None
SessionLocal = None


def init_engine_and_session(config: Config):
    """Initialize SQLAlchemy engine and session factory using provided config."""
    global _engine, SessionLocal
    if _engine is None:
        db_uri = config.build_sqlalchemy_uri()
        _engine = create_engine(db_uri, pool_pre_ping=True, future=True)
        SessionLocal = scoped_session(sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True))
    return _engine, SessionLocal


def init_db(config: Config):
    """Create all tables if they do not exist."""
    engine, _ = init_engine_and_session(config)
    Base.metadata.create_all(bind=engine)
