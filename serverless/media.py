import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_py
from mediapipe.tasks.python.vision.core.vision_task_running_mode import (
    VisionTaskRunningMode,
)
from typing import List, Optional, Tuple, Any

from constants import Frame, Result, VideoData, FrameObject, FacingDirection
from calculation import get_knee_angle, get_elbow_angle, determine_facing_direction
from drawing import draw_wireframe


@dataclass
class VideoMetadata:
    """Container for video metadata."""

    width: int
    height: int
    fps: float
    total_frames: int


class FrameProcessor:
    """Handles the processing of individual video frames."""

    def __init__(
        self, frame_obj: FrameObject, mediapipe_processor: "MediaPipeProcessor"
    ):
        self.frame_obj = frame_obj
        self.mediapipe_processor = mediapipe_processor

    def process_frame(
        self, frame: np.ndarray, timestamp_ms: int
    ) -> Optional[Tuple[np.ndarray, Frame]]:
        """
        Processes a single video frame to extract pose landmarks and create a visualization.

        This method applies a dimming effect to the frame, processes it using a
        MediaPipe processor to extract pose landmarks, and then generates a
        visual representation of the landmarks on the frame.

        Args:
            frame (np.ndarray): The input video frame as a NumPy array.
            timestamp_ms (int): The timestamp of the frame in milliseconds.

        Returns:
            Optional[Tuple[np.ndarray, Frame]]: A tuple containing the visualized
            frame and frame data if pose landmarks are detected; otherwise,
            returns None.
        """

        dimmed_frame = cv2.addWeighted(frame, 0.4, np.zeros_like(frame), 0.4, 0)

        results = self.mediapipe_processor.process_frame(frame, timestamp_ms)

        if not results.pose_landmarks:
            return None

        pose_landmarks = results.pose_landmarks[0]

        final_frame, frame_data = self._create_visualization(
            dimmed_frame, pose_landmarks
        )

        return final_frame, frame_data

    def _create_visualization(
        self, dimmed_frame: np.ndarray, pose_landmarks
    ) -> Tuple[np.ndarray, Frame]:
        """
        Creates a visualization of the pose landmarks and calculates relevant metrics.

        This method generates an overlay for the dimmed frame, visualizing the
        pose landmarks and calculating metrics such as knee and elbow angles.
        It combines the original frame with the overlay to produce the final
        visualized frame.

        Args:
            dimmed_frame (np.ndarray): The dimmed video frame as a NumPy array.
            pose_landmarks: The detected pose landmarks used for visualization and
            metric calculation.

        Returns:
            Tuple[np.ndarray, Frame]: A tuple containing the final visualized frame
            and an object containing calculated metrics such as knee and elbow angles.
        """

        overlay = np.zeros_like(dimmed_frame, dtype=np.uint8)

        facing_direction = determine_facing_direction(pose_landmarks)
        draw_wireframe(overlay, pose_landmarks, facing_direction)

        knee_angle = get_knee_angle(
            pose_landmarks, self.frame_obj, facing_direction
        )
        elbow_angle = get_elbow_angle(
            pose_landmarks, self.frame_obj, facing_direction
        )

        result_frame = cv2.addWeighted(dimmed_frame, 1, overlay, 1, 0)

        frame_data = Frame(
            knee_angle=knee_angle, elbow_angle=elbow_angle, joints=pose_landmarks
        )

        return result_frame, frame_data


class VideoWriter:
    """Handles video file writing operations."""

    def __init__(self, output_path: Path, metadata: VideoMetadata):
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore
        self.writer = cv2.VideoWriter(
            str(output_path), fourcc, metadata.fps, (metadata.width, metadata.height)
        )

    def write_frame(self, frame: np.ndarray) -> None:
        """Write a frame to the video file."""
        self.writer.write(frame)

    def close(self) -> None:
        """Close the video writer."""
        self.writer.release()


class MediaPipeProcessor:
    """Handles MediaPipe operations."""

    def __init__(
        self,
        model_path: Path,
        gpu_enabled: bool = False,
        min_pose_confidence: float = 0.8,
        min_tracking_confidence: float = 0.8,
    ):
        base_options = mp_py.BaseOptions(
            model_asset_path=str(model_path),
            delegate=mp.tasks.BaseOptions.Delegate.GPU
            if gpu_enabled
            else mp.tasks.BaseOptions.Delegate.CPU,
        )
        self.options = mp_py.vision.PoseLandmarkerOptions(
            running_mode=VisionTaskRunningMode.VIDEO,
            min_pose_detection_confidence=min_pose_confidence,
            min_tracking_confidence=min_tracking_confidence,
            base_options=base_options,
            output_segmentation_masks=True,
        )
        self.detector = mp_py.vision.PoseLandmarker.create_from_options(self.options)

    def process_frame(self, frame: np.ndarray, timestamp_ms: int):
        """Process a single frame using MediaPipe."""
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)  # type: ignore
        return self.detector.detect_for_video(image, int(timestamp_ms))


class VideoProcessor:
    """Main video processing coordinator."""

    def __init__(self, mediapipe_processor: MediaPipeProcessor, gpu_enabled: bool):
        self.mediapipe_processor = mediapipe_processor
        self.gpu_enabled = gpu_enabled

    def mov_to_mp4(self, input_path: Path, output_path: Path) -> None:
        """
        Converts a MOV file to MP4 format using FFmpeg.

        This method utilizes either GPU-accelerated encoding with NVIDIA NVENC or
        CPU-based encoding with libx264, depending on the GPU availability. It
        constructs the FFmpeg command with appropriate parameters for video quality
        and encoding speed, executes the conversion, and logs the process.

        Args:
            input_path (Path): The path to the input MOV file.
            output_path (Path): The path where the converted MP4 file will be saved.

        Raises:
            RuntimeError: If there is an error during the conversion process.
        """

        try:
            command = ["ffmpeg", "-i", str(input_path)]

            if self.gpu_enabled:
                # GPU-accelerated encoding using NVIDIA NVENC
                # fmt: off
                command.extend(
                    [
                        "-c:v", "h264_nvenc",  # Use NVIDIA GPU encoder
                        "-preset", "p4",  # NVENC preset (p1-p7, p4 is balanced)
                        "-tune", "hq",  # High quality tuning
                        "-rc", "vbr",  # Variable bitrate mode
                        "-cq", "23",  # Quality level (lower = better quality)
                        "-b:v", "0",  # Let NVENC handle bitrate
                        "-maxrate", "130M",  # Maximum bitrate constraint
                        "-bufsize", "130M",  # Buffer size
                    ]
                )
                # fmt: on
            else:
                # CPU-based encoding
                command.extend(["-c:v", "libx264", "-crf", "23", "-preset", "veryfast"])

            command.append(str(output_path))

            result = subprocess.run(command, check=True, capture_output=True, text=True)

            logging.info(
                f"Successfully converted {input_path} to {output_path}, Result: {result}"
            )

            if self.gpu_enabled:
                logging.info("Conversion completed using GPU acceleration (NVENC)")
            else:
                logging.info("Conversion completed using CPU encoding (libx264)")

        except subprocess.CalledProcessError as e:
            logging.error(f"FFmpeg conversion error: {e}")
            logging.error(f"FFmpeg output: {e.stderr}")
            raise RuntimeError("Error converting MOV to MP4")
        except Exception as e:
            logging.error(f"Unexpected error during conversion: {e}")
            raise

    def process_video(self, input_path: Path, output_path: Path) -> Result:
        """
        Process a video file and generate an analyzed output.

        Args:
            input_path (Path): The path to the input video file.
            output_path (Path): The path where the analyzed output will be saved.

        Returns:
            Result: The result of the video processing.

        Raises:
            RuntimeError: If the video file cannot be opened.
        """
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise RuntimeError("Could not open video file")

        try:
            metadata = self._get_video_metadata(cap)
            return self._process_video_frames(cap, output_path, metadata)
        finally:
            cap.release()

    @staticmethod
    def _get_video_metadata(cap: cv2.VideoCapture) -> VideoMetadata:
        """Extract metadata from video capture."""
        return VideoMetadata(
            width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            fps=cap.get(cv2.CAP_PROP_FPS),
            total_frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        )

    def _process_video_frames(
        self, cap: cv2.VideoCapture, output_path: Path, metadata: VideoMetadata
    ) -> Result:
        """
        Process all frames in the video and generate analysis results.

        Args:
            cap (cv2.VideoCapture): The video capture object to read frames from.
            output_path (Path): The path where the analyzed video will be saved.
            metadata (VideoMetadata): Metadata containing video properties like width, height, and fps.

        Returns:
            Result: The result of the video processing, including frame dimensions and analysis data.

        Raises:
            Exception: If an error occurs during frame processing.
        """
        frame_obj = FrameObject(width=metadata.width, height=metadata.height)
        frame_processor = FrameProcessor(frame_obj, self.mediapipe_processor)
        video_writer = VideoWriter(output_path, metadata)
        frames: List[Frame] = []
        facing_direction: FacingDirection = "left"
        timestamp_ms = 0

        try:
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    logging.info("Reached end of video")
                    break

                timestamp_ms += int(1000 / metadata.fps)

                process_result = frame_processor.process_frame(frame, timestamp_ms)

                if process_result is None:
                    video_writer.write_frame(frame)
                    continue

                result_frame, frame_data = process_result
                video_writer.write_frame(result_frame)
                frames.append(frame_data)
                facing_direction = determine_facing_direction(
                    frame_data.joints
                )

            video_data = VideoData(frames=frames, facing_direction=facing_direction)

            return Result(height=metadata.height, width=metadata.width, data=video_data)

        except Exception as e:
            logging.error(f"Error processing video frames: {str(e)}")
            raise
        finally:
            video_writer.close()


class PhotoProcessor:
    """Main photo processing coordinator for segmentation and analysis."""

    def __init__(self, model_path: Path):
        self.model_path = model_path
        self._setup_segmenter()

    def _setup_segmenter(self) -> None:
        """Configure and initialize the MediaPipe segmenter."""
        base_options = mp_py.BaseOptions(model_asset_path=self.model_path)
        options = mp_py.vision.ImageSegmenterOptions(
            running_mode=VisionTaskRunningMode.IMAGE,
            base_options=base_options,
            output_category_mask=True,
        )
        self.segmenter = mp_py.vision.ImageSegmenter.create_from_options(options)

    @staticmethod
    def _get_image_metadata(frame: np.ndarray) -> dict:
        """
        Extract metadata from image frame.

        Args:
            frame (np.ndarray): Input image frame

        Returns:
            dict: Image metadata containing height and width
        """
        return {"height": frame.shape[0], "width": frame.shape[1]}

    @staticmethod
    def _process_mask(mask: Any, frame_shape: tuple) -> np.ndarray:
        """
        Process and normalize the segmentation mask.

        Args:
            mask (np.ndarray): Raw segmentation mask
            frame_shape (tuple): Shape of the original frame

        Returns:
            np.ndarray: Processed and normalized mask
        """
        mask_resized = cv2.resize(mask.numpy_view(), (frame_shape[1], frame_shape[0]))
        return mask_resized.astype(np.float32) / 255.0

    @staticmethod
    def _calculate_points(mask_normalized: np.ndarray, height: int) -> tuple:
        """
        Calculate highest and lowest points from normalized mask.

        Args:
            mask_normalized (np.ndarray): Normalized mask array
            height (int): Image height

        Returns:
            tuple: (highest_point, lowest_point)
        """
        min_y = float("inf")
        max_y = float("-inf")

        for i, row in enumerate(mask_normalized):
            if any(y == 0 for y in row):
                min_y = min(min_y, i)
                max_y = max(max_y, i)

        highest_point = height - min_y
        lowest_point = height - max_y

        logging.info(
            f"Calculated points - Highest: {highest_point}, Lowest: {lowest_point}"
        )
        return highest_point, lowest_point

    def process_photo(self, photo) -> Result:
        """
        Process photo and generate analyzed output.

        Args:
            photo: PhotoFile

        Returns:
            Result: Processing result containing image dimensions and calculated points
        """
        logging.info("Starting photo processing")

        try:
            mp_image = mp.Image.create_from_file(str(photo.local_path))
            frame = cv2.imread(str(photo.local_path))

            metadata = self._get_image_metadata(frame)

            segmentation_result = self.segmenter.segment(mp_image)
            mask = segmentation_result.category_mask

            mask_normalized = self._process_mask(mask, frame.shape)

            highest_point, lowest_point = self._calculate_points(
                mask_normalized, metadata["height"]
            )

            return Result(
                height=metadata["height"],
                width=metadata["width"],
                data=(highest_point, lowest_point),
            )

        finally:
            if os.path.exists(photo.local_path):
                os.remove(photo.local_path)
                logging.info("Deleted temporary photo")
