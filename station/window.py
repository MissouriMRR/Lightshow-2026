from typing import override

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from station.color import Color
from station.drone_display import DroneDisplay
from station.osm_display import OSMDisplay
from station.station_server import StationServer
from station.tab import Tab
from station.telemetry_display import TelemetryDisplay


class Window(QMainWindow):
    """Handles running and communication of the opengl window"""

    station_server: StationServer

    drone_display: DroneDisplay
    osm_display: OSMDisplay
    telemetry_display: TelemetryDisplay

    tabs_list: list[Tab]
    activeTab: int = 0

    def __init__(self, station_server: StationServer):
        super().__init__()

        self.station_server = station_server

        self.tabs_list = []
        maybe_start_frame = self.station_server.config.get_center_coordinates()
        start_frame: list[float]
        if maybe_start_frame:
            start_frame = maybe_start_frame
        else:
            raise RuntimeError("Start frame not found")

        self.setWindowTitle("Station")
        self.resize(800, 600)

        self.drone_display = DroneDisplay(self, self.station_server, start_frame)
        station_server.drone_status_changed.connect(
            self.drone_display.drone_status_listener
        )
        station_server.drone_position_changed.connect(
            self.drone_display.drone_position_listener
        )
        station_server.drone_color_changed.connect(
            self.drone_display.drone_color_listener
        )

        self.osm_display = OSMDisplay(start_frame, self.station_server.drones)
        self.osm_display.hide()
        station_server.drone_status_changed.connect(
            self.osm_display.drone_status_listener
        )
        station_server.drone_position_changed.connect(
            self.osm_display.drone_position_listener
        )
        station_server.drone_color_changed.connect(
            self.osm_display.drone_color_listener
        )

        self.telemetry_display = TelemetryDisplay(self, station_server)
        station_server.drone_status_changed.connect(
            self.telemetry_display.drone_status_listener
        )
        station_server.prearm_passing_changed.connect(
            self.telemetry_display.drone_state_listener
        )
        station_server.status_text_added.connect(
            self.telemetry_display.drone_state_listener
        )
        station_server.battery_changed.connect(
            self.telemetry_display.drone_state_listener
        )

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

        self.tabs_list.append(Tab("aqua", main_split, self.drone_display, "Drone View"))
        self.tabs_list.append(
            Tab("orange", main_split, self.osm_display, "Street View")
        )

        scroll = QScrollArea()
        scroll.setWidget(self.telemetry_display)
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
