from math import copysign
from typing import override

from PySide6.QtCore import QEvent, Slot
from PySide6.QtGui import QColor, QPalette
from PySide6.QtPositioning import QGeoCoordinate
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget
import dronekit
import opengl_station

from common.utils import loc_to_point
from drone.config_parser import ConfigParser
from station.color import Color
from station.point import Point3d
from station.station_server import StationServer


class DroneDisplay(QWidget):
    config: ConfigParser
    opengl_gui: opengl_station.Gui

    furthest_distance: float

    frames: list[list[dronekit.LocationGlobalRelative]]
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

        self.furthest_distance = 0

        drone_frames = self.config.get_all_drone_frames()
        drone_values = list(drone_frames.values())
        self.frames = [[] for _ in range(len(drone_values[0]))]
        for drone_index, frame_names in enumerate(drone_values):
            for frame_index, name in enumerate(frame_names):
                location = self.config.get_frame_location(str(drone_index + 1), name)
                if location is None:
                    raise ValueError(
                        f"Frame {name!r} for drone {drone_index + 1} has no coordinates"
                    )
                self.frames[frame_index].append(location)

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

    @override
    def event(self, event: QEvent, /) -> bool:
        match event.type():
            case opengl_station.GuiReadyEvent.event_number:
                # add drones to opengl widget
                config = self.config
                for id in config.get_drone_ids()[1:]:
                    self.opengl_gui.setIp(
                        int(id),
                        f"{config.get_drone_ip(id)}:{config.get_drone_port(id)}",
                    )

            case _:
                return super().event(event)

        return True

    @Slot(int, opengl_station.DroneStatus)
    def drone_status_listener(
        self, drone_id: int, drone_status: opengl_station.DroneStatus
    ):
        self.opengl_gui.setStatus(drone_id, drone_status)

    @Slot(int, dronekit.LocationGlobalRelative)
    def drone_position_listener(
        self, drone_id: int, position: dronekit.LocationGlobalRelative
    ):
        """Listens for drone position changes to update opengl window"""
        placed = self.place_in_expanse(loc_to_point(position))
        self.opengl_gui.setPos(drone_id, placed.x, placed.y, placed.z)

    @Slot(int, int, int, int)
    def drone_color_listener(self, drone_id: int, r: int, g: int, b: int):
        self.opengl_gui.setColor(
            drone_id, r / 255.0, g / 255.0, b / 255.0, 1.0
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

        combined = [
            self.point_to_meters(loc_to_point(loc))
            for frame in self.frames
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

