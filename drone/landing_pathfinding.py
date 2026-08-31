"""
Landing Pathfinding Algorithm

This algorithm coordinates the landing of multiple drones by:
1. Taking the position of each drone's last node
2. One drone begins to land, lowest altitude first
3. After it arrives, land the drone from the next lowest node
4. Repeat until all drones are done
"""

import asyncio
import json
import logging

import dronekit

from drone.drone import Drone
from drone.goto import move_to
from drone.vehicle import AnyVehicle

type DroneOrVehicle = Drone | AnyVehicle


class LandingPathfinding:
    """
    Manages sequential landing of drones from assigned nodes.
    """

    def __init__(
        self,
        drones: list[DroneOrVehicle],
        landing_nodes: list[dronekit.LocationGlobalRelative],
    ) -> None:
        """
        Initialize the landing pathfinding algorithm.

        Args:
            drones: List of drone objects (must have vehicle attribute with dronekit.Vehicle)
            landing_nodes: List of landing target nodes (dronekit.LocationGlobalRelative) to assign to drones.
                          These should be the last positions from the config JSON.
        """
        self.drones: list[DroneOrVehicle] = drones

        # Sort by altitude, lowest first
        self.landing_nodes: list[dronekit.LocationGlobalRelative] = sorted(
            landing_nodes, key=lambda node: node.alt, reverse=False
        )

        # drone_index -> landing_node
        self.drone_landing_assignments: dict[int, dronekit.LocationGlobalRelative] = {}
        self.completed_landing_drones: set[int] = set()

        if len(drones) > len(landing_nodes):
            logging.warning(
                f"More drones ({len(drones)}) than landing nodes ({len(landing_nodes)}). Some drones will not be assigned."
            )
        elif len(landing_nodes) > len(drones):
            logging.warning(
                f"More landing nodes ({len(landing_nodes)}) than drones ({len(drones)}). Some nodes will not be used."
            )

    def assign_nodes(self) -> None:
        """
        Assign each drone to a landing node.
        Drones are assigned to nodes in order, with lowest altitude nodes assigned first.
        """
        num_assignments = min(len(self.drones), len(self.landing_nodes))

        for i in range(num_assignments):
            node = self.landing_nodes[i]
            self.drone_landing_assignments[i] = node
            logging.info(
                f"Assigned drone {i} to landing node at ({node.lat:.6f}, {node.lon:.6f}, {node.alt:.2f}m)"
            )

    async def land_drone(self, drone_index: int) -> bool:
        """
        Land a single drone using dronekit's LAND or RTL mode.

        Args:
            drone_index: Index of the drone in the drones list

        Returns:
            True if drone successfully initiated landing, False otherwise
        """
        if drone_index not in self.drone_landing_assignments:
            logging.warning(
                f"Drone {drone_index} has no assigned landing node. Skipping."
            )
            return False

        if drone_index >= len(self.drones):
            logging.error(f"Drone index {drone_index} is out of range.")
            return False

        drone = self.drones[drone_index]
        target_node = self.drone_landing_assignments[drone_index]

        # A Drone wraps a vehicle; a raw vehicle is one already.
        vehicle: AnyVehicle = drone.vehicle if isinstance(drone, Drone) else drone

        try:
            # First, ensure the drone is at its final position before landing
            logging.info(
                f"Moving drone {drone_index} to final position ({target_node.lat:.6f}, {target_node.lon:.6f}, {target_node.alt:.2f}m)"
            )
            await move_to(
                vehicle,
                target_node.lat,
                target_node.lon,
                target_node.alt,
            )

            # Wait for mode to be changeable (should be in GUIDED mode after move_to)
            # Give it a moment to ensure mode is stable
            await asyncio.sleep(1.0)

            # Use dronekit's built-in landing mode
            logging.info(f"Setting drone {drone_index} to RTL (Return to Launch) mode")
            vehicle.mode = dronekit.VehicleMode("RTL")
            target_mode = "RTL"
            # Wait for mode change to take effect
            timeout = 10  # 10 second timeout
            elapsed = 0
            while vehicle.mode.name != target_mode and elapsed < timeout:
                await asyncio.sleep(0.5)
                elapsed += 0.5

            if vehicle.mode.name != target_mode:
                logging.warning(
                    f"Drone {drone_index} mode change to {target_mode} may not have taken effect. Current mode: {vehicle.mode.name}"
                )

            self.completed_landing_drones.add(drone_index)
            logging.info(
                f"Drone {drone_index} successfully initiated landing sequence."
            )
            return True

        except Exception as e:
            logging.error(f"Error landing drone {drone_index}: {e}")
            return False

    async def execute_sequential_landing(self) -> None:
        """
        Execute the sequential landing algorithm.
        Moves drones one at a time to their assigned landing nodes, starting with the lowest altitude.
        """
        self.assign_nodes()

        logging.info(
            f"Starting sequential landing for {len(self.drone_landing_assignments)} drones."
        )

        # Process drones in order (lowest altitude first)
        for drone_index in sorted(self.drone_landing_assignments.keys()):
            if drone_index in self.completed_landing_drones:
                continue

            # Move this drone to its assigned landing node
            success = await self.land_drone(drone_index)

            if not success:
                logging.warning(
                    f"Drone {drone_index} failed to reach its landing node. Continuing with next drone."
                )

        logging.info(
            f"Sequential landing complete. {len(self.completed_landing_drones)}/{len(self.drone_landing_assignments)} drones landed."
        )

    def get_landing_assignment(
        self, drone_index: int
    ) -> dronekit.LocationGlobalRelative | None:
        """
        Get the assigned landing node for a specific drone.

        Args:
            drone_index: Index of the drone

        Returns:
            Assigned landing node or None if not assigned
        """
        return self.drone_landing_assignments.get(drone_index)

    def is_landing_complete(self) -> bool:
        """
        Check if all assigned drones have completed their landing.

        Returns:
            True if all drones have landed
        """
        return len(self.completed_landing_drones) == len(self.drone_landing_assignments)


def load_last_positions_from_json(
    config_json_path: str,
) -> list[dronekit.LocationGlobalRelative]:
    """
    Load the last positions for each drone from the config JSON file.

    Args:
        config_json_path: Path to the config JSON file containing drone configurations
                         and coordinates. The file should have a "coordinates" section
                         with drone IDs as keys, each containing stages with [lat, lon, alt] arrays.

    Returns:
        List of LocationGlobalRelative objects representing the last position (highest stage number) for each drone,
        sorted by altitude (lowest first) to match the landing algorithm's behavior.
    """
    # Load config JSON
    with open(config_json_path, "r") as f:
        config_data = json.load(f)

    # Get coordinates section
    if "coordinates" not in config_data:
        logging.error(f"No 'coordinates' section found in {config_json_path}")
        return []

    coordinates_data = config_data["coordinates"]

    # Optionally filter by drones section if it exists
    drone_ids = None
    if "drones" in config_data:
        drone_ids = list(config_data["drones"].keys())

    # Extract last position (highest stage number) for each drone
    # Store as (drone_id, location) tuples to preserve mapping
    last_positions_with_ids: list[tuple[str, dronekit.LocationGlobalRelative]] = []
    for drone_id, stages in coordinates_data.items():
        # Skip if filtering by drones section and this drone isn't in the list
        if drone_ids is not None and drone_id not in drone_ids:
            continue

        # Find the last stage (highest stage number)
        stage_numbers: list[tuple[int, str]] = []
        for stage_key in stages:
            if stage_key.startswith("stage "):
                try:
                    stage_num = int(stage_key.split(" ")[1])
                    stage_numbers.append((stage_num, stage_key))
                except (ValueError, IndexError):
                    logging.warning(
                        f"Invalid stage key format: {stage_key} for drone {drone_id}"
                    )
                    continue

        if not stage_numbers:
            logging.warning(f"No valid stages found for drone {drone_id}")
            continue

        # Get the stage with the highest number
        last_stage_key = max(stage_numbers, key=lambda x: x[0])[1]
        last_pos = stages[last_stage_key]

        if not isinstance(last_pos, list) or len(last_pos) != 3:
            logging.warning(
                f"Invalid position format for drone {drone_id}: expected [lat, lon, alt], got {last_pos}"
            )
            continue

        lat, lon, alt = last_pos
        location = dronekit.LocationGlobalRelative(lat, lon, alt)
        last_positions_with_ids.append((drone_id, location))
        logging.info(
            f"Loaded last position ({last_stage_key}) for drone {drone_id}: ({lat:.6f}, {lon:.6f}, {alt:.2f}m)"
        )

    # Sort by altitude (lowest first) to match landing algorithm behavior
    last_positions_with_ids.sort(key=lambda x: x[1].alt, reverse=False)

    # Return just the locations (sorted by altitude)
    return [location for _, location in last_positions_with_ids]


async def land_swarm_from_json(
    drones: list[DroneOrVehicle],
    config_json_path: str,
) -> None:
    """
    This function loads the last positions (highest stage) from the config JSON file and uses them
    as the final positions. Drones will move to these positions and then land using dronekit's LAND or RTL mode.

    Args:
        drones: List of drone objects
        config_json_path: Path to the config JSON file containing drone configurations
                         and coordinates. The file should have a "coordinates" section
                         with drone IDs as keys, each containing stages with [lat, lon, alt] arrays.
    """
    landing_nodes = load_last_positions_from_json(config_json_path)
    pathfinding = LandingPathfinding(drones, landing_nodes)
    await pathfinding.execute_sequential_landing()


# Example usage
async def example_with_json_files():
    """
    Example of how to use the landing pathfinding algorithm.
    """
    # Example: Load positions from config JSON file
    # from drone import Drone
    # from station import Station
    #
    # station = Station()
    #
    # # Load drone configurations and positions from config JSON
    # config_json = "Pathfinding/example_config.json"
    #
    # with open(config_json, "r") as f:
    #     config_data = json.load(f)
    #     drone_ids = list(config_data["drones"].keys())
    # drones = [
    #     Drone(station, drone_id, [])
    #     for drone_id in drone_ids
    # ]
    # await land_swarm_from_json(drones, config_json)


if __name__ == "__main__":
    # Run example (uncomment when drones are connected)
    # asyncio.run(example_with_json_files())
    pass
