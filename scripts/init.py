from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from src.config.database import Base, schema_Name
from src.repositories import models

Database_URL = "postgresql+psycopg2://user:password!@localhost:5432/COSC4353_DB"
engine = create_engine(Database_URL)

with engine.begin() as conn:
    conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_Name}"'))

Base.metadata.create_all(bind=engine)

SessionLocal= sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Verify tables
inspector = inspect(engine)
print(inspector.get_table_names(schema=schema_Name))
print(f"✅ Database schema '{schema_Name}' and tables created successfully!")
