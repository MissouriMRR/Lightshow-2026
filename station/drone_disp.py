import tkinter
from collections.abc import Callable, Iterable

import dronekit

from common.utils import loc_to_point
from station import draw_utils
from station.handle import Handle
from station.point import Point3d
from station.station_server import StationServer

Drawer = Callable[[float, float, str | None], None]


class DroneDisp(tkinter.Canvas):
    reference: int = 500

    station: StationServer
    expanse: tuple[Point3d, Point3d]
    handle: Handle

    font_size: float
    width: int
    height: int

    def __init__(self, master: tkinter.Misc, station: StationServer) -> None:
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=4, pady=4)

        self.station = station

        self.station.set_drone_position_listener(self.send_redraw)

        self.expanse = self.calc_expanse()

        self.bind("<Configure>", self.handle_resize)
        self.bind("<<Redraw>>", lambda _: self.redraw())

        self.font_size = 20

        self.width = self.reference
        self.height = self.reference

        self.handle = Handle(self, 400, -400)

    def handle_resize(self, event: "tkinter.Event[tkinter.Misc]") -> None:
        self.width = event.width
        self.height = event.height
        self.redraw()

    def send_redraw(self) -> None:
        self.event_generate("<<Redraw>>")

    def redraw(self) -> None:
        small = self.height * 0.95
        ratio = small / self.reference
        self.font_size = 20 * ratio

        self.delete("all")

        self.create_rectangle(0, 0, 500, 500, fill="lightblue", outline="")
        self.draw_ground()
        self.draw_goals()
        self.draw_drones()
        self.scale("all", 0, 0, ratio, ratio)
        self.move("all", self.width / 2, self.height / 2)

        self.handle.rescale(self.width, self.height)

    def draw_locations(
        self,
        positions: list[dronekit.LocationGlobalRelative],
        drawer: Drawer,
        colors: list[str | None] | None = None,
    ) -> None:
        if colors is None:
            colors = [None for _ in positions]
        field_range = self.expanse[1] - self.expanse[0]
        field_range = field_range.apply_over_elements(lambda x: 1 if x == 0 else x)

        scale_factor = (self.reference - 50) / field_range
        center = field_range * 0.5

        for i in range(len(positions)):
            loc = loc_to_point(positions[i])
            loc = loc - self.expanse[0] - center
            loc = loc.mult_point_by_elements(scale_factor)

            screen_points = draw_utils.world_points_to_screen_points(
                1, [loc], self.handle.angle, self.handle.offset
            )

            drawer(screen_points[0].x, screen_points[0].y, colors[i])

    def draw_ground(self) -> None:
        down = -250
        scale = 500
        ground_points = [
            loc_to_point(loc)
            for loc in [
                dronekit.LocationGlobalRelative(-scale, -scale, down),
                dronekit.LocationGlobalRelative(scale, -scale, down),
                dronekit.LocationGlobalRelative(scale, scale, down),
                dronekit.LocationGlobalRelative(-scale, scale, down),
            ]
        ]
        screen_points = draw_utils.world_points_to_screen_points(
            1, ground_points, self.handle.angle, self.handle.offset
        )

        coords: list[float] = []
        for point in reversed(screen_points):
            coords += [point.x, point.y]

        self.create_polygon(*coords, fill="green")

    def draw_goals(self) -> None:
        self.draw_locations(
            self.station.frames[self.station.show_index],
            lambda x, y, color: draw_utils.draw_text(
                self, int(self.font_size), "X", x, y, color=color if color else "red"
            ),
        )

    def draw_drones(self) -> None:
        colors: list[str | None] = [
            "lightgreen" if confirmed else "yellow"
            for confirmed in self.station.get_drone_confirmeds()
        ]
        self.draw_locations(
            self.station.get_drone_positions(),
            lambda x, y, color: draw_utils.draw_circle(
                self, 20, x, y, color if color else "blue"
            ),
            colors,
        )

    def calc_expanse(self) -> tuple[Point3d, Point3d]:
        combined = [loc_to_point(loc) for frame in self.station.frames for loc in frame]

        def edge_rel(predicate: Callable[[Iterable[float]], float]) -> Point3d:
            def edge_it(pull: Callable[[Point3d], float]) -> float:
                return predicate(pull(point) for point in combined)

            return Point3d(
                edge_it(lambda p: p.x), edge_it(lambda p: p.y), edge_it(lambda p: p.z)
            )

        return (edge_rel(lambda vals: min(vals)), edge_rel(lambda vals: max(vals)))
