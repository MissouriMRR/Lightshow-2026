from math import copysign
from typing import cast, override

import dronekit
import opengl_station  # loads opengl_station shared library that the c++ was compiled into
from PySide6.QtCore import QCoreApplication, QEvent, Qt, Signal
from PySide6.QtGui import QColor, QEnterEvent, QMouseEvent, QPalette
from PySide6.QtPositioning import QGeoCoordinate
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLayout,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from common.drone_state import DroneState
from common.utils import loc_to_point, point_to_list
from station.events import (
    ArmEvent,
    DroneColorEvent,
    DroneConnectEvent,
    DronePositionEvent,
)
from station.osm import OSM
from station.point import Point3d
from station.station_server import StationServer
from station.telemetry_display import TelemetryDisplay


class Color(QWidget):
    def __init__(self, color: str):
        super().__init__()

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)


class Tab(QLabel):
    tab_layout: QLayout
    widget: QWidget
    defined_color: str
    tabPos: int = 0
    baseText: str
    hover: bool = False

    tabSignal: Signal = Signal(int)

    def __init__(self, color: str, layout: QLayout, widget: QWidget, tab_text: str):
        super().__init__(color)

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.tab_layout = layout
        self.widget = widget
        self.defined_color = color

        self.baseText = tab_text

        self.setText(tab_text)

        self.setFixedHeight(25)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent):
        if (event.button() == Qt.MouseButton.LeftButton) and (self.hover == True):
            self.updateFillColor("light green")

            current_widget = self.tab_layout.itemAt(self.tab_layout.count() - 1)
            if current_widget is not None:
                to_kill = current_widget.widget()
                if to_kill is not None:
                    self.tab_layout.removeWidget(to_kill)
                    to_kill.hide()
            self.tab_layout.addWidget(self.widget)
            self.widget.show()
            self.tabSignal.emit(self.tabPos)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.updateFillColor("green")

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        self.hover = True
        self.updateFillColor("light green")
        return super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        self.hover = False
        self.updateFillColor(self.defined_color)
        return super().leaveEvent(event)

    # Based on Gemini suggestion
    # Prevents button being highlighted when mouse is not over box
    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self.rect().contains(event.pos()):
            if self.hover:
                self.hover = False
                self.updateFillColor(self.defined_color)
        else:
            if not self.hover:
                self.hover = True
                self.updateFillColor("light green")
        super().mouseMoveEvent(event)

    # mfw Gemini reminds you to refactor
    def updateFillColor(self, color_str: str) -> None:

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color_str))
        self.setPalette(palette)


class OpenGLWindow(QMainWindow):
    """Handles running and communication of the opengl window"""

    station_server: StationServer
    furthest_distance: float

    start_frame: list[float]

    opengl_gui: opengl_station.Gui
    osm: OSM
    telemetry: TelemetryDisplay

    tabsInternalList: list[Tab]
    activeTab: int = 0

    arm_button: QPushButton
    takeoff_button: QPushButton
    step_button: QPushButton
    land_button: QPushButton
    halt_button: QPushButton

    def __init__(self, station_server: StationServer):
        super().__init__()

        self.setWindowTitle("Station")
        self.resize(800, 600)

        self.station_server = station_server
        station_server.set_drone_listeners(
            self.drone_connect_listener,
            self.arm_listener,
            self.drone_position_listener,
            self.drone_color_listener,
        )

        self.tabsInternalList = []

        self.arm_button = QPushButton("arm")
        self.arm_button.clicked.connect(station_server.arm)

        self.takeoff_button = QPushButton("takeoff")
        self.takeoff_button.clicked.connect(station_server.takeoff)

        self.step_button = QPushButton("step")
        self.step_button.clicked.connect(station_server.step)

        self.land_button = QPushButton("land")
        self.land_button.clicked.connect(station_server.land)

        self.halt_button = QPushButton("halt")
        self.halt_button.clicked.connect(station_server.halt)

        mainWidget = QWidget()
        droneViewWidget = QWidget()
        buttonsWidget = Color("blue")

        tabsHolder = Color("grey")
        tabsHolder.setFixedWidth(125)

        self.opengl_gui = opengl_station.Gui()

        self.start_frame = self.calc_center()
        self.osm = OSM(self.start_frame)
        self.osm.hide()

        self.furthest_distance = self.calc_furthest_distance()

        self.telemetry = TelemetryDisplay()
        state = DroneState()
        self.telemetry.add_drone(1, DroneState())
        self.telemetry.add_drone(2, state)
        self.telemetry.add_drone(3, DroneState())
        self.telemetry.add_drone(4, DroneState())
        state.add_line((6, "asdf"))
        state.add_line((5, "what"))
        state.add_line((4, "ohno"))
        state.add_line((3, "ack"))
        state.status = opengl_station.DroneStatus.CONNECTED

        mainBox = QHBoxLayout()
        droneViewSplit = QVBoxLayout()
        buttons = QHBoxLayout()
        tabsHolderLayout = QVBoxLayout()

        mainWidget.setLayout(mainBox)
        mainBox.setSpacing(0)
        mainBox.setContentsMargins(0, 0, 0, 0)
        mainBox.addWidget(tabsHolder)
        mainBox.addWidget(droneViewWidget)

        self.tabsInternalList.append(
            Tab("aqua", mainBox, droneViewWidget, "Drone View")
        )
        self.tabsInternalList.append(Tab("orange", mainBox, self.osm, "Street View"))

        scroll = QScrollArea()
        scroll.setWidget(self.telemetry)
        scroll.setWidgetResizable(True)
        self.tabsInternalList.append(Tab("green", mainBox, scroll, "Telemetry"))

        tabsHolder.setLayout(tabsHolderLayout)
        tabsHolderLayout.setSpacing(10)
        tabsHolderLayout.setContentsMargins(10, 10, 10, 10)

        i: int = 0
        for tabInstance in self.tabsInternalList:
            if i == 0:
                tabInstance.setText("-->" + tabInstance.baseText)
            tabInstance.tabPos = i
            tabInstance.tabSignal.connect(self.highlightActiveTab)
            tabsHolderLayout.addWidget(tabInstance)
            i = i + 1
        tabsHolderLayout.addWidget(QWidget())  # Spacer pushing tabs to top

        droneViewWidget.setLayout(droneViewSplit)
        droneViewSplit.setSpacing(0)
        droneViewSplit.setContentsMargins(0, 0, 0, 0)
        droneViewSplit.addWidget(buttonsWidget)
        droneViewSplit.setStretch(0, 1)
        droneViewSplit.addWidget(self.opengl_gui)
        droneViewSplit.setStretch(1, 7)

        buttonsWidget.setLayout(buttons)
        buttons.setSpacing(0)
        buttons.setContentsMargins(0, 0, 0, 0)

        buttons.addWidget(self.arm_button)
        self.arm_button.setMaximumHeight(1000)

        buttons.addWidget(self.takeoff_button)
        self.takeoff_button.setMaximumHeight(1000)

        buttons.addWidget(self.step_button)
        self.step_button.setMaximumHeight(1000)

        buttons.addWidget(self.land_button)
        self.land_button.setMaximumHeight(1000)

        buttons.addWidget(self.halt_button)
        self.halt_button.setMaximumHeight(1000)

        self.setCentralWidget(mainWidget)

    @override
    def event(self, event: QEvent, /) -> bool:
        match event.type():
            case ArmEvent.event_number:
                event = cast(ArmEvent, event)
                self.opengl_gui.setState(
                    int(event.id),
                    opengl_station.DroneStatus.ARMED
                    if event.armed
                    else opengl_station.DroneStatus.CONNECTED,
                )

            case DroneConnectEvent.event_number:
                event = cast(DroneConnectEvent, event)
                self.opengl_gui.setState(
                    int(event.id), opengl_station.DroneStatus.CONNECTED
                )

            case DronePositionEvent.event_number:
                event = cast(DronePositionEvent, event)
                placed = self.place_in_expanse(loc_to_point(event.position))
                self.opengl_gui.setPos(int(event.id), placed.x, placed.y, placed.z)
                return False

            case DroneColorEvent.event_number:
                event = cast(DroneColorEvent, event)
                self.opengl_gui.setColor(
                    int(event.id), event.r, event.g, event.b, event.a
                )

            case opengl_station.GuiReadyEvent.event_number:
                # add drones to opengl widget
                config = self.station_server.config
                for id in config.get_drone_ids()[1:]:
                    self.opengl_gui.setIp(
                        int(id),
                        f"{config.get_drone_ip(id)}:{config.get_drone_port(id)}",
                    )

            case _:
                return super().event(event)

        return True

    def drone_connect_listener(self, drone_id: str):
        """Listens for drone connection to update opengl window"""
        QCoreApplication.sendEvent(self, DroneConnectEvent(int(drone_id)))

    def arm_listener(self, drone_id: str, armed: bool):
        """Listens for drone arming to update opengl window"""
        QCoreApplication.sendEvent(self, ArmEvent(int(drone_id), armed))

    def drone_position_listener(
        self, drone_id: str, position: dronekit.LocationGlobalRelative
    ):
        """Listens for drone position changes to update opengl window"""
        positionEvent = DronePositionEvent(int(drone_id), position)
        QCoreApplication.sendEvent(self, positionEvent)
        QCoreApplication.sendEvent(self.osm, positionEvent)

    def drone_color_listener(self, drone_id: str, r: int, g: int, b: int):
        colorEvent = DroneColorEvent(
            int(drone_id), r / 255.0, g / 255.0, b / 255.0, 1.0
        )
        QCoreApplication.sendEvent(self, colorEvent)
        QCoreApplication.sendEvent(self.osm, colorEvent)

    def point_to_meters(self, point: Point3d) -> Point3d:
        center = QGeoCoordinate(self.start_frame[0], self.start_frame[1])

        return Point3d(
            QGeoCoordinate(point.x, self.start_frame[1]).distanceTo(center)
            * copysign(1, point.x - self.start_frame[0]),
            point.y,
            QGeoCoordinate(self.start_frame[0], point.z).distanceTo(center)
            * copysign(1, point.z - self.start_frame[1]),
        )

    def calc_furthest_distance(self) -> float:
        """Calculates the maximum distance from center that the drones will achieve"""

        combined = [
            self.point_to_meters(loc_to_point(loc))
            for frame in self.station_server.frames
            for loc in frame
        ]

        return max(
            max([x.x for x in combined]),
            max([x.y for x in combined]),
            max([x.z for x in combined]),
        )

    def place_in_expanse(self, position: Point3d) -> Point3d:
        """Scales drone positions over precalculated expanse"""

        footed = self.point_to_meters(position)
        scaled = footed / self.furthest_distance
        return scaled * 20

    def highlightActiveTab(self, tabNum: int):

        oldTab = self.tabsInternalList[self.activeTab]
        oldTab.setText(oldTab.baseText)

        self.activeTab = tabNum

        newTab = self.tabsInternalList[self.activeTab]
        newTab.setText("-->" + newTab.baseText)

    def calc_center(self) -> list[float]:
        combined = [
            loc_to_point(loc) for frame in self.station_server.frames for loc in frame
        ]

        return point_to_list(sum(combined, start=Point3d(0, 0, 0)) / len(combined))
