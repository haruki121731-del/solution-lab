"""
Architect Agent

Responsibility: Generate competing solution candidates.
Key outputs: 3+ diverse candidates with pros/cons, risks, and implementation paths.
"""

from typing import Any

from pydantic import BaseModel

from agents.base import AgentBase, AgentResult
from schemas.models import (
    Assumption,
    CandidateSolution,
    Evidence,
    EvidenceType,
    ProblemDefinition,
    ResearchFindings,
    Risk,
)


class ArchitectInput(BaseModel):
    """Input for solution architecture."""

    problem: ProblemDefinition
    research: ResearchFindings | None = None
    existing_candidates: list[CandidateSolution] = []
    min_candidates: int = 3


class Architect(AgentBase[ArchitectInput, list[CandidateSolution]]):
    """
    Generates diverse, competing solution candidates.

    Key principles:
    - Generate genuinely different approaches (not variations)
    - Force explicit pros/cons for each
    - Identify key risks upfront
    - Ensure feasibility within constraints
    - Never generate just one candidate
    """

    name = "architect"

    async def execute(
        self,
        input_data: ArchitectInput,
        **kwargs: Any
    ) -> AgentResult[list[CandidateSolution]]:
        """
        Generate solution candidates for the problem.

        MVP: Rule-based candidate generation.
        TODO: LLM-based generation with constraint checking.
        """
        problem = input_data.problem
        research = input_data.research
        min_candidates = input_data.min_candidates

        try:
            candidates = self._generate_candidates(
                problem, research, min_candidates
            )

            # Score candidates based on evidence alignment
            scored_candidates = self._score_candidates(candidates, research)

            evidence = [
                Evidence(
                    claim=f"Generated {len(candidates)} solution candidates",
                    source="architect_agent",
                    evidence_type=EvidenceType.CALCULATION,
                    confidence=0.7,
                    data={"min_requested": min_candidates, "generated": len(candidates)}
                )
            ]

            return AgentResult.ok(data=scored_candidates, evidence=evidence)

        except Exception as e:
            return AgentResult.fail(f"Candidate generation failed: {e}")

    def _generate_candidates(
        self,
        problem: ProblemDefinition,
        research: ResearchFindings | None,
        min_candidates: int
    ) -> list[CandidateSolution]:
        """
        Generate diverse solution candidates.

        MVP: Template-based generation with problem-specific customization.
        """
        candidates: list[CandidateSolution] = []
        problem_text = problem.root_problem.lower()

        # Generate approach archetypes based on problem type
        approaches = self._determine_approaches(problem, problem_text)

        for idx, (approach_type, approach_desc) in enumerate(approaches[:min_candidates], 1):
            candidate = self._build_candidate(
                problem=problem,
                research=research,
                approach_type=approach_type,
                approach_desc=approach_desc,
                index=idx
            )
            candidates.append(candidate)

        return candidates

    def _determine_approaches(
        self,
        problem: ProblemDefinition,
        problem_text: str
    ) -> list[tuple[str, str]]:
        """
        Determine appropriate solution approaches for the problem.

        Returns list of (approach_type, description) tuples.
        """
        approaches: list[tuple[str, str]] = []

        # Pattern-match problem types to approach categories
        is_technical = any(w in problem_text for w in [
            "system", "performance", "database", "api", "code",
            "architecture", "integration", "bug", "error"
        ])

        is_process = any(w in problem_text for w in [
            "workflow", "process", "approval", "manual", "bottleneck",
            "slow", "inefficient", "team", "communication"
        ])

        is_product = any(w in problem_text for w in [
            "user", "customer", "feature", "experience", "engagement",
            "retention", "onboarding", "conversion"
        ])

        if is_technical:
            approaches.extend([
                ("technical", "Optimize existing system architecture"),
                ("technical", "Introduce new technology/component"),
                ("hybrid", "Gradual refactoring with feature flags"),
            ])

        if is_process:
            approaches.extend([
                ("process", "Automate manual workflow"),
                ("process", "Redesign process with fewer steps"),
                ("hybrid", "Human-in-the-loop automation"),
            ])

        if is_product:
            approaches.extend([
                ("product", "Incremental UX improvements"),
                ("product", "Major feature redesign"),
                ("hybrid", "A/B test multiple approaches"),
            ])

        # Ensure we have at least 3 diverse approaches
        if len(approaches) < 3:
            approaches.extend([
                ("process", "Streamline and simplify current approach"),
                ("technical", "Build custom solution from scratch"),
                ("hybrid", "Buy/modify existing solution"),
            ])

        return approaches[:5]  # Cap at 5 approaches

    def _build_candidate(
        self,
        problem: ProblemDefinition,
        research: ResearchFindings | None,
        approach_type: str,
        approach_desc: str,
        index: int
    ) -> CandidateSolution:
        """Build a complete candidate solution."""

        # Generate specific details based on approach
        name = self._generate_name(approach_desc, index)
        description = self._generate_description(problem, approach_desc, approach_type)
        pros = self._generate_pros(problem, approach_type)
        cons = self._generate_cons(problem, approach_type)
        steps = self._generate_implementation_steps(approach_type)
        effort = self._estimate_effort(problem, approach_type)
        risks = self._identify_risks(problem, approach_type)
        assumptions = self._derive_assumptions(problem, approach_type)

        return CandidateSolution(
            id=f"candidate_{index}",
            name=name,
            description=description,
            approach_type=approach_type,
            pros=pros,
            cons=cons,
            implementation_steps=steps,
            estimated_effort=effort,
            key_risks=risks,
            assumptions=assumptions,
            evidence=research.findings if research else []
        )

    def _generate_name(self, approach_desc: str, index: int) -> str:
        """Generate a short, descriptive name."""
        return f"Option {index}: {approach_desc[:40]}"

    def _generate_description(
        self,
        problem: ProblemDefinition,
        approach_desc: str,
        approach_type: str
    ) -> str:
        """Generate detailed description of the approach."""
        return (
            f"{approach_desc} to address: {problem.root_problem} "
            f"This {approach_type} approach focuses on meeting success criteria: "
            f"{', '.join(problem.success_criteria[:2])}."
        )

    def _generate_pros(self, problem: ProblemDefinition, approach_type: str) -> list[str]:
        """Generate pros based on approach type."""
        pros_map: dict[str, list[str]] = {
            "technical": [
                "Addresses root cause directly",
                "Scalable long-term solution",
                "Measurable impact on metrics"
            ],
            "process": [
                "Quick to implement",
                "Low technical risk",
                "Easily reversible if needed"
            ],
            "product": [
                "User-centric approach",
                "Validates assumptions quickly",
                "Can iterate based on feedback"
            ],
            "hybrid": [
                "Balances speed and quality",
                "Reduces risk through validation",
                "Flexible adaptation path"
            ]
        }
        return pros_map.get(approach_type, [
            "Addresses the problem",
            "Feasible within constraints"
        ])

    def _generate_cons(self, problem: ProblemDefinition, approach_type: str) -> list[str]:
        """Generate cons based on approach type."""
        cons_map: dict[str, list[str]] = {
            "technical": [
                "Higher implementation complexity",
                "May require specialized expertise",
                "Longer time to value"
            ],
            "process": [
                "May not address systemic issues",
                "Requires organizational change",
                "Harder to measure direct impact"
            ],
            "product": [
                "User adoption uncertainty",
                "May require significant design work",
                "Success depends on user research accuracy"
            ],
            "hybrid": [
                "More complex to coordinate",
                "Multiple failure points",
                "Requires careful sequencing"
            ]
        }
        return cons_map.get(approach_type, [
            "Implementation effort required",
            "Uncertain outcome"
        ])

    def _generate_implementation_steps(self, approach_type: str) -> list[str]:
        """Generate typical implementation steps."""
        base_steps = [
            "Define detailed requirements and scope",
            "Create implementation plan with milestones",
            "Execute implementation in phases",
            "Validate against success criteria"
        ]

        if approach_type == "technical":
            return [
                "Technical design and architecture review",
                "Proof of concept implementation",
                "Full implementation with testing",
                "Performance validation and monitoring setup"
            ] + base_steps[2:]

        if approach_type == "process":
            return [
                "Map current process in detail",
                "Design new process with stakeholders",
                "Pilot with small team",
                "Roll out with training and documentation"
            ]

        return base_steps

    def _estimate_effort(
        self,
        problem: ProblemDefinition,
        approach_type: str
    ) -> str:
        """Estimate implementation effort."""
        effort_map: dict[str, str] = {
            "technical": "Medium-High (2-4 weeks)",
            "process": "Low-Medium (1-2 weeks)",
            "product": "Medium (2-3 weeks)",
            "hybrid": "Medium-High (3-5 weeks)"
        }
        return effort_map.get(approach_type, "Medium (2-3 weeks)")

    def _identify_risks(
        self,
        problem: ProblemDefinition,
        approach_type: str
    ) -> list[Risk]:
        """Identify key risks for the approach."""
        common_risks = [
            Risk(
                description="Implementation takes longer than estimated",
                likelihood="medium",
                impact="medium",
                mitigation="Build in buffer time; identify quick wins"
            ),
            Risk(
                description="Does not achieve expected outcomes",
                likelihood="medium",
                impact="high",
                mitigation="Define clear success criteria upfront; validate early"
            )
        ]

        if approach_type == "technical":
            common_risks.append(Risk(
                description="Technical debt increases",
                likelihood="low",
                impact="medium",
                mitigation="Code reviews, documentation, testing"
            ))

        if approach_type == "process":
            common_risks.append(Risk(
                description="Team adoption resistance",
                likelihood="medium",
                impact="medium",
                mitigation="Involve team early; clear communication of benefits"
            ))

        return common_risks

    def _derive_assumptions(
        self,
        problem: ProblemDefinition,
        approach_type: str
    ) -> list[Assumption]:
        """Derive approach-specific assumptions."""
        return [
            Assumption(
                statement=f"{approach_type.title()} approach is appropriate for this problem",
                criticality="high",
                validation_needed=True
            ),
            Assumption(
                statement="Required resources will be available when needed",
                criticality="medium",
                validation_needed=False
            )
        ]

    def _score_candidates(
        self,
        candidates: list[CandidateSolution],
        research: ResearchFindings | None
    ) -> list[CandidateSolution]:
        """
        Score candidates based on alignment with evidence.

        MVP: Simple scoring. TODO: More sophisticated multi-factor scoring.
        """
        scored = []
        for candidate in candidates:
            # Base score
            score = 0.5

            # Adjust based on approach type diversity
            if candidate.approach_type == "hybrid":
                score += 0.05  # Slight preference for balanced approaches

            # Adjust based on evidence alignment
            if research and research.findings:
                # Would do actual evidence matching here
                score += 0.1

            # Cap at 0.9 for MVP (never claim high certainty without validation)
            candidate.score = min(0.9, score)
            scored.append(candidate)

        return scored
