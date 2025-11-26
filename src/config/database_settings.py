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
    
    Args:
        create_tables: Whether to create database tables if they don't exist
        
    Returns:
        Configured DatabaseManager instance
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
    
    Returns:
        DatabaseManager instance
        
    Raises:
        RuntimeError: If database hasn't been initialized
    """
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return _db_manager

def get_uow_manager() -> UnitOfWorkManager:
    """
    Get the global Unit of Work manager instance.
    
    Returns:
        UnitOfWorkManager instance
        
    Raises:
        RuntimeError: If database hasn't been initialized
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

# FastAPI dependency to get Unit of Work Manager
def get_uow() -> UnitOfWorkManager:
    """
    FastAPI dependency to get the Unit of Work Manager instance.
    
    Usage in FastAPI routes:
        @app.post("/users/")
        def create_user(user_data: dict, uow_manager: UnitOfWorkManager = Depends(get_uow)):
            with uow_manager.get_uow() as uow:
                # Use uow.users, uow.profiles, etc.
                uow.commit()
    """
    return get_uow_manager()

@asynccontextmanager
async def database_lifespan(app):
    """
    FastAPI lifespan context manager for database initialization.
    
    Usage:
        app = FastAPI(lifespan=database_lifespan)
    """
    # Startup
    initialize_database()
    logger.info("Database initialized for FastAPI app")
    
    yield
    
    # Shutdown
    shutdown_database()
    logger.info("Database shutdown for FastAPI app")