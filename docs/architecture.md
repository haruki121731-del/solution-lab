# Solution Lab Architecture

## Overview

Solution Lab is a multi-agent research OS designed to solve product problems through structured, iterative cycles. It emphasizes explicit state management, structured outputs, and evidence-based reasoning over speculative prose.

## Core Principles

1. **Reduce Uncertainty**: Every cycle must reduce uncertainty, not just produce text
2. **Explicit Assumptions**: All assumptions must be surfaced and validated
3. **Evidence-Based**: Prefer verified evidence over speculation
4. **No False Convergence**: Convergence requires meeting explicit criteria
5. **Clear Boundaries**: Agents have single responsibilities with structured interfaces

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Layer                            │
│                    (app.py - HTTP Interface)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Session Runner                                │
│         (orchestrator/session_runner.py)                         │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Problem │→ │ Research │→ │ Architect│→ │  Critic  │         │
│  │ Framer  │  │          │  │          │  │          │         │
│  └─────────┘  └──────────┘  └──────────┘  └──────────┘         │
│       ↑                                         │                │
│       └──────────────┬──────────────────────────┘                │
│                      ▼                                           │
│                   ┌──────┐                                       │
│                   │Judge │←── Decides next action                │
│                   └──────┘                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Layer                                 │
│  Each agent:                                                    │
│  - Single responsibility                                        │
│  - Structured input/output via Pydantic                         │
│  - Returns AgentResult wrapper                                  │
│  - No LLM framework lock-in                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Tools Layer                                 │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │ FirecrawlClient │  │  (extensible)   │                      │
│  │ (thin adapter)  │  │                 │                      │
│  └─────────────────┘  └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Session Lifecycle

1. **Initialization**
   - SessionInput validated via Pydantic
   - SessionState initialized with UUID
   - Cycle counter starts at 1

2. **Cycle Execution**
   ```
   Cycle 1: Always Problem Framing
       ↓
   [Judge] → Research? (if allowed & cycle 2)
       ↓
   [Judge] → Generate Candidates (min 3)
       ↓
   [Judge] → Critique All Candidates
       ↓
   [Judge] → Assess Convergence
       ↓
   Converged? → Yes: Final Synthesis
              → No: Next Cycle (until max_cycles)
   ```

3. **Artifact Preservation**
   - Every cycle result stored in SessionState
   - All intermediate outputs accessible
   - Final synthesis aggregates all artifacts

## Agent Responsibilities

### ProblemFramer
**Input**: Raw problem description + context  
**Output**: ProblemDefinition with root problem, success criteria, assumptions  
**Key Behavior**: Distills root cause from symptoms, forces explicit success criteria

### Researcher
**Input**: Query + problem context  
**Output**: ResearchFindings with sources, evidence, gaps  
**Key Behavior**: Gathers external evidence, marks unverified findings as hypotheses

### Architect
**Input**: ProblemDefinition + optional ResearchFindings  
**Output**: 3+ CandidateSolution objects with pros/cons/risks  
**Key Behavior**: Generates diverse approaches (not variations), scores candidates

### Critic
**Input**: ProblemDefinition + CandidateSolutions  
**Output**: CritiqueReport per candidate with weaknesses/dealbreakers  
**Key Behavior**: Aggressive critique, surfaces dealbreakers, identifies uncertainties

### Judge
**Input**: Current state (problem, candidates, critiques, cycle info)  
**Output**: ConvergenceStatus + NextAction  
**Key Behavior**: Never claims convergence without evidence, tracks uncertainty reduction

## State Management

### SessionState
Central state container tracking:
- `session_id`: Unique identifier
- `input_data`: Original SessionInput
- `cycles`: List of CycleResult objects (immutable history)
- `current_problem`: Latest ProblemDefinition
- Flags: `research_done`, `candidates_generated`, `critiques_done`

### CycleResult
Immutable record of each cycle:
- `cycle_number`: 1-indexed
- `problem`: ProblemDefinition (if framed/refined)
- `research`: ResearchFindings (if researched)
- `candidates`: List[CandidateSolution] (if generated)
- `critiques`: List[CritiqueReport] (if critiqued)
- `next_action`: What to do next
- `timestamp`: When cycle completed

## Convergence Criteria

The Judge agent enforces strict convergence requirements:

| Criterion | Required | Description |
|-----------|----------|-------------|
| root_problem_defined | Yes | Clear, actionable problem statement |
| sufficient_candidates | Yes | At least 2 candidates compared |
| ideal_candidates | No | At least 3 candidates (preferred) |
| uncertainties_reduced | Yes | No blocker uncertainties remaining |
| risks_surfaced | Yes | All candidates have risk analysis |
| implementation_concrete | Yes | Clear implementation path exists |

**Convergence confidence** = (criteria_met / total_criteria)

## Configuration

All configuration via environment variables:

```bash
# Core
APP_NAME=Solution Lab
DEBUG=false
LOG_LEVEL=INFO

# API
HOST=0.0.0.0
PORT=8000

# LLM (stub for MVP)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_API_KEY=sk-...

# Firecrawl
FIRECRAWL_API_KEY=fc-...
FIRECRAWL_BASE_URL=https://api.firecrawl.dev

# Session
SESSION_STORAGE_PATH=./sessions
MAX_SESSIONS=100
DEFAULT_MAX_CYCLES=5
```

## Extension Points

### Adding New Agents

1. Inherit from `AgentBase[InputT, OutputT]`
2. Define Pydantic input/output models
3. Implement `execute()` method
4. Return `AgentResult[OutputT]`

### Adding New Tools

1. Create adapter in `tools/`
2. Keep interface thin and abstracted
3. Allow injection for testability
4. Mark stub implementations with TODO

### Custom Convergence Criteria

Override `Judge._assess_convergence()` to add domain-specific criteria.

## Testing Strategy

- **Schema Tests**: Validate all Pydantic models
- **Agent Tests**: Unit test each agent in isolation
- **Orchestrator Tests**: Happy path through full session
- **Integration Tests**: End-to-end with real agents (minimal mocking)

## Design Decisions

### Why No Heavy Agent Frameworks?

Frameworks like LangChain, CrewAI, or AutoGen provide convenience but introduce:
- Magic that hides control flow
- Difficulty in debugging
- Framework lock-in
- Opacity in state transitions

Solution Lab prefers explicit orchestration where:
- Control flow is visible in code
- State transitions are explicit
- Agents are swappable
- Logic is testable without frameworks

### Why Structured Outputs?

LLMs are good at reasoning but unreliable with unstructured text:
- Structured outputs (Pydantic) enforce schema
- Downstream agents can depend on fields existing
- Validation catches errors early
- Enables type-safe code throughout

### Why Cycle-Based?

Cycles provide:
- Natural checkpoint boundaries
- Clear artifact preservation points
- Recoverability from failures
- Observable progress
- Debugging visibility
