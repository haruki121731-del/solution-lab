from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from orchestrator.session_runner import SessionRunner
from schemas.models import SessionInput, SessionOutput

session_runner: SessionRunner | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global session_runner
    session_runner = SessionRunner()
    yield
    session_runner = None


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description='Structured multi-agent solution-finding API.',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'] if settings.debug else [],
    allow_credentials=False,
    allow_methods=['GET', 'POST'],
    allow_headers=['*'],
)


@app.get('/')
async def root() -> dict[str, Any]:
    return {
        'name': settings.app_name,
        'version': settings.app_version,
        'endpoints': {'health': 'GET /health', 'solve': 'POST /solve'},
    }


@app.get('/health')
async def health_check() -> dict[str, str]:
    return {'status': 'healthy', 'service': settings.app_name}


@app.post('/solve', response_model=SessionOutput)
async def solve_problem(input_data: SessionInput) -> SessionOutput:
    if session_runner is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Session runner unavailable.')
    return await session_runner.run(input_data)


@app.exception_handler(RuntimeError)
async def runtime_error_handler(_: Request, exc: RuntimeError) -> JSONResponse:
    return JSONResponse(status_code=500, content={'detail': str(exc)})
