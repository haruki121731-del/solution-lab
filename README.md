# Solution Lab

A production-ready multi-agent research OS for structured problem-solving.

## Features

- **Deterministic Agents**: Problem framing, research, design, critique, judgment
- **External API Integration**: Firecrawl (web research), OpenAI/Anthropic (LLM)
- **Persistent Storage**: SQLite-based session storage
- **Authentication**: API key-based access control
- **Extensible Architecture**: Protocol-based adapters for easy extension

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run server (dev mode - no auth required)
uvicorn app:app --reload

# Run with authentication
API_KEYS=your-secret-key uvicorn app:app
```

## API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Solve a problem (dev mode)
curl -X POST http://localhost:8000/solve \
  -H "Content-Type: application/json" \
  -d '{
    "problem_description": "Our checkout flow has 70% abandonment at payment",
    "max_cycles": 5,
    "allow_external_research": true
  }'

# With authentication
curl -X POST http://localhost:8000/solve \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{...}'

# List sessions
curl http://localhost:8000/sessions

# Get specific session
curl http://localhost:8000/sessions/{session_id}
```

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEYS` | Comma-separated API keys | (empty = no auth) |
| `FIRECRAWL_API_KEY` | Firecrawl API key | (optional) |
| `OPENAI_API_KEY` | OpenAI API key | (optional) |
| `ANTHROPIC_API_KEY` | Anthropic API key | (optional) |
| `SESSION_STORAGE_PATH` | SQLite database path | `./data/sessions.db` |

## Testing

```bash
pytest
```

## Architecture

```
app.py (FastAPI layer)
├── auth/ (API key authentication)
├── agents/ (5 deterministic agents)
│   ├── base.py (AgentResult, AgentProtocol)
│   ├── problem_framer.py
│   ├── researcher.py
│   ├── architect.py
│   ├── critic.py
│   └── judge.py
├── orchestrator/ (session_runner.py)
├── storage/ (SQLite persistence)
├── tools/ (Research adapters)
└── schemas/ (Pydantic models)
```
