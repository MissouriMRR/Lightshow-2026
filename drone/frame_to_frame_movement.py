"""
Move drones from their current frame coordinates to the next frame coordinates in config JSON.
"""

import asyncio
import logging

import dronekit

from drone.drone import Drone
from drone.goto import move_to
from drone.json_parser import ConfigParser
from drone.vehicle import AnyVehicle


def get_frame_flight_speed(
    config_json_path: str, drone_id: str, frame_name: str
) -> float | None:
    """Get the flight speed for a drone's frame.

    Args:
        config_json_path: Path to the config JSON file.
        drone_id: Drone id key (as string).
        frame_name: Frame name (e.g., "frame 1").

    Returns:
        Flight speed in m/s, or None if not found.
    """
    try:
        parser = ConfigParser(config_json_path)
    except (FileNotFoundError, Exception) as e:
        logging.error("Failed to load config from %s: %s", config_json_path, e)
        return None

    return parser.get_frame_flight_speed(drone_id, frame_name)


def get_frame_time_delay(
    config_json_path: str, drone_id: str, frame_name: str
) -> float | None:
    """Get the time delay for a drone's frame.

    Args:
        config_json_path: Path to the config JSON file.
        drone_id: Drone id key (as string).
        frame_name: Frame name (e.g., "frame 1").

    Returns:
        Time delay in seconds, or None if not found.
    """
    try:
        parser = ConfigParser(config_json_path)
    except (FileNotFoundError, Exception) as e:
        logging.error("Failed to load config from %s: %s", config_json_path, e)
        return None

    return parser.get_frame_time_delay(drone_id, frame_name)


def load_frame_position_from_json(
    config_json_path: str, drone_id: str, frame_name: str
) -> dronekit.LocationGlobalRelative | None:
    """Load a single drone's frame position from the JSON config.

    Args:
            config_json_path: Path to the config JSON file.
            drone_id: Drone id key (as string) in the config's "show" section.
            frame_name: Frame name (e.g., "frame 1").

    Returns:
            A `dronekit.LocationGlobalRelative` for the requested frame, or `None`
            if the drone or frame is not found or malformed.
    """
    try:
        parser = ConfigParser(config_json_path)
    except (FileNotFoundError, Exception) as e:
        logging.error("Failed to load config from %s: %s", config_json_path, e)
        return None

    location = parser.get_frame_location(drone_id, frame_name)

    if location is None:
        logging.warning("Frame %s not found for drone %s", frame_name, drone_id)

    return location


async def move_drone_to_frame(
    drone: Drone | AnyVehicle,
    config_json_path: str,
    drone_id: str,
    frame_name: str,
) -> bool:
    """Move a single drone to a configured frame using `move_to`.

    Args:
            drone: Drone object (may be a `dronekit.Vehicle` or a wrapper with
                       a `.vehicle` attribute like the project's `Drone` class).
            config_json_path: Path to JSON config.
            drone_id: Drone id key in the JSON show section.
            frame_name: Frame name (e.g., "frame 1").

    Returns:
            True on success, False on error.
    """
    location = load_frame_position_from_json(config_json_path, drone_id, frame_name)
    if location is None:
        return False

    # Resolve the underlying vehicle: a Drone wraps one, a raw vehicle is one.
    vehicle: AnyVehicle = drone.vehicle if isinstance(drone, Drone) else drone

    try:
        await move_to(vehicle, location.lat, location.lon, location.alt)
        logging.info("Drone %s moved to %s", drone_id, frame_name)
        return True
    except Exception as e:
        logging.error("Error moving drone %s to %s: %s", drone_id, frame_name, e)
        return False


async def move_swarm_to_frame_by_id(
    drones_by_id: dict[str, Drone | AnyVehicle],
    config_json_path: str,
    frame_name: str,
) -> dict[str, bool]:
    """Move multiple drones to a given frame.

    Args:
            drones_by_id: Mapping of drone id (string) -> drone object.
            config_json_path: Path to JSON config.
            frame_name: Frame name (e.g., "frame 1").

    Returns:
            A dict mapping drone id -> boolean success.
    """
    tasks = {}
    results: dict[str, bool] = {}

    for drone_id, drone in drones_by_id.items():
        # create a task per drone
        coro = move_drone_to_frame(drone, config_json_path, drone_id, frame_name)
        tasks[drone_id] = asyncio.create_task(coro)

    # await them and collect results
    for drone_id, task in tasks.items():
        try:
            success = await task
        except Exception as e:
            logging.error("Unexpected error moving drone %s: %s", drone_id, e)
            success = False
        results[drone_id] = success

    return results


if __name__ == "__main__":
    # Example usage (not run automatically):
    #
    # from station import Station
    # from drone import Drone
    # station = Station()
    # with open("../Models/Example jsons/example_config.json") as f:
    #     cfg = json.load(f)
    # drone_ids = list(cfg["drones"].keys())
    # drones = {d_id: Drone(station, d_id, []) for d_id in drone_ids}
    # asyncio.run(move_swarm_to_frame_by_id(drones, "../Models/Example jsons/example_config.json", 2))
    pass
