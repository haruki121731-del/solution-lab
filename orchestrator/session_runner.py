from __future__ import annotations

import uuid
from datetime import datetime, timezone

from agents.architect import Architect, ArchitectInput
from agents.critic import Critic, CriticInput
from agents.judge import Judge, JudgeInput
from agents.problem_framer import ProblemFramer, ProblemFramerInput
from agents.researcher import Researcher, ResearcherInput
from schemas.models import (
    CandidateSolution,
    ConvergenceStatus,
    CycleResult,
    NextAction,
    SessionInput,
    SessionOutput,
    SessionState,
)


class SessionRunner:
    def __init__(
        self,
        *,
        framer: ProblemFramer | None = None,
        researcher: Researcher | None = None,
        architect: Architect | None = None,
        critic: Critic | None = None,
        judge: Judge | None = None,
    ) -> None:
        self.framer = framer or ProblemFramer()
        self.researcher = researcher or Researcher()
        self.architect = architect or Architect()
        self.critic = critic or Critic()
        self.judge = judge or Judge()

    async def run(self, input_data: SessionInput) -> SessionOutput:
        state = SessionState(session_id=str(uuid.uuid4())[:8], input_data=input_data)

        while not state.is_complete(input_data.max_cycles):
            cycle = await self._run_cycle(state)
            state.cycles.append(cycle)
            state.updated_at = datetime.now(timezone.utc)

        return self._synthesize_output(state)

    async def _run_cycle(self, state: SessionState) -> CycleResult:
        cycle_number = len(state.cycles) + 1

        if state.problem is None:
            framed = await self.framer.execute(
                ProblemFramerInput(
                    raw_description=state.input_data.problem_description,
                    context=state.input_data.context,
                )
            )
            if not framed.success or framed.data is None:
                raise RuntimeError(framed.error or 'Problem framing failed.')
            state.problem = framed.data
            return CycleResult(
                cycle_number=cycle_number,
                action_taken=NextAction.design,
                notes='Framed the raw problem into a structured working definition.',
                problem=state.problem,
                convergence=ConvergenceStatus(converged=False, confidence=0.25, reason='Problem framed; research/design still needed.'),
            )

        if state.research is None and state.input_data.allow_external_research:
            research = await self.researcher.execute(
                ResearcherInput(
                    query=state.problem.root_problem,
                    problem_context=state.problem.raw_input,
                )
            )
            if not research.success or research.data is None:
                raise RuntimeError(research.error or 'Research failed.')
            state.research = research.data
            return CycleResult(
                cycle_number=cycle_number,
                action_taken=NextAction.research,
                notes='Collected evidence and identified follow-up gaps.',
                problem=state.problem,
                research=state.research,
                convergence=ConvergenceStatus(converged=False, confidence=0.35, reason='Evidence collected; candidates still need comparison.'),
            )

        if len(state.candidates) < 3:
            built = await self.architect.execute(
                ArchitectInput(
                    problem=state.problem,
                    research=state.research,
                    existing_candidates=state.candidates,
                )
            )
            if not built.success or built.data is None:
                raise RuntimeError(built.error or 'Candidate generation failed.')
            state.candidates = built.data
            return CycleResult(
                cycle_number=cycle_number,
                action_taken=NextAction.design,
                notes='Generated competing solution candidates.',
                problem=state.problem,
                research=state.research,
                candidates=state.candidates,
                convergence=ConvergenceStatus(converged=False, confidence=0.45, reason='Candidates exist but still need critique.'),
            )

        if len(state.critiques) < len(state.candidates):
            critiqued = await self.critic.execute(CriticInput(problem=state.problem, candidates=state.candidates))
            if not critiqued.success or critiqued.data is None:
                raise RuntimeError(critiqued.error or 'Critique failed.')
            state.critiques = critiqued.data
            return CycleResult(
                cycle_number=cycle_number,
                action_taken=NextAction.critique,
                notes='Attacked candidate weaknesses and surfaced uncertainties.',
                problem=state.problem,
                research=state.research,
                candidates=state.candidates,
                critiques=state.critiques,
                convergence=ConvergenceStatus(converged=False, confidence=0.56, reason='Critiques complete; ready for final judgment.'),
            )

        judged = await self.judge.execute(
            JudgeInput(
                problem=state.problem,
                cycle_number=cycle_number,
                max_cycles=state.input_data.max_cycles,
                research=state.research,
                candidates=state.candidates,
                critiques=state.critiques,
                previous_actions=[cycle.action_taken for cycle in state.cycles],
            )
        )
        if not judged.success or judged.data is None:
            raise RuntimeError(judged.error or 'Judgment failed.')

        state.final_synthesis = self._build_synthesis(state)
        return CycleResult(
            cycle_number=cycle_number,
            action_taken=judged.data.next_action,
            notes=judged.data.next_action_reasoning,
            problem=state.problem,
            research=state.research,
            candidates=state.candidates,
            critiques=state.critiques,
            convergence=judged.data.convergence,
        )

    def _build_synthesis(self, state: SessionState) -> str:
        ranked = sorted(
            state.candidates,
            key=lambda candidate: next((c.score for c in state.critiques if c.candidate_id == candidate.id), 0.0),
            reverse=True,
        )
        top = ranked[0] if ranked else None
        summary = [
            f"Problem: {state.problem.root_problem}",
            f"Constraints: {', '.join(state.problem.constraints) if state.problem.constraints else 'None explicitly stated'}",
            f"Top candidate: {top.name if top else 'None'}",
            f"Why it leads: {top.description if top else 'No candidates generated'}",
            'Next step: run a small measured experiment before large rollout.',
        ]
        return '\n'.join(summary)

    def _synthesize_output(self, state: SessionState) -> SessionOutput:
        ranked = sorted(
            state.candidates,
            key=lambda candidate: next((c.score for c in state.critiques if c.candidate_id == candidate.id), candidate.confidence),
            reverse=True,
        )
        final_cycle = state.cycles[-1]
        return SessionOutput(
            session_id=state.session_id,
            problem=state.problem,
            research=state.research,
            candidates=ranked,
            critiques=state.critiques,
            top_candidate=ranked[0] if ranked else None,
            convergence=final_cycle.convergence or ConvergenceStatus(converged=False, confidence=0.0, reason='No convergence produced.'),
            final_synthesis=state.final_synthesis or self._build_synthesis(state),
            cycles_completed=len(state.cycles),
            cycles=state.cycles,
        )
