import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator, JSON
from sqlalchemy.orm import relationship
import json

from ...core.database import Base


class JSONType(TypeDecorator):
    """Custom JSON type that uses JSONB for PostgreSQL and JSON for others."""
    impl = JSON

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is not None:
            # For dialects that store JSON as a string, we need to serialize it.
            if dialect.name != 'postgresql':
                return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            # For dialects that store JSON as a string, we need to deserialize it.
            if dialect.name != 'postgresql':
                return json.loads(value)
        return value


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_type = Column(String, nullable=False)
    payload = Column(JSONType(), nullable=False)
    status = Column(Enum("queued", "processing", "completed", "failed", "retrying", name="job_status"), default="queued")
    retries = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    result = Column(JSONType(), nullable=True)
    error_message = Column(JSONType(), nullable=True)