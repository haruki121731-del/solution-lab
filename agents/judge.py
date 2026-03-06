"""
Judge Agent

Responsibility: Evaluate progress and decide next action.
Key outputs: Convergence status, next action recommendation with reasoning.
"""

from typing import Any

from pydantic import BaseModel

from agents.base import AgentBase, AgentResult
from schemas.models import (
    CandidateSolution,
    ConvergenceStatus,
    CritiqueReport,
    CycleResult,
    Evidence,
    EvidenceType,
    NextAction,
    ProblemDefinition,
    ResearchFindings,
    Uncertainty,
)


class JudgeInput(BaseModel):
    """Input for judge evaluation."""

    problem: ProblemDefinition
    cycle_number: int
    max_cycles: int
    research: ResearchFindings | None = None
    candidates: list[CandidateSolution] = []
    critiques: list[CritiqueReport] = []
    previous_actions: list[NextAction] = []


class JudgeOutput(BaseModel):
    """Output from judge evaluation."""

    convergence: ConvergenceStatus
    next_action: NextAction
    next_action_reasoning: str
    uncertainties_to_resolve: list[Uncertainty] = []


class Judge(AgentBase[JudgeInput, JudgeOutput]):
    """
    Evaluates session state and decides next action.

    Key principles:
    - Never claim convergence without evidence
    - Force explicit uncertainty tracking
    - Prefer actions that reduce uncertainty
    - Respect cycle limits
    - Surface blockers early
    """

    name = "judge"

    # Convergence criteria thresholds
    MIN_CANDIDATES = 2
    IDEAL_CANDIDATES = 3
    MIN_CONFIDENCE = 0.6

    async def execute(
        self,
        input_data: JudgeInput,
        **kwargs: Any
    ) -> AgentResult[JudgeOutput]:
        """
        Evaluate session and determine next action.

        This is the core orchestration decision point.
        """
        try:
            convergence = self._assess_convergence(input_data)
            next_action, reasoning = self._determine_next_action(
                input_data, convergence
            )
            uncertainties = self._identify_critical_uncertainties(input_data)

            output = JudgeOutput(
                convergence=convergence,
                next_action=next_action,
                next_action_reasoning=reasoning,
                uncertainties_to_resolve=uncertainties
            )

            evidence = [
                Evidence(
                    claim=f"Judge recommends {next_action.value}",
                    source="judge_agent",
                    evidence_type=EvidenceType.ANALYSIS,
                    confidence=convergence.confidence,
                    data={
                        "converged": convergence.converged,
                        "cycle": input_data.cycle_number,
                        "max_cycles": input_data.max_cycles
                    }
                )
            ]

            return AgentResult.ok(data=output, evidence=evidence)

        except Exception as e:
            return AgentResult.fail(f"Judge evaluation failed: {e}")

    def _assess_convergence(self, input_data: JudgeInput) -> ConvergenceStatus:
        """
        Assess whether problem is sufficiently solved to converge.

        Criteria (ALL must be met for convergence):
        1. Root problem exists and is well-defined
        2. At least MIN_CANDIDATES candidates compared
        3. Key uncertainties reduced (no blocker uncertainties)
        4. Major risks surfaced
        5. Implementation path is concrete enough
        """
        criteria_met: dict[str, bool] = {}

        # Criterion 1: Root problem exists
        criteria_met["root_problem_defined"] = bool(
            input_data.problem and
            input_data.problem.root_problem and
            len(input_data.problem.root_problem) > 20
        )

        # Criterion 2: Sufficient candidates compared
        candidate_count = len(input_data.candidates)
        criteria_met["sufficient_candidates"] = candidate_count >= self.MIN_CANDIDATES
        criteria_met["ideal_candidates"] = candidate_count >= self.IDEAL_CANDIDATES

        # Criterion 3: Key uncertainties reduced
        blocker_uncertainties = self._count_blocker_uncertainties(input_data)
        criteria_met["uncertainties_reduced"] = blocker_uncertainties == 0

        # Criterion 4: Major risks surfaced
        criteria_met["risks_surfaced"] = self._has_risk_analysis(input_data)

        # Criterion 5: Implementation path concrete
        criteria_met["implementation_concrete"] = self._has_concrete_implementation(
            input_data
        )

        # Calculate confidence based on criteria met
        met_count = sum(criteria_met.values())
        total_criteria = len(criteria_met)
        confidence = met_count / total_criteria

        # Convergence requires ALL criteria except ideal_candidates
        required_criteria = [k for k in criteria_met if k != "ideal_candidates"]
        converged = all(criteria_met[k] for k in required_criteria)

        reason = self._generate_convergence_reason(
            criteria_met, converged, confidence
        )

        return ConvergenceStatus(
            converged=converged,
            confidence=confidence,
            reason=reason,
            criteria_met=criteria_met
        )

    def _determine_next_action(
        self,
        input_data: JudgeInput,
        convergence: ConvergenceStatus
    ) -> tuple[NextAction, str]:
        """
        Determine the next action based on current state.

        Decision tree:
        1. If converged -> CONVERGE
        2. If max cycles reached -> CONVERGE (forced)
        3. If no research and allowed -> RESEARCH
        4. If insufficient candidates -> GENERATE_CANDIDATES
        5. If no critiques -> CRITIQUE
        6. If blocker uncertainties -> REFINE_PROBLEM
        7. Otherwise -> CONVERGE
        """
        cycle = input_data.cycle_number
        max_cycles = input_data.max_cycles

        # Check for forced convergence
        if cycle >= max_cycles:
            return (
                NextAction.CONVERGE,
                f"Max cycles ({max_cycles}) reached. Forcing convergence."
            )

        # If converged, stop
        if convergence.converged:
            return (
                NextAction.CONVERGE,
                "All convergence criteria met. Ready to synthesize solution."
            )

        # Need more candidates
        if len(input_data.candidates) < self.MIN_CANDIDATES:
            return (
                NextAction.GENERATE_CANDIDATES,
                f"Only {len(input_data.candidates)} candidate(s), need at least {self.MIN_CANDIDATES}"
            )

        # Need critiques
        if len(input_data.critiques) < len(input_data.candidates):
            return (
                NextAction.CRITIQUE,
                f"Need critiques for all {len(input_data.candidates)} candidates"
            )

        # Check for blocker uncertainties
        blocker_count = self._count_blocker_uncertainties(input_data)
        if blocker_count > 0:
            return (
                NextAction.REFINE_PROBLEM,
                f"{blocker_count} blocker uncertainty(ies) need resolution"
            )

        # Check if research would help
        if not input_data.research and cycle == 2:
            return (
                NextAction.RESEARCH,
                "No external research yet; gathering evidence would reduce uncertainty"
            )

        # Default: try to converge
        return (
            NextAction.CONVERGE,
            "Attempting convergence with current state"
        )

    def _identify_critical_uncertainties(
        self,
        input_data: JudgeInput
    ) -> list[Uncertainty]:
        """Extract critical uncertainties that need resolution."""
        uncertainties: list[Uncertainty] = []

        # Gather from critiques
        for critique in input_data.critiques:
            for unc in critique.uncertainties_raised:
                if unc.blocker or len(uncertainties) < 3:
                    uncertainties.append(unc)

        # Limit to most critical
        return uncertainties[:5]

    def _count_blocker_uncertainties(self, input_data: JudgeInput) -> int:
        """Count uncertainties that block progress."""
        count = 0
        for critique in input_data.critiques:
            for unc in critique.uncertainties_raised:
                if unc.blocker:
                    count += 1
        return count

    def _has_risk_analysis(self, input_data: JudgeInput) -> bool:
        """Check if major risks have been analyzed."""
        if not input_data.candidates:
            return False

        for candidate in input_data.candidates:
            if not candidate.key_risks:
                return False
        return True

    def _has_concrete_implementation(self, input_data: JudgeInput) -> bool:
        """Check if implementation paths are concrete enough."""
        if not input_data.candidates:
            return False

        for candidate in input_data.candidates:
            if not candidate.implementation_steps:
                return False
            if len(candidate.implementation_steps) < 3:
                return False
        return True

    def _generate_convergence_reason(
        self,
        criteria_met: dict[str, bool],
        converged: bool,
        confidence: float
    ) -> str:
        """Generate human-readable convergence reason."""
        if converged:
            return (
                f"Convergence achieved with {confidence:.0%} confidence. "
                f"All required criteria met: "
                f"{sum(criteria_met.values())}/{len(criteria_met)}."
            )

        # Identify what's missing
        missing = [k for k, v in criteria_met.items() if not v]
        return (
            f"Not converged ({confidence:.0%} confidence). "
            f"Missing: {', '.join(missing)}"
        )
