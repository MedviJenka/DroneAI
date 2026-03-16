import cv2
from time import sleep
from pathlib import Path
from pysimverse import Drone
from ai.agents.vision_agent.crew import vision_agent


SAVE_PATH = Path("drone_capture.png")


def capture_frame(drone: Drone):
    frame, success = drone.get_frame()
    if not success:
        raise RuntimeError("Frame capture failed")
    cv2.imwrite(str(SAVE_PATH), frame)
    return frame


def analyze_environment():
    result = vision_agent(
        prompt="Analyze the landing area. Identify objects and hazards.",
        image_path=str(SAVE_PATH)
    )
    return result


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

            print("Objects:", analysis["objects"])
            print("Hazards:", analysis["hazards"])
            print("Safe:", analysis["is_safe_to_land"])

            if analysis["is_safe_to_land"]:
                print("Safe landing detected")
                drone.land()
                break

            sleep(2)

    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    drone_loop()
