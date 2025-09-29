import datetime
from typing import Optional, Dict, List, Any, Union
from enum import Enum
from pydantic import BaseModel, Field

# Define the Job Status Enum
class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


# --- Request Schemas ---

class JobBase(BaseModel):
    job_type: str = Field(..., example="Data Analysis")
    # Using Dict[str, Any] allows for any valid JSON structure in the payload
    payload: Dict[str, Any] = Field(..., example={"input_data": 100})


class JobCreate(JobBase):
    """Schema for the POST /jobs/submit request body."""
    pass


# --- Base Response Schema for Database Mapping ---

class JobDBBase(BaseModel):
    """
    Base model that defines the Pydantic fields that map directly to the SQL Job model.
    """
    # FIX: Alias to map the SQL column 'id' to the API field 'job_id'
    job_id: int = Field(..., alias="id", example=1)
    job_type: str = Field(..., example="Data Analysis")
    status: JobStatus = Field(..., example=JobStatus.QUEUED)
    retries: int = Field(..., example=0)
    
    # FINAL FIX: Changed the type from 'str' back to 'datetime.datetime'.
    # Pydantic will now accept the Python datetime object from SQLAlchemy and
    # automatically convert it into an ISO 8601 string for the JSON response body.
    created_at: datetime.datetime 
    updated_at: datetime.datetime
    
    result: Optional[Dict[str, Any]] = Field(None, example={"output": 100})
    
    # FIX APPLIED: Changed type to Optional[Union[Dict[str, Any], str]] 
    # to handle both structured JSON errors (from the worker) and simple string errors (like in the test).
    error_message: Optional[Union[Dict[str, Any], str]] = Field(
        None, 
        example={"error": "Database error"}, 
        description="Error message, which can be a simple string or a structured dictionary."
    )

    class Config:
        # Crucial for mapping SQLAlchemy objects
        from_attributes = True
        # Enables mapping SQL field names (like 'id') to Pydantic field names (like 'job_id')
        populate_by_name = True


class JobSubmitResponse(BaseModel):
    """Schema for the 201 response after submitting a job (manually constructed in the router)."""
    message: str = Field(..., example="Job received successfully")
    job_id: int = Field(..., example=1)
    job_type: str = Field(..., example="Data Analysis")
    status: JobStatus = Field(..., example=JobStatus.QUEUED)


class JobStatusResponse(JobDBBase):
    """
    Schema for the GET /jobs/status/{job_id} response and list responses. 
    It inherits all correctly aliased and typed fields from JobDBBase.
    """
    pass