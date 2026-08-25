"""
Database layer (SQLAlchemy).

One engine + session factory for the app's structured data (users, chat
history). The connection URL comes from `DATABASE_URL` (via the secrets layer),
defaulting to a local SQLite file so development and tests need zero setup;
point it at Postgres in production:

    DATABASE_URL=postgresql+psycopg://user:pass@host:5432/dbname

Everything speaks SQLAlchemy, so moving from SQLite to Postgres is a URL change,
not a code change. Tests call `init_engine(<sqlite url>)` + `init_db()` to run
against an isolated throwaway database.
"""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
SessionLocal = sessionmaker(autoflush=False, autocommit=False, future=True)
engine = None


def init_engine(url: str = None):
    """(Re)create the engine and bind the session factory. Called once at import
    for normal app use; tests call it with a temp SQLite URL for isolation."""
    global engine
    if url is None:
        from config.settings import DATABASE_URL
        url = DATABASE_URL

    is_sqlite = url.startswith("sqlite")
    engine = create_engine(
        url,
        future=True,
        # SQLite is used across threads (FastAPI threadpool); allow it.
        connect_args={"check_same_thread": False} if is_sqlite else {},
        # Validate pooled connections before use (matters for Postgres, which can
        # drop idle connections); pointless for SQLite.
        pool_pre_ping=not is_sqlite,
    )
    SessionLocal.configure(bind=engine)
    return engine


def init_db():
    """Create all tables if they don't exist. Safe to call on every startup."""
    if engine is None:
        init_engine()
    from backend import models  # noqa: F401 — registers the mapped classes
    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope():
    """Transactional session: commits on success, rolls back on error, always
    closes. Use for every DB interaction."""
    if engine is None:
        init_engine()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Create the default engine at import so ordinary app use has one ready.
init_engine()
