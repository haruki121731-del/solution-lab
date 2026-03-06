"""
Researcher Agent

Responsibility: Gather external evidence to inform solution generation.
Key outputs: Structured findings with confidence scores, source attribution.
"""

from typing import Any

from pydantic import BaseModel

from agents.base import AgentBase, AgentResult
from schemas.models import Evidence, EvidenceType, ResearchFindings


class ResearcherInput(BaseModel):
    """Input for research phase."""

    query: str
    problem_context: str
    existing_evidence: list[Evidence] = []


class Researcher(AgentBase[ResearcherInput, ResearchFindings]):
    """
    Gathers external evidence to reduce uncertainty.

    Key principles:
    - Always attribute sources
    - Confidence-score all findings
    - Identify remaining gaps explicitly
    - Prefer quantitative over qualitative
    """

    name = "researcher"

    def __init__(self, firecrawl_client: Any | None = None):
        """
        Initialize researcher with optional Firecrawl client.

        Args:
            firecrawl_client: Client for external research (optional for MVP)
        """
        self.firecrawl = firecrawl_client

    async def execute(
        self,
        input_data: ResearcherInput,
        **kwargs: Any
    ) -> AgentResult[ResearchFindings]:
        """
        Execute research based on query and context.

        MVP: Returns structured placeholder with explicit gaps.
        TODO: Integrate Firecrawl for live research.
        """
        query = input_data.query
        context = input_data.problem_context

        try:
            findings = await self._conduct_research(query, context)
            return AgentResult.ok(
                data=findings,
                evidence=findings.findings
            )
        except Exception as e:
            # Research failure should not block - return empty with gaps noted
            return AgentResult.ok(
                data=ResearchFindings(
                    query=query,
                    sources=[],
                    findings=[],
                    gaps_remain=True,
                    suggested_followups=[
                        f"Research failed: {e}. Manual research recommended."
                    ]
                )
            )

    async def _conduct_research(
        self,
        query: str,
        context: str
    ) -> ResearchFindings:
        """
        Conduct research and return structured findings.

        MVP implementation returns placeholder findings.
        Production would use Firecrawl + LLM synthesis.
        """
        sources: list[str] = []
        findings: list[Evidence] = []

        # TODO: Implement actual Firecrawl integration
        # if self.firecrawl:
        #     search_results = await self.firecrawl.search(query)
        #     sources = [r.url for r in search_results]
        #     findings = self._synthesize_findings(search_results, context)

        # MVP: Return evidence-based placeholders with clear marking
        findings = self._generate_placeholder_findings(query, context)

        return ResearchFindings(
            query=query,
            sources=sources or ["placeholder: no external source"],
            findings=findings,
            gaps_remain=True,  # Always true until real research implemented
            suggested_followups=self._suggest_followups(query, findings)
        )

    def _generate_placeholder_findings(
        self,
        query: str,
        context: str
    ) -> list[Evidence]:
        """
        Generate placeholder findings marked as hypotheses.

        These are structured guesses to demonstrate the schema.
        All marked as hypotheses with low confidence.
        """
        query_lower = query.lower()

        findings: list[Evidence] = []

        # Pattern-match to provide semi-relevant placeholders
        if any(w in query_lower for w in ["performance", "slow", "speed"]):
            findings.append(Evidence(
                claim="Common performance bottlenecks include N+1 queries and missing indexes",
                source="researcher_agent_placeholder",
                evidence_type=EvidenceType.HYPOTHESIS,
                confidence=0.6,
                data={"basis": "common_patterns", "needs_verification": True}
            ))

        if any(w in query_lower for w in ["user", "ux", "experience"]):
            findings.append(Evidence(
                claim="User research typically reveals 3-5 critical pain points",
                source="researcher_agent_placeholder",
                evidence_type=EvidenceType.HYPOTHESIS,
                confidence=0.5,
                data={"basis": "industry_average", "needs_verification": True}
            ))

        if any(w in query_lower for w in ["cost", "price", "budget"]):
            findings.append(Evidence(
                claim="Solutions often have hidden operational costs not visible upfront",
                source="researcher_agent_placeholder",
                evidence_type=EvidenceType.HYPOTHESIS,
                confidence=0.7,
                data={"basis": "historical_pattern", "needs_verification": True}
            ))

        # Always add a generic finding
        findings.append(Evidence(
            claim=f"Domain research for '{query[:50]}...' is pending",
            source="researcher_agent_placeholder",
            evidence_type=EvidenceType.HYPOTHESIS,
            confidence=0.3,
            data={"basis": "no_research_yet", "needs_verification": True}
        ))

        return findings

    def _suggest_followups(
        self,
        query: str,
        findings: list[Evidence]
    ) -> list[str]:
        """Suggest follow-up research actions."""
        followups = [
            "Conduct competitor analysis for similar solutions",
            "Gather user interview data if user-facing problem",
            "Review technical documentation for implementation constraints",
        ]

        # Add specific followups based on query
        if "performance" in query.lower():
            followups.insert(0, "Profile current system to establish baseline metrics")

        return followups
