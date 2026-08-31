import dronekit


class Config:
    frames: list[list[dronekit.LocationGlobalRelative]]
    ips: list[str]

    def __init__(
        self,
        frames: list[list[dronekit.LocationGlobalRelative]],
        ips: list[str],
    ):
        self.frames = frames
        self.ips = ips
