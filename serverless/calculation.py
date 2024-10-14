import mediapipe as mp
import numpy as np
from mediapipe.tasks.python.components.containers.landmark import NormalizedLandmark


def get_knee_angle(landmarks: list[NormalizedLandmark], frame, facing_direction) -> int:
    """
    Extracts the three relevant coordinates for calculating the knee angle from a mediapipe landmark object.
    Args:
        landmarks: Default MediaPipe landmark object
        frame: Object containing width and height of the recorded video frame
        facing_direction: Direction the user is facing from the camera view
    Returns:
        (int): angle of the knee
    """
    mp_pose = mp.solutions.pose
    lm = landmarks
    width = frame.width
    height = frame.height

    if facing_direction == "left":
        hip = [
            lm[mp_pose.PoseLandmark.LEFT_HIP.value].x * width,
            lm[mp_pose.PoseLandmark.LEFT_HIP.value].y * height,
        ]
        knee = [
            lm[mp_pose.PoseLandmark.LEFT_KNEE.value].x * width,
            lm[mp_pose.PoseLandmark.LEFT_KNEE.value].y * height,
        ]
        ankle = [
            lm[mp_pose.PoseLandmark.LEFT_ANKLE.value].x * width,
            lm[mp_pose.PoseLandmark.LEFT_ANKLE.value].y * height,
        ]
    else:
        hip = [
            lm[mp_pose.PoseLandmark.RIGHT_HIP.value].x * width,
            lm[mp_pose.PoseLandmark.RIGHT_HIP.value].y * height,
        ]
        knee = [
            lm[mp_pose.PoseLandmark.RIGHT_KNEE.value].x * width,
            lm[mp_pose.PoseLandmark.RIGHT_KNEE.value].y * height,
        ]
        ankle = [
            lm[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x * width,
            lm[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y * height,
        ]

    hip_array = np.array(hip)
    knee_array = np.array(knee)
    ankle_array = np.array(ankle)

    angle = calculate_angle(hip_array, knee_array, ankle_array)

    return angle


def get_elbow_angle(
    landmarks: list[NormalizedLandmark], frame, facing_direction
) -> int:
    """
    Extracts the three relevant coordinates for calculating the elbow angle from a mediapipe landmark object.
    Args:
        landmarks: Default MediaPipe landmark object
        frame: Object containing width and height of the recorded video frame
        facing_direction: Direction the user is facing from the camera view
    Returns:
        (int): angle of the elbow
    """
    mp_pose = mp.solutions.pose
    lm = landmarks
    width = frame.width
    height = frame.height

    if facing_direction == "left":
        shoulders = [
            lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x * width,
            lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y * height,
        ]
        elbow = [
            lm[mp_pose.PoseLandmark.LEFT_ELBOW.value].x * width,
            lm[mp_pose.PoseLandmark.LEFT_ELBOW.value].y * height,
        ]
        wrist = [
            lm[mp_pose.PoseLandmark.LEFT_WRIST.value].x * width,
            lm[mp_pose.PoseLandmark.LEFT_WRIST.value].y * height,
        ]
    else:
        shoulders = [
            lm[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x * width,
            lm[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y * height,
        ]
        elbow = [
            lm[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x * width,
            lm[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y * height,
        ]
        wrist = [
            lm[mp_pose.PoseLandmark.RIGHT_WRIST.value].x * width,
            lm[mp_pose.PoseLandmark.RIGHT_WRIST.value].y * height,
        ]

    shoulders_array = np.array(shoulders)
    elbow_array = np.array(elbow)
    wrist_array = np.array(wrist)

    angle = calculate_angle(shoulders_array, elbow_array, wrist_array)

    return angle


def calculate_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> int:
    """
    Uses the dot product to calculate the angle between three points. The point of the calculated angle has to be passed as the second parameter.
    Args:
        a: coordinates of the first point
        b: coordinates of the second point (where the angle is measured)
        c: coordinates of the third point

    Returns:
        (int): angle
    """
    v1 = a - b
    v2 = c - b

    dot_product = np.dot(v1, v2)
    magnitude_v1 = np.linalg.norm(v1)
    magnitude_v2 = np.linalg.norm(v2)

    cosine_angle = dot_product / (magnitude_v1 * magnitude_v2)
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)

    angle = np.degrees(np.arccos(cosine_angle))

    return angle


def determine_facing_direction(landmarks: list[NormalizedLandmark]) -> str:
    """
    Determines if the person is facing left or right based on arm positions relative to the shoulders.
    Args:
        landmarks: Default MediaPipe landmark object

    Returns:
    str: 'left' or 'right' depending on the facing direction
    """
    mp_pose = mp.solutions.pose
    lm = landmarks
    r_wrist_x = lm[mp_pose.PoseLandmark.RIGHT_WRIST.value].x
    r_elbow_x = lm[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x
    l_wrist_x = lm[mp_pose.PoseLandmark.LEFT_WRIST.value].x
    l_elbow_x = lm[mp_pose.PoseLandmark.LEFT_ELBOW.value].x

    if l_wrist_x < l_elbow_x:
        return "left"
    elif r_wrist_x > r_elbow_x:
        return "right"
    else:
        return "left"
