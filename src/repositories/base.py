"""
SQLAlchemy Base configuration.

This module provides the declarative base class that all models inherit from.
Separated to avoid circular imports between database.py and models.py.
"""
from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

# Don't specify a schema - use PostgreSQL default 'public' schema
schema_Name = None

metadata = MetaData(schema=schema_Name)

Base = declarative_base(metadata=metadata)
