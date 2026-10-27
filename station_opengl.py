import asyncio
import threading

from PySide6.QtCore import QLoggingCategory
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtWidgets import QApplication

from station.opengl_window import OpenGLWindow
from station.station_server import StationServer


def main() -> None:
    fmt = QSurfaceFormat()
    fmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
    fmt.setDepthBufferSize(24)
    fmt.setVersion(3, 3)
    fmt.setSamples(4)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)

    QLoggingCategory.setFilterRules("qt.widgets.painting.warning=false")

    app = QApplication([])

    station_server = StationServer()
    window = OpenGLWindow(station_server)

    threading.Thread(target=asyncio.run, args=(station_server.run(),)).start()

    window.show()
    app.exec()


if __name__ == "__main__":
    main()
