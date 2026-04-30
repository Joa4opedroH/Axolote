from __future__ import annotations

import argparse
from pathlib import Path

from skylimpiadas.config import load_mission_config
from skylimpiadas.hardware.mavlink import DroneKitTelemetryClient, TelemetryClient
from skylimpiadas.mapping.capture import capture_images
from skylimpiadas.scoring import software_score
from skylimpiadas.vision.detector import detect_directory, write_detections


DEFAULT_CONFIG = Path("configs/mission_2026.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="skylimpiadas")
    subparsers = parser.add_subparsers(dest="command", required=True)

    mission_parser = subparsers.add_parser("mission", help="show mission configuration")
    mission_parser.add_argument("config", nargs="?", default=DEFAULT_CONFIG)

    score_parser = subparsers.add_parser("score", help="calculate software score")
    score_parser.add_argument("--mapping", type=int, required=True)
    score_parser.add_argument("--identification", type=int, required=True)
    score_parser.add_argument("--music", type=int, default=0)

    detect_parser = subparsers.add_parser("detect", help="detect bases in a directory")
    detect_parser.add_argument("image_dir")
    detect_parser.add_argument("--config", default=DEFAULT_CONFIG)
    detect_parser.add_argument("--output", default="data/processed/detections.json")

    capture_parser = subparsers.add_parser("capture", help="capture camera images with GPS metadata")
    capture_parser.add_argument("--output", default="data/captures")
    capture_parser.add_argument("--config", default=DEFAULT_CONFIG)
    capture_parser.add_argument("--camera", type=int, default=None)
    capture_parser.add_argument("--interval", type=float, default=None)
    capture_parser.add_argument("--duration", type=float, default=None)
    capture_parser.add_argument("--connection", default=None, help="DroneKit connection string")

    args = parser.parse_args(argv)
    if args.command == "mission":
        config = load_mission_config(args.config)
        print(f"Mission: {config.name}")
        print("Mapping polygon:")
        for lat, lon in config.mapping_polygon:
            print(f"  - {lat}, {lon}")
        print("Targets:")
        for target in config.bases:
            print(f"  - {target.name}: {target.shape}, HSV {target.hsv_lower}..{target.hsv_upper}")
        return 0

    if args.command == "score":
        print(f"{software_score(args.mapping, args.identification, args.music):.2f}")
        return 0

    if args.command == "detect":
        detections = detect_directory(args.image_dir, args.config)
        write_detections(args.output, detections)
        print(f"Wrote {len(detections)} detections to {args.output}")
        return 0

    if args.command == "capture":
        config = load_mission_config(args.config)
        capture_config = config.capture
        telemetry: TelemetryClient
        if args.connection:
            telemetry = DroneKitTelemetryClient(args.connection)
        else:
            telemetry = TelemetryClient()
        count = capture_images(
            output_dir=args.output,
            camera_index=args.camera if args.camera is not None else int(capture_config.get("camera_index", 0)),
            interval_seconds=args.interval if args.interval is not None else float(capture_config.get("interval_seconds", 2.0)),
            duration_seconds=args.duration,
            telemetry=telemetry,
            width=capture_config.get("image_width"),
            height=capture_config.get("image_height"),
        )
        print(f"Captured {count} images in {args.output}")
        return 0

    return 1
