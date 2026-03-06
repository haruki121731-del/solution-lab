"""
Tests for schema validation.

Ensures all Pydantic models validate correctly.
"""

import pytest
from pydantic import ValidationError

from schemas.models import (
    Assumption,
    CandidateSolution,
    ConvergenceStatus,
    CritiqueReport,
    CycleResult,
    Evidence,
    EvidenceType,
    NextAction,
    ProblemDefinition,
    ResearchFindings,
    Risk,
    SessionInput,
    SessionOutput,
    SessionState,
    Uncertainty,
)


class TestEvidence:
    """Tests for Evidence model."""

    def test_valid_evidence(self):
        """Test creating valid evidence."""
        evidence = Evidence(
            claim="Test claim",
            source="test",
            evidence_type=EvidenceType.USER_INPUT,
            confidence=0.8
        )
        assert evidence.claim == "Test claim"
        assert evidence.confidence == 0.8

    def test_confidence_bounds(self):
        """Test confidence must be 0-1."""
        with pytest.raises(ValidationError):
            Evidence(
                claim="Test",
                source="test",
                evidence_type=EvidenceType.HYPOTHESIS,
                confidence=1.5  # Invalid
            )


class TestAssumption:
    """Tests for Assumption model."""

    def test_valid_assumption(self):
        """Test creating valid assumption."""
        assumption = Assumption(
            statement="Users will adopt this feature",
            criticality="high",
            validation_needed=True
        )
        assert assumption.criticality == "high"
        assert assumption.validation_needed is True

    def test_invalid_criticality(self):
        """Test criticality must be low/medium/high."""
        with pytest.raises(ValidationError):
            Assumption(
                statement="Test",
                criticality="extreme",  # Invalid
                validation_needed=True
            )


class TestRisk:
    """Tests for Risk model."""

    def test_valid_risk(self):
        """Test creating valid risk."""
        risk = Risk(
            description="Implementation delays",
            likelihood="medium",
            impact="high",
            mitigation="Add buffer time"
        )
        assert risk.likelihood == "medium"
        assert risk.impact == "high"


class TestProblemDefinition:
    """Tests for ProblemDefinition model."""

    def test_valid_problem(self):
        """Test creating valid problem definition."""
        problem = ProblemDefinition(
            raw_input="Our API is too slow",
            root_problem="API response times exceed acceptable thresholds",
            success_criteria=["Response time under 200ms", "Error rate below 1%"],
            constraints=["Must use existing infrastructure"],
            stakeholders=["Engineering", "Product"],
            assumptions=[
                Assumption(
                    statement="Current database is the bottleneck",
                    criticality="high",
                    validation_needed=True
                )
            ]
        )
        assert len(problem.success_criteria) == 2

    def test_empty_success_criteria_fails(self):
        """Test that empty success criteria fails."""
        with pytest.raises(ValidationError):
            ProblemDefinition(
                raw_input="Problem",
                root_problem="Root",
                success_criteria=[]  # Empty - should fail
            )


class TestCandidateSolution:
    """Tests for CandidateSolution model."""

    def test_valid_candidate(self):
        """Test creating valid candidate."""
        candidate = CandidateSolution(
            id="c1",
            name="Optimize database queries",
            description="Add indexes and optimize N+1 queries",
            approach_type="technical",
            pros=["Fast implementation", "High impact"],
            cons=["Requires downtime", "Risk of regression"],
            implementation_steps=["Analyze queries", "Add indexes", "Test"],
            estimated_effort="Medium (1-2 weeks)",
            key_risks=[
                Risk(
                    description="Database corruption",
                    likelihood="low",
                    impact="high",
                    mitigation="Full backup before changes"
                )
            ]
        )
        assert candidate.score is None  # Not scored yet

    def test_score_bounds(self):
        """Test score must be 0-1."""
        with pytest.raises(ValidationError):
            CandidateSolution(
                id="c1",
                name="Test",
                description="Test",
                approach_type="technical",
                pros=["Pro"],
                cons=["Con"],
                score=1.5  # Invalid
            )


class TestCritiqueReport:
    """Tests for CritiqueReport model."""

    def test_valid_critique(self):
        """Test creating valid critique."""
        critique = CritiqueReport(
            candidate_id="c1",
            weaknesses=["Expensive", "Complex"],
            dealbreakers=["Requires unavailable expertise"]
        )
        assert len(critique.weaknesses) == 2


class TestSessionInput:
    """Tests for SessionInput model."""

    def test_valid_input(self):
        """Test creating valid session input."""
        input_data = SessionInput(
            problem_description="Our checkout flow has high abandonment",
            max_cycles=5,
            allow_external_research=True,
            context={"team_size": 5}
        )
        assert input_data.max_cycles == 5

    def test_short_description_fails(self):
        """Test that short descriptions fail."""
        with pytest.raises(ValidationError):
            SessionInput(
                problem_description="Too short"
            )

    def test_max_cycles_bounds(self):
        """Test max_cycles bounds."""
        with pytest.raises(ValidationError):
            SessionInput(
                problem_description="Valid problem description here",
                max_cycles=0  # Invalid - minimum 1
            )

        with pytest.raises(ValidationError):
            SessionInput(
                problem_description="Valid problem description here",
                max_cycles=25  # Invalid - maximum 20
            )


class TestConvergenceStatus:
    """Tests for ConvergenceStatus model."""

    def test_valid_convergence(self):
        """Test creating valid convergence status."""
        status = ConvergenceStatus(
            converged=True,
            confidence=0.85,
            reason="All criteria met",
            criteria_met={
                "root_problem_defined": True,
                "sufficient_candidates": True
            }
        )
        assert status.converged is True

    def test_confidence_bounds(self):
        """Test confidence bounds."""
        with pytest.raises(ValidationError):
            ConvergenceStatus(
                converged=True,
                confidence=1.5,  # Invalid
                reason="Test"
            )


class TestSessionState:
    """Tests for SessionState model."""

    def test_current_cycle(self):
        """Test current cycle calculation."""
        state = SessionState(
            session_id="test-123",
            input_data=SessionInput(problem_description="Test problem description here")
        )
        assert state.current_cycle == 1

        # Add a cycle
        state.cycles.append(CycleResult(
            cycle_number=1,
            next_action=NextAction.GENERATE_CANDIDATES,
            next_action_reasoning="Test"
        ))
        assert state.current_cycle == 2

    def test_is_complete(self):
        """Test completion detection."""
        state = SessionState(
            session_id="test-123",
            input_data=SessionInput(
                problem_description="Test problem description here",
                max_cycles=3
            )
        )
        assert not state.is_complete(3)

        # Add cycles to reach max
        for i in range(3):
            state.cycles.append(CycleResult(
                cycle_number=i+1,
                next_action=NextAction.GENERATE_CANDIDATES,
                next_action_reasoning="Test"
            ))

        assert state.is_complete(3)


class TestCycleResult:
    """Tests for CycleResult model."""

    def test_valid_cycle(self):
        """Test creating valid cycle result."""
        cycle = CycleResult(
            cycle_number=1,
            next_action=NextAction.RESEARCH,
            next_action_reasoning="Need more evidence"
        )
        assert cycle.cycle_number == 1


class TestResearchFindings:
    """Tests for ResearchFindings model."""

    def test_valid_findings(self):
        """Test creating valid research findings."""
        findings = ResearchFindings(
            query="performance optimization techniques",
            sources=["https://example.com/article"],
            findings=[
                Evidence(
                    claim="Caching improves performance",
                    source="example.com",
                    evidence_type=EvidenceType.EXTERNAL_RESEARCH,
                    confidence=0.9
                )
            ],
            gaps_remain=True,
            suggested_followups=["Research specific technologies"]
        )
        assert findings.gaps_remain is True


class TestUncertainty:
    """Tests for Uncertainty model."""

    def test_valid_uncertainty(self):
        """Test creating valid uncertainty."""
        uncertainty = Uncertainty(
            question="Will users adopt this feature?",
            blocker=True,
            reduction_strategy="User interviews"
        )
        assert uncertainty.blocker is True
