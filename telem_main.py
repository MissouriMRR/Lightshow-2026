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
    telemetry.set_drone(0, DroneState())
    telemetry.set_drone(1, DroneState())
    telemetry.set_drone(2, DroneState())
    telemetry.set_drone(3, DroneState())
    telemetry.set_drone(4, DroneState())
    telemetry.set_drone(5, DroneState())
    telemetry.set_drone(6, DroneState())
    telemetry.set_drone(7, DroneState())
    telemetry.set_drone(8, DroneState())
    telemetry.set_drone(9, DroneState())
    telemetry.set_drone(10, DroneState())
    telemetry.set_drone(11, DroneState())
    telemetry.set_drone(12, DroneState())
    telemetry.set_drone(13, DroneState())
    telemetry.set_drone(14, DroneState())
    telemetry.set_drone(15, DroneState())
    telemetry.set_drone(16, DroneState())
    telemetry.set_drone(17, DroneState())
    telemetry.set_drone(18, DroneState())
    telemetry.set_drone(19, DroneState())
    telemetry.set_drone(20, DroneState())
    telemetry.set_drone(21, DroneState())
    telemetry.set_drone(22, DroneState())
    telemetry.set_drone(23, DroneState())
    telemetry.set_drone(24, DroneState())
    telemetry.set_drone(25, DroneState())
    telemetry.set_drone(26, DroneState())
    telemetry.set_drone(27, DroneState())
    telemetry.set_drone(28, DroneState())
    telemetry.set_drone(29, DroneState())
    telemetry.set_drone(30, DroneState())
    telemetry.set_drone(31, DroneState())
    telemetry.set_drone(32, DroneState())
    telemetry.set_drone(33, DroneState())
    telemetry.set_drone(34, DroneState())
    telemetry.set_drone(35, DroneState())
    telemetry.set_drone(36, DroneState())
    telemetry.set_drone(37, DroneState())
    telemetry.set_drone(38, DroneState())
    telemetry.set_drone(39, DroneState())
    telemetry.set_drone(40, DroneState())
    telemetry.set_drone(41, DroneState())
    telemetry.set_drone(42, DroneState())
    telemetry.set_drone(43, DroneState())
    telemetry.set_drone(44, DroneState())
    telemetry.set_drone(45, DroneState())
    telemetry.set_drone(46, DroneState())
    telemetry.set_drone(47, DroneState())
    telemetry.set_drone(48, DroneState())
    telemetry.set_drone(49, DroneState())
    telemetry.set_drone(50, DroneState())
    telemetry.set_drone(51, DroneState())
    telemetry.set_drone(52, DroneState())
    telemetry.set_drone(53, DroneState())

    scroll.setWidget(telemetry)
    scroll.setWidgetResizable(True)

    window.setCentralWidget(scroll)

    window.show()
    app.exec()

if __name__ == "__main__":
    main()
