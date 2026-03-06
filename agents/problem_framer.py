from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agents.base import AgentResult
from schemas.models import Assumption, Evidence, EvidenceType, ProblemDefinition


class ProblemFramerInput(BaseModel):
    raw_description: str
    context: dict[str, Any] = Field(default_factory=dict)


class ProblemFramer:
    async def execute(self, input_data: ProblemFramerInput) -> AgentResult[ProblemDefinition]:
        raw = input_data.raw_description.strip()
        root_problem = raw[0].upper() + raw[1:]

        constraints: list[str] = []
        for key, value in input_data.context.items():
            constraints.append(f'{key}={value}')

        success_criteria = [
            'Reduce the primary bottleneck with a measurable outcome.',
            'Keep implementation feasible for the current team and constraints.',
            'Preserve user trust while improving throughput or conversion.',
        ]

        assumptions = [
            Assumption(statement='The described bottleneck is real and worth solving first.', confidence=0.74),
            Assumption(statement='The team can instrument or observe the affected workflow.', confidence=0.70),
        ]

        evidence = [
            Evidence(
                title='User stated problem',
                summary=raw,
                source='session-input',
                evidence_type=EvidenceType.user_input,
                confidence=0.95,
            )
        ]

        problem = ProblemDefinition(
            raw_input=raw,
            root_problem=root_problem,
            success_criteria=success_criteria,
            constraints=constraints,
            assumptions=assumptions,
        )
        return AgentResult.ok(problem, evidence)
