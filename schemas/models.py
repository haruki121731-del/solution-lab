"""
Core Pydantic models for Solution Lab.

All agents communicate via these structured schemas, never loose prose.
"""

from datetime import datetime, timezone

def utc_now():
    """Return current UTC time."""
    return datetime.now(timezone.utc)
from enum import Enum, auto
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EvidenceType(str, Enum):
    """Classification of evidence sources."""

    USER_INPUT = "user_input"
    EXTERNAL_RESEARCH = "external_research"
    CALCULATION = "calculation"
    ANALOGY = "analogy"
    EXPERT_OPINION = "expert_opinion"
    HYPOTHESIS = "hypothesis"  # Marked as unverified
    ANALYSIS = "analysis"  # Derived from analysis process


class Evidence(BaseModel):
    """A piece of evidence supporting or refuting a claim."""

    claim: str = Field(description="What is being asserted")
    source: str = Field(description="Origin of this evidence")
    evidence_type: EvidenceType = Field(description="Classification of evidence")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence score (0-1)"
    )
    data: dict[str, Any] = Field(
        default_factory=dict, description="Structured supporting data"
    )
    is_verified: bool = Field(
        default=False, description="Whether this evidence has been verified"
    )


class Assumption(BaseModel):
    """An explicit assumption made during problem-solving."""

    statement: str = Field(description="The assumption being made")
    criticality: str = Field(
        pattern="^(low|medium|high)$",
        description="Impact if assumption is wrong"
    )
    validation_needed: bool = Field(
        description="Whether this assumption needs validation"
    )
    evidence: list[Evidence] = Field(default_factory=list)


class Risk(BaseModel):
    """A identified risk in a solution candidate."""

    description: str = Field(description="What could go wrong")
    likelihood: str = Field(
        pattern="^(low|medium|high)$",
        description="Probability of occurrence"
    )
    impact: str = Field(
        pattern="^(low|medium|high)$",
        description="Severity if it occurs"
    )
    mitigation: str | None = Field(
        default=None, description="How to reduce this risk"
    )


class Uncertainty(BaseModel):
    """An identified uncertainty that needs resolution."""

    question: str = Field(description="What is unknown")
    blocker: bool = Field(
        description="Whether this blocks progress without answer"
    )
    reduction_strategy: str | None = Field(
        default=None, description="How to reduce this uncertainty"
    )


class ProblemDefinition(BaseModel):
    """The framed root problem with context."""

    raw_input: str = Field(description="Original user input")
    root_problem: str = Field(description="Core problem distilled")
    success_criteria: list[str] = Field(
        min_length=1, description="How we know we solved it"
    )
    constraints: list[str] = Field(default_factory=list)
    stakeholders: list[str] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )


class ResearchFindings(BaseModel):
    """Structured findings from external research."""

    query: str = Field(description="What was researched")
    sources: list[str] = Field(default_factory=list)
    findings: list[Evidence] = Field(default_factory=list)
    gaps_remain: bool = Field(
        description="Whether critical gaps remain after research"
    )
    suggested_followups: list[str] = Field(default_factory=list)


class CandidateSolution(BaseModel):
    """A proposed solution candidate."""

    id: str = Field(description="Unique identifier")
    name: str = Field(description="Short descriptive name")
    description: str = Field(description="Detailed explanation")
    approach_type: str = Field(
        description="Category: technical, process, hybrid, etc."
    )
    pros: list[str] = Field(min_length=1)
    cons: list[str] = Field(min_length=1)
    implementation_steps: list[str] = Field(default_factory=list)
    estimated_effort: str | None = Field(
        default=None, description="T-shirt size or time estimate"
    )
    key_risks: list[Risk] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Evaluated score"
    )


class CritiqueReport(BaseModel):
    """Aggressive critique of solution candidates."""

    candidate_id: str = Field(description="Which candidate was critiqued")
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(min_length=1)
    dealbreakers: list[str] = Field(default_factory=list)
    uncertainties_raised: list[Uncertainty] = Field(default_factory=list)
    comparison_to_others: dict[str, str] = Field(
        default_factory=dict,
        description="How this compares to other candidates by ID"
    )


class NextAction(str, Enum):
    """Possible next actions in the solution cycle."""

    RESEARCH = "research"
    GENERATE_CANDIDATES = "generate_candidates"
    CRITIQUE = "critique"
    REFINE_PROBLEM = "refine_problem"
    CONVERGE = "converge"
    NEEDS_HUMAN_INPUT = "needs_human_input"


class ConvergenceStatus(BaseModel):
    """Assessment of whether problem is sufficiently solved."""

    converged: bool = Field(description="Whether convergence achieved")
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(description="Why converged or not")
    criteria_met: dict[str, bool] = Field(
        default_factory=dict,
        description="Which convergence criteria are satisfied"
    )


class CycleResult(BaseModel):
    """Output from a single cycle of the solution loop."""

    cycle_number: int = Field(ge=1)
    problem: ProblemDefinition | None = None
    research: ResearchFindings | None = None
    candidates: list[CandidateSolution] = Field(default_factory=list)
    critiques: list[CritiqueReport] = Field(default_factory=list)
    next_action: NextAction = Field(description="What to do next")
    next_action_reasoning: str = Field(description="Why this action")
    uncertainties: list[Uncertainty] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=utc_now)


class SessionInput(BaseModel):
    """Input to start a solution session."""

    problem_description: str = Field(
        min_length=10,
        description="Raw product problem description"
    )
    max_cycles: int = Field(
        default=5, ge=1, le=20,
        description="Maximum cycles before forced stop"
    )
    allow_external_research: bool = Field(
        default=True,
        description="Whether to allow external research"
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for the session"
    )

    @field_validator("problem_description")
    @classmethod
    def validate_problem_not_empty(cls, v: str) -> str:
        """Ensure problem description has substance."""
        if len(v.strip()) < 10:
            raise ValueError("Problem description must be at least 10 characters")
        return v.strip()


class SessionOutput(BaseModel):
    """Final output from a completed solution session."""

    session_id: str = Field(description="Unique session identifier")
    problem: ProblemDefinition
    research_findings: ResearchFindings | None = None
    candidates: list[CandidateSolution] = Field(default_factory=list)
    top_candidate: CandidateSolution | None = None
    critique_summary: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Summary of critiques by candidate ID"
    )
    convergence: ConvergenceStatus
    final_synthesis: str = Field(description="Executive summary")
    cycles_completed: int = Field(ge=0)
    artifacts_generated: list[str] = Field(default_factory=list)


class SessionState(BaseModel):
    """Internal state tracking for an active session."""

    session_id: str
    input_data: SessionInput
    cycles: list[CycleResult] = Field(default_factory=list)
    current_problem: ProblemDefinition | None = None
    research_done: bool = False
    candidates_generated: int = 0
    critiques_done: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @property
    def current_cycle(self) -> int:
        """Return the current cycle number."""
        return len(self.cycles) + 1

    @property
    def last_cycle(self) -> CycleResult | None:
        """Return the most recent cycle result."""
        return self.cycles[-1] if self.cycles else None

    def is_complete(self, max_cycles: int) -> bool:
        """Check if session has reached completion criteria."""
        if self.current_cycle > max_cycles:
            return True
        last = self.last_cycle
        if last and last.next_action == NextAction.CONVERGE:
            return True
        return False
