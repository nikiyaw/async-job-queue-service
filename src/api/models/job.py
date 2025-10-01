import datetime
from typing import Optional, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field


# --- Job Status Enum ---
class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


# --- Request Schemas ---
class JobBase(BaseModel):
    job_type: str = Field(
        default=...,
        description="Type of job",
        json_schema_extra={"example": "Data Analysis"},
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Payload data",
        json_schema_extra={"example": {"input_data": 100}},
    )


class JobCreate(JobBase):
    """Schema for the POST /jobs/submit request body."""
    pass


# --- Base DB Schema ---
class JobDBBase(BaseModel):
    job_id: int = Field(
        default=...,
        description="Job ID",
        json_schema_extra={"example": 1},
    )
    job_type: str = Field(
        default=...,
        description="Type of job",
        json_schema_extra={"example": "Data Analysis"},
    )
    status: JobStatus = Field(
        default=JobStatus.QUEUED,
        description="Current status",
        json_schema_extra={"example": JobStatus.QUEUED},
    )
    retries: int = Field(
        default=0,
        description="Number of retries",
        json_schema_extra={"example": 0},
    )
    created_at: datetime.datetime = Field(
        default=...,
        description="Job creation timestamp",
    )
    updated_at: datetime.datetime = Field(
        default=...,
        description="Job update timestamp",
    )
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Result data",
        json_schema_extra={"example": {"output": 100}},
    )
    error_message: Optional[Union[str, Dict[str, Any]]] = Field(
        default=None,
        description="Error message, string or structured dict",
        json_schema_extra={"example": {"error": "Database error"}},
    )

    class Config:
        from_attributes = True
        populate_by_name = True


# --- Response Schemas ---
class JobSubmitResponse(BaseModel):
    message: str = Field(
        default=...,
        description="Response message",
        json_schema_extra={"example": "Job received successfully"},
    )
    job_id: int = Field(
        default=...,
        description="Job ID",
        json_schema_extra={"example": 1},
    )
    job_type: str = Field(
        default=...,
        description="Type of job",
        json_schema_extra={"example": "Data Analysis"},
    )
    status: JobStatus = Field(
        default=JobStatus.QUEUED,
        description="Current status",
        json_schema_extra={"example": JobStatus.QUEUED},
    )


class JobStatusResponse(JobDBBase):
    """Schema for GET /jobs/status/{job_id} responses."""
    pass