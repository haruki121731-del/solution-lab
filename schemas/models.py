from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EvidenceType(str, Enum):
    user_input = 'user_input'
    heuristic = 'heuristic'
    external = 'external'
    benchmark = 'benchmark'


class NextAction(str, Enum):
    research = 'research'
    design = 'design'
    critique = 'critique'
    converge = 'converge'


class RiskSeverity(str, Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'


class Evidence(BaseModel):
    title: str
    summary: str
    source: str
    evidence_type: EvidenceType
    confidence: float = Field(ge=0.0, le=1.0)
    url: str | None = None


class Assumption(BaseModel):
    statement: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class Uncertainty(BaseModel):
    question: str
    impact: str
    suggested_resolution: str


class Risk(BaseModel):
    name: str
    description: str
    severity: RiskSeverity = RiskSeverity.medium
    mitigation: str


class ProblemDefinition(BaseModel):
    raw_input: str
    root_problem: str
    success_criteria: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)


class ResearchFindings(BaseModel):
    findings: list[Evidence] = Field(default_factory=list)
    research_summary: str = ''
    gaps_remain: bool = True
    suggested_followups: list[str] = Field(default_factory=list)


class CandidateSolution(BaseModel):
    id: str
    name: str
    description: str
    approach_type: str
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    implementation_steps: list[str] = Field(default_factory=list)
    key_risks: list[Risk] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    estimated_effort: str = 'medium'
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class CritiqueReport(BaseModel):
    candidate_id: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    open_questions: list[Uncertainty] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0, default=0.5)


class ConvergenceStatus(BaseModel):
    converged: bool = False
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    reason: str


class CycleResult(BaseModel):
    cycle_number: int
    action_taken: NextAction
    notes: str
    problem: ProblemDefinition | None = None
    research: ResearchFindings | None = None
    candidates: list[CandidateSolution] = Field(default_factory=list)
    critiques: list[CritiqueReport] = Field(default_factory=list)
    convergence: ConvergenceStatus | None = None


class SessionInput(BaseModel):
    problem_description: str = Field(min_length=10)
    max_cycles: int = Field(default=5, ge=1, le=10)
    allow_external_research: bool = True
    context: dict[str, Any] = Field(default_factory=dict)

    @field_validator('problem_description')
    @classmethod
    def strip_problem(cls, value: str) -> str:
        return value.strip()


class SessionState(BaseModel):
    session_id: str
    input_data: SessionInput
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    problem: ProblemDefinition | None = None
    research: ResearchFindings | None = None
    candidates: list[CandidateSolution] = Field(default_factory=list)
    critiques: list[CritiqueReport] = Field(default_factory=list)
    cycles: list[CycleResult] = Field(default_factory=list)
    final_synthesis: str = ''

    def is_complete(self, max_cycles: int) -> bool:
        if len(self.cycles) >= max_cycles:
            return True
        if self.cycles and self.cycles[-1].convergence and self.cycles[-1].convergence.converged:
            return True
        return False


class SessionOutput(BaseModel):
    session_id: str
    problem: ProblemDefinition
    research: ResearchFindings | None = None
    candidates: list[CandidateSolution] = Field(default_factory=list)
    critiques: list[CritiqueReport] = Field(default_factory=list)
    top_candidate: CandidateSolution | None = None
    convergence: ConvergenceStatus
    final_synthesis: str
    cycles_completed: int
    cycles: list[CycleResult] = Field(default_factory=list)
