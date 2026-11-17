from __future__ import annotations

from pathlib import Path
from typing import cast, override

from PySide6.QtCore import QPoint, QPointF, Qt, QUrl, Slot
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

from common.drone_state import DroneState

class Overlay(QWidget):
    map: OSMDisplay

    def __init__(self, parent: OSMDisplay):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.map = parent

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setBrush(Qt.BrushStyle.SolidPattern)
        self.map.paint_points(painter)
        painter.end()


# class for type checker
class Map(QQuickItem):
    def fromCoordinate(self, _coord: QGeoCoordinate, _bound: bool) -> QPointF:
        return QPointF(0, 0)

    def toCoordinate(self, _point: QPointF, _bound: bool) -> QGeoCoordinate:
        return QGeoCoordinate(0, 0)


class OSMDisplay(QQuickWidget):
    map_object: Map
    mouse_down: bool = False

    last_mouse_pos: QPoint
    pan_speed: float = 0.01

    overlay: Overlay
    drones: dict[int, DroneState]
    placed_points: dict[int, QPoint]

    def __init__(self, start: list[float], drones: dict[int, DroneState]):
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

        self.drones = drones
        self.placed_points = {}

        self.overlay = Overlay(self)
        self.last_mouse_pos = QPoint(0, 0)

    def getSize(self):
        top_left = self.map_object.toCoordinate(QPointF(0, 0), True)
        bottom_right = self.map_object.toCoordinate(
            QPointF(*self.size().toTuple()), True
        )
        return QPointF(
            abs(top_left.longitude() - bottom_right.longitude()),
            abs(top_left.latitude() - bottom_right.latitude()),
        )

    def place_point(self, drone_id: int) -> None:
        pos = self.drones[drone_id].pos
        pointf = self.map_object.fromCoordinate(QGeoCoordinate(pos.lat, pos.lon), False)

        self.placed_points[drone_id] = pointf.toPoint()

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
            delta = QPointF(event.x(), event.y()) - self.last_mouse_pos
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

        self.last_mouse_pos = QPoint(event.x(), event.y())

    def paint_points(self, painter: QPainter):
        for drone_id in self.drones:
            painter.setBrush(QColor(*self.drones[drone_id].color))
            painter.drawEllipse(self.placed_points[drone_id], 10, 10)

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        self.overlay.repaint()
        super().paintEvent(event)

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.overlay.setGeometry(self.rect())
        self.overlay.raise_()

    @Slot(int)
    def drone_status_listener(self, _drone_id: int):
        self.overlay.update()

    @Slot(int)
    def drone_position_listener(self, drone_id: int):
        self.place_point(drone_id)
        self.overlay.update()

    @Slot(int)
    def drone_color_listener(self, _drone_id: int):
        self.overlay.update()
