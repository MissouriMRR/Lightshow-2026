from typing import override

import opengl_station  # loads opengl_station shared library that the c++ was compiled into
from PySide6.QtGui import QCloseEvent, QColor, QPalette
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from common.drone_state import DroneState
from station.color import Color
from station.drone_display import DroneDisplay
from station.osm import OSM
from station.station_server import StationServer
from station.tab import Tab
from station.telemetry_display import TelemetryDisplay


class Window(QMainWindow):
    """Handles running and communication of the opengl window"""

    station_server: StationServer

    drone_display: DroneDisplay
    osm: OSM
    telemetry: TelemetryDisplay

    tabs_list: list[Tab]
    activeTab: int = 0

    start_frame: list[float]

    def __init__(self, station_server: StationServer):
        super().__init__()

        self.station_server = station_server

        self.tabs_list = []
        self.start_frame = [0, 0, 0]

        self.setWindowTitle("Station")
        self.resize(800, 600)


        self.drone_display = DroneDisplay(self, self.station_server, self.start_frame)
        station_server.drone_status_changed.connect(self.drone_display.drone_status_listener)
        station_server.drone_position_changed.connect(self.drone_display.drone_position_listener)
        station_server.drone_color_changed.connect(self.drone_display.drone_color_listener)

        self.osm = OSM(self.start_frame)
        self.osm.hide()
        station_server.drone_status_changed.connect(self.osm.drone_status_listener)
        station_server.drone_position_changed.connect(self.osm.drone_position_listener)
        station_server.drone_color_changed.connect(self.osm.drone_color_listener)

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

        tabs_widget = Color("grey")
        tabs_widget.setFixedWidth(125)
        tabs_holder = QVBoxLayout()

        main_widget = QWidget()
        main_split = QHBoxLayout()

        main_widget.setLayout(main_split)
        main_split.setSpacing(0)
        main_split.setContentsMargins(0, 0, 0, 0)
        main_split.addWidget(tabs_widget)
        main_split.addWidget(self.drone_display)

        self.tabs_list.append(
            Tab("aqua", main_split, self.drone_display, "Drone View")
        )
        self.tabs_list.append(Tab("orange", main_split, self.osm, "Street View"))

        scroll = QScrollArea()
        scroll.setWidget(self.telemetry)
        scroll.setWidgetResizable(True)
        self.tabs_list.append(Tab("green", main_split, scroll, "Telemetry"))

        tabs_widget.setLayout(tabs_holder)
        tabs_holder.setSpacing(10)
        tabs_holder.setContentsMargins(10, 10, 10, 10)

        i: int = 0
        for tab in self.tabs_list:
            if i == 0:
                tab.setText("-->" + tab.baseText)
            tab.tabPos = i
            tab.tabSignal.connect(self.highlightActiveTab)
            tabs_holder.addWidget(tab)
            i = i + 1
        tabs_holder.addWidget(QWidget())  # Spacer pushing tabs to top

        self.setCentralWidget(main_widget)

    @override
    def closeEvent(self, event: QCloseEvent, /) -> None:
        self.station_server.stop()

    def highlightActiveTab(self, tabNum: int):

        oldTab = self.tabs_list[self.activeTab]
        oldTab.setText(oldTab.baseText)

        self.activeTab = tabNum

        newTab = self.tabs_list[self.activeTab]
        newTab.setText("-->" + newTab.baseText)
