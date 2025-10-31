"""
Repositories package for the volunteer management system.

This package contains the database layer implementation including:
- SQLAlchemy models 
- Repository implementations
- Unit of Work pattern
- PostgreSQL database configuration and setup
- FastAPI integration utilities

Usage:
    from repositories import DatabaseManager
    
    db_manager = DatabaseManager()
    db_manager.initialize()
"""

# Core database functionality
from .database import (
    DatabaseManager, 
    create_database_engine,
    create_tables,
    drop_tables,
    check_database_connection,
)

# Unit of Work pattern
from .unit_of_work import (
    SqlAlchemyUnitOfWork,
    UnitOfWorkManager,
    create_uow_manager,
)

# SQLAlchemy models (for migrations and advanced usage)
from .models import Base

__all__ = [
    # Database configuration
    "DatabaseManager",
    "create_database_engine", 
    "create_tables",
    "drop_tables",
    "check_database_connection",
    
    # Unit of Work
    "SqlAlchemyUnitOfWork",
    "UnitOfWorkManager",
    "create_uow_manager",
    
    # SQLAlchemy
    "Base",
]