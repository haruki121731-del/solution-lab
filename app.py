"""
Solution Lab - FastAPI Entry Point

Multi-agent research OS for solving product problems through structured cycles.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from orchestrator.session_runner import SessionRunner
from schemas.models import (
    CycleResult,
    SessionInput,
    SessionOutput,
)


# Global state
session_runner: SessionRunner | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global session_runner
    # Startup
    session_runner = SessionRunner()
    yield
    # Shutdown
    session_runner = None


app = FastAPI(
    title=settings.app_name,
    description="Multi-agent research OS for structured problem-solving",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.app_name}


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint with API info."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "endpoints": {
            "solve": "POST /solve - Run a solution session",
            "health": "GET /health - Health check"
        }
    }


@app.post("/solve", response_model=SessionOutput)
async def solve_problem(input_data: SessionInput) -> SessionOutput:
    """
    Run a complete solution session.

    This endpoint orchestrates the full cycle:
    1. Problem framing
    2. External research (if enabled)
    3. Candidate generation
    4. Aggressive critique
    5. Convergence judgment

    The process continues until convergence or max_cycles is reached.
    """
    if not session_runner:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session runner not initialized"
        )

    try:
        result = await session_runner.run(input_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session execution failed: {str(e)}"
        )


@app.post("/solve/async")
async def solve_problem_async(input_data: SessionInput) -> dict[str, str]:
    """
    Start an async solution session.

    TODO: Implement async job queue for long-running sessions.
    """
    # Placeholder for async implementation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Async sessions not yet implemented"
    )


# Error handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
