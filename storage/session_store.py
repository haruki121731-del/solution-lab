from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from schemas.models import SessionOutput, SessionState


class SessionStore(ABC):
    """Abstract base for session persistence."""

    @abstractmethod
    async def save(self, session: SessionState | SessionOutput) -> None: ...

    @abstractmethod
    async def get(self, session_id: str) -> SessionOutput | None: ...

    @abstractmethod
    async def list_all(self, limit: int = 100) -> list[dict[str, Any]]: ...


class SQLiteSessionStore(SessionStore):
    """SQLite-based session storage."""

    def __init__(self, db_path: str | Path = './sessions.db') -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    problem TEXT NOT NULL,
                    final_synthesis TEXT NOT NULL,
                    cycles_completed INTEGER NOT NULL,
                    converged BOOLEAN NOT NULL,
                    data TEXT NOT NULL
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_created 
                ON sessions(created_at DESC)
            ''')

    async def save(self, session: SessionState | SessionOutput) -> None:
        """Save session to database."""
        if isinstance(session, SessionState):
            # Convert SessionState to SessionOutput for storage
            from schemas.models import ConvergenceStatus

            output = SessionOutput(
                session_id=session.session_id,
                problem=session.problem,
                research=session.research,
                candidates=session.candidates,
                critiques=session.critiques,
                top_candidate=session.candidates[0] if session.candidates else None,
                convergence=session.cycles[-1].convergence if session.cycles else ConvergenceStatus(converged=False, confidence=0.0, reason=''),
                final_synthesis=session.final_synthesis,
                cycles_completed=len(session.cycles),
                cycles=session.cycles,
            )
        else:
            output = session

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                INSERT OR REPLACE INTO sessions 
                (session_id, created_at, updated_at, problem, final_synthesis, cycles_completed, converged, data)
                VALUES (?, datetime('now'), datetime('now'), ?, ?, ?, ?, ?)
                ''',
                (
                    output.session_id,
                    output.problem.root_problem,
                    output.final_synthesis,
                    output.cycles_completed,
                    output.convergence.converged,
                    output.model_dump_json(),
                ),
            )

    async def get(self, session_id: str) -> SessionOutput | None:
        """Retrieve session by ID."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                'SELECT data FROM sessions WHERE session_id = ?', (session_id,)
            ).fetchone()
            if row:
                return SessionOutput.model_validate_json(row[0])
            return None

    async def list_all(self, limit: int = 100) -> list[dict[str, Any]]:
        """List recent sessions."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                '''
                SELECT session_id, created_at, problem, cycles_completed, converged 
                FROM sessions 
                ORDER BY created_at DESC 
                LIMIT ?
                ''',
                (limit,),
            ).fetchall()
            return [
                {
                    'session_id': row[0],
                    'created_at': row[1],
                    'problem': row[2],
                    'cycles_completed': row[3],
                    'converged': row[4],
                }
                for row in rows
            ]
