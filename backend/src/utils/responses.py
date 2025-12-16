from typing import Any, Optional, Dict
from fastapi.responses import JSONResponse

def success_response(data: Any = None, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "data": data
        }
    )

def error_response(
    message: str,
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    error_content = {"message": message}
    if details:
        error_content["details"] = details

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": error_content
        }
    )
