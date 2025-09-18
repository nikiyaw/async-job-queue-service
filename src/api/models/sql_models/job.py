from sqlalchemy import Column, Integer, String, JSON, DateTime, Enum
from sqlalchemy.orm import relationship
import datetime

from ..core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(Enum("queued", "processing", "completed", "failed", name="job_status"), default="queued")
    retries = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)