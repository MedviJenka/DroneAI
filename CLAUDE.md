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

## Configuration

`settings.py` — `Config` (pydantic-settings) reads `.env`. Both keys are required:
- `OPENAI_API_KEY` — used by CrewAI LLM (GPT-4o)
- `LOGFIRE_TOKEN` — used by the `Log` class for structured logging

## Architecture

### Entry Point
`main.py` — connects to a drone via `pysimverse`, streams camera frames to `drone_capture.png`, and calls the vision agent every 2 seconds. Landing requires **both** `target_found=True` and `is_safe_to_land=True`.

Movement dispatch uses `MOVE_ACTIONS` (keyed by `move_to` string). `MOVE_DISTANCE = 50` is the unit for all moves.

### Logging
`log.py` — `Log(name=...)` wraps logfire. Access via `log.fire.info(...)` / `log.fire.error(...)`.

### AI Layer (`ai/`)
- **`ai/config.py`** — `AgentInfrastructure` base class: wraps CrewAI `LLM` (GPT-4o), loads agent/task configs from YAML, exposes `cached_property` LLM.
- **`ai/agents/vision_agent/crew.py`** — `VisionAgent(AgentInfrastructure)` with `@CrewBase`. One agent (`researcher`) using `VisionTool`, one task (`research_task`) with `VisionToolSchema` as structured output. Public entry: `vision_agent(prompt, image_path) -> dict`.
- **`ai/agents/vision_agent/config/`** — YAML configs. Task template uses `{prompt}` and `{image_path_url}` as input variables (note: `image_path_url`, not `image_path`).

### Output Schema (`VisionToolSchema`)
- `objects: list[str]` — detected objects
- `hazards: list[str]` — detected hazards
- `is_safe_to_land: bool` — safe to land at current position
- `target_found: bool` — whether the target (blue circle) is visible
- `distance_from_obstacles: list[ObstaclesSchema]` — each has `obstacle_name` and `distance_to_obstacle`
- `move_to: Movements` — directional suggestion (`RIGHT/LEFT/UP/DOWN/FORWARD/BACKWARD`)

### Adding a New Agent
Follow the `vision_agent` pattern:
1. Create `ai/agents/<name>/` with `crew.py`, `tools/`, and `config/agents.yaml` + `config/tasks.yaml`.
2. Subclass `AgentInfrastructure` and decorate with `@CrewBase`.
3. Define `@agent`, `@task`, and `@crew` methods.
4. Use `ai/agents/vision_agent/tools/custom_tool.py` as a tool template (subclass `BaseTool`).
