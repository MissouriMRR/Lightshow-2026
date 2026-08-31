import dronekit


class DroneState:
    pos: dronekit.LocationGlobalRelative
    state: dronekit.SystemStatus
    armed: bool
    confirmed: bool
    frame: int

    def __init__(self):
        self.pos = dronekit.LocationGlobalRelative(0, 0, 0)
        self.state = dronekit.SystemStatus("UNINIT")
        self.armed = False
        self.confirmed = True
        self.frame = -1
