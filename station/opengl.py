import subprocess
import os
import asyncio
from typing import Callable, Iterable

import dronekit

from common.utils import loc_to_point
from station.point import Point3d
from station.station_server import StationServer

class OpenGLWindow:
    stationgui: subprocess.Popen[str]
    station_server: StationServer
    expanse: tuple[Point3d, Point3d]

    def __init__(self, station_server: StationServer):
        os.chdir("Station")
        self.stationgui = subprocess.Popen(["./a.out"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        self.station_server = station_server
        station_server.set_drone_listeners(self.drone_connect_listener, self.arm_listener, self.drone_position_listener)

        self.expanse = self.calc_expanse()
        # self.expanse = (Point3d(self.expanse[0].x, 0, self.expanse[0].z), self.expanse[1])

    async def readline(self) -> str | None:
        if self.stationgui.stdout == None:
            return None
        return self.stationgui.stdout.readline()

    async def check_station(self):
        while self.stationgui.poll() is None:

            line = None
            try:
                line = await asyncio.wait_for(self.readline(), timeout=1.0)
            except TimeoutError:
                continue

            if line is not None and line != "":
                line = line[0:-1]
                match line:
                    case "Arm":
                        self.station_server.arm()
                    case "TakeOff":
                        self.station_server.takeoff()
                    case "Step":
                        self.station_server.step()
                    case "Land":
                        self.station_server.land()
                    case "Halt":
                        self.station_server.halt()
                    case "Close":
                        self.stationgui.kill()
                    case _:
                        print("Unrecognized Button:", line)

    def drone_connect_listener(self, drone_id: str):
        if self.stationgui.stdin is None:
            return

        self.stationgui.stdin.write(f"{drone_id}:1\n")
        self.stationgui.stdin.flush()

    def arm_listener(self, drone_id: str, armed: bool):
        if self.stationgui.stdin is None:
            return

        self.stationgui.stdin.write(f"{drone_id}:{2 if armed else 1}\n")
        self.stationgui.stdin.flush()

    def drone_position_listener(self, drone_id: str, position: dronekit.LocationGlobalRelative):
        if self.stationgui.stdin is None:
            return

        placed = self.place_in_expanse(loc_to_point(position))
        self.stationgui.stdin.write(f"{drone_id}:({round(placed.x)},{round(placed.y)},{round(placed.z)})\n")
        self.stationgui.stdin.flush()

    def calc_expanse(self) -> tuple[Point3d, Point3d]:
        combined = [loc_to_point(loc) for frame in self.station_server.frames for loc in frame]

        def edge_rel(predicate: Callable[[Iterable[float]], float]) -> Point3d:
            def edge_it(pull: Callable[[Point3d], float]) -> float:
                return predicate(pull(point) for point in combined)

            return Point3d(
                edge_it(lambda p: p.x), edge_it(lambda p: p.y), edge_it(lambda p: p.z)
            )

        return (edge_rel(lambda vals: min(vals)), edge_rel(lambda vals: max(vals)))

    def place_in_expanse(self, position: Point3d) -> Point3d:
        range = self.expanse[1] - self.expanse[0]
        range = range.apply_over_elements(lambda num: 1 if num < 0.0001 else num)
        bounded = position - self.expanse[0]
        scaled = bounded.mult_point_by_elements(1 / range)
        return scaled * 10;
