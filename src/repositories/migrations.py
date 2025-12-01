import sys
from src.config.logging_config import logger
from pathlib import Path
import os

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

"""
Database migration and setup script.

This script provides utilities for setting up the PostgreSQL database,
creating tables, and running basic migrations.

Usage:
    python -m repositories.migrations create_tables
    python -m repositories.migrations drop_tables
    python -m repositories.migrations check_connection
"""

from repositories import (
    DatabaseManager,
    create_tables,
    drop_tables,
    check_database_connection,
)

def create_tables_command():
    """Create all database tables."""
    db_manager = DatabaseManager()
    
    try:
        db_manager.initialize(create_tables_if_not_exist=True)
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        sys.exit(1)
    finally:
        db_manager.close()

def drop_tables_command():
    """Drop all database tables."""
    db_manager = DatabaseManager()
    
    try:
        db_manager.initialize(create_tables_if_not_exist=False)
        engine = db_manager.get_engine()
        
        # Confirm before dropping
        response = input("Are you sure you want to drop all tables? This will delete all data! (y/N): ")
        if response.lower() != 'y':
            logger.info("Operation cancelled.")
            return
        
        drop_tables(engine)
        logger.info("Database tables dropped successfully!")
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        sys.exit(1)
    finally:
        db_manager.close()

def check_connection_command():
    """Check database connection."""
    db_manager = DatabaseManager()
    
    try:
        db_manager.initialize(create_tables_if_not_exist=False)
        engine = db_manager.get_engine()
        
        if check_database_connection(engine):
            logger.info("Database connection successful!")
        else:
            logger.error("Database connection failed!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to check connection: {e}")
        sys.exit(1)
    finally:
        db_manager.close()

def main():
    """Main command dispatcher."""
    if len(sys.argv) < 2:
        print("Usage: python -m repositories.migrations <command>")
        print("Commands:")
        print("  create_tables    - Create all database tables")
        print("  drop_tables      - Drop all database tables")
        print("  check_connection - Check database connection")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "create_tables":
        create_tables_command()
    elif command == "drop_tables":
        drop_tables_command()
    elif command == "check_connection":
        check_connection_command()
    else:
        logger.error(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()