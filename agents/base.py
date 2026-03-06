"""
Base agent class with common functionality.

All agents inherit from AgentBase and implement the execute method.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from schemas.models import Evidence


InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class AgentResult(BaseModel, Generic[OutputT]):
    """Standard wrapper for all agent results."""

    success: bool
    data: OutputT | None = None
    error: str | None = None
    evidence_used: list[Evidence] = []
    processing_time_ms: int | None = None

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def ok(cls, data: OutputT, evidence: list[Evidence] | None = None) -> "AgentResult[OutputT]":
        """Create a successful result."""
        return cls(success=True, data=data, evidence_used=evidence or [])

    @classmethod
    def fail(cls, error: str) -> "AgentResult[OutputT]":
        """Create a failed result."""
        return cls(success=False, error=error)


class AgentBase(ABC, Generic[InputT, OutputT]):
    """Abstract base for all agents."""

    name: str = "base_agent"

    @abstractmethod
    async def execute(self, input_data: InputT, **kwargs: Any) -> AgentResult[OutputT]:
        """
        Execute the agent's primary function.

        Args:
            input_data: The input data for this agent
            **kwargs: Additional context parameters

        Returns:
            AgentResult wrapping the structured output
        """
        pass

    def _create_evidence(
        self,
        claim: str,
        evidence_type: str,
        confidence: float = 0.5,
        **kwargs: Any
    ) -> Evidence:
        """Helper to create evidence objects."""
        return Evidence(
            claim=claim,
            source=f"{self.name}_agent",
            evidence_type=evidence_type,  # type: ignore
            confidence=confidence,
            data=kwargs,
        )
