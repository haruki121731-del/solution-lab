from __future__ import annotations

from pydantic import BaseModel, Field

from agents.base import AgentResult
from schemas.models import Evidence, ResearchFindings
from tools.research import HeuristicResearchClient, ResearchClient


class ResearcherInput(BaseModel):
    query: str
    problem_context: str
    existing_evidence: list[Evidence] = Field(default_factory=list)


class Researcher:
    def __init__(self, client: ResearchClient | None = None) -> None:
        self.client = client or HeuristicResearchClient()

    async def execute(self, input_data: ResearcherInput) -> AgentResult[ResearchFindings]:
        evidence = await self.client.search(input_data.query, problem_context=input_data.problem_context)
        merged = [*input_data.existing_evidence, *evidence]
        findings = ResearchFindings(
            findings=merged,
            research_summary='Collected direct problem evidence and generic improvement heuristics to reduce uncertainty before proposing solutions.',
            gaps_remain=True,
            suggested_followups=[
                'Instrument the bottleneck with event-level telemetry.',
                'Interview 3-5 affected users or operators.',
            ],
        )
        return AgentResult.ok(findings, evidence)
