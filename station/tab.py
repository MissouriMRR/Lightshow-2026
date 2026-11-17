from typing import override

from PySide6.QtCore import QEvent, Signal
from PySide6.QtGui import QColor, QEnterEvent, QMouseEvent, QPalette, Qt
from PySide6.QtWidgets import QLabel, QLayout, QWidget


class Tab(QLabel):
    tab_layout: QLayout
    widget: QWidget
    defined_color: str
    tabPos: int = 0
    baseText: str
    hover: bool = False

    tabSignal: Signal = Signal(int)

    def __init__(self, color: str, layout: QLayout, widget: QWidget, tab_text: str):
        super().__init__(color)

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.tab_layout = layout
        self.widget = widget
        self.defined_color = color

        self.baseText = tab_text

        self.setText(tab_text)

        self.setFixedHeight(25)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent):
        if (event.button() == Qt.MouseButton.LeftButton) and (self.hover == True):
            self.updateFillColor("light green")

            current_widget = self.tab_layout.itemAt(self.tab_layout.count() - 1)
            if current_widget is not None:
                to_kill = current_widget.widget()
                if to_kill is not None:
                    self.tab_layout.removeWidget(to_kill)
                    to_kill.hide()
            self.tab_layout.addWidget(self.widget)
            self.widget.show()
            self.tabSignal.emit(self.tabPos)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.updateFillColor("green")

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        self.hover = True
        self.updateFillColor("light green")
        return super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        self.hover = False
        self.updateFillColor(self.defined_color)
        return super().leaveEvent(event)

    # Based on Gemini suggestion
    # Prevents button being highlighted when mouse is not over box
    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self.rect().contains(event.pos()):
            if self.hover:
                self.hover = False
                self.updateFillColor(self.defined_color)
        else:
            if not self.hover:
                self.hover = True
                self.updateFillColor("light green")
        super().mouseMoveEvent(event)

    # mfw Gemini reminds you to refactor
    def updateFillColor(self, color_str: str) -> None:

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color_str))
        self.setPalette(palette)
