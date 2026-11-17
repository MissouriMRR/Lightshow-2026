from math import copysign
from typing import override

from PySide6.QtCore import QEvent, Slot
from PySide6.QtGui import QColor, QPalette
from PySide6.QtPositioning import QGeoCoordinate
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget
import dronekit
import opengl_station

from common.drone_state import DroneState
from common.utils import loc_to_point
from drone.config_parser import ConfigParser
from station.color import Color
from station.point import Point3d
from station.station_server import StationServer


class DroneDisplay(QWidget):
    config: ConfigParser
    opengl_gui: opengl_station.Gui

    furthest_distance: float

    start_frame: list[float]

    station_server: StationServer

    arm_button: QPushButton
    takeoff_button: QPushButton
    step_button: QPushButton
    land_button: QPushButton
    halt_button: QPushButton

    def __init__(self, parent: QWidget | None, station_server: StationServer, start_frame: list[float]):
        super().__init__(parent)

        self.station_server = station_server
        self.config = station_server.config
        self.opengl_gui = opengl_station.Gui(self)

        self.opengl_gui.guiReady.connect(self.populateIps)

        self.furthest_distance = 0

        self.start_frame = start_frame
        self.furthest_distance = self.calc_furthest_distance()


        self.arm_button = QPushButton("arm")
        self.arm_button.clicked.connect(station_server.arm)
        self.arm_button.setMaximumHeight(1000)

        self.takeoff_button = QPushButton("takeoff")
        self.takeoff_button.clicked.connect(station_server.takeoff)
        self.takeoff_button.setMaximumHeight(1000)

        self.step_button = QPushButton("step")
        self.step_button.clicked.connect(station_server.step)
        self.step_button.setMaximumHeight(1000)

        self.land_button = QPushButton("land")
        self.land_button.clicked.connect(station_server.land)
        self.land_button.setMaximumHeight(1000)

        self.halt_button = QPushButton("halt")
        self.halt_button.clicked.connect(station_server.halt)
        self.halt_button.setMaximumHeight(1000)


        buttons_widget = Color("blue")
        buttons_holder = QHBoxLayout()

        buttons_widget.setLayout(buttons_holder)
        buttons_holder.setSpacing(0)
        buttons_holder.setContentsMargins(0, 0, 0, 0)

        buttons_holder.addWidget(self.arm_button)
        buttons_holder.addWidget(self.takeoff_button)
        buttons_holder.addWidget(self.step_button)
        buttons_holder.addWidget(self.land_button)
        buttons_holder.addWidget(self.halt_button)


        drone_view_split = QVBoxLayout()
        self.setLayout(drone_view_split)

        drone_view_split.setSpacing(0)
        drone_view_split.setContentsMargins(0, 0, 0, 0)
        drone_view_split.addWidget(buttons_widget)
        drone_view_split.setStretch(0, 1)
        drone_view_split.addWidget(self.opengl_gui)
        drone_view_split.setStretch(1, 7)

    @Slot()
    def populateIps(self):
        config = self.config
        for id in config.get_drone_ids()[1:]:
            self.opengl_gui.setIp(
                int(id),
                f"{config.get_drone_ip(id)}:{config.get_drone_port(id)}",
            )

    @Slot(int, opengl_station.DroneStatus)
    def drone_status_listener(
        self, drone_id: int
    ):
        self.opengl_gui.setStatus(drone_id, self.station_server.drones[drone_id].status)

    @Slot(int, dronekit.LocationGlobalRelative)
    def drone_position_listener(
        self, drone_id: int
    ):
        """Listens for drone position changes to update opengl window"""
        placed = self.place_in_expanse(loc_to_point(self.station_server.drones[drone_id].pos))
        self.opengl_gui.setPos(drone_id, placed.x, placed.y, placed.z)

    @Slot(int, int, int, int)
    def drone_color_listener(self, drone_id: int):
        color = self.station_server.drones[drone_id].color
        self.opengl_gui.setColor(
            drone_id, color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, 1.0
        )

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

        w = self.config.get_max_width()
        l = self.config.get_max_length()
        h = self.config.get_max_height()

        if w and l and h:
            return max(w, l, h)
        return -1

    def place_in_expanse(self, position: Point3d) -> Point3d:
        """Scales drone positions over precalculated expanse"""

        footed = self.point_to_meters(position)
        scaled = footed / self.furthest_distance
        return scaled * 20
