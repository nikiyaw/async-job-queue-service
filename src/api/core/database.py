from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .settings import settings

# SQLAlchemy engine
engine = create_engine(settings.database_url)

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