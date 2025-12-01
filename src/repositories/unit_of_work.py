"""
SQLAlchemy Unit of Work implementation.

This module provides transaction management and repository access
through the Unit of Work pattern. It ensures that all operations
within a transaction are committed or rolled back together.
"""
from __future__ import annotations
from typing import Generator, Protocol
from contextlib import contextmanager

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import Engine

from ..domain.repositories import UnitOfWork
from .sqlalchemy_repositories import (
    SqlAlchemyUserRepository,
    SqlAlchemyProfileRepository,
    SqlAlchemyEventRepository,
    SqlAlchemyOpportunityRepository,
    SqlAlchemyMatchRepository,
    SqlAlchemyMatchRequestRepository,
    SqlAlchemyNotificationRepository,
    SqlAlchemyVolunteerHistoryRepository,
)

class SqlAlchemyUnitOfWork:
    """SQLAlchemy implementation of UnitOfWork."""
    
    def __init__(self, session: Session):
        self.session = session
        self._setup_repositories()
    
    def _setup_repositories(self) -> None:
        """Initialize all repositories with the current session."""
        self.users = SqlAlchemyUserRepository(self.session)
        self.profiles = SqlAlchemyProfileRepository(self.session)
        self.events = SqlAlchemyEventRepository(self.session)
        self.opportunities = SqlAlchemyOpportunityRepository(self.session)
        self.matches = SqlAlchemyMatchRepository(self.session)
        self.match_requests = SqlAlchemyMatchRequestRepository(self.session)
        self.notifications = SqlAlchemyNotificationRepository(self.session)
        self.volunteer_history = SqlAlchemyVolunteerHistoryRepository(self.session)
    
    def commit(self) -> None:
        """Commit the current transaction."""
        self.session.commit()
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.session.rollback()

class UnitOfWorkManager:
    """
    Factory for creating Unit of Work instances with proper session management.
    
    This class manages the SQLAlchemy session lifecycle and provides
    context managers for transaction handling.
    """
    
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory
    
    @contextmanager
    def get_uow(self) -> Generator[SqlAlchemyUnitOfWork, None, None]:
        """
        Get a Unit of Work instance within a transaction context.
        
        Usage:
            with uow_manager.get_uow() as uow:
                # Do work with repositories
                user = uow.users.get_by_email("test@example.com")
                uow.commit()  # Commit changes
        
        The session will be automatically closed when exiting the context,
        and rolled back if an exception occurs.
        """
        session = self.session_factory()
        try:
            uow = SqlAlchemyUnitOfWork(session)
            yield uow
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_uow(self) -> SqlAlchemyUnitOfWork:
        """
        Create a Unit of Work instance.
        
        Warning: When using this method, you're responsible for managing
        the session lifecycle (commit/rollback/close).
        Consider using get_uow() context manager instead.
        """
        session = self.session_factory()
        return SqlAlchemyUnitOfWork(session)

def create_uow_manager(engine: Engine) -> UnitOfWorkManager:
    """
    Create a UnitOfWorkManager from a SQLAlchemy engine.
    
    Args:
        engine: SQLAlchemy engine instance
        
    Returns:
        Configured UnitOfWorkManager instance
    """
    session_factory = sessionmaker(bind=engine)
    return UnitOfWorkManager(session_factory)