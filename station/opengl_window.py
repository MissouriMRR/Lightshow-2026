import asyncio
from collections.abc import Callable, Iterable
from uu import Error

import dronekit
import opengl_station  # loads opengl_station shared library that the c++ was compiled into

from common.utils import loc_to_point
from station.point import Point3d
from station.station_server import StationServer


class OpenGLWindow:
    """Handles running and communication of the opengl window"""

    station_server: StationServer
    expanse: tuple[Point3d, Point3d]

    def __init__(self, station_server: StationServer):
        self.station_server = station_server
        station_server.set_drone_listeners(
            self.drone_connect_listener, self.arm_listener, self.drone_position_listener
        )

        # force minimum y to be 0
        self.expanse = self.calc_expanse()
        tmp = self.expanse[0]
        tmp.y = 0
        self.expanse = (tmp, self.expanse[1])

        opengl_station.setup()

        # add drones to opengl window
        config = self.station_server.config
        for id in config.get_drone_ids()[1:]:
            opengl_station.set_ip(
                int(id), f"{config.get_drone_ip(id)}:{config.get_drone_port(id)}"
            )

    async def check_station(self):
        """Runs opengl window until it should close"""

        while not opengl_station.should_close():
            match opengl_station.loop():
                case opengl_station.LoopReturn.Nothing:
                    pass
                case opengl_station.LoopReturn.Arm:
                    self.station_server.arm()
                case opengl_station.LoopReturn.Takeoff:
                    self.station_server.takeoff()
                case opengl_station.LoopReturn.Step:
                    self.station_server.step()
                case opengl_station.LoopReturn.Land:
                    self.station_server.land()
                case opengl_station.LoopReturn.Halt:
                    self.station_server.halt()
                case unexpected:
                    raise Error(f"unexpected LoopReturn '{unexpected}'")
            await asyncio.sleep(0)

        opengl_station.cleanup()
        self.station_server.stop()

    def drone_connect_listener(self, drone_id: str):
        """Listens for drone connection to update opengl window"""

        opengl_station.set_state(int(drone_id), opengl_station.DroneState.Connected)

    def arm_listener(self, drone_id: str, armed: bool):
        """Listens for drone arming to update opengl window"""

        opengl_station.set_state(
            int(drone_id),
            opengl_station.DroneState.Armed
            if armed
            else opengl_station.DroneState.Disconnected,
        )

    def drone_position_listener(
        self, drone_id: str, position: dronekit.LocationGlobalRelative
    ):
        """Listens for drone position changes to update opengl window"""

        placed = self.place_in_expanse(loc_to_point(position))
        opengl_station.set_pos(int(drone_id), placed.x, placed.y, placed.z)

    def calc_expanse(self) -> tuple[Point3d, Point3d]:
        """Calculates the minimum and maximum positions which the drones will take"""

        combined = [
            loc_to_point(loc) for frame in self.station_server.frames for loc in frame
        ]

        def edge_rel(predicate: Callable[[Iterable[float]], float]) -> Point3d:
            def edge_it(pull: Callable[[Point3d], float]) -> float:
                return predicate(pull(point) for point in combined)

            return Point3d(
                edge_it(lambda p: p.x), edge_it(lambda p: p.y), edge_it(lambda p: p.z)
            )

        return (edge_rel(min), edge_rel(max))

    def place_in_expanse(self, position: Point3d) -> Point3d:
        """Scales drone positions over precalculated expanse"""

        range = self.expanse[1] - self.expanse[0]
        range = range.apply_over_elements(lambda num: 1 if num < 0.0001 else num)
        bounded = position - self.expanse[0]
        scaled = bounded.mult_point_by_elements(1 / range)
        return scaled * 20
