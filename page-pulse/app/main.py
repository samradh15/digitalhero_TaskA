from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import traceback
import sys

from app.audit import run_audit
from app.errors import AuditError, upstream_error

app = FastAPI(title="Page Pulse API")

class AuditRequest(BaseModel):
    url: str

@app.exception_handler(AuditError)
async def audit_error_handler(request: Request, exc: AuditError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message
            }
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the real exception server-side
    print(f"Unhandled exception: {exc}", file=sys.stderr)
    traceback.print_exc()
    
    # Never leak stack trace to client, return UPSTREAM_ERROR
    err = upstream_error()
    return JSONResponse(
        status_code=err.status_code,
        content={
            "error": {
                "code": err.code,
                "message": err.message
            }
        }
    )

@app.post("/api/audit")
async def audit_endpoint(payload: AuditRequest):
    # run_audit handles SSRF guard, fetching, parsing, and exceptions
    result = await run_audit(payload.url)
    return result

# Serve static files at root
app.mount("/", StaticFiles(directory="static", html=True), name="static")
