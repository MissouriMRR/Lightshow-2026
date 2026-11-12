from enum import Enum

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QWidget

class DroneStatus(Enum):
    DISCONNECTED = 1
    CONNECTED = 2
    ARMED = 3

class GuiReadyEvent(QEvent):
    event_number: int

class Gui(QWidget):
    def setStatus(self, id: int, state: DroneStatus) -> None: ...
    def setPos(self, id: int, x: float, y: float, z: float) -> None: ...
    def setIp(self, id: int, ip: str) -> None: ...
    def setColor(self, id: int, r: float, g: float, b: float, a: float) -> None: ...
