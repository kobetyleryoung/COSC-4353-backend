# scripts/init.py
from sqlalchemy import text, inspect
from src.repositories import models            # ensure models are imported
from src.repositories.models import Base
from src.repositories.database import create_database_engine

# Build the engine using your existing env-aware helper
engine = create_database_engine()

SCHEMA_NAME = getattr(models, "schema_Name", "public")
with engine.begin() as conn:
    if SCHEMA_NAME != "public":
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA_NAME}"'))
        conn.execute(text(f"SET search_path TO {SCHEMA_NAME}, public"))

# Create tables/constraints
Base.metadata.create_all(bind=engine, checkfirst=True)

# Verify
insp = inspect(engine)
print("Schemas:", insp.get_schema_names())
print(f"Tables in '{SCHEMA_NAME}':", insp.get_table_names(schema=SCHEMA_NAME))
print(f"✅ Schema '{SCHEMA_NAME}' and tables created successfully.")
