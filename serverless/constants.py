from typing import Any, List, Literal, Optional, Union
from pydantic import BaseModel
from mediapipe.python.solutions import pose

type FacingDirection = Union[Literal["left"], Literal["right"]]
type ProcessType = Union[Literal["video", "photo"]]

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

class Frame(BaseModel):
    knee_angle: float
    elbow_angle: float
    joints: Any

class VideoData(BaseModel):
    frames: List[Frame]
    facing_direction: FacingDirection


class PhotoData(BaseModel):
    highest_point: float
    lowest_point: float


class Result(BaseModel):
    height: int
    width: int
    data: Any


class FrameObject(BaseModel):
    width: int
    height: int


class ProcessingResult(BaseModel):
    success: bool
    error: Optional[str] = None
    result: Optional[Result] = None
