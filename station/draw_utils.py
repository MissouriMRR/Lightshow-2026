import math
import tkinter
from collections.abc import Sequence

from station.point import Point3d


def draw_circle(
    canvas: tkinter.Canvas,
    size: float,
    x: float,
    y: float,
    color: str = "blue",
    tags: str = "",
) -> None:
    canvas.create_oval(
        x - size / 2,
        y - size / 2,
        x + size / 2,
        y + size / 2,
        fill=color,
        outline="",
        tags=tags,
    )


def draw_text(
    canvas: tkinter.Canvas,
    font_size: int,
    text: str,
    x: float,
    y: float,
    color: str = "white",
    tags: str = "",
) -> None:
    canvas.create_text(
        x, y, text=text, font=("Arial", max(int(font_size), 2)), fill=color, tags=tags
    )


def world_points_to_screen_points(
    scale: float,
    points: list[Point3d],
    angle: Sequence[float],
    offset: Point3d | None = None,
) -> list[Point3d]:
    if offset is None:
        offset = Point3d(0, 0, 0)

    out: list[Point3d] = []

    for point in points:
        x, y, z = point * scale + offset
        y *= -1

        # calculate orthographic projection
        screen_x = x * math.cos(angle[0]) + z * math.sin(angle[0])
        screen_y = (
            x * math.sin(angle[0]) * math.sin(angle[1])
            + y * math.cos(angle[1])
            + z * math.cos(angle[0]) * -math.sin(angle[1])
        )
        screen_order_index = (
            -x * math.sin(angle[0]) * math.cos(angle[1])
            + y * math.sin(angle[1])
            + z * math.cos(angle[0]) * math.cos(angle[1])
        )

        out.append(Point3d(screen_x, screen_y, screen_order_index))

    return out


def get_right(angle: Sequence[float]) -> Point3d:
    return Point3d(math.cos(angle[0]), 0, math.sin(angle[0]))


def get_up(angle: Sequence[float]) -> Point3d:
    return Point3d(
        -math.sin(angle[0]) * math.sin(angle[1]),
        math.cos(angle[1]),
        math.cos(angle[0]) * math.sin(angle[1]),
    )
