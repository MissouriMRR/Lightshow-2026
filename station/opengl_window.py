from collections.abc import Callable, Iterable
from typing import cast, override

import dronekit
import opengl_station  # loads opengl_station shared library that the c++ was compiled into
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPalette
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from common.utils import loc_to_point
from station.events import ArmEvent, DroneConnectEvent, DronePositionEvent
from station.osm import OSM
from station.point import Point3d
from station.station_server import StationServer


class Color(QWidget):
    def __init__(self, color: str):
        super().__init__()

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)


class Tab(Color):
    tab_layout: QLayout
    widget: QWidget

    def __init__(self, color: str, layout: QLayout, widget: QWidget):
        super().__init__(color)

        self.tab_layout = layout
        self.widget = widget

        self.setFixedHeight(55)

    @override
    def mouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            current_widget = self.tab_layout.itemAt(self.tab_layout.count() - 1)
            if current_widget is not None:
                to_kill = current_widget.widget()
                if to_kill is not None:
                    self.tab_layout.removeWidget(to_kill)
                    to_kill.hide()
            self.tab_layout.addWidget(self.widget)
            self.widget.show()


class OpenGLWindow(QMainWindow):
    """Handles running and communication of the opengl window"""

    station_server: StationServer
    expanse: tuple[Point3d, Point3d]

    opengl_gui: opengl_station.Gui
    osm: OSM

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
            self.drone_connect_listener, self.arm_listener, self.drone_position_listener
        )

        # force minimum y to be 0
        self.expanse = self.calc_expanse()
        tmp = self.expanse[0]
        tmp.y = 0
        self.expanse = (tmp, self.expanse[1])

        self.arm_button = QPushButton("arm")
        self.arm_button.clicked.connect(lambda: self.button_click(station_server.arm))

        self.takeoff_button = QPushButton("takeoff")
        self.takeoff_button.clicked.connect(
            lambda: self.button_click(station_server.takeoff)
        )

        self.step_button = QPushButton("step")
        self.step_button.clicked.connect(lambda: self.button_click(station_server.step))

        self.land_button = QPushButton("land")
        self.land_button.clicked.connect(lambda: self.button_click(station_server.land))

        self.halt_button = QPushButton("halt")
        self.halt_button.clicked.connect(lambda: self.button_click(station_server.halt))

        mainWidget = QWidget()
        buttonWidget = QWidget()
        buttonsWidget = Color("blue")

        tmpTabs = Color("red")
        tmpTabs.setFixedWidth(75)

        self.opengl_gui = opengl_station.Gui()
        self.osm = OSM()
        self.osm.hide()

        mainBox = QHBoxLayout()
        buttonSplit = QVBoxLayout()
        buttons = QHBoxLayout()
        tmpTabsLayout = QVBoxLayout()

        mainWidget.setLayout(mainBox)
        mainBox.setSpacing(0)
        mainBox.setContentsMargins(0, 0, 0, 0)
        mainBox.addWidget(tmpTabs)
        mainBox.addWidget(buttonWidget)

        tmpTabs.setLayout(tmpTabsLayout)
        tmpTabsLayout.setSpacing(10)
        tmpTabsLayout.setContentsMargins(10, 10, 10, 10)
        tmpTabsLayout.addWidget(Tab("blue", mainBox, buttonWidget))
        tmpTabsLayout.addWidget(Tab("orange", mainBox, self.osm))
        tmpTabsLayout.addWidget(QWidget())  # Spacer pushing tabs to top

        buttonWidget.setLayout(buttonSplit)
        buttonSplit.setSpacing(0)
        buttonSplit.setContentsMargins(0, 0, 0, 0)
        buttonSplit.addWidget(buttonsWidget)
        buttonSplit.setStretch(0, 1)
        buttonSplit.addWidget(self.opengl_gui)
        buttonSplit.setStretch(1, 7)

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
                    opengl_station.DroneState.ARMED
                    if event.armed
                    else opengl_station.DroneState.CONNECTED,
                )

            case DroneConnectEvent.event_number:
                event = cast(DroneConnectEvent, event)
                self.opengl_gui.setState(
                    int(event.id), opengl_station.DroneState.CONNECTED
                )

            case DronePositionEvent.event_number:
                event = cast(DronePositionEvent, event)
                placed = self.place_in_expanse(loc_to_point(event.position))
                self.opengl_gui.setPos(int(event.id), placed.x, placed.y, placed.z)
                return False

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

    def button_click(self, function: Callable[[], None]):
        function()

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
        QCoreApplication.sendEvent(self, DronePositionEvent(int(drone_id), position))
        QCoreApplication.sendEvent(
            self.osm, DronePositionEvent(int(drone_id), position)
        )

    def calc_expanse(self) -> tuple[Point3d, Point3d]:
        """Calculates the minimum and maximum positions which the drones will take"""

        combined = [
            loc_to_point(loc) for frame in self.station_server.frames for loc in frame
        ]

        def edge_rel(predicate: Callable[[Iterable[float]], float]) -> Point3d:
            def edge_it(pull: Callable[[Point3d], float]) -> float:
                return predicate(pull(point) for point in combined)

            return Point3d(
                edge_it(lambda p: p.x), edge_it(lambda p: p.y), edge_it(lambda p: p.z)
            )

        return (edge_rel(min), edge_rel(max))

    def place_in_expanse(self, position: Point3d) -> Point3d:
        """Scales drone positions over precalculated expanse"""

        range = self.expanse[1] - self.expanse[0]
        range = range.apply_over_elements(lambda num: 1 if num < 0.0001 else num)
        bounded = position - self.expanse[0]
        scaled = bounded.mult_point_by_elements(1 / range)
        return scaled * 20
