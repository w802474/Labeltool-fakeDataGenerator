"""Database configuration and session management."""
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from loguru import logger

from app.infrastructure.database.models import Base
from app.config.settings import settings


class DatabaseConfig:
    """Database configuration manager."""
    
    def __init__(self):
        # Get database URL from settings
        self.database_url = settings.database_url
        
        # MySQL connection arguments with proper charset and timezone
        connect_args = {
            "charset": "utf8mb4",
            "use_unicode": True,
            "autocommit": False,
        }
        
        # Create async engine for MySQL
        self.engine = create_async_engine(
            self.database_url,
            echo=settings.database_echo,
            connect_args=connect_args,
        )
        
        # Create session factory
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        logger.info(f"Database configured: {self.database_url}")
    
    async def create_tables(self):
        """Create all database tables."""
        try:
            logger.info("Creating database connection...")
            async with self.engine.begin() as conn:
                logger.info("Connected to database, creating tables...")
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    async def drop_tables(self):
        """Drop all database tables. Use with caution!"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session."""
        async with self.async_session() as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"Database session error: {e}")
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self):
        """Close database engine."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database engine closed")


# Global database configuration instance
_db_config: DatabaseConfig = None


def get_database_config() -> DatabaseConfig:
    """Get global database configuration instance."""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    db_config = get_database_config()
    async for session in db_config.get_session():
        yield session


async def init_database():
    """Initialize database on application startup."""    
    db_config = get_database_config()
    await db_config.create_tables()
    logger.info("Database initialization completed")


async def close_database():
    """Close database on application shutdown."""
    global _db_config
    if _db_config:
        await _db_config.close()
        _db_config = None
    logger.info("Database connection closed")