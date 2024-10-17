from typing import Union, Literal

from mediapipe.python.solutions import pose
from pydantic import BaseModel

# general config
RETRIES = 5

# types
type ProcessType = Union[Literal["photo"], Literal["video"]]
type FacingDirection = Union[Literal["left"], Literal["right"]]


# class
class FrameObject(BaseModel):
    width: int
    height: int


# model config
POSE_LANDMARKER_TASK = "pose_landmarker.task"
SELFIE_SEGMENTER_TFLITE = "selfie_segmenter.tflite"

# color constants to visualize landmarks in video
LINE_COLOR = (255, 0, 136)
JOINT_COLOR = (255, 0, 34)
ANGLE_COLOR = (255, 0, 190)

# landmark collections
BODY_LANDMARKS = {
    "left": [
        pose.PoseLandmark.LEFT_SHOULDER,
        pose.PoseLandmark.LEFT_ELBOW,
        pose.PoseLandmark.LEFT_WRIST,
        pose.PoseLandmark.LEFT_HIP,
        pose.PoseLandmark.LEFT_KNEE,
        pose.PoseLandmark.LEFT_ANKLE,
        pose.PoseLandmark.LEFT_HEEL,
        pose.PoseLandmark.LEFT_FOOT_INDEX,
    ],
    "right": [
        pose.PoseLandmark.RIGHT_SHOULDER,
        pose.PoseLandmark.RIGHT_ELBOW,
        pose.PoseLandmark.RIGHT_WRIST,
        pose.PoseLandmark.RIGHT_HIP,
        pose.PoseLandmark.RIGHT_KNEE,
        pose.PoseLandmark.RIGHT_ANKLE,
        pose.PoseLandmark.RIGHT_HEEL,
        pose.PoseLandmark.RIGHT_FOOT_INDEX,
    ],
}

BODY_CONNECTIONS = {
    "left": [
        (pose.PoseLandmark.LEFT_SHOULDER, pose.PoseLandmark.LEFT_ELBOW),
        (pose.PoseLandmark.LEFT_ELBOW, pose.PoseLandmark.LEFT_WRIST),
        (pose.PoseLandmark.LEFT_SHOULDER, pose.PoseLandmark.LEFT_HIP),
        (pose.PoseLandmark.LEFT_HIP, pose.PoseLandmark.LEFT_KNEE),
        (pose.PoseLandmark.LEFT_KNEE, pose.PoseLandmark.LEFT_ANKLE),
        (pose.PoseLandmark.LEFT_ANKLE, pose.PoseLandmark.LEFT_HEEL),
        (pose.PoseLandmark.LEFT_ANKLE, pose.PoseLandmark.LEFT_FOOT_INDEX),
        (pose.PoseLandmark.LEFT_HEEL, pose.PoseLandmark.LEFT_FOOT_INDEX),
    ],
    "right": [
        (pose.PoseLandmark.RIGHT_SHOULDER, pose.PoseLandmark.RIGHT_ELBOW),
        (pose.PoseLandmark.RIGHT_ELBOW, pose.PoseLandmark.RIGHT_WRIST),
        (pose.PoseLandmark.RIGHT_SHOULDER, pose.PoseLandmark.RIGHT_HIP),
        (pose.PoseLandmark.RIGHT_HIP, pose.PoseLandmark.RIGHT_KNEE),
        (pose.PoseLandmark.RIGHT_KNEE, pose.PoseLandmark.RIGHT_ANKLE),
        (pose.PoseLandmark.RIGHT_ANKLE, pose.PoseLandmark.RIGHT_HEEL),
        (pose.PoseLandmark.RIGHT_ANKLE, pose.PoseLandmark.RIGHT_FOOT_INDEX),
        (pose.PoseLandmark.RIGHT_HEEL, pose.PoseLandmark.RIGHT_FOOT_INDEX),
    ],
}
