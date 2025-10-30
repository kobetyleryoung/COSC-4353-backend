from sqlalchemy import create_engine, text
from src.config.database import Base, schema_Name
#add models here so from src.domain, we need to create a separate folder to create the schema tables

Database_URL="postgresql+psycopg2://user:password@localhost:5432/COSC4353_DB"

engine= create_engine(Database_URL)

with engine.connect() as conn:
    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_Name}"))
    conn.commit()

Base.metadata.create_all(bind=engine)

print(f"✅ Database schema '{schema_Name}' and tables created successfully!")