from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
import datetime

from ...core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_type = Column(String, nullable=False)
    # Use a conditional type: JSONB for Postgres, JSON for others (like SQLite)
    payload = Column(JSONB if Base.metadata.bind and Base.metadata.bind.name == 'postgresql' else JSON, nullable=False)
    status = Column(Enum("queued", "processing", "completed", "failed", "retrying", name="job_status"), default="queued")
    retries = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    # Use a conditional type for the result column as well
    result = Column(JSONB if Base.metadata.bind and Base.metadata.bind.name == 'postgresql' else JSON, nullable=True)
    error_message = Column(JSONB, nullable=True)