"""Database management module for CyberCorp server."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text
import asyncio
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./cybercorp.db")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create declarative base for ORM models
Base = declarative_base()

class DatabaseManager:
    """Database connection and session management."""
    
    def __init__(self):
        self._engine = engine
        self._base = Base
    
    async def initialize(self):
        """Initialize database with required tables."""
        async with self._engine.begin() as conn:
            await conn.run_sync(self._base.metadata.create_all)
    
    async def get_session(self) -> AsyncSession:
        """Async database session generator."""
        async with AsyncSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> bool:
        """Check if database connection is alive."""
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception:
            return False

# Global database manager instance
database_manager = DatabaseManager()