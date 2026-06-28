from crewai import Agent, Task, LLM
from functools import cached_property
from settings import Config
from pydantic import BaseModel
from typing import Optional, Generic, TypeVar
from dataclasses import dataclass
from pathlib import Path


T = TypeVar('T', bound=BaseModel)


@dataclass
class SingleAgent(Generic[T]):

    config: Path = Path('config/agents.yaml')

    def __post_init__(self) -> None:
        self.llm = LLM(model='anthropic/claude-opus-4-6', api_key=Config.ANTHROPIC_API_KEY)

    def run(self, prompt: str, schema: Optional[T] = None) -> any:
        agent = Agent(config=self.config)
        return agent.kickoff(messages=prompt, response_format=schema).pydantic.model_dump() if schema else agent.kickoff(messages=prompt).raw


class AgentInfrastructure:
    def __init__(self,
        agents: list[Agent] = None,
        tasks: list[Task] = None,
        agents_config: dict = "config/agents.yaml",
        tasks_config: dict = "config/tasks.yaml",
        temperature: float = 0.0,
    ) -> None:

        self.agents: list[Agent] = agents
        self.tasks: list[Task] = tasks
        self.agents_config: dict = agents_config
        self.tasks_config: dict = tasks_config
        self.temperature: float = temperature

    @cached_property
    def llm(self) -> LLM:
        return LLM(model='gpt-5.2', api_key=Config.OPENAI_API_KEY, temperature=self.temperature)
