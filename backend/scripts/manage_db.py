#!/usr/bin/env python3
"""Database management script for LabelTool."""
import asyncio
import os
import sys
from pathlib import Path

# Add backend app to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from app.infrastructure.database.config import get_database_config, init_database, close_database
from app.config.settings import settings


async def create_tables():
    """Create all database tables."""
    try:
        logger.info("Creating database tables...")
        await init_database()
        logger.success("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False
    return True


async def drop_tables():
    """Drop all database tables."""
    try:
        logger.warning("Dropping all database tables...")
        db_config = get_database_config()
        await db_config.drop_tables()
        logger.success("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        return False
    return True


async def test_connection():
    """Test database connection."""
    try:
        logger.info("Testing database connection...")
        db_config = get_database_config()
        
        # Test basic connection
        async for session in db_config.get_session():
            # Execute a simple query to test connection
            result = await session.execute("SELECT 1 as test")
            test_value = result.scalar()
            if test_value == 1:
                logger.success("Database connection test passed")
                return True
            else:
                logger.error("Database connection test failed - unexpected result")
                return False
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


async def reset_database():
    """Reset database by dropping and recreating all tables."""
    logger.warning("Resetting database - this will delete all data!")
    
    # Drop tables
    if not await drop_tables():
        return False
    
    # Create tables
    if not await create_tables():
        return False
    
    logger.success("Database reset completed successfully")
    return True


def show_config():
    """Show current database configuration."""
    logger.info("Current database configuration:")
    logger.info(f"Database URL: {settings.database_url}")
    logger.info(f"Pool size: {settings.db_pool_size}")
    logger.info(f"Max overflow: {settings.db_max_overflow}")
    logger.info(f"Pool timeout: {settings.db_pool_timeout}")
    logger.info(f"Pool recycle: {settings.db_pool_recycle}")


async def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("Database Management Script for LabelTool")
        print("\nUsage: python manage_db.py <command>")
        print("\nCommands:")
        print("  create      - Create all database tables")
        print("  drop        - Drop all database tables")
        print("  reset       - Drop and recreate all tables (WARNING: deletes all data)")
        print("  test        - Test database connection")
        print("  config      - Show current database configuration")
        print("\nExamples:")
        print("  python manage_db.py create")
        print("  python manage_db.py test")
        print("  python manage_db.py reset")
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "create":
            success = await create_tables()
        elif command == "drop":
            # Ask for confirmation
            response = input("This will delete all data. Are you sure? (y/N): ")
            if response.lower() == 'y':
                success = await drop_tables()
            else:
                logger.info("Operation cancelled")
                return
        elif command == "reset":
            # Ask for confirmation
            response = input("This will delete ALL data and recreate tables. Are you sure? (y/N): ")
            if response.lower() == 'y':
                success = await reset_database()
            else:
                logger.info("Operation cancelled")
                return
        elif command == "test":
            success = await test_connection()
        elif command == "config":
            show_config()
            return
        else:
            logger.error(f"Unknown command: {command}")
            return
        
        if success:
            logger.success(f"Command '{command}' completed successfully")
        else:
            logger.error(f"Command '{command}' failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        # Close database connections
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())