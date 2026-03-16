from crewai import Crew, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import VisionTool
from pydantic import BaseModel, Field
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


class VisionToolSchema(BaseModel):
    objects:         list[str] = Field(default_factory=list, description='describe what do you see in camera')
    hazards:         list[str] = Field(default_factory=list, description='describe what do hazards are found')
    is_safe_to_land: bool      = Field(...,                  description='in this state, is the drone safe?')


@CrewBase
class VisionAgent(AgentInfrastructure):

    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config['researcher'], tools=[VisionTool()], llm=self.llm, verbose=True)

    @task
    def research_task(self, **kwargs: str) -> Task:
        return Task(config=self.tasks_config['research_task'], output_pydantic=VisionToolSchema, **kwargs)

    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks, verbose=True)


def vision_agent(prompt: str, image_path: str) -> dict:
    return VisionAgent().crew().kickoff(inputs={'prompt': prompt, 'image_path_url': image_path}).pydantic.model_dump()


if __name__ == '__main__':
    print(vision_agent(prompt='hi', image_path=r'C:\Users\medvi\PycharmProjects\PythonProject\drone_capture.png'))
