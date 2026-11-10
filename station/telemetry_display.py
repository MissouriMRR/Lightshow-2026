from typing import Callable, cast, override

from PySide6.QtCore import QEvent, QModelIndex, QObject, QPersistentModelIndex, QPoint, QSize, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPaintEvent, QPainter, QPalette, QRegion
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListView, QListWidget, QListWidgetItem, QPushButton, QSizePolicy, QStyle, QStyleOptionViewItem, QStyledItemDelegate, QVBoxLayout, QWidget
from opengl_station import DroneStatus

from common.drone_state import DroneState

from pymavlink import mavutil


class DroneNotFoundError(Exception):
    pass


class SmallLabel(QLabel):
    def __init__(self, text: str | None):
        super().__init__(text)

        self.setSizePolicy(
                QSizePolicy.Policy.Fixed,
                QSizePolicy.Policy.Fixed,
                )


class ClickFilter(QObject):
    f: Callable[[], None]

    def __init__(self, parent: QObject, f: Callable[[], None]):
        super().__init__(parent)
        self.f = f

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress:
            self.f()
            return True

        return super().eventFilter(watched, event)


class DroneTelemetry(QWidget):
    id: int
    state: DroneState
    messageLayout: QVBoxLayout

    base: QWidget
    arrow: SmallLabel

    info: QWidget

    stateLabel: QLabel
    battLabel: QLabel

    item: QListWidgetItem

    def __init__(self, parent: QWidget, id: int, state: DroneState, item: QListWidgetItem):
        super().__init__(parent)

        self.id = id
        self.state = state
        self.item = item

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

        self.base = QWidget()
        self.setSeverityColor(self.base, self.state.min_line)
        self.base.installEventFilter(ClickFilter(self, self.onClick))

        baseLayout = QHBoxLayout()
        self.base.setLayout(baseLayout)
        baseLayout.setSpacing(0)
        baseLayout.setContentsMargins(0, 0, 0, 0)
        baseLayout.addWidget(SmallLabel(str(id)))

        baseLayout.addStretch()

        self.arrow = SmallLabel("\\/")
        baseLayout.addWidget(self.arrow)

        layout.addWidget(self.base)

        messages = QWidget()
        self.messageLayout = QVBoxLayout()
        messages.setLayout(self.messageLayout)
        self.messageLayout.setSpacing(0)
        self.messageLayout.setContentsMargins(0, 0, 0, 0)

        statuses = QWidget()
        statuses_layout = QHBoxLayout()
        statuses_layout.setSpacing(0)
        statuses_layout.setContentsMargins(0, 0, 0, 0)
        statuses.setLayout(statuses_layout)

        self.stateLabel = SmallLabel("")
        self.battLabel = SmallLabel("")

        statuses_layout.addWidget(SmallLabel("STATUS: "))
        statuses_layout.addWidget(self.stateLabel)
        statuses_layout.addWidget(QWidget())
        statuses_layout.addWidget(SmallLabel("BATT: "))
        statuses_layout.addWidget(self.battLabel)

        self.info = QWidget()
        infoLayout = QVBoxLayout()
        infoLayout.setSpacing(0)
        infoLayout.setContentsMargins(0, 0, 0, 0)
        self.info.setLayout(infoLayout)

        infoLayout.addWidget(statuses)
        infoLayout.addWidget(messages)

        layout.addWidget(self.info)

        self.info.hide()
        self.item.setData(Qt.ItemDataRole.UserRole, self.state.min_line)

    def setSeverityColor(self, widget: QWidget, severity: int) -> None:
        color: str
        if severity <= mavutil.mavlink.MAV_SEVERITY_ERROR:
            color = "red"
        elif severity == mavutil.mavlink.MAV_SEVERITY_WARNING:
            color = "yellow"
        else:
            color = "white"
        widget.setStyleSheet(f"background-color: {color};")

    @override
    def paintEvent(self, event: QPaintEvent, /) -> None:
        self.item.setData(Qt.ItemDataRole.UserRole, self.state.min_line)

        self.stateLabel.setText(["DISCONNECTED", "CONNECTED", "ARMED"][self.state.status.value])
        self.battLabel.setText(f"{self.state.battery:.1f}")

        self.setSeverityColor(self.base, self.state.min_line)

        lines = self.state.get_lines()
        for i in range(len(lines)):
            item = self.messageLayout.itemAt(i)
            widget: QLabel
            if item is None:
                widget = QLabel()
                widget.setAutoFillBackground(True)
                self.messageLayout.addWidget(widget)
            else:
                widget = item.widget()  # pyright: ignore[reportAssignmentType]
            
            severity, msg = lines[i]
            widget.setText(msg)

            self.setSeverityColor(widget, severity)

    def onClick(self) -> None:
        self.info.setVisible(not self.info.isVisible())
        self.item.setSizeHint(self.sizeHint())
        self.item.listWidget().updateGeometries()

        self.arrow.setText("/\\" if self.info.isVisible() else "\\/")


class DroneTelemetryItem(QListWidgetItem):
    @override
    def __lt__(self, other: QListWidgetItem):
        return self.data(Qt.ItemDataRole.UserRole) < other.data(Qt.ItemDataRole.UserRole)


class TelemetryDisplay(QListWidget):
    drones: dict[int, DroneTelemetry]

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.drones = {}
        self.setSortingEnabled(True)

    def add_drone(self, drone_id: int, state: DroneState):
        item = DroneTelemetryItem()
        item.setData(Qt.ItemDataRole.UserRole, 7)
        self.addItem(item)

        widget = DroneTelemetry(self, drone_id, state, item)
        item.setSizeHint(widget.sizeHint())

        self.setItemWidget(item, widget)

        self.drones[drone_id] = widget
