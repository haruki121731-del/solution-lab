from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from auth.api_key import get_api_key_auth
from config import settings
from orchestrator.session_runner import SessionRunner
from schemas.models import SessionInput, SessionOutput
from storage.session_store import SQLiteSessionStore

# Global state
session_runner: SessionRunner | None = None
session_store: SQLiteSessionStore | None = None
auth = get_api_key_auth()


@asynccontextmanager
async def lifespan(_: FastAPI):
    global session_runner, session_store
    session_runner = SessionRunner()
    session_store = SQLiteSessionStore(settings.session_storage_path)
    yield
    session_runner = None
    session_store = None


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
        'endpoints': {
            'health': 'GET /health',
            'solve': 'POST /solve (auth optional)',
            'sessions': 'GET /sessions (list)',
            'session': 'GET /sessions/{id} (retrieve)',
        },
        'auth_required': bool(auth.valid_keys),
    }


@app.get('/health')
async def health_check() -> dict[str, str]:
    return {'status': 'healthy', 'service': settings.app_name}


@app.post('/solve', response_model=SessionOutput)
async def solve_problem(
    input_data: SessionInput,
    api_key: str = Depends(auth),
) -> SessionOutput:
    if session_runner is None or session_store is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Session runner unavailable.')

    result = await session_runner.run(input_data)

    # Persist session
    await session_store.save(result)

    return result


@app.get('/sessions')
async def list_sessions(
    limit: int = 100,
    api_key: str = Depends(auth),
) -> list[dict[str, Any]]:
    if session_store is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Session store unavailable.')

    return await session_store.list_all(limit=limit)


@app.get('/sessions/{session_id}')
async def get_session(
    session_id: str,
    api_key: str = Depends(auth),
) -> SessionOutput:
    if session_store is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Session store unavailable.')

    result = await session_store.get(session_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Session not found.')

    return result


@app.exception_handler(RuntimeError)
async def runtime_error_handler(_: Request, exc: RuntimeError) -> JSONResponse:
    return JSONResponse(status_code=500, content={'detail': str(exc)})
