from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from psycopg_pool import ConnectionPool
from .config import settings

SQLALCHEMY_DATABASE_URL = settings.db_url

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_recycle=3600)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Connection pool for psycopg3 (LangGraph PostgresSaver)
_pool: ConnectionPool | None = None

def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        # psycopg3 doesn't like +asyncpg or +psycopg2 in the URI
        db_uri = SQLALCHEMY_DATABASE_URL.replace("+psycopg2", "").replace("+asyncpg", "")
        _pool = ConnectionPool(
            conninfo=db_uri,
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,
            }
        )
    return _pool
