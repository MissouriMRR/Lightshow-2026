import asyncio
import logging
import math

import dronekit
import utm

from drone.vehicle import AnyVehicle


def calculate_distance(
    lat_deg_1: float,
    lon_deg_1: float,
    altitude_m_1: float,
    lat_deg_2: float,
    lon_deg_2: float,
    altitude_m_2: float,
) -> float:
    """
    Calculate the distance, in meters, between two coordinates

    Parameters
    ----------
    lat_deg_1 : float
        The latitude, in degrees, of the first coordinate.
    lon_deg_1 : float
        The longitude, in degrees, of the first coordinate.
    altitude_m_1 : float
        The altitude, in meters, of the first coordinate.
    lat_deg_2 : float
        The latitude, in degrees, of the second coordinate.
    lon_deg_2 : float
        The longitude, in degrees, of the second coordinate.
    altitude_m_2 : float
        The altitude, in meters, of the second coordinate.

    Returns
    -------
    float
        The distance between the two coordinates.
    """
    easting_2, northing_2, zone_num_2, zone_letter_2 = utm.from_latlon(
        lat_deg_2, lon_deg_2
    )
    easting_1, northing_1, _, _ = utm.from_latlon(
        lat_deg_1,
        lon_deg_1,
        force_zone_number=zone_num_2,
        force_zone_letter=zone_letter_2,
    )

    return math.hypot(
        easting_1 - easting_2,
        northing_1 - northing_2,
        altitude_m_1 - altitude_m_2,
    )


async def move_to(
    drone: AnyVehicle,
    latitude: float,
    longitude: float,
    altitude: float,
    airspeed: float | None = None,
    tolerance: float | None = None,
) -> None:
    """
    This function takes in a latitude, longitude and altitude and autonomously
    moves the drone to that waypoint.

    Parameters
    ----------
    drone : AnyVehicle
        The drone to move.
    latitude : float
        The requested latitude to move to, in degrees.
    longitude : float
        The requested longitude to move to, in degrees.
    altitude : float
        The requested altitude to go to, in meters.
    airspeed : float, default None
        The requested airspeed in meters per second,
        or None to let DroneKit decide the airspeed.
    tolerance : float, default None
        The tolerance in meters, or None to use the default tolerance of 1 meter.
    """
    drone.simple_goto(
        dronekit.LocationGlobalRelative(latitude, longitude, altitude),
        airspeed=airspeed,
    )
    if tolerance is None:
        tolerance = 6

    location_reached: bool = False

    logging.info("Going to waypoint")
    while not location_reached:
        position: dronekit.LocationGlobalRelative = drone.location.global_relative_frame

        # continuously checks current latitude, longitude and altitude of the drone
        drone_lat: float = position.lat
        drone_long: float = position.lon
        drone_alt: float = position.alt

        total_distance: float = calculate_distance(
            drone_lat,
            drone_long,
            drone_alt,
            latitude,
            longitude,
            altitude,
        )

        if total_distance < tolerance:
            location_reached = True
            logging.info("Arrived %sm away from waypoint", total_distance)
            break

        # tell machine to sleep to prevent constant polling, preventing battery drain
        await asyncio.sleep(1.0)
