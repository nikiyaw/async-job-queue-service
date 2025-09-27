from pydantic import BaseModel
from typing import Dict, Any
from enum import Enum

class JobStatus(str, Enum):
    """
    Defines the possible states for a background job, used for API response validation
    and consistent status tracking across the application.
    The values correspond directly to the strings used in the database Enum column.
    """
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class JobSubmission(BaseModel):
    job_type: str
    payload: Dict[str, Any]