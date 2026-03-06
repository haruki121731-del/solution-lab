from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Protocol, TypeVar

from schemas.models import Evidence

InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')


@dataclass(slots=True)
class AgentResult(Generic[OutputT]):
    success: bool
    data: OutputT | None = None
    error: str | None = None
    evidence_used: list[Evidence] = field(default_factory=list)

    @classmethod
    def ok(cls, data: OutputT, evidence_used: list[Evidence] | None = None) -> 'AgentResult[OutputT]':
        return cls(success=True, data=data, evidence_used=evidence_used or [])

    @classmethod
    def fail(cls, error: str) -> 'AgentResult[OutputT]':
        return cls(success=False, error=error)


class AgentProtocol(Protocol[InputT, OutputT]):
    async def execute(self, input_data: InputT) -> AgentResult[OutputT]: ...
