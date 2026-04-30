from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from skylimpiadas.config import BaseTarget, load_mission_config


@dataclass(frozen=True)
class Detection:
    target: str
    shape: str
    image: str
    area_px: float
    vertices: int
    centroid_px: tuple[int, int]
    bbox_px: tuple[int, int, int, int]
    confidence: float


def detect_directory(image_dir: str | Path, config_path: str | Path) -> list[Detection]:
    image_dir = Path(image_dir)
    config = load_mission_config(config_path)
    detections: list[Detection] = []
    for image_path in sorted(_iter_images(image_dir)):
        detections.extend(detect_image(image_path, config.bases))
    return detections


def write_detections(path: str | Path, detections: list[Detection]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps([asdict(item) for item in detections], indent=2),
        encoding="utf-8",
    )


def detect_image(image_path: str | Path, targets: list[BaseTarget]) -> list[Detection]:
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Install the optional vision dependencies with .[vision].") from exc

    image_path = Path(image_path)
    image = cv2.imread(str(image_path))
    if image is None:
        raise RuntimeError(f"Could not read image: {image_path}")

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    detections: list[Detection] = []
    for target in targets:
        lower = np.array(target.hsv_lower, dtype=np.uint8)
        upper = np.array(target.hsv_upper, dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)
        mask = cv2.medianBlur(mask, 5)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = float(cv2.contourArea(contour))
            if area < target.min_area_px:
                continue
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
            vertices = len(approx)
            if not _matches_shape(target.shape, vertices):
                continue
            moments = cv2.moments(contour)
            if moments["m00"] == 0:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            detections.append(
                Detection(
                    target=target.name,
                    shape=target.shape,
                    image=image_path.name,
                    area_px=area,
                    vertices=vertices,
                    centroid_px=(int(moments["m10"] / moments["m00"]), int(moments["m01"] / moments["m00"])),
                    bbox_px=(x, y, w, h),
                    confidence=_shape_confidence(target.shape, vertices),
                )
            )
    return detections


def _iter_images(path: Path):
    for suffix in ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"):
        yield from path.glob(suffix)


def _matches_shape(shape: str, vertices: int) -> bool:
    if shape == "triangle":
        return vertices == 3
    if shape == "hexagon":
        return 5 <= vertices <= 7
    return True


def _shape_confidence(shape: str, vertices: int) -> float:
    expected = {"triangle": 3, "hexagon": 6}.get(shape)
    if expected is None:
        return 0.5
    return max(0.0, 1.0 - abs(expected - vertices) / expected)
