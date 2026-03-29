"""
Database factory.

Usage:
    from db import get_db
    db = get_db()

The active backend is controlled by DATABASE env var:
  - "supabase"     → SupabaseRepository (default)
  - "internal_db"  → PostgresRepository (local PostgreSQL via asyncpg)

Pool lifecycle is managed in main.py lifespan via init_pool() / close_pool().
"""
import asyncpg
from config import settings
from db.base import AbstractRepository

_pool: asyncpg.Pool | None = None
_db_instance: AbstractRepository | None = None


async def init_pool(url: str) -> None:
    """Create the asyncpg connection pool. Called at startup when DATABASE=internal_db."""
    global _pool, _db_instance
    _pool = await asyncpg.create_pool(url, min_size=2, max_size=10)
    from db.postgres_repo import PostgresRepository
    _db_instance = PostgresRepository(_pool)


async def close_pool() -> None:
    """Close the asyncpg pool. Called at shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_db() -> AbstractRepository:
    """Return the active repository instance (singleton)."""
    global _db_instance
    if _db_instance is None:
        if settings.DATABASE == "internal_db":
            raise RuntimeError(
                "internal_db pool not initialized. Ensure init_pool() was called at startup."
            )
        from db.supabase_repo import SupabaseRepository
        _db_instance = SupabaseRepository()
    return _db_instance
