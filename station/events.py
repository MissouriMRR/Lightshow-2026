import dronekit
from PySide6.QtCore import QEvent


class ArmEvent(QEvent):
    armed: bool
    id: int
    event_number: int = QEvent.registerEventType()

    def __init__(self, id: int, armed: bool):
        super().__init__(QEvent.Type(self.event_number))
        self.armed = armed
        self.id = id


class DronePositionEvent(QEvent):
    position: dronekit.LocationGlobalRelative
    event_number: int = QEvent.registerEventType()
    id: int

    def __init__(self, id: int, position: dronekit.LocationGlobalRelative):
        super().__init__(QEvent.Type(self.event_number))
        self.position = position
        self.id = id


class DroneConnectEvent(QEvent):
    event_number: int = QEvent.registerEventType()
    id: int

    def __init__(self, id: int):
        super().__init__(QEvent.Type(self.event_number))
        self.id = id


class DroneColorEvent(QEvent):
    event_number: int = QEvent.registerEventType()
    id: int
    r: float
    g: float
    b: float
    a: float

    def __init__(self, id: int, r: float, g: float, b: float, a: float):
        super().__init__(QEvent.Type(self.event_number))
        self.id = id
        self.r = r
        self.g = g
        self.b = b
        self.a = a
