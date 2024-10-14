import cv2
import numpy as np
from mediapipe.python.solutions import pose

import constants
# from serverless.calculation import calculate_angle


def draw_knee_angle_arc(frame, hip, knee, ankle):
    """
    Draw the minor arc at the knee joint.
    Always draws the smaller angle between the segments.

    Args:
        frame: The video frame to draw on
        hip: (x, y) coordinates of the hip landmark (normalized)
        knee: (x, y) coordinates of the knee landmark (normalized)
        ankle: (x, y) coordinates of the ankle landmark (normalized)
    """
    h, w = frame.shape[:2]
    knee_px = (int(knee[0] * w), int(knee[1] * h))

    thigh_vector = np.array([hip[0] * w - knee[0] * w, hip[1] * h - knee[1] * h])
    shin_vector = np.array([ankle[0] * w - knee[0] * w, ankle[1] * h - knee[1] * h])

    thigh_length = np.linalg.norm(thigh_vector)
    shin_length = np.linalg.norm(shin_vector)

    radius = int(min(thigh_length, shin_length) * 0.3)

    start_angle = np.degrees(np.arctan2(thigh_vector[1], thigh_vector[0]))
    end_angle = np.degrees(np.arctan2(shin_vector[1], shin_vector[0]))

    start_angle = start_angle % 360
    end_angle = end_angle % 360

    diff1 = (end_angle - start_angle) % 360
    diff2 = (start_angle - end_angle) % 360

    if diff1 <= diff2:
        arc_start = start_angle
        arc_end = start_angle + diff1
    else:
        arc_start = end_angle
        arc_end = end_angle + diff2

    cv2.ellipse(
        frame,
        center=knee_px,
        axes=(radius, radius),
        angle=0,
        startAngle=arc_start,
        endAngle=arc_end,
        color=constants.ANGLE_COLOR,
        thickness=2,
        lineType=cv2.LINE_AA,
    )


def draw_wireframe(frame, landmarks, facing_direction):
    """
    Draw only the left side of the body, including detailed foot visualization.
    Args:
        frame: The video frame to draw on
        landmarks: calculated landmarks of the person
    """
    for connection in constants.BODY_CONNECTIONS[facing_direction]:
        start_idx, end_idx = connection
        start = landmarks[start_idx]
        end = landmarks[end_idx]

        start_coords = (int(start.x * frame.shape[1]), int(start.y * frame.shape[0]))
        end_coords = (int(end.x * frame.shape[1]), int(end.y * frame.shape[0]))

        cv2.line(
            frame,
            start_coords,
            end_coords,
            constants.LINE_COLOR,
            3,
            lineType=cv2.LINE_AA,
        )

    for idx in constants.BODY_LANDMARKS[facing_direction]:
        landmark = landmarks[idx]
        coords = (int(landmark.x * frame.shape[1]), int(landmark.y * frame.shape[0]))
        overlay = frame.copy()
        cv2.circle(overlay, coords, 10, constants.JOINT_COLOR, -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    if facing_direction == "left":
        hip = landmarks[pose.PoseLandmark.LEFT_HIP]
        knee = landmarks[pose.PoseLandmark.LEFT_KNEE]
        ankle = landmarks[pose.PoseLandmark.LEFT_ANKLE]
    else:
        hip = landmarks[pose.PoseLandmark.RIGHT_HIP]
        knee = landmarks[pose.PoseLandmark.RIGHT_HIP]
        ankle = landmarks[pose.PoseLandmark.RIGHT_ANKLE]

    hip_coords = (hip.x, hip.y)
    knee_coords = (knee.x, knee.y)
    ankle_coords = (ankle.x, ankle.y)

    # angle = calculate_angle(hip_array, knee_array, ankle_array)
    draw_knee_angle_arc(frame, hip_coords, knee_coords, ankle_coords)
