import mediapipe as mp
import numpy as np
from mediapipe.tasks.python.components.containers.landmark import NormalizedLandmark

from config import FacingDirection

class Calculator:
    @staticmethod
    def get_knee_angle(
        landmarks: list[NormalizedLandmark], frame, facing_direction
    ) -> int:
        """
        Calculate the knee angle based on landmarks and facing direction.

        Args:
            landmarks (list[NormalizedLandmark]): A list of normalized landmarks representing body key points.
            frame: The frame object containing width and height attributes.
            facing_direction (str): The direction the subject is facing ("left" or "right").

        Returns:
            int: The calculated knee angle in degrees.

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

        angle = Calculator.calculate_angle(hip_array, knee_array, ankle_array)

        return angle

    @staticmethod
    def get_elbow_angle(
        landmarks: list[NormalizedLandmark], frame, facing_direction
    ) -> int:
        """Calculate the elbow angle based on landmarks and facing direction.

        Args:
            landmarks (list[NormalizedLandmark]): A list of normalized landmarks representing body key points.
            frame: The frame object containing width and height attributes.
            facing_direction (str): The direction the subject is facing ("left" or "right").

        Returns:
            int: The calculated elbow angle in degrees.
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

        angle = Calculator.calculate_angle(shoulders_array, elbow_array, wrist_array)

        return angle

    @staticmethod
    def calculate_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> int:
        """
        Calculate the angle formed by three points in a 2D space.

        Args:
            a (np.ndarray): A 1D array representing the coordinates of the first point.
            b (np.ndarray): A 1D array representing the coordinates of the vertex point.
            c (np.ndarray): A 1D array representing the coordinates of the second point.

        Returns:
            int: The calculated angle in degrees, rounded to the nearest integer.
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

    @staticmethod
    def determine_facing_direction(
        landmarks: list[NormalizedLandmark],
    ) -> FacingDirection:
        """
        Determine the facing direction based on wrist and elbow positions.

        This method analyzes the x-coordinates of the left and right wrists and elbows
        to ascertain whether the subject is facing left or right. It assumes that
        if the left wrist is positioned to the left of the left elbow, the subject
        is facing left, and vice versa for the right side.

        Args:
            landmarks (list[NormalizedLandmark]): A list of normalized pose landmarks
                containing at least the wrist and elbow landmarks.

        Returns:
            FacingDirection: A string indicating the facing direction, either "left" or "right".
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
