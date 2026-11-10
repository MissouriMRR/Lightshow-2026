from typing import override

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QApplication, QMainWindow, QScrollArea, QWidget

from common.drone_state import DroneState

from station.telemetry_display import DroneTelemetry, TelemetryDisplay

def main() -> None:
    app = QApplication([])

    window = QMainWindow()

    scroll = QScrollArea()

    telemetry = TelemetryDisplay()
    telemetry.add_drone(0, DroneState())
    telemetry.add_drone(1, DroneState())
    telemetry.add_drone(2, DroneState())
    telemetry.add_drone(3, DroneState())
    telemetry.add_drone(4, DroneState())
    telemetry.add_drone(5, DroneState())
    telemetry.add_drone(6, DroneState())
    telemetry.add_drone(7, DroneState())
    telemetry.add_drone(8, DroneState())
    telemetry.add_drone(9, DroneState())
    telemetry.add_drone(10, DroneState())
    telemetry.add_drone(11, DroneState())
    telemetry.add_drone(12, DroneState())
    telemetry.add_drone(13, DroneState())
    telemetry.add_drone(14, DroneState())
    telemetry.add_drone(15, DroneState())
    telemetry.add_drone(16, DroneState())
    telemetry.add_drone(17, DroneState())
    telemetry.add_drone(18, DroneState())
    telemetry.add_drone(19, DroneState())
    telemetry.add_drone(20, DroneState())
    telemetry.add_drone(21, DroneState())
    telemetry.add_drone(22, DroneState())
    telemetry.add_drone(23, DroneState())
    telemetry.add_drone(24, DroneState())
    telemetry.add_drone(25, DroneState())
    telemetry.add_drone(26, DroneState())
    telemetry.add_drone(27, DroneState())
    telemetry.add_drone(28, DroneState())
    telemetry.add_drone(29, DroneState())
    telemetry.add_drone(30, DroneState())
    telemetry.add_drone(31, DroneState())
    telemetry.add_drone(32, DroneState())
    telemetry.add_drone(33, DroneState())
    telemetry.add_drone(34, DroneState())
    telemetry.add_drone(35, DroneState())
    telemetry.add_drone(36, DroneState())
    telemetry.add_drone(37, DroneState())
    telemetry.add_drone(38, DroneState())
    telemetry.add_drone(39, DroneState())
    telemetry.add_drone(40, DroneState())
    telemetry.add_drone(41, DroneState())
    telemetry.add_drone(42, DroneState())
    telemetry.add_drone(43, DroneState())
    telemetry.add_drone(44, DroneState())
    telemetry.add_drone(45, DroneState())
    telemetry.add_drone(46, DroneState())
    telemetry.add_drone(47, DroneState())
    telemetry.add_drone(48, DroneState())
    telemetry.add_drone(49, DroneState())
    telemetry.add_drone(50, DroneState())
    telemetry.add_drone(51, DroneState())
    telemetry.add_drone(52, DroneState())
    telemetry.add_drone(53, DroneState())

    scroll.setWidget(telemetry)
    scroll.setWidgetResizable(True)

    window.setCentralWidget(scroll)

    window.show()
    app.exec()

if __name__ == "__main__":
    main()
