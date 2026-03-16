import cv2
from time import sleep
from pathlib import Path
from pysimverse import Drone
from ai.agents.vision_agent.crew import vision_agent
from log import Log


log = Log(name='main-drone')

SAVE_PATH = Path("drone_capture.png")

MOVE_DISTANCE = 50

MOVE_ACTIONS = {
    "FORWARD": lambda d: d.move_forward(MOVE_DISTANCE),
    "BACKWARD": lambda d: d.move_backward(MOVE_DISTANCE),
    "RIGHT": lambda d: d.move_right(MOVE_DISTANCE),
    "LEFT": lambda d: d.move_left(MOVE_DISTANCE),
    "UP": lambda d: d.move_up(MOVE_DISTANCE),
    "DOWN": lambda d: d.move_down(MOVE_DISTANCE),
    "ROTATE": lambda d: d.rotate(angle=MOVE_DISTANCE),
}


def capture_frame(drone: Drone):
    frame, success = drone.get_frame()
    if not success:
        log.fire.error('failed to capture image')
        raise RuntimeError("Frame capture failed")
    cv2.imwrite(str(SAVE_PATH), frame)
    return frame


def analyze_environment():
    result = vision_agent(
        prompt=(
            "Analyze the drone camera feed. Identify all objects and hazards. "
            "Decide whether it is safe to land. If not safe, suggest the best "
            "direction to move (FORWARD/BACKWARD/LEFT/RIGHT/UP/DOWN/ROTATE) to avoid hazards."
            "find the target and land on it"
        ),
        image_path=str(SAVE_PATH),
    )
    return result


def execute_movement(drone: Drone, move_to: str | None):
    if not move_to:
        return
    action = MOVE_ACTIONS.get(move_to.upper())
    if action:
        log.fire.info(f"Moving: {move_to}")
        action(drone)
    else:
        log.fire.error(f"Unknown direction: {move_to}")


def drone_loop():
    drone = Drone()
    drone.connect()
    drone.take_off(takeoff_height=100)
    drone.streamon()

    try:
        while True:
            frame = capture_frame(drone)

            cv2.imshow("drone", frame)
            cv2.waitKey(1)

            analysis = analyze_environment()

            log.fire.info(f"Objects: {analysis['objects']}")
            log.fire.info(f"Hazards: {analysis['hazards']}")
            log.fire.info(f"Safe to land: {analysis['is_safe_to_land']}")
            log.fire.info(f"Suggested move: {analysis.get('move_to')}")
            log.fire.info(f'is target found? {analysis.get('target_found')}')

            if analysis.get('target_found'):
                if analysis["is_safe_to_land"]:
                    log.fire.info("Safe landing spot found — landing.")
                    drone.land()
                    break

            execute_movement(drone, analysis.get("move_to"))
            sleep(2)

    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    drone_loop()
