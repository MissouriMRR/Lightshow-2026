import math
import tkinter

from station import draw_utils
from station.point import Point3d


class Handle:
    points: list[Point3d]

    def __init__(self, canvas: tkinter.Canvas, x: int, y: int) -> None:
        self.canvas: tkinter.Canvas = canvas

        self.mouse_left_down: bool = False
        self.mouse_right_down: bool = False

        self.canvas.bind("<Motion>", self.motion)
        self.canvas.bind("<Button-1>", lambda _: self.set_mouse_left_down(True))
        self.canvas.bind("<ButtonRelease-1>", lambda _: self.set_mouse_left_down(False))
        self.canvas.bind("<Button-3>", lambda _: self.set_mouse_right_down(True))
        self.canvas.bind(
            "<ButtonRelease-3>", lambda _: self.set_mouse_right_down(False)
        )

        self.screen_coords: list[tuple[Point3d, str]] = []

        self.handle_points: list[Point3d] = [
            Point3d(1, 0, 0),
            Point3d(-1, 0, 0),
            Point3d(0, 1, 0),
            Point3d(0, -1, 0),
            Point3d(0, 0, 1),
            Point3d(0, 0, -1),
        ]

        self.label_to_angle: dict[str, list[float]] = {
            "lat": [-math.pi / 2, 0],
            "-lat": [math.pi / 2, 0],
            "alt": [0, -math.pi / 2],
            "-alt": [0, math.pi / 2],
            "lon": [0, 0],
            "-lon": [math.pi, 0],
        }

        self.last_mouse_pos: list[int] = [0, 0]

        self.width: int = 500
        self.height: int = 500

        self.canvas.configure(bg="lightblue")

        self.offset: Point3d = Point3d(0, 0, 0)
        self.angle: list[float] = [0.0, 0.0]
        self.pos: list[int] = [x, y]
        self.center: Point3d = Point3d(250, 250, 0)
        self.initial_scale: float = 60
        self.scale: float = self.initial_scale
        self.current_label: str = ""

        self.recalc_points()

    def recalc_points(self) -> None:
        self.points = draw_utils.world_points_to_screen_points(
            self.scale, self.handle_points, self.angle
        )
        self.screen_coords = self.labelize(
            [self.translate(point) for point in self.points]
        )

    def rescale(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.scale = self.initial_scale * (height / 500)
        self.center = self.translate(Point3d(0, 0, 0))

        self.recalc_points()
        self.redraw()

    def redraw(self) -> None:
        self.canvas.delete("handle")
        self.draw_handle(self.screen_coords)

    def translate(self, point: Point3d) -> Point3d:
        return Point3d(
            point.x + self.width - self.scale * 1.5, point.y + self.scale * 1.5, point.z
        )

    def labelize(self, points: list[Point3d]) -> list[tuple[Point3d, str]]:
        labels = list(self.label_to_angle.keys())
        return [(point, labels[i]) for i, point in enumerate(points)]

    def draw_handle(self, points: list[tuple[Point3d, str]]) -> None:
        points.sort(key=lambda pair: pair[0].z)

        for point, label in points:
            screen_x, screen_y, _ = point
            self.canvas.create_line(
                self.center.x,
                self.center.y,
                screen_x,
                screen_y,
                fill="black",
                width=(1 / 20.0) * self.scale,
                tags="handle",
            )
            draw_utils.draw_circle(
                self.canvas,
                self.scale / 2,
                screen_x,
                screen_y,
                color=("darkblue" if label == self.current_label else "blue"),
                tags="handle",
            )
            draw_utils.draw_text(
                self.canvas,
                int(self.scale // 5),
                label,
                screen_x,
                screen_y,
                tags="handle",
            )

    def check_inside_circle(self) -> str:
        for point, label in reversed(self.screen_coords):
            screen_x, screen_y, _ = point
            if (
                abs(self.last_mouse_pos[0] - screen_x) < self.scale / 4
                and abs(self.last_mouse_pos[1] - screen_y) < self.scale / 4
            ):
                return label
        return ""

    def set_mouse_left_down(self, mouse_left_down: bool) -> None:
        if (
            self.center.x - self.scale * 2
            < self.last_mouse_pos[0]
            < self.center.x + self.scale * 2
            and self.center.y - self.scale * 2
            < self.last_mouse_pos[1]
            < self.center.y + self.scale * 2
        ):
            self.mouse_left_down = mouse_left_down

        if mouse_left_down and self.current_label != "":
            self.angle = list(self.label_to_angle[self.current_label])
            self.mouse_left_down = False
            self.redraw()

    def set_mouse_right_down(self, mouse_right_down: bool) -> None:
        self.mouse_right_down = mouse_right_down

    def motion(self, event: "tkinter.Event[tkinter.Misc]") -> None:
        sensitivity = 0.01
        pan_sensitivity = 0.5

        diff = [-(self.last_mouse_pos[0] - event.x), (self.last_mouse_pos[1] - event.y)]

        if self.mouse_right_down:
            self.offset += draw_utils.get_right(self.angle) * diff[0] * pan_sensitivity
            self.offset += draw_utils.get_up(self.angle) * diff[1] * pan_sensitivity

        if self.mouse_left_down:
            self.angle[0] += diff[0] * sensitivity
            self.angle[1] += diff[1] * sensitivity
            self.recalc_points()
        elif label := self.check_inside_circle():
            self.current_label = label
        else:
            self.current_label = ""

        self.canvas.event_generate("<<Redraw>>")
        self.last_mouse_pos = [event.x, event.y]
