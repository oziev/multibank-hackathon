from pydantic import BaseModel
from typing import Any, Optional, Dict

class SuccessResponse(BaseModel):
    success: bool = True
    data: Any

class ErrorDetail(BaseModel):
    message: str
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
