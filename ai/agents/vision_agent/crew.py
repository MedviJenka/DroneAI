from typing import Literal
from crewai import Crew
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel, Field
from crewai import Agent, Task
from ai.config import AgentInfrastructure
from ai.agents.vision_agent.tools.custom_tool import TargetFinderTool


type Movements    = Literal['RIGHT', 'LEFT', 'UP', 'DOWN', 'FORWARD', 'BACKWARD', 'ROTATE']
type FramePos     = Literal['center', 'left', 'right', 'top', 'bottom', 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'not_visible']
type TargetSize   = Literal['not_visible', 'small', 'medium', 'large']
type FlightPhase  = Literal['search', 'approach', 'position_overhead', 'confirm_overhead', 'land']


class ObstaclesSchema(BaseModel):
    obstacle_name:        str   = Field(..., description='obstacle name')
    distance_to_obstacle: float = Field(..., description='approximate distance from and to the obstacles')


class VisionToolSchema(BaseModel):
    scene_summary:           str                   = Field(...,                  description='one-sentence summary of what the drone camera currently sees')
    flight_phase:            FlightPhase           = Field(...,                  description='current phase of navigation: search / approach / position_overhead / confirm_overhead / land')
    objects:                 list[str]             = Field(default_factory=list, description='all objects visible in the camera feed')
    hazards:                 list[str]             = Field(default_factory=list, description='hazards that could interfere with landing')
    distance_from_obstacles: list[ObstaclesSchema] = Field(...,                  description='estimated distance to each visible obstacle')
    target_found:            bool                  = Field(...,                  description='whether the target landing pad is visible in the frame')
    target_position:         FramePos              = Field(...,                  description='position of the target in the camera frame; not_visible if target_found=False')
    target_size:             TargetSize            = Field(...,                  description='apparent size of the target in frame — indicates proximity; not_visible if target_found=False')
    move_to:                 Movements             = Field(default=None,         description='direction to move next; None if landing')
    camera_angle:            int                   = Field(default=0,            description='incremental camera tilt in degrees: negative=tilt down toward ground, positive=tilt up, 0=no change')
    is_safe_to_land:         bool                  = Field(...,                  description='True only when camera is pointing down, target is centered and large in frame')


@CrewBase
class VisionAgent(AgentInfrastructure):

    def manager_agent(self) -> Agent:
        return Agent(config=self.agents_config['manager_agent'], tools=[TargetFinderTool()], llm=self.llm, verbose=True)

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
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
            manager_agent=self.manager_agent(),
            manager_llm=self.llm,
        )


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
