import json
import logging
from collections.abc import Callable
from typing import Any

import dronekit


class ConfigParser:
    """Parser for drone swarm configuration JSON files."""

    def __init__(self, config_path: str):
        """Initialize parser with a configuration file.

        Args:
            config_path: Path to the JSON configuration file.

        Raises:
            FileNotFoundError: If the config file does not exist.
            json.JSONDecodeError: If the config file is not valid JSON.
        """
        self.config_path: str = config_path
        self.config_data: dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load and parse the JSON configuration file."""
        try:
            with open(self.config_path, "r") as f:
                self.config_data = json.load(f)
            logging.info("Loaded configuration from %s", self.config_path)
        except FileNotFoundError:
            logging.error("Configuration file not found: %s", self.config_path)
            raise
        except json.JSONDecodeError as e:
            logging.error("Invalid JSON in configuration file: %s", e)
            raise

    # ============ GroundStation Configuration Access ============

    def get_ground_station_connection(self) -> tuple[str, str] | None:
        gs = self.config_data.get("gs", {})
        ip = gs.get("ip")
        port = gs.get("port")

        if ip is None or port is None:
            return None
        return (ip, port)

    # ============ Drone Configuration Access ============

    def get_drone_ids(self) -> list[str]:
        """Get all drone IDs from the configuration.

        Returns:
            List of drone ID strings, or empty list if no drones found.
        """
        drones = self.config_data.get("drones", {})
        return list(drones.keys())

    def get_drone_ip(self, drone_id: str) -> str | None:
        """Get the IP address for a specific drone.

        Args:
            drone_id: Drone ID (as string).

        Returns:
            IP address string, or None if not found.
        """
        drone = self.config_data.get("drones", {}).get(drone_id)
        if drone is None:
            logging.warning("Drone %s not found in configuration", drone_id)
            return None
        return drone.get("ip")

    def get_drone_port(self, drone_id: str) -> str | None:
        """Get the port for a specific drone.

        Args:
            drone_id: Drone ID (as string).

        Returns:
            Port string, or None if not found.
        """
        drone = self.config_data.get("drones", {}).get(drone_id)
        if drone is None:
            logging.warning("Drone %s not found in configuration", drone_id)
            return None
        return drone.get("port")

    def get_drone_connection(self, drone_id: str) -> tuple[str, str] | None:
        """Get the IP and port for a specific drone.

        Args:
            drone_id: Drone ID (as string).

        Returns:
            Tuple of (ip, port), or None if not found.
        """
        ip = self.get_drone_ip(drone_id)
        port = self.get_drone_port(drone_id)
        if ip is None or port is None:
            return None
        return (ip, port)

    def get_number_of_drones(self):
        return len(self.config_data["drones"])

    # ============ Ground Station Access  ============
    def get_gs_ip(self):
        """Get the IP address for the ground station.

        Returns:
            IP address string, or None if not found.
        """
        gs = self.config_data.get("gs", {})
        return gs.get("ip")

    def get_gs_port(self):
        """Get the port for the ground station

        Returns:
            Port as integer, or None if not found.
        """
        gs = self.config_data.get("gs", {})
        port = gs.get("port")
        return int(port) if port else None

    def get_gs_connection(self):
        """Get the IP and port for ground station

        Returns:
            Tuple of (ip, port), or None if not found.
        """
        ip = self.get_gs_ip()
        port = self.get_gs_port()
        if ip is None or port is None:
            return None
        return (ip, port)

    # ============ Show/Frame Data Access ============

    def get_frame_names(self, drone_id: str) -> list[str]:
        """Get all frame names for a specific drone.

        Args:
            drone_id: Drone ID (as string).

        Returns:
            List of frame name strings, or empty list if drone not found.
        """
        frames = self.config_data.get("show", {}).get(drone_id, {})
        return list(frames.keys())

    def get_frame_coordinates(
        self, drone_id: str, frame_name: str
    ) -> list[float] | None:
        """Get the coordinates for a specific frame.

        Args:
            drone_id: Drone ID (as string).
            frame_name: Frame name (e.g., "frame 1").

        Returns:
            List of [latitude, longitude, altitude], or None if not found.
        """
        frame = self.config_data.get("show", {}).get(drone_id, {}).get(frame_name)
        if frame is None:
            logging.warning("Frame %s not found for drone %s", frame_name, drone_id)
            return None

        coords = frame.get("coordinates")
        if not isinstance(coords, list) or len(coords) != 3:
            logging.warning(
                "Invalid coordinates for drone %s %s: %r",
                drone_id,
                frame_name,
                coords,
            )
            return None
        return coords

    def get_frame_time_delay(self, drone_id: str, frame_name: str) -> float | None:
        """Get the time delay for a specific frame.

        Args:
            drone_id: Drone ID (as string).
            frame_name: Frame name (e.g., "frame 1").

        Returns:
            Time delay in seconds, or None if not found.
        """
        frame = self.config_data.get("show", {}).get(drone_id, {}).get(frame_name)
        if frame is None:
            logging.warning("Frame %s not found for drone %s", frame_name, drone_id)
            return None
        return frame.get("time_delay")

    def get_frame_flight_speed(self, drone_id: str, frame_name: str) -> float | None:
        """Get the flight speed for a specific frame.

        Args:
            drone_id: Drone ID (as string).
            frame_name: Frame name (e.g., "frame 1").

        Returns:
            Flight speed in m/s, or None if not found.
        """
        frame = self.config_data.get("show", {}).get(drone_id, {}).get(frame_name)
        if frame is None:
            logging.warning("Frame %s not found for drone %s", frame_name, drone_id)
            return None
        return frame.get("flight_speed")

    def get_frame_data(self, drone_id: str, frame_name: str) -> dict[str, Any] | None:
        """Get all data for a specific frame.

        Args:
            drone_id: Drone ID (as string).
            frame_name: Frame name (e.g., "frame 1").

        Returns:
            Dictionary with keys: coordinates, time_delay, flight_speed.
            Returns None if frame not found.
        """
        frame = self.config_data.get("show", {}).get(drone_id, {}).get(frame_name)
        if frame is None:
            logging.warning("Frame %s not found for drone %s", frame_name, drone_id)
            return None
        return frame

    def get_frame_location(
        self, drone_id: str, frame_name: str
    ) -> dronekit.LocationGlobalRelative | None:
        """Get a dronekit.LocationGlobalRelative for a specific frame.

        Args:
            drone_id: Drone ID (as string).
            frame_name: Frame name (e.g., "frame 1").

        Returns:
            dronekit.LocationGlobalRelative object, or None if not found.
        """
        coords = self.get_frame_coordinates(drone_id, frame_name)
        if coords is None:
            return None
        lat, lon, alt = coords
        return dronekit.LocationGlobalRelative(lat, lon, alt)

    # ============ Local Info Access ============

    def get_self_id(self) -> str | None:
        """Get the selfId from localInfo.

        Returns:
            Self ID string, or None if not found.
        """
        return self.config_data.get("localInfo", {}).get("selfId")

    def get_speed_test_kb_data_size(self) -> str | None:
        """Get the speedTestKbDataSize from localInfo.

        Returns:
            Data size string, or None if not found.
        """
        return self.config_data.get("localInfo", {}).get("speedTestKbDataSize")

    def get_local_info(self) -> dict[str, Any]:
        """Get all local information.

        Returns:
            Dictionary containing localInfo data.
        """
        return self.config_data.get("localInfo", {})

    # ============ Dimensions ============

    def get_center_coordinates(self) -> list[float] | None:
        """Get the center coordinates from dimensions.

        Returns:
            List of [latitude, longitude, altitude], or None if not found.
        """
        center = self.config_data.get("dimensions", {}).get("center_coordinates")
        if not isinstance(center, list) or len(center) != 3:
            logging.warning("Invalid center coordinates: %r", center)
            return None
        return center

    def get_max_width(self) -> float | None:
        """Get the maximum width from dimensions.

        Returns:
            Maximum width value, or None if not found.
        """
        return self.config_data.get("dimensions", {}).get("max_width")

    def get_max_length(self) -> float | None:
        """Get the maximum length from dimensions.

        Returns:
            Maximum length value, or None if not found.
        """
        return self.config_data.get("dimensions", {}).get("max_length")

    def get_max_height(self) -> float | None:
        """Get the maximum height from dimensions.

        Returns:
            Maximum height value, or None if not found.
        """
        return self.config_data.get("dimensions", {}).get("max_height")

    def get_dimensions(self) -> dict[str, Any]:
        """Get all dimension information.

        Returns:
            Dictionary containing center_coordinates, max_width, max_length, max_height.
        """
        return self.config_data.get("dimensions", {})

    def get_center_location(self) -> dronekit.LocationGlobalRelative | None:
        """Get a dronekit.LocationGlobalRelative for the center coordinates.

        Returns:
            dronekit.LocationGlobalRelative object, or None if not found.
        """
        coords = self.get_center_coordinates()
        if coords is None:
            return None
        lat, lon, alt = coords
        return dronekit.LocationGlobalRelative(lat, lon, alt)

    # ============ Drone Configuration Modification ============

    def set_drone_ip(self, drone_id: str, ip: str) -> None:
        """Set the IP address for a specific drone.

        Args:
            drone_id: Drone ID (as string).
            ip: IP address to set.
        """
        if "drones" not in self.config_data:
            self.config_data["drones"] = {}
        if drone_id not in self.config_data["drones"]:
            self.config_data["drones"][drone_id] = {}
        self.config_data["drones"][drone_id]["ip"] = ip
        logging.info("Set IP for drone %s to %s", drone_id, ip)

    def set_drone_port(self, drone_id: str, port: str) -> None:
        """Set the port for a specific drone.

        Args:
            drone_id: Drone ID (as string).
            port: Port to set.
        """
        if "drones" not in self.config_data:
            self.config_data["drones"] = {}
        if drone_id not in self.config_data["drones"]:
            self.config_data["drones"][drone_id] = {}
        self.config_data["drones"][drone_id]["port"] = port
        logging.info("Set port for drone %s to %s", drone_id, port)

    def set_drone_connection(self, drone_id: str, ip: str, port: str) -> None:
        """Set the IP and port for a specific drone.

        Args:
            drone_id: Drone ID (as string).
            ip: IP address to set.
            port: Port to set.
        """
        self.set_drone_ip(drone_id, ip)
        self.set_drone_port(drone_id, port)

    def add_drone(self, drone_id: str, ip: str, port: str) -> None:
        """Add a new drone to the configuration.

        Args:
            drone_id: Drone ID (as string).
            ip: IP address for the drone.
            port: Port for the drone.
        """
        if "drones" not in self.config_data:
            self.config_data["drones"] = {}
        self.config_data["drones"][drone_id] = {"ip": ip, "port": port}
        if "show" not in self.config_data:
            self.config_data["show"] = {}
        self.config_data["show"][drone_id] = {}
        logging.info("Added drone %s with IP %s and port %s", drone_id, ip, port)

    def remove_drone(self, drone_id: str) -> None:
        """Remove a drone from the configuration.

        Args:
            drone_id: Drone ID (as string).
        """
        if "drones" in self.config_data and drone_id in self.config_data["drones"]:
            del self.config_data["drones"][drone_id]
        if "show" in self.config_data and drone_id in self.config_data["show"]:
            del self.config_data["show"][drone_id]
        logging.info("Removed drone %s", drone_id)

    # ============ Frame Data Modification ============

    def set_frame_coordinates(
        self, drone_id: str, frame_name: str, coordinates: list[float]
    ) -> None:
        """Set the coordinates for a specific frame.

        Args:
            drone_id: Drone ID (as string).
            frame_name: Frame name (e.g., "frame 1").
            coordinates: List of [latitude, longitude, altitude].

        Raises:
            ValueError: If coordinates is not a list of 3 floats.
        """
        if len(coordinates) != 3:
            raise ValueError(
                f"Coordinates must be a list of 3 floats, got: {coordinates}"
            )
        if "show" not in self.config_data:
            self.config_data["show"] = {}
        if drone_id not in self.config_data["show"]:
            self.config_data["show"][drone_id] = {}
        if frame_name not in self.config_data["show"][drone_id]:
            self.config_data["show"][drone_id][frame_name] = {}
        self.config_data["show"][drone_id][frame_name]["coordinates"] = coordinates
        logging.info(
            "Set coordinates for frame %s of drone %s to %s",
            frame_name,
            drone_id,
            coordinates,
        )

    def set_frame_time_delay(
        self, drone_id: str, frame_name: str, time_delay: float
    ) -> None:
        """Set the time delay for a specific frame.

        Args:
            drone_id: Drone ID (as string).
            frame_name: Frame name (e.g., "frame 1").
            time_delay: Time delay in seconds.
        """
        if "show" not in self.config_data:
            self.config_data["show"] = {}
        if drone_id not in self.config_data["show"]:
            self.config_data["show"][drone_id] = {}
        if frame_name not in self.config_data["show"][drone_id]:
            self.config_data["show"][drone_id][frame_name] = {}
        self.config_data["show"][drone_id][frame_name]["time_delay"] = time_delay
        logging.info(
            "Set time_delay for frame %s of drone %s to %s",
            frame_name,
            drone_id,
            time_delay,
        )

    def set_frame_flight_speed(
        self, drone_id: str, frame_name: str, flight_speed: float
    ) -> None:
        """Set the flight speed for a specific frame.

        Args:
            drone_id: Drone ID (as string).
            frame_name: Frame name (e.g., "frame 1").
            flight_speed: Flight speed in m/s.
        """
        if "show" not in self.config_data:
            self.config_data["show"] = {}
        if drone_id not in self.config_data["show"]:
            self.config_data["show"][drone_id] = {}
        if frame_name not in self.config_data["show"][drone_id]:
            self.config_data["show"][drone_id][frame_name] = {}
        self.config_data["show"][drone_id][frame_name]["flight_speed"] = flight_speed
        logging.info(
            "Set flight_speed for frame %s of drone %s to %s",
            frame_name,
            drone_id,
            flight_speed,
        )

    def set_frame_data(
        self,
        drone_id: str,
        frame_name: str,
        coordinates: list[float],
        time_delay: float,
        flight_speed: float,
    ) -> None:
        """Set all data for a specific frame.

        Args:
            drone_id: Drone ID (as string).
            frame_name: Frame name (e.g., "frame 1").
            coordinates: List of [latitude, longitude, altitude].
            time_delay: Time delay in seconds.
            flight_speed: Flight speed in m/s.

        Raises:
            ValueError: If coordinates is not a list of 3 floats.
        """
        self.set_frame_coordinates(drone_id, frame_name, coordinates)
        self.set_frame_time_delay(drone_id, frame_name, time_delay)
        self.set_frame_flight_speed(drone_id, frame_name, flight_speed)

    def add_frame(
        self,
        drone_id: str,
        frame_name: str,
        coordinates: list[float],
        time_delay: float,
        flight_speed: float,
    ) -> None:
        """Add a new frame for a specific drone.

        Args:
            drone_id: Drone ID (as string).
            frame_name: Frame name (e.g., "frame 2").
            coordinates: List of [latitude, longitude, altitude].
            time_delay: Time delay in seconds.
            flight_speed: Flight speed in m/s.

        Raises:
            ValueError: If coordinates is not a list of 3 floats.
        """
        self.set_frame_data(drone_id, frame_name, coordinates, time_delay, flight_speed)
        logging.info("Added frame %s for drone %s", frame_name, drone_id)

    def remove_frame(self, drone_id: str, frame_name: str) -> None:
        """Remove a frame from a specific drone.

        Args:
            drone_id: Drone ID (as string).
            frame_name: Frame name to remove.
        """
        if (
            "show" in self.config_data
            and drone_id in self.config_data["show"]
            and frame_name in self.config_data["show"][drone_id]
        ):
            del self.config_data["show"][drone_id][frame_name]
            logging.info("Removed frame %s for drone %s", frame_name, drone_id)

    # ============ Local Info Modification ============

    def set_self_id(self, self_id: str) -> None:
        """Set the selfId in localInfo.

        Args:
            self_id: Self ID string to set.
        """
        if "localInfo" not in self.config_data:
            self.config_data["localInfo"] = {}
        self.config_data["localInfo"]["selfId"] = self_id
        logging.info("Set selfId to %s", self_id)

    def set_speed_test_kb_data_size(self, data_size: str) -> None:
        """Set the speedTestKbDataSize in localInfo.

        Args:
            data_size: Data size string to set.
        """
        if "localInfo" not in self.config_data:
            self.config_data["localInfo"] = {}
        self.config_data["localInfo"]["speedTestKbDataSize"] = data_size
        logging.info("Set speedTestKbDataSize to %s", data_size)

    def set_local_info(self, local_info: dict[str, Any]) -> None:
        """Set all local information.

        Args:
            local_info: Dictionary containing localInfo data.
        """
        if "localInfo" not in self.config_data:
            self.config_data["localInfo"] = {}
        self.config_data["localInfo"].update(local_info)
        logging.info("Updated localInfo with %s", local_info)

    # ============ Dimensions Modification ============

    def set_center_coordinates(self, coordinates: list[float]) -> None:
        """Set the center coordinates in dimensions.

        Args:
            coordinates: List of [latitude, longitude, altitude].

        Raises:
            ValueError: If coordinates is not a list of 3 floats.
        """
        if len(coordinates) != 3:
            raise ValueError(
                f"Coordinates must be a list of 3 floats, got: {coordinates}"
            )
        if "dimensions" not in self.config_data:
            self.config_data["dimensions"] = {}
        self.config_data["dimensions"]["center_coordinates"] = coordinates
        logging.info("Set center_coordinates to %s", coordinates)

    def set_max_width(self, max_width: float) -> None:
        """Set the maximum width in dimensions.

        Args:
            max_width: Maximum width value.
        """
        if "dimensions" not in self.config_data:
            self.config_data["dimensions"] = {}
        self.config_data["dimensions"]["max_width"] = max_width
        logging.info("Set max_width to %s", max_width)

    def set_max_length(self, max_length: float) -> None:
        """Set the maximum length in dimensions.

        Args:
            max_length: Maximum length value.
        """
        if "dimensions" not in self.config_data:
            self.config_data["dimensions"] = {}
        self.config_data["dimensions"]["max_length"] = max_length
        logging.info("Set max_length to %s", max_length)

    def set_max_height(self, max_height: float) -> None:
        """Set the maximum height in dimensions.

        Args:
            max_height: Maximum height value.
        """
        if "dimensions" not in self.config_data:
            self.config_data["dimensions"] = {}
        self.config_data["dimensions"]["max_height"] = max_height
        logging.info("Set max_height to %s", max_height)

    def set_dimensions(self, dimensions: dict[str, Any]) -> None:
        """Set all dimension information.

        Args:
            dimensions: Dictionary containing center_coordinates, max_width, max_length, max_height.
        """
        if "dimensions" not in self.config_data:
            self.config_data["dimensions"] = {}
        self.config_data["dimensions"].update(dimensions)
        logging.info("Updated dimensions with %s", dimensions)

    # ============ File Operations ============

    def save_config(self, output_path: str | None = None) -> None:
        """Save the configuration to a JSON file.

        Args:
            output_path: Path to save the configuration to. If None, uses the original config_path.

        Raises:
            IOError: If the file cannot be written.
        """
        path = output_path or self.config_path
        try:
            with open(path, "w") as f:
                json.dump(self.config_data, f, indent=4)
            logging.info("Saved configuration to %s", path)
        except OSError as e:
            logging.error("Failed to save configuration to %s: %s", path, e)
            raise

    # ============ Utility Methods ============

    def get_for_all_drones(self, p: Callable[[str], object]) -> list[object]:
        return [p(drone_id) for drone_id in self.get_drone_ids()[1:]]

    def get_all_drone_frames(self) -> dict[str, list[str]]:
        """Get all frames for all drones.

        Returns:
            Dictionary mapping drone_id -> list of frame names.
        """
        result = {}
        for drone_id in self.get_drone_ids()[1:]:
            result[drone_id] = self.get_frame_names(drone_id)
        return result

    def validate(self) -> tuple[bool, list[str]]:
        """Validate the configuration structure and data.

        Returns:
            Tuple of (is_valid, list_of_errors).
        """
        errors = []

        if "drones" not in self.config_data:
            errors.append("Missing 'drones' section")
        if "show" not in self.config_data:
            errors.append("Missing 'show' section")

        drones = self.config_data.get("drones", {})
        for drone_id, drone_info in drones.items():
            if not isinstance(drone_info, dict):
                errors.append(f"Drone {drone_id} info is not a dictionary")
            elif "ip" not in drone_info or "port" not in drone_info:
                errors.append(f"Drone {drone_id} missing 'ip' or 'port'")

        show = self.config_data.get("show", {})
        for drone_id, frames in show.items():
            if not isinstance(frames, dict):
                errors.append(f"Drone {drone_id} frames is not a dictionary")
            else:
                for frame_name, frame_data in frames.items():
                    if not isinstance(frame_data, dict):
                        errors.append(
                            f"Frame {frame_name} for drone {drone_id} is not a dictionary"
                        )
                    else:
                        if "coordinates" not in frame_data:
                            errors.append(
                                f"Frame {frame_name} for drone {drone_id} missing 'coordinates'"
                            )
                        if "time_delay" not in frame_data:
                            errors.append(
                                f"Frame {frame_name} for drone {drone_id} missing 'time_delay'"
                            )
                        if "flight_speed" not in frame_data:
                            errors.append(
                                f"Frame {frame_name} for drone {drone_id} missing 'flight_speed'"
                            )

                        coords = frame_data.get("coordinates")
                        if not isinstance(coords, list) or len(coords) != 3:
                            errors.append(
                                f"Frame {frame_name} for drone {drone_id} has invalid coordinates: {coords}"
                            )

        return (len(errors) == 0, errors)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    parser = ConfigParser("../Models/Example jsons/example_config.json")

    # Drone info
    print("Drone IDs:", parser.get_drone_ids())
    print("Drone 1 connection:", parser.get_drone_connection("1"))

    # Frame info
    print("Drone 1 frames:", parser.get_frame_names("1"))
    print(
        "Drone 1, frame 1 coordinates:",
        parser.get_frame_coordinates("1", "frame 1"),
    )
    print(
        "Drone 1, frame 1 time delay:",
        parser.get_frame_time_delay("1", "frame 1"),
    )
    print(
        "Drone 1, frame 1 flight speed:",
        parser.get_frame_flight_speed("1", "frame 1"),
    )

    # Local info
    print("Self ID:", parser.get_self_id())

    # Dimensions info
    print("Center coordinates:", parser.get_center_coordinates())
    print("Max width:", parser.get_max_width())
    print("Max length:", parser.get_max_length())
    print("Max height:", parser.get_max_height())
    print("All dimensions:", parser.get_dimensions())

    # Validation
    is_valid, errors = parser.validate()
    print(f"Configuration valid: {is_valid}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
