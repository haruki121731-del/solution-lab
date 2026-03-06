"""
Critic Agent

Responsibility: Aggressively critique solution candidates.
Key outputs: Dealbreakers, weaknesses, uncertainties raised, comparison matrix.
"""

from typing import Any

from pydantic import BaseModel

from agents.base import AgentBase, AgentResult
from schemas.models import (
    CandidateSolution,
    CritiqueReport,
    Evidence,
    EvidenceType,
    ProblemDefinition,
    Uncertainty,
)


class CriticInput(BaseModel):
    """Input for critique phase."""

    problem: ProblemDefinition
    candidates: list[CandidateSolution]


class Critic(AgentBase[CriticInput, list[CritiqueReport]]):
    """
    Aggressively critiques solution candidates to find flaws.

    Key principles:
    - No candidate is above scrutiny
    - Surface dealbreakers explicitly
    - Identify what we still don't know
    - Compare candidates against each other
    - Be constructive but ruthless
    """

    name = "critic"

    async def execute(
        self,
        input_data: CriticInput,
        **kwargs: Any
    ) -> AgentResult[list[CritiqueReport]]:
        """
        Critique all solution candidates.

        MVP: Rule-based critique generation.
        TODO: LLM-based deep critique with evidence checking.
        """
        problem = input_data.problem
        candidates = input_data.candidates

        if len(candidates) < 1:
            return AgentResult.fail("No candidates to critique")

        try:
            reports = self._critique_all(problem, candidates)
            evidence = self._generate_critique_evidence(reports)
            return AgentResult.ok(data=reports, evidence=evidence)

        except Exception as e:
            return AgentResult.fail(f"Critique failed: {e}")

    def _critique_all(
        self,
        problem: ProblemDefinition,
        candidates: list[CandidateSolution]
    ) -> list[CritiqueReport]:
        """Generate critique reports for all candidates."""
        reports: list[CritiqueReport] = []

        for candidate in candidates:
            report = self._critique_single(problem, candidate, candidates)
            reports.append(report)

        return reports

    def _critique_single(
        self,
        problem: ProblemDefinition,
        candidate: CandidateSolution,
        all_candidates: list[CandidateSolution]
    ) -> CritiqueReport:
        """
        Generate a critique report for a single candidate.

        Critique dimensions:
        1. Alignment with problem and success criteria
        2. Feasibility given constraints
        3. Risk exposure
        4. Evidence quality
        5. Comparison to alternatives
        """
        strengths = self._identify_strengths(candidate, problem)
        weaknesses = self._identify_weaknesses(candidate, problem)
        dealbreakers = self._identify_dealbreakers(candidate, problem)
        uncertainties = self._identify_uncertainties(candidate, problem)
        comparisons = self._compare_to_others(candidate, all_candidates)

        return CritiqueReport(
            candidate_id=candidate.id,
            strengths=strengths,
            weaknesses=weaknesses,
            dealbreakers=dealbreakers,
            uncertainties_raised=uncertainties,
            comparison_to_others=comparisons
        )

    def _identify_strengths(
        self,
        candidate: CandidateSolution,
        problem: ProblemDefinition
    ) -> list[str]:
        """Identify genuine strengths (for balance)."""
        strengths: list[str] = []

        # Strength: Clear alignment with success criteria
        if candidate.pros:
            strengths.append(f"Clear benefits: {candidate.pros[0]}")

        # Strength: Has implementation plan
        if len(candidate.implementation_steps) >= 3:
            strengths.append("Well-structured implementation approach")

        # Strength: Risks identified (self-awareness)
        if len(candidate.key_risks) >= 2:
            strengths.append("Risks have been proactively identified")

        # Strength: Evidence-backed
        if candidate.evidence:
            strengths.append(f"Backed by {len(candidate.evidence)} evidence items")

        return strengths[:3]  # Cap at 3

    def _identify_weaknesses(
        self,
        candidate: CandidateSolution,
        problem: ProblemDefinition
    ) -> list[str]:
        """Identify weaknesses through systematic questioning."""
        weaknesses: list[str] = []

        # Weakness: Vague description
        if len(candidate.description) < 100:
            weaknesses.append(
                "Description lacks detail - implementation approach is unclear"
            )

        # Weakness: Insufficient cons analysis
        if len(candidate.cons) < 2:
            weaknesses.append(
                "Limited acknowledgment of downsides - may be overoptimistic"
            )

        # Weakness: No mitigation for high risks
        high_risks = [r for r in candidate.key_risks if r.likelihood == "high"]
        unmitigated = [r for r in high_risks if not r.mitigation]
        if unmitigated:
            weaknesses.append(
                f"{len(unmitigated)} high-likelihood risk(s) lack mitigation plans"
            )

        # Weakness: Weak evidence
        hypothesis_evidence = [
            e for e in candidate.evidence
            if e.evidence_type == EvidenceType.HYPOTHESIS
        ]
        if len(hypothesis_evidence) > len(candidate.evidence) / 2:
            weaknesses.append(
                "Most evidence is unverified hypothesis - needs validation"
            )

        # Weakness: Missing effort estimate
        if not candidate.estimated_effort:
            weaknesses.append("No effort estimate makes planning impossible")

        # Weakness: Weak confidence score
        if candidate.score and candidate.score < 0.5:
            weaknesses.append(
                f"Low confidence score ({candidate.score:.2f}) suggests uncertainty"
            )

        return weaknesses

    def _identify_dealbreakers(
        self,
        candidate: CandidateSolution,
        problem: ProblemDefinition
    ) -> list[str]:
        """Identify potential dealbreakers that could kill this approach."""
        dealbreakers: list[str] = []

        # Dealbreaker: Conflicts with hard constraints
        for constraint in problem.constraints:
            if "budget" in constraint.lower() and "high" in candidate.estimated_effort.lower():
                dealbreakers.append(
                    f"May exceed budget constraints: {constraint}"
                )

        # Dealbreaker: Critical unvalidated assumption
        critical_unvalidated = [
            a for a in candidate.assumptions
            if a.criticality == "high" and a.validation_needed
        ]
        if critical_unvalidated:
            dealbreakers.append(
                f"{len(critical_unvalidated)} critical assumption(s) need validation"
            )

        # Dealbreaker: No clear path to success criteria
        if not problem.success_criteria:
            dealbreakers.append("No success criteria defined for the problem")

        # Dealbreaker: Blocker-level uncertainty
        blockers = [r for r in candidate.key_risks if r.impact == "high" and r.likelihood == "high"]
        if blockers:
            dealbreakers.append(
                f"{len(blockers)} critical risk(s) that could block success"
            )

        return dealbreakers

    def _identify_uncertainties(
        self,
        candidate: CandidateSolution,
        problem: ProblemDefinition
    ) -> list[Uncertainty]:
        """Identify uncertainties that need resolution."""
        uncertainties: list[Uncertainty] = []

        # Uncertainty: User impact (if applicable)
        if any(w in problem.root_problem.lower() for w in ["user", "customer"]):
            uncertainties.append(Uncertainty(
                question=f"How will users actually respond to {candidate.name}?",
                blocker=False,
                reduction_strategy="User testing or A/B experiment"
            ))

        # Uncertainty: Technical feasibility
        if candidate.approach_type == "technical":
            uncertainties.append(Uncertainty(
                question="Can the technical approach scale as needed?",
                blocker=True,
                reduction_strategy="Proof of concept with load testing"
            ))

        # Uncertainty: Effort accuracy
        uncertainties.append(Uncertainty(
            question=f"Is effort estimate ({candidate.estimated_effort}) accurate?",
            blocker=False,
            reduction_strategy="Break down into tasks and estimate each"
        ))

        # Uncertainty: Assumption validity
        if candidate.assumptions:
            uncertainties.append(Uncertainty(
                question=f"Are the {len(candidate.assumptions)} key assumptions valid?",
                blocker=True,
                reduction_strategy="Validate each assumption with data or expert input"
            ))

        return uncertainties

    def _compare_to_others(
        self,
        candidate: CandidateSolution,
        all_candidates: list[CandidateSolution]
    ) -> dict[str, str]:
        """Generate comparison statements to other candidates."""
        comparisons: dict[str, str] = {}

        others = [c for c in all_candidates if c.id != candidate.id]

        for other in others:
            # Compare on key dimensions
            if candidate.estimated_effort and other.estimated_effort:
                if "low" in candidate.estimated_effort.lower():
                    comparisons[other.id] = (
                        f"Faster to implement than {other.name}"
                    )
                elif "high" in other.estimated_effort.lower():
                    comparisons[other.id] = (
                        f"More conservative than {other.name}"
                    )
                else:
                    comparisons[other.id] = (
                        f"Comparable effort to {other.name}"
                    )
            else:
                comparisons[other.id] = f"Alternative to consider: {other.name}"

        return comparisons

    def _generate_critique_evidence(
        self,
        reports: list[CritiqueReport]
    ) -> list[Evidence]:
        """Generate evidence items from critique process."""
        total_weaknesses = sum(len(r.weaknesses) for r in reports)
        total_dealbreakers = sum(len(r.dealbreakers) for r in reports)

        return [
            Evidence(
                claim=f"Critique identified {total_weaknesses} weaknesses across {len(reports)} candidates",
                source="critic_agent",
                evidence_type=EvidenceType.ANALYSIS,
                confidence=0.8,
                data={
                    "candidates_critiqued": len(reports),
                    "weaknesses_found": total_weaknesses,
                    "dealbreakers_found": total_dealbreakers
                }
            )
        ]
