from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# Get DB credentials from environment variables (best practice)
# We'll hardcode them for now since we haven't done docker-compose for the whole stack yet.
# In Week 3, we'll switch this to use environment variables.
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5433/jobs_db")

# SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our models
Base = declarative_base()

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()