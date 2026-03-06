from __future__ import annotations

from pydantic import BaseModel

from agents.base import AgentResult
from schemas.models import CandidateSolution, CritiqueReport, ProblemDefinition, Uncertainty


class CriticInput(BaseModel):
    problem: ProblemDefinition
    candidates: list[CandidateSolution]


class Critic:
    async def execute(self, input_data: CriticInput) -> AgentResult[list[CritiqueReport]]:
        reports: list[CritiqueReport] = []
        for candidate in input_data.candidates:
            score = max(0.35, min(0.9, candidate.confidence - 0.08 * len(candidate.key_risks)))
            reports.append(
                CritiqueReport(
                    candidate_id=candidate.id,
                    strengths=candidate.pros[:2],
                    weaknesses=[
                        *candidate.cons[:2],
                        'Needs explicit success metric and rollout guardrail.' if 'metric' not in candidate.description.lower() else 'Still requires disciplined rollout.',
                    ],
                    open_questions=[
                        Uncertainty(
                            question='What would falsify this approach within two weeks?',
                            impact='Prevents slow-motion commitment to a weak idea.',
                            suggested_resolution='Define a short experiment with success and failure thresholds.',
                        )
                    ],
                    score=score,
                )
            )
        return AgentResult.ok(reports)
