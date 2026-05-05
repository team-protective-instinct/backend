from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from psycopg import Connection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import ConnectionPool

from .config import Settings


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, settings: Settings) -> None:
        self._engine: Engine = create_engine(
            settings.db_url,
            pool_recycle=3600,
        )
        self._session_factory: sessionmaker[Session] = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
        )
        
        # Connection pool for psycopg3 (LangGraph PostgresSaver)
        db_uri = settings.db_url.replace("+psycopg2", "").replace("+asyncpg", "")
        self._pool: ConnectionPool[Connection[DictRow]] = ConnectionPool(
            conninfo=db_uri,
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,
                "row_factory": dict_row,
            }
        )

    def create_database(self) -> None:
        with self._engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(self._engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session: Session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @property
    def pool(self) -> ConnectionPool[Connection[DictRow]]:
        return self._pool
