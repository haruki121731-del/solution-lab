"""
Session Runner - Core orchestration logic.

Manages the solution loop lifecycle:
1. Initialize session state
2. Run cycles (problem -> research -> candidates -> critique -> judge)
3. Track progress and artifacts
4. Produce final synthesis
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from agents.architect import Architect, ArchitectInput
from agents.critic import Critic, CriticInput
from agents.judge import Judge, JudgeInput
from agents.problem_framer import ProblemFramer, ProblemFramerInput
from agents.researcher import Researcher, ResearcherInput
from config import settings
from schemas.models import (
    CandidateSolution,
    ConvergenceStatus,
    CritiqueReport,
    CycleResult,
    NextAction,
    ProblemDefinition,
    ResearchFindings,
    SessionInput,
    SessionOutput,
    SessionState,
)


class SessionRunner:
    """
    Orchestrates the multi-agent solution cycle.

    Design principles:
    - Explicit state management
    - Clear phase transitions
    - Artifact preservation
    - Graceful degradation
    """

    def __init__(
        self,
        framer: ProblemFramer | None = None,
        researcher: Researcher | None = None,
        architect: Architect | None = None,
        critic: Critic | None = None,
        judge: Judge | None = None
    ):
        """Initialize with injectable agents for testability."""
        self.framer = framer or ProblemFramer()
        self.researcher = researcher or Researcher()
        self.architect = architect or Architect()
        self.critic = critic or Critic()
        self.judge = judge or Judge()

    async def run(self, input_data: SessionInput) -> SessionOutput:
        """
        Run a complete solution session.

        Args:
            input_data: Session parameters including problem description

        Returns:
            SessionOutput with final synthesis and all artifacts
        """
        # Initialize session
        session_id = str(uuid.uuid4())[:8]
        state = SessionState(
            session_id=session_id,
            input_data=input_data
        )

        # Run cycles until complete
        while not state.is_complete(input_data.max_cycles):
            cycle_result = await self._run_cycle(state)
            state.cycles.append(cycle_result)
            state.updated_at = datetime.now(timezone.utc)

        # Generate final output
        return self._synthesize_output(state)

    async def _run_cycle(self, state: SessionState) -> CycleResult:
        """
        Execute a single cycle of the solution loop.

        Phase determination:
        - Cycle 1: Always frame problem
        - Cycle 2+: Based on judge's recommendation
        """
        cycle_num = state.current_cycle
        input_data = state.input_data

        # Phase 1: Problem Framing (always cycle 1)
        if cycle_num == 1:
            return await self._execute_problem_framing(state)

        # Determine what to do based on current state
        judge_input = self._build_judge_input(state)
        judge_result = await self.judge.execute(judge_input)

        if not judge_result.success or not judge_result.data:
            # Judge failure - attempt graceful recovery
            return self._handle_judge_failure(cycle_num)

        next_action = judge_result.data.next_action

        # Execute based on judge recommendation
        if next_action == NextAction.RESEARCH:
            return await self._execute_research(state)

        if next_action == NextAction.GENERATE_CANDIDATES:
            return await self._execute_candidate_generation(state)

        if next_action == NextAction.CRITIQUE:
            return await self._execute_critique(state)

        if next_action == NextAction.REFINE_PROBLEM:
            return await self._execute_problem_refinement(state)

        # Default: Converge
        return await self._execute_convergence(state, judge_result.data.convergence)

    async def _execute_problem_framing(self, state: SessionState) -> CycleResult:
        """Execute the problem framing phase."""
        framer_input = ProblemFramerInput(
            raw_description=state.input_data.problem_description,
            context=state.input_data.context
        )

        result = await self.framer.execute(framer_input)

        if result.success and result.data:
            state.current_problem = result.data
            return CycleResult(
                cycle_number=state.current_cycle,
                problem=result.data,
                next_action=NextAction.GENERATE_CANDIDATES,
                next_action_reasoning="Problem framed, ready to generate solutions"
            )

        # Framing failure
        return CycleResult(
            cycle_number=state.current_cycle,
            next_action=NextAction.NEEDS_HUMAN_INPUT,
            next_action_reasoning=f"Problem framing failed: {result.error}"
        )

    async def _execute_research(self, state: SessionState) -> CycleResult:
        """Execute the research phase."""
        if not state.current_problem:
            return CycleResult(
                cycle_number=state.current_cycle,
                next_action=NextAction.REFINE_PROBLEM,
                next_action_reasoning="Cannot research without defined problem"
            )

        research_input = ResearcherInput(
            query=state.current_problem.root_problem,
            problem_context=state.current_problem.raw_input,
            existing_evidence=[]
        )

        result = await self.researcher.execute(research_input)

        if result.success and result.data:
            state.research_done = True
            return CycleResult(
                cycle_number=state.current_cycle,
                problem=state.current_problem,
                research=result.data,
                next_action=NextAction.GENERATE_CANDIDATES,
                next_action_reasoning="Research complete, ready for candidates"
            )

        return CycleResult(
            cycle_number=state.current_cycle,
            problem=state.current_problem,
            next_action=NextAction.GENERATE_CANDIDATES,
            next_action_reasoning="Research failed, proceeding with candidates anyway"
        )

    async def _execute_candidate_generation(
        self,
        state: SessionState
    ) -> CycleResult:
        """Execute the candidate generation phase."""
        if not state.current_problem:
            return CycleResult(
                cycle_number=state.current_cycle,
                next_action=NextAction.REFINE_PROBLEM,
                next_action_reasoning="Cannot generate candidates without problem"
            )

        # Get research from previous cycle if available
        research = None
        if state.cycles:
            for cycle in reversed(state.cycles):
                if cycle.research:
                    research = cycle.research
                    break

        architect_input = ArchitectInput(
            problem=state.current_problem,
            research=research,
            existing_candidates=[],
            min_candidates=3
        )

        result = await self.architect.execute(architect_input)

        if result.success and result.data:
            state.candidates_generated = len(result.data)
            return CycleResult(
                cycle_number=state.current_cycle,
                problem=state.current_problem,
                research=research,
                candidates=result.data,
                next_action=NextAction.CRITIQUE,
                next_action_reasoning=f"Generated {len(result.data)} candidates, ready for critique"
            )

        return CycleResult(
            cycle_number=state.current_cycle,
            problem=state.current_problem,
            next_action=NextAction.NEEDS_HUMAN_INPUT,
            next_action_reasoning=f"Candidate generation failed: {result.error}"
        )

    async def _execute_critique(self, state: SessionState) -> CycleResult:
        """Execute the critique phase."""
        if not state.current_problem:
            return CycleResult(
                cycle_number=state.current_cycle,
                next_action=NextAction.REFINE_PROBLEM,
                next_action_reasoning="Cannot critique without problem"
            )

        # Get candidates from previous cycle
        candidates: list[CandidateSolution] = []
        research: ResearchFindings | None = None

        for cycle in reversed(state.cycles):
            if cycle.candidates and not candidates:
                candidates = cycle.candidates
            if cycle.research and not research:
                research = cycle.research
            if candidates:
                break

        if not candidates:
            return CycleResult(
                cycle_number=state.current_cycle,
                problem=state.current_problem,
                next_action=NextAction.GENERATE_CANDIDATES,
                next_action_reasoning="No candidates found to critique"
            )

        critic_input = CriticInput(
            problem=state.current_problem,
            candidates=candidates
        )

        result = await self.critic.execute(critic_input)

        if result.success and result.data:
            state.critiques_done = len(result.data)

            # Judge what to do next
            judge_input = JudgeInput(
                problem=state.current_problem,
                cycle_number=state.current_cycle,
                max_cycles=state.input_data.max_cycles,
                research=research,
                candidates=candidates,
                critiques=result.data
            )
            judge_result = await self.judge.execute(judge_input)

            next_action = NextAction.CONVERGE
            reasoning = "Critique complete, evaluating convergence"

            if judge_result.success and judge_result.data:
                next_action = judge_result.data.next_action
                reasoning = judge_result.data.next_action_reasoning

            return CycleResult(
                cycle_number=state.current_cycle,
                problem=state.current_problem,
                research=research,
                candidates=candidates,
                critiques=result.data,
                next_action=next_action,
                next_action_reasoning=reasoning
            )

        return CycleResult(
            cycle_number=state.current_cycle,
            problem=state.current_problem,
            candidates=candidates,
            next_action=NextAction.CONVERGE,
            next_action_reasoning=f"Critique failed: {result.error}, attempting convergence"
        )

    async def _execute_problem_refinement(
        self,
        state: SessionState
    ) -> CycleResult:
        """Execute problem refinement when blockers found."""
        # For MVP: just re-frame with current state context
        if state.current_problem:
            refined_context = {
                **state.input_data.context,
                "refinement_cycle": state.current_cycle,
                "previous_root": state.current_problem.root_problem
            }

            framer_input = ProblemFramerInput(
                raw_description=state.input_data.problem_description,
                context=refined_context
            )

            result = await self.framer.execute(framer_input)

            if result.success and result.data:
                state.current_problem = result.data
                return CycleResult(
                    cycle_number=state.current_cycle,
                    problem=result.data,
                    next_action=NextAction.GENERATE_CANDIDATES,
                    next_action_reasoning="Problem refined based on new insights"
                )

        return CycleResult(
            cycle_number=state.current_cycle,
            next_action=NextAction.NEEDS_HUMAN_INPUT,
            next_action_reasoning="Problem refinement required but failed"
        )

    async def _execute_convergence(
        self,
        state: SessionState,
        convergence: ConvergenceStatus
    ) -> CycleResult:
        """Execute convergence phase."""
        # Gather all artifacts
        candidates: list[CandidateSolution] = []
        critiques: list[CritiqueReport] = []
        research: ResearchFindings | None = None

        for cycle in reversed(state.cycles):
            if cycle.candidates and not candidates:
                candidates = cycle.candidates
            if cycle.critiques and not critiques:
                critiques = cycle.critiques
            if cycle.research and not research:
                research = cycle.research

        return CycleResult(
            cycle_number=state.current_cycle,
            problem=state.current_problem,
            research=research,
            candidates=candidates,
            critiques=critiques,
            next_action=NextAction.CONVERGE,
            next_action_reasoning=f"Convergence: {convergence.reason}"
        )

    def _handle_judge_failure(self, cycle_num: int) -> CycleResult:
        """Handle judge agent failure gracefully."""
        return CycleResult(
            cycle_number=cycle_num,
            next_action=NextAction.NEEDS_HUMAN_INPUT,
            next_action_reasoning="Judge evaluation failed - manual intervention needed"
        )

    def _build_judge_input(self, state: SessionState) -> JudgeInput:
        """Build judge input from current state."""
        candidates: list[CandidateSolution] = []
        critiques: list[CritiqueReport] = []
        research: ResearchFindings | None = None
        previous_actions: list[NextAction] = []

        for cycle in state.cycles:
            previous_actions.append(cycle.next_action)
            if cycle.candidates:
                candidates = cycle.candidates
            if cycle.critiques:
                critiques = cycle.critiques
            if cycle.research:
                research = cycle.research

        return JudgeInput(
            problem=state.current_problem,
            cycle_number=state.current_cycle,
            max_cycles=state.input_data.max_cycles,
            research=research,
            candidates=candidates,
            critiques=critiques,
            previous_actions=previous_actions
        )

    def _synthesize_output(self, state: SessionState) -> SessionOutput:
        """Generate final session output from state."""
        if not state.cycles:
            raise ValueError("No cycles completed")

        # Get final artifacts
        final_cycle = state.cycles[-1]
        problem = state.current_problem
        research: ResearchFindings | None = None
        all_candidates: list[CandidateSolution] = []
        all_critiques: list[CritiqueReport] = []

        for cycle in state.cycles:
            if cycle.research:
                research = cycle.research
            if cycle.candidates:
                all_candidates = cycle.candidates
            if cycle.critiques:
                all_critiques = cycle.critiques

        # Determine top candidate
        top_candidate = self._select_top_candidate(all_candidates, all_critiques)

        # Build critique summary
        critique_summary: dict[str, list[str]] = {}
        for critique in all_critiques:
            critique_summary[critique.candidate_id] = critique.weaknesses

        # Assess convergence
        convergence = self._final_convergence_assessment(
            state, problem, all_candidates
        )

        # Generate synthesis
        synthesis = self._generate_synthesis(
            problem, all_candidates, top_candidate, convergence
        )

        return SessionOutput(
            session_id=state.session_id,
            problem=problem,
            research_findings=research,
            candidates=all_candidates,
            top_candidate=top_candidate,
            critique_summary=critique_summary,
            convergence=convergence,
            final_synthesis=synthesis,
            cycles_completed=len(state.cycles),
            artifacts_generated=[
                f"problem_definition_{state.session_id}",
                f"candidates_{len(all_candidates)}",
                f"critiques_{len(all_critiques)}"
            ]
        )

    def _select_top_candidate(
        self,
        candidates: list[CandidateSolution],
        critiques: list[CritiqueReport]
    ) -> CandidateSolution | None:
        """Select the best candidate based on scores and critiques."""
        if not candidates:
            return None

        # Build dealbreaker map
        dealbreakers: dict[str, int] = {}
        for critique in critiques:
            dealbreakers[critique.candidate_id] = len(critique.dealbreakers)

        # Score candidates
        scored: list[tuple[CandidateSolution, float]] = []
        for candidate in candidates:
            score = candidate.score or 0.5
            # Penalize dealbreakers
            score -= dealbreakers.get(candidate.id, 0) * 0.2
            scored.append((candidate, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0] if scored else None

    def _final_convergence_assessment(
        self,
        state: SessionState,
        problem: ProblemDefinition | None,
        candidates: list[CandidateSolution]
    ) -> ConvergenceStatus:
        """Final convergence assessment for output."""
        criteria_met: dict[str, bool] = {
            "root_problem_defined": bool(problem and problem.root_problem),
            "sufficient_candidates": len(candidates) >= settings.min_candidates_for_convergence,
            "uncertainties_reduced": True,  # Simplified for MVP
            "risks_surfaced": len(candidates) > 0 and all(c.key_risks for c in candidates),
            "implementation_concrete": len(candidates) > 0 and all(
                len(c.implementation_steps) >= 3 for c in candidates
            )
        }

        converged = all(criteria_met.values())
        confidence = sum(criteria_met.values()) / len(criteria_met)

        return ConvergenceStatus(
            converged=converged,
            confidence=confidence,
            reason="Final assessment based on completed cycles",
            criteria_met=criteria_met
        )

    def _generate_synthesis(
        self,
        problem: ProblemDefinition | None,
        candidates: list[CandidateSolution],
        top_candidate: CandidateSolution | None,
        convergence: ConvergenceStatus
    ) -> str:
        """Generate executive summary synthesis."""
        if not problem:
            return "No problem definition available."

        lines = [
            "# Solution Lab Synthesis",
            "",
            f"## Problem",
            problem.root_problem,
            "",
            f"## Success Criteria",
        ]

        for criterion in problem.success_criteria:
            lines.append(f"- {criterion}")

        lines.extend([
            "",
            f"## Candidates Evaluated: {len(candidates)}",
        ])

        for c in candidates:
            score_str = f" ({c.score:.0%})" if c.score else ""
            lines.append(f"- **{c.name}**{score_str}: {c.description[:100]}...")

        if top_candidate:
            lines.extend([
                "",
                "## Recommended Approach",
                f"**{top_candidate.name}**",
                "",
                "### Implementation Steps",
            ])
            for step in top_candidate.implementation_steps:
                lines.append(f"1. {step}")

        lines.extend([
            "",
            f"## Convergence Status",
            f"- **Converged**: {'Yes' if convergence.converged else 'No'}",
            f"- **Confidence**: {convergence.confidence:.0%}",
            f"- **Reason**: {convergence.reason}",
        ])

        return "\n".join(lines)
