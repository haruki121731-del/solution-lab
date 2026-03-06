import pytest

from schemas.models import (
    ConvergenceStatus,
    CycleResult,
    NextAction,
    ProblemDefinition,
    SessionInput,
    SessionOutput,
    SessionState,
)
from storage.session_store import SQLiteSessionStore


@pytest.mark.asyncio
async def test_save_and_get_session(tmp_path) -> None:
    db_path = tmp_path / 'test.db'
    store = SQLiteSessionStore(db_path)

    # Create test data
    state = SessionState(
        session_id='test-123',
        input_data=SessionInput(problem_description='Test problem with enough length'),
    )
    state.problem = ProblemDefinition(
        raw_input='Test problem',
        root_problem='Test root',
    )
    state.cycles.append(
        CycleResult(
            cycle_number=1,
            action_taken=NextAction.design,
            notes='Test',
            convergence=ConvergenceStatus(converged=True, confidence=0.8, reason='Test'),
        )
    )
    state.final_synthesis = 'Test synthesis'

    # Save
    await store.save(state)

    # Retrieve
    result = await store.get('test-123')
    assert result is not None
    assert result.session_id == 'test-123'
    assert result.problem.root_problem == 'Test root'
    assert result.cycles_completed == 1
    assert result.convergence.converged is True


@pytest.mark.asyncio
async def test_list_sessions(tmp_path) -> None:
    db_path = tmp_path / 'test.db'
    store = SQLiteSessionStore(db_path)

    # Create multiple sessions
    for i in range(3):
        output = SessionOutput(
            session_id=f'session-{i}',
            problem=ProblemDefinition(raw_input=f'Test {i}', root_problem=f'Root {i}'),
            convergence=ConvergenceStatus(converged=True, confidence=0.8, reason='Test'),
            final_synthesis=f'Synthesis {i}',
            cycles_completed=5,
        )
        await store.save(output)

    # List
    sessions = await store.list_all(limit=10)
    assert len(sessions) == 3
    assert all('session_id' in s for s in sessions)
    assert all('problem' in s for s in sessions)


@pytest.mark.asyncio
async def test_get_nonexistent(tmp_path) -> None:
    db_path = tmp_path / 'test.db'
    store = SQLiteSessionStore(db_path)

    result = await store.get('nonexistent')
    assert result is None
