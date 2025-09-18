from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# Database connection string
DATABASE_URL = "postgresql://user:password@localhost:5433/jobs_db" 

# SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our models
Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(Enum("queued", "processing", "completed", "failed", name="job_status"), default="queued")
    retries = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)