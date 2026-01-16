"""Database connection and session management."""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _is_pooler_connection(url: str) -> bool:
    """Check if URL is a Supabase pooler connection (uses PgBouncer)."""
    return "pooler.supabase.com" in url


def _create_engine():
    """Create async engine with smart pool configuration."""
    url = settings.database_url

    # Use NullPool for pooler connections (external pooling via PgBouncer)
    # Use standard pooling for direct connections
    if _is_pooler_connection(url):
        logger.info("Using NullPool for Supabase pooler connection")
        return create_async_engine(
            url,
            echo=settings.debug,
            poolclass=NullPool,
        )

    logger.info("Using standard pool for direct database connection")
    return create_async_engine(
        url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
    )


# Create async engine
engine = _create_engine()

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def verify_database_connection() -> None:
    """Verify database connection on startup.

    Raises:
        RuntimeError: If database connection fails.
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("Database connection verified successfully")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise RuntimeError(f"Failed to connect to database: {e}") from e
