from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from psycopg_pool import ConnectionPool

from .config import Settings


Base = declarative_base()


class Database:
    def __init__(self, settings: Settings) -> None:
        self._engine = create_engine(
            settings.db_url,
            pool_recycle=3600,
        )
        self._session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
        )
        
        # Connection pool for psycopg3 (LangGraph PostgresSaver)
        db_uri = settings.db_url.replace("+psycopg2", "").replace("+asyncpg", "")
        self._pool = ConnectionPool(
            conninfo=db_uri,
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,
            }
        )

    def create_database(self) -> None:
        Base.metadata.create_all(self._engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        session: Session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @property
    def pool(self) -> ConnectionPool:
        return self._pool
