import json
from collections.abc import Callable

import dronekit

from station.point import Point3d


# I programmed the graphics with y as up, so
def loc_to_point(a: dronekit.LocationGlobalRelative) -> Point3d:
    return Point3d(a.lat, a.alt, a.lon)


def point_to_loc(a: Point3d) -> dronekit.LocationGlobalRelative:
    return dronekit.LocationGlobalRelative(a.x, a.z, a.y)


def list_to_loc(a: list[float]) -> dronekit.LocationGlobalRelative:
    return dronekit.LocationGlobalRelative(a[0], a[1], a[2])


def point_to_list(a: Point3d) -> list[float]:
    return [a.x, a.z, a.y]
