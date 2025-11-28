"""
Database initialization for the FastAPI application.

This module handles setting up the PostgreSQL database connection and making
the Unit of Work available to the FastAPI dependency injection system.
"""
from __future__ import annotations
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import Depends
from sqlalchemy import Engine

from ..repositories.database import DatabaseManager
from ..repositories.unit_of_work import UnitOfWorkManager, SqlAlchemyUnitOfWork

logger = logging.getLogger(__name__)

# Global database manager instance
_db_manager: Optional[DatabaseManager] = None
_uow_manager: Optional[UnitOfWorkManager] = None

def initialize_database(create_tables: bool = True) -> DatabaseManager:
    """
    Initialize the PostgreSQL database connection.

    """
    global _db_manager, _uow_manager
    
    if _db_manager is not None:
        logger.info("Database already initialized")
        return _db_manager
    
    logger.info("Initializing PostgreSQL database connection...")
    
    _db_manager = DatabaseManager()
    _db_manager.initialize(create_tables_if_not_exist=create_tables)
    _uow_manager = _db_manager.get_uow_manager()
    
    logger.info("Database initialization completed")
    return _db_manager

def get_database_manager() -> DatabaseManager:
    """
    Get the global database manager instance.
    """
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return _db_manager

def get_uow_manager() -> UnitOfWorkManager:
    """
    Get the global Unit of Work manager instance.

    """
    if _uow_manager is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return _uow_manager

def shutdown_database():
    """Shutdown the database connection."""
    global _db_manager, _uow_manager
    
    if _db_manager:
        _db_manager.close()
        _db_manager = None
        _uow_manager = None
        logger.info("Database connection closed")

# FastAPI dependency to get Unit of Work
def get_uow():
    """
    FastAPI dependency to get a Unit of Work instance with automatic transaction management.
    
    Usage in FastAPI routes:
        @app.post("/users/")
        def create_user(user_data: dict, uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
            # Use uow.users, uow.profiles, etc.
            # Transaction is automatically committed on success
    """
    uow_manager = get_uow_manager()
    uow = uow_manager.create_uow()
    try:
        yield uow
        uow.commit() 
    except Exception:
        uow.rollback() 
        raise
    finally:
        uow.session.close()

@asynccontextmanager
async def database_lifespan(app):

    # Startup
    initialize_database()
    logger.info("Database initialized for FastAPI app")
    
    yield
    
    # Shutdown
    shutdown_database()
    logger.info("Database shutdown for FastAPI app")