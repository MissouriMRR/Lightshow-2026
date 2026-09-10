from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import override


class Point3d:
    x: float
    y: float
    z: float

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z

    def __sub__(self, b: Point3d) -> Point3d:
        return Point3d(self.x - b.x, self.y - b.y, self.z - b.z)

    def __add__(self, b: Point3d) -> Point3d:
        return Point3d(self.x + b.x, self.y + b.y, self.z + b.z)

    def __mul__(self, a: float) -> Point3d:
        return Point3d(self.x * a, self.y * a, self.z * a)

    def __rtruediv__(self, a: float) -> Point3d:
        return Point3d(a / self.x, a / self.y, a / self.z)

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y
        yield self.z

    @override
    def __str__(self) -> str:
        return "< " + str(self.x) + ", " + str(self.y) + ", " + str(self.z) + " >"

    def mult_point_by_elements(self, b: Point3d) -> Point3d:
        return Point3d(self.x * b.x, self.y * b.y, self.z * b.z)

    def apply_over_elements(self, b: Callable[[float], float]) -> Point3d:
        return Point3d(b(self.x), b(self.y), b(self.z))
