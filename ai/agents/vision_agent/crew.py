from typing import Literal

from crewai import Crew, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import VisionTool
from pydantic import BaseModel, Field
from crewai import Agent, Task
from ai.config import AgentInfrastructure


type Movements = Literal['RIGHT', 'LEFT', 'UP', 'DOWN', 'FORWARD', 'BACKWARD']


class ObstaclesSchema(BaseModel):
    obstacle_name: str
    distance_to_obstacle: float


class VisionToolSchema(BaseModel):
    objects:                 list[str]             = Field(default_factory=list, description='describe what do you see in camera')
    hazards:                 list[str]             = Field(default_factory=list, description='describe what do hazards are found')
    is_safe_to_land:         bool                  = Field(...,                  description='in this state, is the drone safe?')
    distance_from_obstacles: list[ObstaclesSchema] = Field(..., description='distance from and to the obstacles')
    move_to:                 Movements             = Field(default=None, description='move if necessary')
    target_found:            bool                  = Field(..., description='target a blue circle')


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
