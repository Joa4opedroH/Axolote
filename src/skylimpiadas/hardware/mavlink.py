from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GpsFix:
    lat: float | None
    lon: float | None
    alt: float | None


class TelemetryClient:
    def current_gps(self) -> GpsFix:
        return GpsFix(lat=None, lon=None, alt=None)

    def close(self) -> None:
        return None


class DroneKitTelemetryClient(TelemetryClient):
    def __init__(self, connection_string: str, wait_ready: bool = False) -> None:
        try:
            from dronekit import connect
        except ImportError as exc:
            raise RuntimeError("Install the optional drone dependencies with .[drone].") from exc
        self._vehicle = connect(connection_string, wait_ready=wait_ready)

    def current_gps(self) -> GpsFix:
        location = self._vehicle.location.global_relative_frame
        return GpsFix(lat=location.lat, lon=location.lon, alt=location.alt)

    def close(self) -> None:
        self._vehicle.close()
