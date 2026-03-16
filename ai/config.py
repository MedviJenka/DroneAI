from crewai import LLM
from crewai import Agent, Task
from functools import cached_property
from settings import Config


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
        return LLM(model='gpt-4o', api_key=Config.OPENAI_API_KEY, temperature=self.temperature)
