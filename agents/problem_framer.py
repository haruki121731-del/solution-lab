"""
Problem Framer Agent

Responsibility: Transform raw user input into a structured, well-defined problem.
Key outputs: Root problem, success criteria, constraints, explicit assumptions.
"""

from typing import Any

from pydantic import BaseModel

from agents.base import AgentBase, AgentResult
from schemas.models import (
    Assumption,
    Evidence,
    EvidenceType,
    ProblemDefinition,
)


class ProblemFramerInput(BaseModel):
    """Input for problem framing."""

    raw_description: str
    context: dict[str, Any] = {}

    class Config:
        arbitrary_types_allowed = True


class ProblemFramer(AgentBase[ProblemFramerInput, ProblemDefinition]):
    """
    Frames raw problem descriptions into structured problem definitions.

    Key principles:
    - Distills root cause from symptoms
    - Forces explicit success criteria
    - Surfaces hidden assumptions
    - Never accepts vague problem statements
    """

    name = "problem_framer"

    async def execute(
        self,
        input_data: ProblemFramerInput,
        **kwargs: Any
    ) -> AgentResult[ProblemDefinition]:
        """
        Frame the problem from raw input.

        For the MVP, this uses rule-based extraction.
        TODO: Integrate LLM for sophisticated framing.
        """
        raw = input_data.raw_description.strip()
        context = input_data.context

        # TODO: Replace with LLM-based extraction
        # For MVP: structured extraction with validation
        try:
            problem_def = self._frame_problem(raw, context)
            return AgentResult.ok(
                data=problem_def,
                evidence=[
                    self._create_evidence(
                        claim=f"Root problem identified: {problem_def.root_problem}",
                        evidence_type=EvidenceType.USER_INPUT,
                        confidence=0.8,
                    )
                ]
            )
        except Exception as e:
            return AgentResult.fail(f"Problem framing failed: {e}")

    def _frame_problem(
        self,
        raw: str,
        context: dict[str, Any]
    ) -> ProblemDefinition:
        """
        Extract structured problem definition from raw input.

        MVP implementation uses heuristic extraction.
        Production would use structured LLM prompting.
        """
        # Heuristic: First sentence often contains the core problem
        sentences = [s.strip() for s in raw.split(".") if s.strip()]
        root_problem = sentences[0] if sentences else raw

        # Extract explicit constraints from context
        constraints: list[str] = context.get("constraints", [])
        stakeholders: list[str] = context.get("stakeholders", [])

        # Generate success criteria from problem nature
        success_criteria = self._derive_success_criteria(root_problem, context)

        # Surface assumptions that need validation
        assumptions = self._surface_assumptions(raw, context)

        return ProblemDefinition(
            raw_input=raw,
            root_problem=self._refine_root_problem(root_problem),
            success_criteria=success_criteria,
            constraints=constraints,
            stakeholders=stakeholders,
            assumptions=assumptions,
            context={
                "framing_method": "heuristic_mvp",
                "source_length": len(raw),
                "context_keys": list(context.keys()),
            }
        )

    def _refine_root_problem(self, raw_root: str) -> str:
        """Clean and refine the root problem statement."""
        # Remove filler words, focus on action/object
        refined = raw_root.strip()

        # Ensure problem statement ends with question or challenge form
        if not any(refined.endswith(end) for end in ["?", ".", "!"]):
            refined += "."

        # TODO: More sophisticated refinement via LLM
        return refined

    def _derive_success_criteria(
        self,
        root_problem: str,
        context: dict[str, Any]
    ) -> list[str]:
        """Derive measurable success criteria from problem."""
        criteria: list[str] = []

        # Always include a feasibility criterion
        criteria.append("Solution is implementable within given constraints")

        # Add problem-specific criteria
        problem_lower = root_problem.lower()

        if any(word in problem_lower for word in ["slow", "performance", "speed", "latency"]):
            criteria.append("Performance metric improves measurably (target: 2x improvement)")

        if any(word in problem_lower for word in ["user", "customer", "experience", "ux"]):
            criteria.append("User satisfaction metric improves or remains neutral")

        if any(word in problem_lower for word in ["cost", "expensive", "budget", "price"]):
            criteria.append("Cost impact is quantified and acceptable")

        # Allow override from context
        if "success_criteria" in context:
            criteria.extend(context["success_criteria"])

        return list(dict.fromkeys(criteria))  # Deduplicate while preserving order

    def _surface_assumptions(
        self,
        raw: str,
        context: dict[str, Any]
    ) -> list[Assumption]:
        """Surface implicit assumptions that may be wrong."""
        assumptions: list[Assumption] = []

        # Common assumptions to check
        default_assumptions = [
            (
                "The problem as stated is the real problem (not a symptom)",
                "high",
                True
            ),
            (
                "Sufficient resources exist to implement a solution",
                "medium",
                False
            ),
            (
                "Stakeholders agree on problem definition",
                "high",
                True
            ),
        ]

        for stmt, crit, needs_val in default_assumptions:
            assumptions.append(Assumption(
                statement=stmt,
                criticality=crit,  # type: ignore
                validation_needed=needs_val
            ))

        # Add context-specific assumptions
        if context.get("budget_limit"):
            assumptions.append(Assumption(
                statement=f"Budget limit of {context['budget_limit']} is accurate and fixed",
                criticality="high",
                validation_needed=True
            ))

        return assumptions


# Reconcile imports
ProblemFramerInput.__module__ = "agents.problem_framer"
