import json
from collections.abc import Callable

import dronekit
from Station.point import Point3d

from common.config import Config


def parse_json(filename: str) -> Config:
    with open(filename) as file:
        config = json.loads(file.read())

    show: list[list[dronekit.LocationGlobalRelative]] = [
        [] for _ in config["show"]["1"]
    ]
    for drone in config["show"].values():
        for i, frame in enumerate(drone.values()):
            show[i].append(list_to_loc(frame["coordinates"]))

    return Config(show, [drone["ip"] for drone in config["drones"].values()])


def parse_csv(filename: str) -> list[dronekit.LocationGlobalRelative]:
    epsilon = 0.0001
    positions: list[dronekit.LocationGlobalRelative] = []
    with open(filename) as lines:
        lines.readline()
        for line in lines:
            lat, lon, alt = [float(s) for s in line.split(",")]
            new_loc = dronekit.LocationGlobalRelative(lat, lon, alt)
            if not any(
                abs(x.lat - new_loc.lat) < epsilon
                and abs(x.lon - new_loc.lon) < epsilon
                and abs(x.alt - new_loc.alt) < epsilon
                for x in positions
            ):
                positions.append(new_loc)
    return positions


def parse_txt(filename: str) -> list[dronekit.LocationGlobalRelative]:
    epsilon = 0.1
    positions: list[dronekit.LocationGlobalRelative] = []
    with open(filename) as lines:
        for line in lines:
            alt, lat = [float(s) for s in line.split(" ")]
            # divide by 100 to keep coordinates within the latitude and
            # longitude maximum ranges
            new_loc = dronekit.LocationGlobalRelative(lat / 100, 0, alt / 100)
            if not any(
                abs(x.lat - new_loc.lat) < epsilon
                and abs(x.lon - new_loc.lon) < epsilon
                and abs(x.alt - new_loc.alt) < epsilon
                for x in positions
            ):
                positions.append(new_loc)

    minalt = min(x.alt for x in positions)
    return [
        dronekit.LocationGlobalRelative(pos.lat, pos.lon, pos.alt - minalt)
        for pos in positions
    ]


def parse_lla(filename: str) -> list[dronekit.LocationGlobalRelative]:
    positions: list[dronekit.LocationGlobalRelative] = []
    with open(filename) as lines:
        for line in lines:
            lat, long, alt = [float(s) for s in line.split(",")]
            positions.append(dronekit.LocationGlobalRelative(lat, long, alt))
    return positions


def partition[T](
    predicate: Callable[[T], bool], items: list[T]
) -> tuple[list[T], list[T]]:
    yes: list[T] = []
    no: list[T] = []
    for x in items:
        if predicate(x):
            yes.append(x)
        else:
            no.append(x)

    return (yes, no)


# I programmed the graphics with y as up, so
def loc_to_point(a: dronekit.LocationGlobalRelative) -> Point3d:
    return Point3d(a.lat, a.alt, a.lon)


def point_to_loc(a: Point3d) -> dronekit.LocationGlobalRelative:
    return dronekit.LocationGlobalRelative(a.x, a.y, a.z)


def list_to_loc(a: list[float]) -> dronekit.LocationGlobalRelative:
    return dronekit.LocationGlobalRelative(a[0], a[1], a[2])
