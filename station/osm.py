from pathlib import Path
from typing import cast, override

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import (
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

from station.events import DronePositionEvent


class Overlay(QWidget):
    points: list[QPoint]

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.points = []

    def set_points(self, points: list[QPoint]):
        self.points = points

    @override
    def paintEvent(self, paint_event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setBrush(Qt.BrushStyle.SolidPattern)
        painter.setBrush(Qt.GlobalColor.red)
        for point in self.points:
            painter.drawEllipse(point, 10, 10)
        painter.end()


# class for type checker
class Map(QQuickItem):
    def fromCoordinate(self, _coord: QGeoCoordinate, _bound: bool) -> QPointF:
        return QPointF(0, 0)

    def toCoordinate(self, _point: QPointF, _bound: bool) -> QGeoCoordinate:
        return QGeoCoordinate(0, 0)


class OSM(QQuickWidget):
    map_object: Map
    mouse_down: bool = False

    last: QPoint
    pan_speed: float = 0.01

    overlay: Overlay

    drone_points: dict[int, QGeoCoordinate]

    def __init__(self):
        super().__init__()
        self.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

        qml_path = Path.cwd() / "map.qml"
        self.setSource(QUrl.fromLocalFile(str(qml_path)))

        tmp_map_object = self.rootObject().findChild(QQuickItem, "Map")
        if tmp_map_object is not None:
            self.map_object = cast(Map, tmp_map_object)
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

    def place_points(self) -> list[QPoint]:
        return [
            self.map_object.fromCoordinate(x, False).toPoint()
            for x in self.drone_points.values()
        ]

    @override
    def wheelEvent(self, e: QWheelEvent):
        zoom_amount = 1 if e.angleDelta().y() > 0 else -1
        current_zoom = self.map_object.property("zoomLevel")
        self.map_object.setProperty(
            "zoomLevel", min(15, max(2, current_zoom + zoom_amount))
        )

    @override
    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.RightButton:
            self.mouse_down = True
            QGuiApplication.setOverrideCursor(Qt.CursorShape.OpenHandCursor)

    @override
    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.RightButton:
            self.mouse_down = False
            QGuiApplication.restoreOverrideCursor()

    @override
    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        if self.mouse_down:
            delta = QPointF(e.x(), e.y()) - self.last
            delta.setX(delta.x() * self.getSize().x() / self.width())
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

        self.last = QPoint(e.x(), e.y())

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        self.overlay.set_points(self.place_points())
        self.overlay.repaint()
        return super().paintEvent(event)

    @override
    def resizeEvent(self, e: QResizeEvent) -> None:
        super().resizeEvent(e)
        self.overlay.setGeometry(self.rect())
        self.overlay.raise_()

    @override
    def event(self, e: QEvent) -> bool:
        if e.type() == DronePositionEvent.event_number:
            pos_event = cast(DronePositionEvent, e)
            self.drone_points[pos_event.id] = QGeoCoordinate(
                pos_event.position.lat, pos_event.position.lon
            )
            return False

        return super().event(e)
