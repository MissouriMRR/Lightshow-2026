from dataclasses import dataclass, field
import time

import dronekit
from opengl_station import DroneStatus

from interdrone.message_types import MessageType


@dataclass
class DroneState:
    # Prearm checks
    # VerticalSpeed
    # Battery
    # State?

    pos: dronekit.LocationGlobalRelative = dronekit.LocationGlobalRelative(0, 0, 0)
    status: DroneStatus = DroneStatus.DISCONNECTED
    frame: int = -1
    battery: float = 0.0
    _lines: list[tuple[int, str]] = field(default_factory=lambda: [])
    min_line: int = 7
    state: DroneStatus = DroneStatus.DISCONNECTED
    last_heartbeat: float = field(default_factory=time.time)
    is_responsive: bool = False
    pending_confirmation: MessageType | None = None
    pending_confirmation_time: float = 0.0

    def add_line(self, line: tuple[int, str]):
        self.min_line = min(line[0], self.min_line)
        self._lines.append(line)

    def get_lines(self):
        return self._lines
