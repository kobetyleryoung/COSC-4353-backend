from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

# Don't specify a schema - use PostgreSQL default 'public' schema
schema_Name = None

metadata = MetaData(schema=schema_Name)

Base = declarative_base(metadata=metadata)
