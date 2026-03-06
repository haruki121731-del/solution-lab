# Solution Lab

A multi-agent research OS for solving product problems through structured cycles.

## Overview

Solution Lab transforms vague product problems into actionable solutions through an iterative, evidence-based process:

1. **Frame** the root problem
2. **Gather** external evidence
3. **Generate** competing solution candidates
4. **Critique** them aggressively
5. **Decide** the next best action
6. **Repeat** until convergence

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd solution-lab

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### Run the Server

```bash
# Development
uvicorn app:app --reload

# Production
uvicorn app:app --host 0.0.0.0 --port 8000
```

### API Usage

```bash
# Health check
curl http://localhost:8000/health

# Solve a problem
curl -X POST http://localhost:8000/solve \
  -H "Content-Type: application/json" \
  -d '{
    "problem_description": "Our user onboarding flow has 60% drop-off at email verification",
    "max_cycles": 5,
    "allow_external_research": true,
    "context": {"team_size": 5}
  }'
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for detailed system design.

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Problem   │────▶│   Research   │────▶│   Architect │
│   Framer    │     │              │     │             │
└─────────────┘     └──────────────┘     └─────────────┘
      ↑                                          │
      └───────────────┬──────────────────────────┘
                      ▼
               ┌────────────┐
               │   Judge    │ ← Decides next action
               │ (converge? │
               └────────────┘
                      │
                      ▼
               ┌────────────┐
               │   Critic   │ ← Attacks candidates
               └────────────┘
```

## Project Structure

```
solution-lab/
├── app.py                     # FastAPI entry point
├── config.py                  # Environment configuration
├── requirements.txt           # Dependencies
├── schemas/
│   ├── models.py             # Pydantic models
│   └── __init__.py
├── agents/
│   ├── base.py               # Agent base class
│   ├── problem_framer.py     # Problem framing agent
│   ├── researcher.py         # External research agent
│   ├── architect.py          # Solution generation agent
│   ├── critic.py             # Solution critique agent
│   ├── judge.py              # Convergence judge agent
│   └── __init__.py
├── orchestrator/
│   ├── session_runner.py     # Main orchestration logic
│   └── __init__.py
├── tools/
│   ├── firecrawl_client.py   # Web research adapter
│   └── __init__.py
├── tests/
│   ├── test_schemas.py       # Schema validation tests
│   ├── test_orchestrator.py  # Orchestrator tests
│   └── conftest.py           # Pytest configuration
└── docs/
    ├── architecture.md       # System architecture
    └── roadmap.md            # Development roadmap
```

## Key Features

### Structured Outputs
Every agent returns structured Pydantic models, not loose prose:

```python
class CandidateSolution(BaseModel):
    id: str
    name: str
    description: str
    approach_type: str
    pros: list[str]
    cons: list[str]
    key_risks: list[Risk]
    implementation_steps: list[str]
```

### Explicit Convergence
The system never claims convergence without evidence. Convergence requires:
- Root problem defined
- 2+ candidates compared
- Key uncertainties reduced
- Major risks surfaced
- Concrete implementation path

### Artifact Preservation
All intermediate outputs are preserved in session state:
- Problem definitions
- Research findings
- Solution candidates
- Critique reports
- Cycle-by-cycle decisions

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/solve` | POST | Run complete solution session |

### POST /solve

**Request Body** (SessionInput):
```json
{
  "problem_description": "string (min 10 chars)",
  "max_cycles": 5,
  "allow_external_research": true,
  "context": {}
}
```

**Response** (SessionOutput):
```json
{
  "session_id": "abc123",
  "problem": { ... },
  "candidates": [ ... ],
  "top_candidate": { ... },
  "convergence": {
    "converged": true,
    "confidence": 0.85,
    "reason": "All criteria met"
  },
  "final_synthesis": "# Solution Lab Synthesis\n\n## Problem..."
}
```

## Development

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=.

# Specific test file
pytest tests/test_schemas.py

# Verbose
pytest -v
```

### Code Quality

```bash
# Type checking
mypy .

# Linting
ruff check .

# Formatting
ruff format .
```

### Adding a New Agent

1. Create file in `agents/your_agent.py`
2. Inherit from `AgentBase[Input, Output]`
3. Define Pydantic input/output models
4. Implement `execute()` method
5. Add to `agents/__init__.py`
6. Wire into `SessionRunner`

Example:
```python
from agents.base import AgentBase, AgentResult

class YourAgentInput(BaseModel):
    data: str

class YourAgentOutput(BaseModel):
    result: str

class YourAgent(AgentBase[YourAgentInput, YourAgentOutput]):
    async def execute(self, input_data, **kwargs) -> AgentResult[YourAgentOutput]:
        # Your logic here
        return AgentResult.ok(data=YourAgentOutput(result="done"))
```

## Configuration

All configuration via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | Solution Lab | App name |
| `DEBUG` | false | Debug mode |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8000 | Server port |
| `LLM_MODEL` | gpt-4 | LLM model |
| `LLM_API_KEY` | None | OpenAI/Anthropic key |
| `FIRECRAWL_API_KEY` | None | Firecrawl key |
| `DEFAULT_MAX_CYCLES` | 5 | Max solution cycles |

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) for detailed development plans.

**Current (MVP)**:
- ✅ FastAPI server
- ✅ 5 core agents
- ✅ Session orchestration
- ✅ Schema validation
- ✅ Basic tests

**Next**:
- LLM integration
- Firecrawl research
- Session persistence
- Async job queue

## Core Principles

1. **Reduce Uncertainty**: Every cycle must reduce uncertainty, not just produce text
2. **Explicit Assumptions**: Surface and validate all assumptions
3. **Evidence-Based**: Prefer verified evidence over speculation
4. **No False Convergence**: Meet explicit criteria before claiming done
5. **Clear Boundaries**: Single-responsibility agents with structured interfaces

## License

MIT
