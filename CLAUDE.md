# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DroneAI** — an autonomous drone control system that uses a CrewAI vision agent to analyze the drone's camera feed and make landing decisions in real time.

## Commands

This project uses `uv` for dependency management (Python 3.13).

```bash
# Install dependencies
uv sync

# Run the main drone loop
uv run python main.py

# Run the vision agent standalone (for testing)
uv run python ai/agents/vision_agent/crew.py

# Add a dependency
uv add <package>
```

## Architecture

### Entry Point
`main.py` — connects to a drone via `pysimverse`, streams camera frames, saves each frame as `drone_capture.png`, and calls the vision agent every 2 seconds. Lands automatically when the agent reports `is_safe_to_land=True`.

### Configuration
`settings.py` — loads `.env` and exposes `Config` (a `pydantic-settings` instance) with `OPENAI_API_KEY`. The `OPENAI_API_KEY` must be set in `.env`.

### AI Layer (`ai/`)
- **`ai/config.py`** — `AgentInfrastructure` base class: wraps CrewAI `LLM` (GPT-4o via OpenAI), loads agent/task configs from YAML, and exposes a `cached_property` LLM instance.
- **`ai/agents/vision_agent/crew.py`** — `VisionAgent(AgentInfrastructure)` decorated with `@CrewBase`. Defines one agent (`researcher`) using `VisionTool` and one task (`research_task`) with structured Pydantic output (`VisionToolSchema`). The public entry point is `vision_agent(prompt, image_path) -> dict`.
- **`ai/agents/vision_agent/config/agents.yaml`** / **`tasks.yaml`** — CrewAI YAML configs for agent role/goal/backstory and task description/expected output.

### Output Schema
`VisionToolSchema` (in `crew.py`) is the structured output returned by the crew:
- `objects: list[str]` — detected objects
- `hazards: list[str]` — detected hazards
- `is_safe_to_land: bool` — landing decision
- `distance_from_obstacles: list[ObstaclesSchema]`
- `move_to: Movements` — directional movement suggestion (`RIGHT/LEFT/UP/DOWN/FORWARD/BACKWARD`)

### Adding a New Agent
Follow the `vision_agent` pattern:
1. Create `ai/agents/<name>/` with `crew.py`, `tools/`, and `config/agents.yaml` + `config/tasks.yaml`.
2. Subclass `AgentInfrastructure` and decorate with `@CrewBase`.
3. Define `@agent`, `@task`, and `@crew` methods.
