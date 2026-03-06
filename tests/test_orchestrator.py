"""
Tests for orchestrator happy path.

Ensures the session runner completes successfully.
"""

import pytest

from agents.architect import Architect
from agents.critic import Critic
from agents.judge import Judge
from agents.problem_framer import ProblemFramer
from agents.researcher import Researcher
from orchestrator.session_runner import SessionRunner
from schemas.models import (
    CandidateSolution,
    CritiqueReport,
    Evidence,
    EvidenceType,
    NextAction,
    ProblemDefinition,
    ResearchFindings,
    SessionInput,
)


class TestSessionRunnerHappyPath:
    """Happy path tests for SessionRunner."""

    @pytest.fixture
    def session_input(self):
        """Create a test session input."""
        return SessionInput(
            problem_description="Our user onboarding flow has a 60% drop-off rate at the email verification step",
            max_cycles=5,
            allow_external_research=True,
            context={"team_size": 5, "current_conversion": 0.4}
        )

    @pytest.fixture
    def runner(self):
        """Create a session runner with real agents."""
        return SessionRunner()

    @pytest.mark.asyncio
    async def test_complete_session(self, runner, session_input):
        """Test that a complete session runs successfully."""
        result = await runner.run(session_input)

        # Assert session completed
        assert result.session_id is not None
        assert len(result.session_id) > 0

        # Assert problem was framed
        assert result.problem is not None
        assert len(result.problem.root_problem) > 10
        assert len(result.problem.success_criteria) >= 1

        # Assert candidates were generated
        assert len(result.candidates) >= 2
        assert len(result.candidates) >= 3  # Should have at least 3

        # Assert top candidate selected
        assert result.top_candidate is not None
        assert result.top_candidate.id is not None

        # Assert convergence assessed
        assert result.convergence is not None
        assert result.convergence.confidence > 0
        assert len(result.convergence.reason) > 0

        # Assert synthesis generated
        assert len(result.final_synthesis) > 100
        assert "Problem" in result.final_synthesis

        # Assert cycles completed
        assert result.cycles_completed >= 3  # At least framing, candidates, critique

    @pytest.mark.asyncio
    async def test_problem_framing_phase(self, runner, session_input):
        """Test that problem framing works correctly."""
        # Run just the first phase via direct call
        from agents.problem_framer import ProblemFramerInput

        framer_input = ProblemFramerInput(
            raw_description=session_input.problem_description,
            context=session_input.context
        )

        framer = ProblemFramer()
        result = await framer.execute(framer_input)

        assert result.success is True
        assert result.data is not None
        assert isinstance(result.data, ProblemDefinition)
        assert "onboarding" in result.data.root_problem.lower()
        assert len(result.data.success_criteria) >= 1
        assert len(result.data.assumptions) >= 1

    @pytest.mark.asyncio
    async def test_research_phase(self, runner):
        """Test that research phase works correctly."""
        from agents.researcher import ResearcherInput

        researcher = Researcher()
        research_input = ResearcherInput(
            query="user onboarding optimization",
            problem_context="High drop-off in email verification",
            existing_evidence=[]
        )

        result = await researcher.execute(research_input)

        assert result.success is True
        assert result.data is not None
        assert isinstance(result.data, ResearchFindings)
        assert result.data.gaps_remain is True  # MVP always returns gaps
        assert len(result.data.suggested_followups) >= 1

    @pytest.mark.asyncio
    async def test_architect_phase(self, runner):
        """Test that candidate generation works correctly."""
        from agents.architect import ArchitectInput

        # First frame a problem
        problem = ProblemDefinition(
            raw_input="Slow API performance",
            root_problem="API response times exceed 500ms for key endpoints",
            success_criteria=["Response time under 200ms", "Maintain 99.9% uptime"],
            constraints=["Use existing database"],
            assumptions=[]
        )

        architect = Architect()
        architect_input = ArchitectInput(
            problem=problem,
            research=None,
            existing_candidates=[],
            min_candidates=3
        )

        result = await architect.execute(architect_input)

        assert result.success is True
        assert result.data is not None
        assert len(result.data) >= 3

        for candidate in result.data:
            assert isinstance(candidate, CandidateSolution)
            assert len(candidate.pros) >= 1
            assert len(candidate.cons) >= 1
            assert len(candidate.implementation_steps) >= 1
            assert candidate.estimated_effort is not None

    @pytest.mark.asyncio
    async def test_critic_phase(self, runner):
        """Test that critique phase works correctly."""
        from agents.critic import CriticInput

        problem = ProblemDefinition(
            raw_input="Test",
            root_problem="Test problem",
            success_criteria=["Success"]
        )

        candidates = [
            CandidateSolution(
                id="c1",
                name="Option 1",
                description="First approach",
                approach_type="technical",
                pros=["Fast"],
                cons=["Risky"],
                key_risks=[]
            ),
            CandidateSolution(
                id="c2",
                name="Option 2",
                description="Second approach",
                approach_type="process",
                pros=["Safe"],
                cons=["Slow"],
                key_risks=[]
            )
        ]

        critic = Critic()
        critic_input = CriticInput(
            problem=problem,
            candidates=candidates
        )

        result = await critic.execute(critic_input)

        assert result.success is True
        assert result.data is not None
        assert len(result.data) == 2

        for critique in result.data:
            assert isinstance(critique, CritiqueReport)
            assert len(critique.weaknesses) >= 1

    @pytest.mark.asyncio
    async def test_judge_phase(self, runner):
        """Test that judge phase works correctly."""
        from agents.judge import JudgeInput, JudgeOutput

        problem = ProblemDefinition(
            raw_input="Test",
            root_problem="Test problem with sufficient detail for testing",
            success_criteria=["Criterion 1", "Criterion 2"],
            constraints=["Constraint 1"]
        )

        candidates = [
            CandidateSolution(
                id="c1",
                name="Option 1",
                description="Detailed description for testing purposes",
                approach_type="technical",
                pros=["Fast", "Scalable"],
                cons=["Complex", "Expensive"],
                implementation_steps=["Step 1", "Step 2", "Step 3"],
                key_risks=[]
            ),
            CandidateSolution(
                id="c2",
                name="Option 2",
                description="Another detailed description for testing",
                approach_type="process",
                pros=["Simple", "Cheap"],
                cons=["Slow", "Limited"],
                implementation_steps=["Step A", "Step B", "Step C"],
                key_risks=[]
            )
        ]

        judge = Judge()
        judge_input = JudgeInput(
            problem=problem,
            cycle_number=3,
            max_cycles=5,
            research=None,
            candidates=candidates,
            critiques=[]
        )

        result = await judge.execute(judge_input)

        assert result.success is True
        assert result.data is not None
        assert isinstance(result.data, JudgeOutput)
        assert result.data.convergence is not None
        assert result.data.next_action is not None
        assert len(result.data.next_action_reasoning) > 0


class TestSessionRunnerEdgeCases:
    """Edge case tests for SessionRunner."""

    @pytest.mark.asyncio
    async def test_minimal_problem(self):
        """Test with minimal but valid problem description."""
        runner = SessionRunner()
        input_data = SessionInput(
            problem_description="x" * 10,  # Minimum valid length
            max_cycles=3
        )

        result = await runner.run(input_data)
        assert result.session_id is not None
        assert result.problem is not None

    @pytest.mark.asyncio
    async def test_single_cycle_limit(self):
        """Test with single cycle limit."""
        runner = SessionRunner()
        input_data = SessionInput(
            problem_description="Our API is too slow and needs optimization immediately",
            max_cycles=1
        )

        result = await runner.run(input_data)
        assert result.cycles_completed == 1
        # Should still have framed the problem
        assert result.problem is not None

    @pytest.mark.asyncio
    async def test_no_external_research(self):
        """Test with external research disabled."""
        runner = SessionRunner()
        input_data = SessionInput(
            problem_description="Our database queries are causing performance issues",
            max_cycles=5,
            allow_external_research=False
        )

        result = await runner.run(input_data)
        assert result.session_id is not None
        # Should still complete without research
        assert len(result.candidates) >= 2


class TestAgentIntegration:
    """Tests for agent integration points."""

    @pytest.mark.asyncio
    async def test_evidence_flow(self):
        """Test that evidence flows through agents."""
        framer = ProblemFramer()
        from agents.problem_framer import ProblemFramerInput

        result = await framer.execute(ProblemFramerInput(
            raw_description="Test problem with sufficient length",
            context={}
        ))

        assert result.success is True
        assert len(result.evidence_used) >= 1
        assert result.evidence_used[0].confidence > 0

    @pytest.mark.asyncio
    async def test_agent_result_fail(self):
        """Test that agent failures are handled gracefully."""
        from agents.base import AgentResult
        from schemas.models import ProblemDefinition

        # Test failure result creation
        fail_result = AgentResult[ProblemDefinition].fail("Test error")
        assert fail_result.success is False
        assert fail_result.error == "Test error"
        assert fail_result.data is None
