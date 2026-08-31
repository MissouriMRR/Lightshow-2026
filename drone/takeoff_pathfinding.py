"""
Takeoff Pathfinding Algorithm

This algorithm coordinates the takeoff of multiple drones by:
1. Assigning each drone to a node
2. One drone moves to the highest node by altitude
3. After it arrives, move a different drone to the next highest node
4. Repeat until all drones are done
"""

import json
import logging

import dronekit

from drone.drone import Drone
from drone.goto import move_to
from drone.vehicle import AnyVehicle

type DroneOrVehicle = Drone | AnyVehicle


class TakeoffPathfinding:
    """
    Manages sequential takeoff of drones to assigned nodes.
    """

    def __init__(
        self,
        drones: list[DroneOrVehicle],
        nodes: list[dronekit.LocationGlobalRelative],
    ) -> None:
        """
        Initialize the takeoff pathfinding algorithm.

        Args:
            drones: List of drone objects (must have vehicle attribute with dronekit.Vehicle)
            nodes: List of target nodes (dronekit.LocationGlobalRelative) to assign to drones.
                   If None, will use drone.model from each drone (if available)
        """
        self.drones: list[DroneOrVehicle] = drones

        # Sort by altitude, highest first
        self.nodes: list[dronekit.LocationGlobalRelative] = sorted(
            nodes, key=lambda node: node.alt, reverse=True
        )
        # drone_index -> node
        self.drone_assignments: dict[int, dronekit.LocationGlobalRelative] = {}
        self.completed_drones: set[int] = set()

        if len(drones) > len(nodes):
            logging.warning(
                f"More drones ({len(drones)}) than nodes ({len(nodes)}). Some drones will not be assigned."
            )
        elif len(nodes) > len(drones):
            logging.warning(
                f"More nodes ({len(nodes)}) than drones ({len(drones)}). Some nodes will not be used."
            )

    def assign_nodes(self) -> None:
        """
        Assign each drone to a node.
        Drones are assigned to nodes in order, with highest altitude nodes assigned first.
        """
        num_assignments = min(len(self.drones), len(self.nodes))

        for i in range(num_assignments):
            node = self.nodes[i]
            self.drone_assignments[i] = node
            logging.info(
                f"Assigned drone {i} to node at ({node.lat:.6f}, {node.lon:.6f}, {node.alt:.2f}m)"
            )

    async def takeoff_drone(self, drone_index: int) -> bool:
        """
        Move a single drone to its assigned node.

        Args:
            drone_index: Index of the drone in the drones list

        Returns:
            True if drone successfully reached its node, False otherwise
        """
        if drone_index not in self.drone_assignments:
            logging.warning(f"Drone {drone_index} has no assigned node. Skipping.")
            return False

        if drone_index >= len(self.drones):
            logging.error(f"Drone index {drone_index} is out of range.")
            return False

        drone = self.drones[drone_index]
        target_node = self.drone_assignments[drone_index]

        # A Drone wraps a vehicle; a raw vehicle is one already.
        vehicle: AnyVehicle = drone.vehicle if isinstance(drone, Drone) else drone

        logging.info(
            f"Moving drone {drone_index} to node at altitude {target_node.alt:.2f}m"
        )

        try:
            await move_to(vehicle, target_node.lat, target_node.lon, target_node.alt)

            self.completed_drones.add(drone_index)
            logging.info(f"Drone {drone_index} successfully reached its assigned node.")
            return True

        except Exception as e:
            logging.error(f"Error moving drone {drone_index} to its node: {e}")
            return False

    async def execute_sequential_takeoff(self) -> None:
        """
        Execute the sequential takeoff algorithm.
        Moves drones one at a time to their assigned nodes, starting with the highest altitude.
        """
        self.assign_nodes()

        logging.info(
            f"Starting sequential takeoff for {len(self.drone_assignments)} drones."
        )

        # Process drones in order
        for drone_index in sorted(self.drone_assignments.keys()):
            if drone_index in self.completed_drones:
                continue

            # Move this drone to its assigned node
            success = await self.takeoff_drone(drone_index)

            if not success:
                logging.warning(
                    f"Drone {drone_index} failed to reach its node. Continuing with next drone."
                )

        logging.info(
            f"Sequential takeoff complete. {len(self.completed_drones)}/{len(self.drone_assignments)} drones reached their nodes."
        )

    def get_assignment(
        self, drone_index: int
    ) -> dronekit.LocationGlobalRelative | None:
        """
        Get the assigned node for a specific drone.

        Args:
            drone_index: Index of the drone

        Returns:
            Assigned node or None if not assigned
        """
        return self.drone_assignments.get(drone_index)

    def is_complete(self) -> bool:
        """
        Check if all assigned drones have completed their takeoff.

        Returns:
            True if all drones have reached their nodes
        """
        return len(self.completed_drones) == len(self.drone_assignments)


def load_first_positions_from_json(
    config_json_path: str,
) -> list[dronekit.LocationGlobalRelative]:
    """
    Load the first positions for each drone from the config JSON file.

    Args:
        config_json_path: Path to the config JSON file containing drone configurations
                         and coordinates. The file should have a "coordinates" section
                         with drone IDs as keys, each containing stages with [lat, lon, alt] arrays.

    Returns:
        List of LocationGlobalRelative objects representing the first position (stage 1) for each drone,
        sorted by altitude (highest first) to match the takeoff algorithm's behavior.
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

    # Extract first position (stage 1) for each drone
    first_positions: list[dronekit.LocationGlobalRelative] = []
    for drone_id, stages in coordinates_data.items():
        # Skip if filtering by drones section and this drone isn't in the list
        if drone_ids is not None and drone_id not in drone_ids:
            continue

        # Get stage 1 (first position)
        if "stage 1" not in stages:
            logging.warning(f"No 'stage 1' found for drone {drone_id}")
            continue

        first_pos = stages["stage 1"]
        if not isinstance(first_pos, list) or len(first_pos) != 3:
            logging.warning(
                f"Invalid position format for drone {drone_id}: expected [lat, lon, alt], got {first_pos}"
            )
            continue

        lat, lon, alt = first_pos
        location = dronekit.LocationGlobalRelative(lat, lon, alt)
        first_positions.append(location)
        logging.info(
            f"Loaded first position for drone {drone_id}: ({lat:.6f}, {lon:.6f}, {alt:.2f}m)"
        )

    # Sort by altitude (highest first) to match takeoff algorithm behavior
    first_positions.sort(key=lambda pos: pos.alt, reverse=True)

    return first_positions


async def takeoff_swarm_from_json(
    drones: list[DroneOrVehicle],
    config_json_path: str,
) -> None:
    """
    This function loads the first positions (stage 1) from the config JSON file and uses them
    as the takeoff targets for the drones.

    Args:
        drones: List of drone objects
        config_json_path: Path to the config JSON file containing drone configurations
                         and coordinates. The file should have a "coordinates" section
                         with drone IDs as keys, each containing stages with [lat, lon, alt] arrays.
    """
    nodes = load_first_positions_from_json(config_json_path)
    pathfinding = TakeoffPathfinding(drones, nodes)
    await pathfinding.execute_sequential_takeoff()


# Example usage
async def example_with_json_files():
    """
    Example of how to use the takeoff pathfinding algorithm.
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
    # await takeoff_swarm_from_json(drones, config_json)


if __name__ == "__main__":
    # Run example (uncomment when drones are connected)
    # asyncio.run(example_with_json_files())
    pass
