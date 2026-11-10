import dronekit
from opengl_station import DroneStatus


class DroneState:
    # Prearm checks
    # VerticalSpeed
    # Battery
    # State?

    pos: dronekit.LocationGlobalRelative
    state: dronekit.SystemStatus
    status: DroneStatus
    confirmed: bool
    frame: int
    battery: float
    _lines: list[tuple[int, str]]
    min_line: int

    def __init__(self):
        self.pos = dronekit.LocationGlobalRelative(0, 0, 0)
        self.state = dronekit.SystemStatus("UNINIT")
        self.status = DroneStatus.DISCONNECTED
        self.confirmed = True
        self.frame = -1
        self.battery = 0.0
        self._lines = []
        self.min_line = 7

    def add_line(self, line: tuple[int, str]):
        self.min_line = min(line[0], self.min_line)
        self._lines.append(line)

    def get_lines(self):
        return self._lines
