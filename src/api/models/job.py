from pydantic import BaseModel
from typing import Dict, Any

class JobSubmission(BaseModel):
    job_type: str
    payload: Dict[str, Any]