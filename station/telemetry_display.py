from typing import cast, override

from PySide6.QtCore import QEvent
from PySide6.QtGui import QColor, QMouseEvent, QPalette
from PySide6.QtWidgets import QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from common.drone_state import DroneState


class DroneNotFoundError(Exception):
    pass


class DroneTelemetry(QWidget):
    id: int
    state: DroneState
    messages: QWidget
    messageLayout: QVBoxLayout

    def __init__(self, parent: QWidget, id: int, state: DroneState):
        super().__init__(parent)

        self.id = id
        self.state = state

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("purple"))
        self.setPalette(palette)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        layout.addWidget(QLabel(str(id)))

        self.messages = QWidget()
        self.messageLayout = QVBoxLayout()
        self.messages.setLayout(self.messageLayout)
        self.messageLayout.setSpacing(0)
        self.messageLayout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self.messages)

        self.messageLayout.addWidget(QLabel("asdf"))
        self.messageLayout.addWidget(QLabel("asdf"))
        self.messageLayout.addWidget(QLabel("asdf"))
        self.messageLayout.addWidget(QLabel("asdf"))

        self.messages.hide()

    @override
    def mousePressEvent(self, event: QMouseEvent, /) -> None:
        self.messages.setVisible(not self.messages.isVisible())


class TelemetryDisplay(QWidget):
    drones: dict[int, DroneTelemetry]
    hbox: QVBoxLayout

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.drones = {}
        self.hbox = QVBoxLayout()
        self.hbox.setSpacing(0)
        self.hbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.hbox)

        self.hbox.addWidget(QWidget())

    def set_drone(self, drone_id: int, state: DroneState):
        drone = self.drones.get(drone_id)
        if drone is None:
            widget = DroneTelemetry(self, drone_id, state)
            self.drones[drone_id] = widget
            self.hbox.insertWidget(self.hbox.count() - 1, widget)
        else:
            drone.state = state
