import pytest

from orchestrator.session_runner import SessionRunner
from schemas.models import SessionInput


@pytest.mark.asyncio
async def test_runner_completes_and_returns_top_candidate() -> None:
    runner = SessionRunner()
    result = await runner.run(
        SessionInput(
            problem_description='Our onboarding flow loses too many users at email verification.',
            max_cycles=5,
            allow_external_research=True,
            context={'team_size': 4},
        )
    )

    assert result.problem.root_problem
    assert result.research is not None
    assert len(result.candidates) >= 3
    assert len(result.critiques) == len(result.candidates)
    assert result.top_candidate is not None
    assert result.convergence.confidence > 0
    assert 'Problem:' in result.final_synthesis


@pytest.mark.asyncio
async def test_runner_works_without_research() -> None:
    runner = SessionRunner()
    result = await runner.run(
        SessionInput(
            problem_description='Our API is too slow during peak traffic and users abandon requests.',
            max_cycles=5,
            allow_external_research=False,
        )
    )

    assert result.problem is not None
    assert len(result.candidates) >= 3
    assert result.cycles_completed >= 4
