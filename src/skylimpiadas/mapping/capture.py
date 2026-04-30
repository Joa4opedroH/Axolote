from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from skylimpiadas.hardware.mavlink import GpsFix, TelemetryClient


def capture_images(
    output_dir: str | Path,
    camera_index: int = 0,
    interval_seconds: float = 2.0,
    duration_seconds: float | None = None,
    telemetry: TelemetryClient | None = None,
    width: int | None = None,
    height: int | None = None,
) -> int:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("Install the optional vision dependencies with .[vision].") from exc

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    telemetry = telemetry or TelemetryClient()

    camera = cv2.VideoCapture(camera_index)
    if width:
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    if height:
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    if not camera.isOpened():
        raise RuntimeError(f"Could not open camera index {camera_index}")

    start = time.monotonic()
    count = 0
    try:
        while duration_seconds is None or time.monotonic() - start < duration_seconds:
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError("Camera frame capture failed")

            timestamp = datetime.now(timezone.utc).isoformat()
            stem = timestamp.replace(":", "").replace("+", "Z")
            image_path = output / f"{stem}.jpg"
            metadata_path = output / f"{stem}.json"
            gps = telemetry.current_gps()

            cv2.imwrite(str(image_path), frame)
            metadata_path.write_text(
                json.dumps(
                    {
                        "image": image_path.name,
                        "timestamp_utc": timestamp,
                        "gps": _gps_to_dict(gps),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            count += 1
            time.sleep(interval_seconds)
    finally:
        camera.release()
        telemetry.close()
    return count


def _gps_to_dict(gps: GpsFix) -> dict[str, float | None]:
    return {"lat": gps.lat, "lon": gps.lon, "alt": gps.alt}
