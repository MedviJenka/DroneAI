from typing import Literal

from crewai import Crew
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel, Field
from crewai import Agent, Task
from ai.config import AgentInfrastructure
from ai.agents.vision_agent.tools.custom_tool import TargetFinderTool


type Movements = Literal['RIGHT', 'LEFT', 'UP', 'DOWN', 'FORWARD', 'BACKWARD', 'ROTATE']


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
    def vision_agent(self) -> Agent:
        return Agent(config=self.agents_config['vision_agent'], tools=[TargetFinderTool()], llm=self.llm, verbose=True)

    @agent
    def pilot_agent(self) -> Agent:
        return Agent(config=self.agents_config['pilot_agent'], tools=[], llm=self.llm, verbose=True)

    @task
    def vision_task(self, **kwargs: str) -> Task:
        return Task(config=self.tasks_config['vision_task'], **kwargs)

    @task
    def pilot_task(self, **kwargs: str) -> Task:
        return Task(config=self.tasks_config['pilot_task'], output_pydantic=VisionToolSchema, **kwargs)

    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks, verbose=True)


def vision_agent(image_path: str, target_image_path: str) -> dict:
    return VisionAgent().crew().kickoff(inputs={
        'image_path_url': image_path,
        'target_image_path': target_image_path,
    }).pydantic.model_dump()


if __name__ == '__main__':
    print(vision_agent(
        image_path=r'C:\Users\medvi\PycharmProjects\PythonProject\drone_capture.png',
        target_image_path=r'C:\Users\medvi\PycharmProjects\PythonProject\target.png',
    ))
