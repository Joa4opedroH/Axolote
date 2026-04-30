from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BaseTarget:
    name: str
    shape: str
    hsv_lower: tuple[int, int, int]
    hsv_upper: tuple[int, int, int]
    min_area_px: int


@dataclass(frozen=True)
class MissionConfig:
    name: str
    mapping_polygon: list[tuple[float, float]]
    capture: dict[str, Any]
    bases: list[BaseTarget]
    webodm: dict[str, Any]


def load_mission_config(path: str | Path) -> MissionConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    bases = [
        BaseTarget(
            name=name,
            shape=entry["shape"],
            hsv_lower=tuple(entry["hsv_lower"]),
            hsv_upper=tuple(entry["hsv_upper"]),
            min_area_px=int(entry.get("min_area_px", 300)),
        )
        for name, entry in raw["bases"].items()
    ]
    return MissionConfig(
        name=raw["name"],
        mapping_polygon=[tuple(point) for point in raw["mapping_polygon"]],
        capture=raw.get("capture", {}),
        bases=bases,
        webodm=raw.get("webodm", {}),
    )
