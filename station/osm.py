from pathlib import Path
from typing import cast, override

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt, QUrl, Slot
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QResizeEvent,
    QWheelEvent,
)
from PySide6.QtPositioning import QGeoCoordinate
from PySide6.QtQuick import QQuickItem
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtWidgets import QWidget
import dronekit
from opengl_station import DroneStatus


class Overlay(QWidget):
    points: list[tuple[QPoint, tuple[int, int, int]]]

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.points = []

    def set_points(self, points: list[tuple[QPoint, tuple[int, int, int]]]):
        self.points = points

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setBrush(Qt.BrushStyle.SolidPattern)
        for point in self.points:
            painter.setBrush(QColor(*point[1]))
            painter.drawEllipse(point[0], 10, 10)
        painter.end()


# class for type checker
class Map(QQuickItem):
    def fromCoordinate(self, _coord: QGeoCoordinate, _bound: bool) -> QPointF:
        return QPointF(0, 0)

    def toCoordinate(self, _point: QPointF, _bound: bool) -> QGeoCoordinate:
        return QGeoCoordinate(0, 0)


class DronePoint:
    position: QGeoCoordinate
    color: tuple[int, int, int]

    def __init__(self):
        self.position = QGeoCoordinate(0, 0)
        self.color = (255, 0, 0)


class OSM(QQuickWidget):
    map_object: Map
    mouse_down: bool = False

    last: QPoint
    pan_speed: float = 0.01

    overlay: Overlay

    drone_points: dict[int, DronePoint]

    def __init__(self, start: list[float]):
        super().__init__()
        self.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

        qml_path = Path.cwd() / "map.qml"
        self.setSource(QUrl.fromLocalFile(str(qml_path)))

        tmp_map_object = self.rootObject().findChild(QQuickItem, "Map")
        if tmp_map_object is not None:
            self.map_object = cast(Map, tmp_map_object)
            self.map_object.setProperty("center", QGeoCoordinate(start[0], start[1]))
        else:
            raise FileNotFoundError("could not find Map in qml")

        self.overlay = Overlay(self)
        self.drone_points = {}
        self.last = QPoint(0, 0)

    def getSize(self):
        top_left = self.map_object.toCoordinate(QPointF(0, 0), True)
        bottom_right = self.map_object.toCoordinate(
            QPointF(*self.size().toTuple()), True
        )
        return QPointF(
            abs(top_left.longitude() - bottom_right.longitude()),
            abs(top_left.latitude() - bottom_right.latitude()),
        )

    def place_points(self) -> list[tuple[QPoint, tuple[int, int, int]]]:
        return [
            (self.map_object.fromCoordinate(x.position, False).toPoint(), x.color)
            for x in self.drone_points.values()
        ]

    @override
    def wheelEvent(self, e: QWheelEvent):
        zoom_amount = 1 if e.angleDelta().y() > 0 else -1
        current_zoom = self.map_object.property("zoomLevel")
        self.map_object.setProperty(
            "zoomLevel", min(19, max(2, current_zoom + zoom_amount))
        )

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self.mouse_down = True
            QGuiApplication.setOverrideCursor(Qt.CursorShape.OpenHandCursor)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self.mouse_down = False
            QGuiApplication.restoreOverrideCursor()

    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.mouse_down:
            delta = QPointF(event.x(), event.y()) - self.last
            delta.setX(-delta.x() * self.getSize().x() / self.width())
            delta.setY(delta.y() * self.getSize().y() / self.height())

            current: QGeoCoordinate = self.map_object.property("center")
            self.map_object.setProperty(
                "center",
                QGeoCoordinate(
                    current.latitude() + delta.y(), current.longitude() + delta.x()
                ),
            )

            panned = self.map_object.property("center")
            if (
                abs(panned.longitude() - current.longitude()) < 0.000001
                and delta.x() != 0
            ):
                self.map_object.setProperty(
                    "center",
                    QGeoCoordinate(panned.latitude(), -current.longitude() + delta.x()),
                )

        self.last = QPoint(event.x(), event.y())

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        self.overlay.set_points(self.place_points())
        self.overlay.repaint()
        super().paintEvent(event)

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.overlay.setGeometry(self.rect())
        self.overlay.raise_()

    @Slot(int, DroneStatus)
    def drone_status_listener(self, drone_id: int, drone_status: DroneStatus):
        if drone_id not in self.drone_points:
            self.drone_points[drone_id] = DronePoint()

    @Slot(int, dronekit.LocationGlobalRelative)
    def drone_position_listener(self, drone_id: int, position: dronekit.LocationGlobalRelative):
        self.drone_points[drone_id].position = QGeoCoordinate(
            position.lat, position.lon
        )
        self.update()

    @Slot(int, dronekit.LocationGlobalRelative)
    def drone_color_listener(self, drone_id: int, r: int, g: int, b: int):
        self.drone_points[drone_id].color = (r, g, b)
        self.update()
