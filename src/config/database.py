from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

schema_Name="COSC4353_DB"

metadata = MetaData(schema=schema_Name)

Base = declarative_base(metadata=metadata)
