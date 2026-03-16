from typing import Callable

import cv2
from time import sleep
from pathlib import Path
from pydantic import BaseModel
from pysimverse import Drone
from ai.agents.vision_agent.crew import vision_agent
from log import Log


log = Log(name='main-drone')

SAVE_PATH = Path("drone_capture.png")

TARGET_PATH = Path("target.png")

MOVE_DISTANCE = 100


class MoveActions(BaseModel):
    forward:  int = MOVE_DISTANCE
    backward: int = MOVE_DISTANCE
    left:     int = MOVE_DISTANCE
    right:    int = MOVE_DISTANCE
    up:       int = MOVE_DISTANCE
    down:     int = MOVE_DISTANCE
    rotate:   int = MOVE_DISTANCE

    def action_map(self) -> dict[str, Callable[[Drone], None]]:
        return {
            "FORWARD": lambda d: d.move_forward(self.forward),
            "BACKWARD": lambda d: d.move_backward(self.backward),
            "LEFT": lambda d: d.move_left(self.left),
            "RIGHT": lambda d: d.move_right(self.right),
            "UP": lambda d: d.move_up(self.up),
            "DOWN": lambda d: d.move_down(self.down),
            "ROTATE": lambda d: d.rotate(angle=self.rotate),
        }


actions = MoveActions()


def execute_movement(drone: Drone, move_to: str | None):
    if not move_to:
        return

    action = actions.action_map().get(move_to.upper())

    if action:
        log.fire.info(f"Moving: {move_to}")
        action(drone)
    else:
        log.fire.error(f"Unknown direction: {move_to}")


def capture_frame(drone: Drone):
    frame, success = drone.get_frame()
    if not success:
        log.fire.error('failed to capture image')
        raise RuntimeError("Frame capture failed")
    cv2.imwrite(str(SAVE_PATH), frame)
    return frame


def analyze_environment():
    return vision_agent(image_path=str(SAVE_PATH), target_image_path=str(TARGET_PATH))


def execute_camera(drone: Drone, camera_angle: int = 45):
    if camera_angle != 0:
        log.fire.info(f"Camera tilt: {camera_angle}°")
        drone.rotate_camera(camera_angle)


def drone_loop(initial_altitude: int = 100):
    drone = Drone()
    drone.connect()
    drone.take_off(takeoff_height=initial_altitude)
    drone.streamon()

    try:
        while True:
            frame = capture_frame(drone)

            cv2.imshow("drone", frame)
            cv2.waitKey(1)

            analysis = analyze_environment()

            log.fire.info(f"Scene: {analysis.get('scene_summary')}")
            log.fire.info(f"Phase: {analysis.get('flight_phase')}")
            log.fire.info(f"Target found: {analysis.get('target_found')} | position: {analysis.get('target_position')} | size: {analysis.get('target_size')}")
            log.fire.info(f"Objects: {analysis['objects']}")
            log.fire.info(f"Hazards: {analysis['hazards']}")
            log.fire.info(f"Move: {analysis.get('move_to')} | camera: {analysis.get('camera_angle', 0)}° | safe to land: {analysis['is_safe_to_land']}")

            execute_camera(drone, analysis.get("camera_angle", 0))
            execute_movement(drone, analysis.get("move_to"))

            if analysis["is_safe_to_land"]:
                log.fire.info("Directly above target — landing.")
                drone.land()
                break
            sleep(2)

    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    drone_loop()
