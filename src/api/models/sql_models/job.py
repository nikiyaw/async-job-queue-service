from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator, JSON
from sqlalchemy.orm import relationship
import datetime

from ...core.database import Base

class JSONType(TypeDecorator):
    """Custom JSON type that uses JSONB for PostgreSQL and JSON for others."""
    impl = JSON

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        # For other dialects, JSON is often stored as a string
        return value

    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        # For other dialects, JSON is often stored as a string
        return value


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_type = Column(String, nullable=False)
    # Use our custom JSONType which handles the dialect logic
    payload = Column(JSONType(), nullable=False)
    status = Column(Enum("queued", "processing", "completed", "failed", "retrying", name="job_status"), default="queued")
    retries = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    # Use our custom JSONType for the result column
    result = Column(JSONType(), nullable=True)
    error_message = Column(String, nullable=True)