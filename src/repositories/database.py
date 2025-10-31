"""
Database configuration and setup utilities for PostgreSQL.

This module handles SQLAlchemy engine creation and database initialization
for the volunteer management system using PostgreSQL.
"""
from __future__ import annotations
import os
from typing import Optional

from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import sessionmaker

from src.config.logging_config import logger
from .models import Base
from .unit_of_work import UnitOfWorkManager, create_uow_manager


def get_postgres_url() -> str:
    """
    Get PostgreSQL connection URL from environment variables.
    
    Returns:
        PostgreSQL connection URL
    """
    # Check for full DATABASE_URL first
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Build from individual components
    host = os.getenv("DATABASE_HOST", "localhost")
    port = os.getenv("DATABASE_PORT", "5432")
    database = os.getenv("DATABASE_NAME", "volunteer_management")
    username = os.getenv("DATABASE_USER", "postgres")
    password = os.getenv("DATABASE_PASSWORD", "postgres")
    
    return f"postgresql://{username}:{password}@{host}:{port}/{database}"


def create_database_engine() -> Engine:
    """
    Create a PostgreSQL SQLAlchemy engine.
    
    Returns:
        Configured SQLAlchemy engine for PostgreSQL
    """
    url = get_postgres_url()
    echo = os.getenv("DATABASE_ECHO", "false").lower() == "true"
    
    return create_engine(
        url,
        echo=echo,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600
    )

def create_tables(engine: Engine) -> None:
    """
    Create all database tables.
    
    Args:
        engine: SQLAlchemy engine
    """
    logger.info("Creating database tables...")
    Base.metadata.create_all(engine)
    logger.info("Database tables created successfully")

def drop_tables(engine: Engine) -> None:
    """
    Drop all database tables.
    
    Warning: This will delete all data!
    
    Args:
        engine: SQLAlchemy engine
    """
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(engine)
    logger.info("Database tables dropped")

def check_database_connection(engine: Engine) -> bool:
    """
    Check if the database connection is working.
    
    Args:
        engine: SQLAlchemy engine
        
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

class DatabaseManager:
    """
    Simple database management class for PostgreSQL.
    """
    
    def __init__(self):
        self.engine: Optional[Engine] = None
        self.uow_manager: Optional[UnitOfWorkManager] = None
    
    def initialize(self, create_tables_if_not_exist: bool = True) -> None:
        """
        Initialize the database connection and setup.
        
        Args:
            create_tables_if_not_exist: Whether to create tables if they don't exist
        """
        postgres_url = get_postgres_url()
        logger.info(f"Initializing database connection to PostgreSQL...")
        
        # Create engine
        self.engine = create_database_engine()
        
        # Check connection
        if not check_database_connection(self.engine):
            raise RuntimeError("Failed to connect to PostgreSQL database")
        
        # Create tables if requested
        if create_tables_if_not_exist:
            create_tables(self.engine)
        
        # Create UoW manager
        self.uow_manager = create_uow_manager(self.engine)
        
        logger.info("PostgreSQL database initialized successfully")
    
    def get_uow_manager(self) -> UnitOfWorkManager:
        """
        Get the Unit of Work manager.
        
        Returns:
            UnitOfWorkManager instance
            
        Raises:
            RuntimeError: If database hasn't been initialized
        """
        if self.uow_manager is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.uow_manager
    
    def get_engine(self) -> Engine:
        """
        Get the SQLAlchemy engine.
        
        Returns:
            SQLAlchemy Engine instance
            
        Raises:
            RuntimeError: If database hasn't been initialized
        """
        if self.engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.engine
    
    def close(self) -> None:
        """Close the database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")