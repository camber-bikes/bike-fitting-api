import asyncio
from typing import TypedDict
from math import sqrt
import uuid
import numpy as np


from google.protobuf.internal.containers import RepeatedCompositeFieldContainer
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import engine
from app.dbmodels import (
    FacingDirection,
    Frame,
    Person,
    Photo,
    PhotoResult,
    Scan,
    ScanResult,
    Status,
    Video,
    VideoResult,
)


class DirectedPoints(TypedDict):
    ANKLE: int
    KNEE: int
    HIP: int


class Selector(TypedDict):
    left: DirectedPoints
    right: DirectedPoints


class Point(BaseModel):
    x: int
    y: int

    def to_np(self) -> np.ndarray:
        """
        Convert the Point object to a NumPy array.
        """

        return np.array([self.x, self.y])


CYCLING_KNEE_RANGE = (140, 150)
BEST_CYCLING_KNEE_ANGLE = 142.5

SELECTORS: Selector = {
    "left": {
        "ANKLE": 27,  # pose.PoseLandmark.LEFT_ANKLE.value,
        "KNEE": 25,  # pose.PoseLandmark.LEFT_KNEE.value,
        "HIP": 23,  # pose.PoseLandmark.LEFT_HIP.value,
    },
    "right": {
        "ANKLE": 28,  # pose.PoseLandmark.RIGHT_ANKLE.value,
        "KNEE": 26,  # pose.PoseLandmark.RIGHT_KNEE.value,
        "HIP": 24,  # pose.PoseLandmark.RIGHT_HIP.value,
    },
}

TIMEOUT_AFTER_S = 120
REFETCH_EVERY_S = 1


async def wait_until_both_ready(session: AsyncSession, scan_id: int) -> None:
    """
    Wait until both the photo and video processing are done.

    Args:
        session: The database session.
        scan_id: The ID of the scan.

    Raises:
        TimeoutException: If the status check exceeds the timeout.
    """

    gathered = asyncio.gather(
        wait_until_photo_ready(session, scan_id),
        wait_until_video_ready(session, scan_id),
    )
    await asyncio.wait_for(gathered, timeout=TIMEOUT_AFTER_S)


async def wait_until_photo_ready(session: AsyncSession, scan_id: int) -> None:
    """
    Wait until the photo processing is done.
    """

    status = await get_photo_status(session, scan_id)
    while status != Status.done:
        await asyncio.sleep(REFETCH_EVERY_S)
        status = await get_photo_status(session, scan_id)


async def wait_until_video_ready(session: AsyncSession, scan_id: int) -> None:
    """
    Wait until the video processing is done.
    """

    status = await get_video_status(session, scan_id)
    while status != Status.done:
        await asyncio.sleep(REFETCH_EVERY_S)
        status = await get_video_status(session, scan_id)


async def get_video_status(session: AsyncSession, scan_id: int) -> Status:
    """
    Retrieve the status of a video associated with a scan.

    Args:
        session: The database session.
        scan_id: The ID of the scan.

    Returns:
        The status of the video.
    """

    video_status = await session.exec(
        select(Video.status).where(Video.scan_id == scan_id)
    )
    video_status = video_status.one()
    return Status[video_status]


async def get_photo_status(session: AsyncSession, scan_id: int) -> Status:
    """
    Retrieve the status of a photo associated with a scan.

    Args:
        session: The database session.
        scan_id: The ID of the scan.

    Returns:
        The status of the photo.
    """

    photo_status = await session.exec(
        select(Photo.status).where(Photo.scan_id == scan_id)
    )
    photo_status = photo_status.one()
    return Status[photo_status]


async def get_video_result(session: AsyncSession, scan_id: int) -> VideoResult:
    """
    Retrieve the video processing result for a specific scan.

    Args:
        session: The database session.
        scan_id: The ID of the scan.

    Returns:
        The video result.

    Raises:
        Exception: If no result is found.
    """

    res = await session.exec(
        select(Video.process_result).where(Video.scan_id == scan_id)
    )
    result: VideoResult | None = res.first()
    if result is None:
        raise Exception(f"no result of video, scan_id: {scan_id}")

    return result


async def get_photo_result(session: AsyncSession, scan_id: int) -> PhotoResult:
    """
    Retrieve the photo processing result for a specific scan.

    Args:
        session: The database session.
        scan_id: The ID of the scan.

    Returns:
        The photo result.

    Raises:
        Exception: If no result is found.
    """

    res = await session.exec(
        select(Photo.process_result).where(Photo.scan_id == scan_id)
    )
    result: PhotoResult | None = res.first()
    if result is None:
        raise Exception(f"no result of photo, scan_id: {scan_id}")

    return result


async def get_person(session: AsyncSession, scan: Scan) -> Person:
    """
    Retrieve the person associated with a scan.

    Args:
        session: The database session.
        scan: The Scan object.

    Returns:
        The Person object.
    """

    res = await session.exec(select(Person).where(Person.id == scan.person_id))
    return res.one()


async def get_scan(session: AsyncSession, scan_uuid: uuid.UUID) -> Scan:
    """
    Retrieve the scan object using a scan UUID.

    Args:
        session: The database session.
        scan_uuid: The UUID of the scan.

    Returns:
        The Scan object.
    """

    res = await session.exec(select(Scan).where(Scan.uuid == scan_uuid))
    return res.one()


def get_px_to_cm_ratio(person: Person, photo_result: PhotoResult) -> float:
    """
    Calculate the ratio of pixels to centimeters based on the person's height and the photo result.

    Args:
        person: The Person object.
        photo_result: The PhotoResult object.

    Returns:
        The pixel-to-centimeter ratio.
    """

    height = float(person.height_cm)
    pixel_size = float(photo_result["data"][0]) - float(photo_result["data"][1])

    return height / pixel_size


def get_min_max_frames(frames: list[Frame]) -> tuple[Frame, Frame]:
    """
    Find the frames with the minimum and maximum knee angles.

    Args:
        knee_angles: A list of knee angles.

    Returns:
        A tuple containing the indices of the frames with the minimum and maximum angles.
    """

    min_angle = float("inf")
    min_angle_index = -1
    max_angle = -1.0
    max_angle_index = -1
    for i, frame in enumerate(frames):
        angle = frame["knee_angle"]
        if angle < min_angle:
            min_angle = angle
            min_angle_index = i
        if angle > max_angle:
            max_angle = angle
            max_angle_index = i
    return frames[min_angle_index], frames[max_angle_index]


def get_knee_values(
    joints: RepeatedCompositeFieldContainer,
    facing_direction: FacingDirection,
) -> tuple[Point, Point, Point]:
    """
    Get the coordinates of the ankle, knee, and hip points based on the facing direction.

    Args:
        joints: The joint positions.
        facing_direction: The direction the person is facing.

    Returns:
        A tuple of three Points: ankle, knee, and hip.
    """

    foot: Point = joints[SELECTORS[facing_direction]["ANKLE"]]
    knee: Point = joints[SELECTORS[facing_direction]["KNEE"]]
    hip: Point = joints[SELECTORS[facing_direction]["HIP"]]

    return (foot, knee, hip)


def distance_between(a: Point, b: Point) -> float:
    """
    Calculate the Euclidean distance between two points.

    Args:
        a: The first point.
        b: The second point.

    Returns:
        The distance between the two points.
    """

    x_diff = abs(a.x - b.x)
    y_diff = abs(a.y - b.y)

    return sqrt(x_diff**2 + y_diff**2)


def get_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> int:
    """
    Uses the dot product to calculate the angle between three points.
    Args:
        a: coordinates of the first point.
        b: coordinates of the second point (where the angle is measured).
        c: coordinates of the third point.

    Returns:
        The calculated angle in degrees.
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


def is_in_range(x: float, from_to: tuple[float, float]) -> bool:
    """
    Check if a value is within a specified range.

    Args:
        x: The value to check.
        from_to: A tuple representing the range (inclusive).

    Returns:
        True if x is within the range, otherwise False.
    """

    return from_to[0] <= x and x <= from_to[1]


async def run_analysis(scan_uuid: uuid.UUID) -> ScanResult:
    """
    Perform an analysis of a scan to calculate the optimal saddle position.

    Args:
        scan_uuid: The UUID of the scan.

    Returns:
        A dictionary with the calculated saddle position in centimeters.
    """

    async with AsyncSession(engine) as session:
        scan = await get_scan(session, scan_uuid)
        await wait_until_both_ready(session, scan.id)

        photo_result = await get_photo_result(session, scan.id)
        video_result = await get_video_result(session, scan.id)
        person = await get_person(session, scan)

        frames = video_result["data"]["frames"]

        # TODO: check if maybe lowest point of ankle and/or foot is better
        _, max_angle_frame = get_min_max_frames(frames)

        foot, knee, hip = get_knee_values(
            max_angle_frame["joints"],
            video_result["data"]["facing_direction"],
        )

        knee_angle = get_angle(foot.to_np(), knee.to_np(), hip.to_np())

        if is_in_range(knee_angle, CYCLING_KNEE_RANGE):
            return {"saddle_x_cm": 0, "saddle_y_cm": 0}

        thigh_length_px = distance_between(hip, knee)
        lower_leg_length_px = distance_between(knee, foot)

        saddle_vec = Point(x=hip.x - foot.x, y=hip.y - foot.y)
        saddle_vec_length_px = sqrt(saddle_vec.x**2 + saddle_vec.y**2)
        # saddle_vec_angle = np.arccos(saddle_vec.y / saddle_vec.x)

        # use law of cosines
        new_saddle_length_px = sqrt(
            thigh_length_px**2
            + lower_leg_length_px**2
            + 2 * thigh_length_px * lower_leg_length_px * BEST_CYCLING_KNEE_ANGLE
        )
        saddle_length_diff_px = new_saddle_length_px - saddle_vec_length_px

        pixel_to_cm_ratio = get_px_to_cm_ratio(person, photo_result)
        saddle_length_diff_cm = pixel_to_cm_ratio * saddle_length_diff_px
        return {"saddle_x_cm": 0, "saddle_y_cm": saddle_length_diff_cm}