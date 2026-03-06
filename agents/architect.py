from __future__ import annotations

from pydantic import BaseModel, Field

from agents.base import AgentResult
from schemas.models import CandidateSolution, ProblemDefinition, ResearchFindings, Risk, RiskSeverity


class ArchitectInput(BaseModel):
    problem: ProblemDefinition
    research: ResearchFindings | None = None
    existing_candidates: list[CandidateSolution] = Field(default_factory=list)
    min_candidates: int = 3


class Architect:
    async def execute(self, input_data: ArchitectInput) -> AgentResult[list[CandidateSolution]]:
        base = input_data.problem.root_problem.lower()
        cues = ' '.join([base, input_data.problem.raw_input.lower()])

        candidates = [
            CandidateSolution(
                id='instrument-and-fix',
                name='Instrument bottleneck and remove friction',
                description='Add precise measurement around the failing step, then remove the largest friction point in the current flow.',
                approach_type='product',
                pros=['Grounded in measurement', 'Fastest path to a meaningful win'],
                cons=['Requires event instrumentation', 'May only solve the top layer first'],
                implementation_steps=[
                    'Define funnel events and failure taxonomy.',
                    'Measure where and why users abandon.',
                    'Remove the top friction point and rerun the experiment.',
                ],
                key_risks=[
                    Risk(
                        name='Partial diagnosis',
                        description='Telemetry may explain where abandonment happens but not the deeper motivation.',
                        severity=RiskSeverity.medium,
                        mitigation='Pair analytics with short interviews or session review.',
                    )
                ],
                evidence_refs=['User stated problem', 'Problem statement signal'],
                estimated_effort='small-to-medium',
                confidence=0.81,
            ),
            CandidateSolution(
                id='assisted-flow',
                name='Guided or assisted flow',
                description='Redesign the experience so the user gets clear guidance, fallback paths, and fewer opportunities to stall.',
                approach_type='ux',
                pros=['Reduces ambiguity', 'Improves trust and comprehension'],
                cons=['Needs UX design work', 'May not fix backend causes'],
                implementation_steps=[
                    'Map confusing or ambiguous states in the flow.',
                    'Add contextual guidance and fallback actions.',
                    'Test the new guided flow against the current baseline.',
                ],
                key_risks=[
                    Risk(
                        name='Cosmetic redesign',
                        description='A nicer flow can fail if the real bottleneck is operational or technical.',
                        severity=RiskSeverity.medium,
                        mitigation='Validate backend latency, deliverability, and error rates before shipping.',
                    )
                ],
                evidence_refs=['General product principle'],
                estimated_effort='medium',
                confidence=0.72,
            ),
            CandidateSolution(
                id='automation-or-defaults',
                name='Automate the fragile step or replace it with defaults',
                description='Where possible, remove the manual step entirely by automation, smart defaults, or background completion.',
                approach_type='system',
                pros=['Can create step-function improvement', 'Lower ongoing user effort'],
                cons=['Highest implementation complexity', 'Risk of hidden edge cases'],
                implementation_steps=[
                    'Identify the most fragile manual step.',
                    'Design a safe automation or default path.',
                    'Roll out behind a flag and monitor exceptions.',
                ],
                key_risks=[
                    Risk(
                        name='Automation errors',
                        description='Automatic actions can fail silently or produce trust-damaging mistakes.',
                        severity=RiskSeverity.high,
                        mitigation='Introduce guardrails, observability, and human fallback paths.',
                    )
                ],
                evidence_refs=['General product principle'],
                estimated_effort='medium-to-large',
                confidence=0.68,
            ),
        ]

        if 'api' in cues or 'latency' in cues or 'slow' in cues:
            candidates[0].name = 'Profile hot paths and optimize latency bottlenecks'
            candidates[0].description = 'Measure the slowest endpoints or queries, then remove the hottest performance bottleneck first.'
            candidates[0].implementation_steps = [
                'Profile request and query timings.',
                'Fix the slowest hot path.',
                'Load-test the new baseline and watch regressions.',
            ]

        return AgentResult.ok(candidates[: max(input_data.min_candidates, 3)])
