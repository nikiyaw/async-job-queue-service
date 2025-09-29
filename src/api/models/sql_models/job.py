import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator, JSON
from sqlalchemy.orm import relationship
from sqlalchemy import inspect
from sqlalchemy.ext.mutable import MutableDict

from ...core.database import Base


class JSONType(TypeDecorator):
    """Custom JSON type that uses JSONB for PostgreSQL and JSON for others."""
    impl = JSON

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        # Let SQLAlchemy handle serialization; don't double-serialize here.
        return value

    def process_result_value(self, value, dialect):
        # Let SQLAlchemy return Python objects (no manual json.loads).
        return value


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_type = Column(String, nullable=False)
    payload = Column(JSONType(), nullable=False)
    # store textual enum (portable across SQLite and Postgres)
    status = Column(
        Enum("queued", "processing", "completed", "failed", "retrying", name="job_status", native_enum=False),
        default="queued",
        nullable=False,
    )
    retries = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    result = Column(JSONType(), nullable=True)
    error_message = Column(JSONType(), nullable=True)