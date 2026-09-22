import threading

from station.opengl import OpenGLWindow
from station.station_server import StationServer
import asyncio


async def main() -> None:
    station_server = StationServer()

    threading.Thread(
        target=lambda: asyncio.run(station_server.run()), daemon=True
    ).start()

    window = OpenGLWindow(station_server)
    await window.check_station()

if __name__ == "__main__":
    asyncio.run(main())
