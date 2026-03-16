import base64
from typing import Type

from crewai import LLM
from crewai.tools import BaseTool
from crewai.utilities.types import LLMMessage
from pydantic import BaseModel, Field, PrivateAttr

from settings import Config


class TargetFinderInput(BaseModel):
    drone_image_path: str = Field(..., description="Path to the current drone camera frame.")
    target_image_path: str = Field(..., description="Path to the target sample image to find and land on.")


class TargetFinderTool(BaseTool):
    name: str = "Target Finder Tool"
    description: str = (
        "Compares the drone's current camera frame against a target sample image. "
        "Determines whether the target is visible, where it is in the frame, and "
        "which direction the drone should move to center on it and land."
    )
    args_schema: Type[BaseModel] = TargetFinderInput

    _llm: LLM | None = PrivateAttr(default=None)

    @property
    def llm(self) -> LLM:
        if self._llm is None:
            self._llm = LLM(model="gpt-4o", api_key=Config.OPENAI_API_KEY, temperature=0.0)
        return self._llm

    def _run(self, drone_image_path: str, target_image_path: str) -> str:
        target_b64 = self._encode(target_image_path)
        drone_b64 = self._encode(drone_image_path)

        messages: list[LLMMessage] = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "IMAGE 1 — this is the TARGET (landing pad) you must find and land on:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{target_b64}"}},
                    {"type": "text", "text": "IMAGE 2 — this is the current drone camera feed:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{drone_b64}"}},
                    {
                        "type": "text",
                        "text": (
                            "Analyze Image 2 to answer:\n"
                            "1. Is the target from Image 1 visible in Image 2? (yes/no)\n"
                            "2. If visible, where is it in the frame? (center / left / right / top / bottom / top-left / top-right / bottom-left / bottom-right)\n"
                            "3. Approximate distance: is the drone directly above it, close, or far?\n"
                            "4. Best direction to move to center the drone over the target (FORWARD/BACKWARD/LEFT/RIGHT/UP/DOWN).\n"
                            "5. Is it safe to land right now? (the target must be centered and no obstacles underneath)\n"
                            "6. List any objects and hazards visible in Image 2.\n"
                            "Respond clearly and concisely."
                        ),
                    },
                ],
            }
        ]

        return self.llm.call(messages=messages)

    @staticmethod
    def _encode(path: str) -> str:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
