import asyncio
from enum import Enum

import dronekit

from drone.drone_connection import DroneConnection
from drone.goto import move_to
from drone.json_parser import ConfigParser
from drone.sim_vehicle import SimVehicle
from drone.vehicle import AnyVehicle


class Drone:
    class State(Enum):
        GetPosition = 1
        LiftOff = 2
        GetOtherPositions = 3
        CommunicateShowState = 4
        MoveToPredefinedPosition = 5
        PTGPathfinding = 6

    vehicle: AnyVehicle
    model: list[dronekit.LocationGlobalRelative]

    show_index: int
    state: State

    _initialized: bool

    connection: DroneConnection
    jsonConfigData: ConfigParser

    def __init__(
        self,
        drone_id: str,
        connection: DroneConnection | None = None,
        use_test_vehicle: bool = True,
        vehicle_connection_string: str = "",
    ) -> None:
        self.jsonConfigData = ConfigParser("./Models/Example jsons/example_config.json")
        self.jsonConfigData.set_self_id(drone_id)

        if connection is None:
            self.connection = DroneConnection(self.jsonConfigData)
        else:
            self.connection = connection
        self.connection.register_callbacks(self)

        # Initialize drone and connect to flight controller
        if use_test_vehicle:
            self.vehicle = SimVehicle()
            print("[Drone] Using SimVehicle for simulation")
        else:
            self.vehicle = self._connect_to_vehicle(vehicle_connection_string or None)

        # TODO: Implement with JSON "Show" Class object
        self.model = []
        for name in self.jsonConfigData.get_frame_names(drone_id):
            location = self.jsonConfigData.get_frame_location(drone_id, name)
            if location is None:
                raise ValueError(
                    f"Frame {name!r} for drone {drone_id} has no valid coordinates"
                )
            self.model.append(location)

        self.show_index = -1
        self.state = self.State.GetPosition
        self._initialized = False

    def _connect_to_vehicle(
        self, connection_string: str | None = None
    ) -> dronekit.Vehicle:
        """
        Connect to the flight controller via DroneKit.

        Args:
            connection_string: Connection string for the flight controller.
                Common examples:
                - Windows USB: 'COM14' or 'Com14'
                - Windows Telemetry Radio: 'com14' (also set baud=57600)
                - Linux USB: '/dev/ttyUSB0'
                - Linux Serial (Raspberry Pi): '/dev/ttyAMA0' (also set baud=57600)

                If None, attempts common defaults for Windows and Linux platforms.

        Returns:
            Connected dronekit.Vehicle instance

        Raises:
            TimeoutError: If unable to connect to flight controller
        """
        # Default connection attempts if none provided
        if connection_string is None:
            connection_attempts = [
                # Windows USB connections (COM 3-14)
                "COM14:57600",
                "COM3:57600",
                "COM4:57600",
                # Linux USB/Serial connections
                "/dev/ttyUSB0",  # Linux USB
                "/dev/ttyAMA0",  # Raspberry Pi UART
            ]
        else:
            connection_attempts = [connection_string]

        last_error = None

        for attempt in connection_attempts:
            try:
                print(f"[Drone] Attempting connection to flight controller: {attempt}")
                vehicle = dronekit.connect(attempt, wait_ready=True, timeout=10)
                print(
                    f"[Drone] Successfully connected to flight controller via {attempt}"
                )
                return vehicle
            except Exception as e:
                last_error = e
                print(f"[Drone] Failed to connect via {attempt}: {e}")
        # If all attempts failed, raise error
        attempts = len(connection_attempts)
        raise TimeoutError(
            f"[Drone] Failed to connect after {attempts} attempts; last error: {last_error}"
        )

    async def arm(self) -> bool:
        while not self.vehicle.is_armable:
            await asyncio.sleep(0)

        self.vehicle.mode = dronekit.VehicleMode("GUIDED")
        self.vehicle.armed = True
        while not self.vehicle.armed or self.vehicle.mode.name != "GUIDED":
            await asyncio.sleep(0)
        return True

    async def dearm(self) -> bool:
        self.vehicle.armed = False
        while self.vehicle.armed:
            await asyncio.sleep(0)
        return True

    async def takeoff(self) -> None:
        self.show_index = 0
        self.vehicle.simple_takeoff(self.model[0].alt)
        while (
            self.vehicle.location.global_relative_frame.alt < self.model[0].alt * 0.95
        ):
            await asyncio.sleep(0)

        await move_to(
            self.vehicle, self.model[0].lat, self.model[0].lon, self.model[0].alt
        )

    async def step(self) -> None:
        self.show_index += 1
        await move_to(
            self.vehicle,
            self.model[self.show_index].lat,
            self.model[self.show_index].lon,
            self.model[self.show_index].alt,
        )

    async def land(self) -> None:
        self.show_index = -1

        self.vehicle.mode = dronekit.VehicleMode("LAND")
        while self.vehicle.location.global_relative_frame.alt > 0:
            await asyncio.sleep(0)

        self.vehicle.armed = False
        while self.vehicle.armed:
            await asyncio.sleep(0)

    async def halt(self) -> None:
        self.vehicle.mode = dronekit.VehicleMode("LOITER")
        await asyncio.sleep(0.1)

    # Dispatch function based on drone state enum to be run in an infinite loop
    async def tick(self) -> None:
        await self.connection.tick()
