# Solution Lab

A multi-agent research system for structured problem-solving.

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

## API

```bash
# Health check
curl http://localhost:8000/health

# Solve a problem
curl -X POST http://localhost:8000/solve \
  -H "Content-Type: application/json" \
  -d '{
    "problem_description": "Our checkout flow has 70% abandonment at payment",
    "max_cycles": 5,
    "allow_external_research": true
  }'
```

## Architecture

Deterministic agents with explicit state management:

1. **ProblemFramer** → Structured problem definition
2. **Researcher** → Evidence collection (adapter-based)
3. **Architect** → 3+ competing solution candidates
4. **Critic** → Weakness analysis
5. **Judge** → Convergence decision

## Testing

```bash
pytest
```

## Design Principles

- Deterministic orchestration (LLM adapters behind interfaces)
- Explicit state transitions
- Testable without external APIs
- Convergence is code-level, not vibe-based
