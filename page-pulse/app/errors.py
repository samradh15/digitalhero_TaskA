from fastapi import HTTPException
from pydantic import BaseModel

class ErrorDetail(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    error: ErrorDetail

class AuditError(Exception):
    def __init__(self, code: str, status_code: int, message: str):
        self.code = code
        self.status_code = status_code
        self.message = message
        super().__init__(message)

def create_error(code: str, status_code: int, message: str) -> AuditError:
    return AuditError(code=code, status_code=status_code, message=message)

# Helper functions to quickly raise specific errors
def invalid_url(message: str = "Malformed URL."):
    return create_error("INVALID_URL", 400, message)

def private_address(message: str = "This URL points to a private address and can't be scanned."):
    return create_error("PRIVATE_ADDRESS", 400, message)

def timeout(message: str = "Couldn't reach this URL — the server didn't respond within 10s."):
    return create_error("TIMEOUT", 504, message)

def connection_failed(reason: str):
    return create_error("CONNECTION_FAILED", 502, f"Couldn't connect to this host. ({reason})")

def non_html_response(content_type: str):
    return create_error("NON_HTML_RESPONSE", 415, f"Expected text/html, but received {content_type}.")

def too_many_redirects():
    return create_error("TOO_MANY_REDIRECTS", 502, "This URL redirected more than 5 times.")

def response_too_large():
    return create_error("RESPONSE_TOO_LARGE", 413, "This page is too large to audit.")

def upstream_error():
    return create_error("UPSTREAM_ERROR", 502, "An unexpected error occurred while processing the URL.")
