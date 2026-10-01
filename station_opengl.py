import asyncio

from station.opengl import OpenGLWindow
from station.station_server import StationServer


async def main() -> None:
    station_server = StationServer()
    window = OpenGLWindow(station_server)

    await asyncio.gather(station_server.run(), window.check_station())


if __name__ == "__main__":
    asyncio.run(main())
