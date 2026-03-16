# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DroneAI** — an autonomous drone control system that uses a hierarchical CrewAI multi-agent system to analyze the drone's camera feed and navigate to a target landing pad.

## Commands

This project uses `uv` for dependency management (Python 3.13).

```bash
uv sync                                    # install dependencies
uv run python main.py                      # run the full drone loop
uv run python ai/agents/vision_agent/crew.py  # test the vision crew standalone
uv add <package>                           # add a dependency
```

## Configuration

`settings.py` — `Config` (pydantic-settings) reads `.env`. Both keys required:
- `OPENAI_API_KEY` — used by CrewAI LLM (GPT-4o) and TargetFinderTool
- `LOGFIRE_TOKEN` — used by the `Log` class for structured logging via logfire

## Architecture

### Entry Point (`main.py`)
- `drone_loop()` — connects, takes off, loops: capture frame → analyze → apply camera tilt → execute movement → check landing
- `MoveActions` (Pydantic model) — configurable distances per direction, exposes `action_map() -> dict[str, Callable]`
- `execute_camera(drone, angle)` — calls `drone.rotate_camera(angle)`; negative = tilt down, positive = tilt up
- Landing condition: `is_safe_to_land=True` in the analysis output (checked after executing movement)
- `MOVE_DISTANCE = 100`, `target.png` is the reference landing pad image

### AI Layer (`ai/`)

**`ai/config.py`** — `AgentInfrastructure` base class: wraps `LLM(model='gpt-4o')`, loads `agents_config`/`tasks_config` from YAML, exposes `cached_property` LLM.

**`ai/agents/vision_agent/crew.py`** — `VisionAgent(AgentInfrastructure)` with `@CrewBase`.

Crew runs in **hierarchical process** with a `manager_agent` that orchestrates `vision_agent` and `pilot_agent`:
```python
Crew(agents=..., tasks=..., manager_agent=self.manager_agent(), manager_llm=self.llm, memory=True)
```

Three agents (defined in `agents.yaml`):
| Agent | Tools | Role |
|---|---|---|
| `manager_agent` | `TargetFinderTool` | Orchestrates delegation |
| `vision_agent` | `TargetFinderTool` | Analyzes camera feed vs target |
| `pilot_agent` | none | Decides navigation commands |

Two tasks (defined in `tasks.yaml`):
- `vision_task` → plain text analysis output; agent: `vision_agent`
- `pilot_task` → `VisionToolSchema` structured output; agent: `pilot_agent`; `context: [vision_task]`

**`TargetFinderTool`** (`tools/custom_tool.py`) — sends both `drone_image_path` and `target_image_path` to GPT-4o in a single multi-image call. Returns a 6-point analysis (target visible?, position, distance, direction, safe to land?, hazards).

### Output Schema (`VisionToolSchema`)
- `objects: list[str]`, `hazards: list[str]`
- `is_safe_to_land: bool`
- `distance_from_obstacles: list[ObstaclesSchema]` — each has `obstacle_name`, `distance_to_obstacle`
- `move_to: Movements` — `RIGHT/LEFT/UP/DOWN/FORWARD/BACKWARD/ROTATE`
- `target_found: bool`
- `camera_angle: int` — incremental tilt in degrees (negative = down, 0 = no change)

### Navigation Logic (pilot_task phases)
1. **SEARCH** — target not visible → `ROTATE`, camera stays forward
2. **APPROACH** — target visible in forward camera → `FORWARD` + `camera_angle=-30` to tilt down
3. **POSITION OVERHEAD** — camera at ~-30° to -60°, lateral corrections (LEFT/RIGHT/FORWARD/BACKWARD)
4. **CONFIRM OVERHEAD** — camera ~-90°, target centered → `DOWN` to descend
5. **LAND** — camera down, target centered and large → `is_safe_to_land=True`

### pysimverse Drone API (key methods)
- `drone.rotate_camera(angle)` — tilts camera; sends `angle` as RC `cameraangle` for `abs(angle/40)` seconds
- `drone.rotate(angle)` — yaw rotation; speed `rotation_speed/70`, duration `abs(angle/60)` seconds
- Movement methods: `move_forward/backward/left/right/up/down(distance)` — duration = `distance / speed`
- Default `speed=20`, `rotation_speed=15`

### Adding a New Agent
Follow the `vision_agent` pattern:
1. Create `ai/agents/<name>/` with `crew.py`, `tools/`, `config/agents.yaml`, `config/tasks.yaml`
2. Subclass `AgentInfrastructure`, decorate with `@CrewBase`
3. Define `@agent`, `@task`, `@crew` methods
4. For tools, subclass `BaseTool` from `crewai.tools` (see `custom_tool.py` as template)
