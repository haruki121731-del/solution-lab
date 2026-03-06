from __future__ import annotations

from pydantic import BaseModel, Field

from agents.base import AgentResult
from schemas.models import (
    CandidateSolution,
    ConvergenceStatus,
    CritiqueReport,
    NextAction,
    ProblemDefinition,
    ResearchFindings,
    Uncertainty,
)


class JudgeInput(BaseModel):
    problem: ProblemDefinition
    cycle_number: int
    max_cycles: int
    research: ResearchFindings | None = None
    candidates: list[CandidateSolution] = Field(default_factory=list)
    critiques: list[CritiqueReport] = Field(default_factory=list)
    previous_actions: list[NextAction] = Field(default_factory=list)


class JudgeOutput(BaseModel):
    convergence: ConvergenceStatus
    next_action: NextAction
    next_action_reasoning: str
    uncertainties_to_resolve: list[Uncertainty] = Field(default_factory=list)


class Judge:
    async def execute(self, input_data: JudgeInput) -> AgentResult[JudgeOutput]:
        enough_candidates = len(input_data.candidates) >= 3
        has_research = input_data.research is not None
        has_critiques = len(input_data.critiques) >= len(input_data.candidates) and bool(input_data.candidates)
        avg_score = sum(c.score for c in input_data.critiques) / len(input_data.critiques) if input_data.critiques else 0.0

        if enough_candidates and has_critiques and (has_research or input_data.cycle_number >= 2):
            converged = avg_score >= 0.45 or input_data.cycle_number >= input_data.max_cycles
            convergence = ConvergenceStatus(
                converged=converged,
                confidence=min(0.92, 0.45 + avg_score / 2),
                reason='The system has compared multiple candidates, surfaced risks, and identified a leading option.' if converged else 'More evidence is needed before final synthesis.',
            )
            next_action = NextAction.converge if converged else NextAction.research
            reasoning = 'Enough structure exists to synthesize a leading recommendation.' if converged else 'Research should reduce the remaining uncertainty before convergence.'
        elif not has_research:
            convergence = ConvergenceStatus(converged=False, confidence=0.25, reason='No research pass has been completed yet.')
            next_action = NextAction.research
            reasoning = 'Collecting evidence is the highest-leverage next move.'
        elif not enough_candidates:
            convergence = ConvergenceStatus(converged=False, confidence=0.32, reason='Too few competing solution paths exist.')
            next_action = NextAction.design
            reasoning = 'Generate additional alternatives before choosing.'
        else:
            convergence = ConvergenceStatus(converged=False, confidence=0.38, reason='Candidates need adversarial review before convergence.')
            next_action = NextAction.critique
            reasoning = 'Critique the options harder before final selection.'

        uncertainties = [
            Uncertainty(
                question='Which metric will determine whether the top candidate truly improved the problem?',
                impact='Without this, convergence is theatre wearing a lab coat.',
                suggested_resolution='Define a primary metric and minimum detectable improvement before implementation.',
            )
        ]
        return AgentResult.ok(
            JudgeOutput(
                convergence=convergence,
                next_action=next_action,
                next_action_reasoning=reasoning,
                uncertainties_to_resolve=uncertainties,
            )
        )
