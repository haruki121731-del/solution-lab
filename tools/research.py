from __future__ import annotations

from typing import Protocol

from schemas.models import Evidence, EvidenceType


class ResearchClient(Protocol):
    async def search(self, query: str, *, problem_context: str) -> list[Evidence]: ...


class HeuristicResearchClient:
    async def search(self, query: str, *, problem_context: str) -> list[Evidence]:
        return [
            Evidence(
                title='Problem statement signal',
                summary=f'User problem indicates: {problem_context}',
                source='session-input',
                evidence_type=EvidenceType.user_input,
                confidence=0.88,
            ),
            Evidence(
                title='General product principle',
                summary='High-friction flows usually improve when the system removes manual steps, reduces ambiguity, and instruments the bottleneck.',
                source='heuristic-library',
                evidence_type=EvidenceType.heuristic,
                confidence=0.66,
            ),
        ]
