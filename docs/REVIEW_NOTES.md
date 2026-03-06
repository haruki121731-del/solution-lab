# Review Notes

This refactor prioritizes correctness, explicit state, and testability over theatrical agent chatter.

## Design choices

- Deterministic agents first. LLM integrations should be added behind interfaces, not smeared through the core loop.
- Convergence is a code-level decision informed by agent outputs, not a vibe.
- Research is adapter-based so Firecrawl or any other source can be plugged in later.
- Session output always contains comparable artifacts: problem, research, candidates, critiques, convergence.
