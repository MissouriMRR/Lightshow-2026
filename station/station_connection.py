import asyncio
import queue
import threading
from typing import Protocol

import dronekit

from drone.json_parser import ConfigParser
from interdrone.networking_interface import NetworkingInterface
from interdrone.networking_thread import NetworkingThread
from station.ground_station_controller import DroneState, GroundStationController


class PositionReceiver(Protocol):
    """The slice of ``StationServer`` that :class:`StationConnection` calls back."""

    def set_position(self, id: str, pos: dronekit.LocationGlobalRelative) -> None: ...


class StationConnectionLike(Protocol):
    """The connection surface :class:`~station.station_server.StationServer` drives.

    Satisfied by :class:`StationConnection` (real networking) and
    :class:`~station.null_station_connection.NullStationConnection` (no-op).
    """

    def set_server(self, server: PositionReceiver, /) -> None: ...
    async def ping(self, id: str, /) -> bool: ...
    async def send_poll(self, id: str, /) -> dronekit.LocationGlobalRelative: ...
    async def arm_drone(self, id: str, /) -> bool: ...
    async def dearm_drone(self, id: str, /) -> None: ...
    async def send_takeoff(self, id: str, /) -> bool: ...
    async def send_step(self, id: str, /) -> None: ...
    async def send_landing(self, id: str, /) -> None: ...
    async def send_halt(self, id: str, /) -> None: ...
    async def tick(self) -> None: ...


class StationConnection:
    server: PositionReceiver | None

    def __init__(self, config: ConfigParser) -> None:
        self.gs: GroundStationController = GroundStationController(config)
        self.server = None

        networkingThreadClass = NetworkingThread()
        resourcesReady: queue.Queue[NetworkingInterface] = queue.Queue(maxsize=1)

        networkingThread = threading.Thread(
            target=networkingThreadClass.run_networking_thread,
            args=(resourcesReady, config),
            daemon=True,
        )
        networkingThread.start()

        self.gs.networking = resourcesReady.get()
        self.gs.set_location_hook(self.on_location)

    def set_server(self, server: PositionReceiver) -> None:
        self.server = server

    def on_location(self, id: int) -> None:
        assert self.server is not None, "set_server must be called first"
        lat, lon, alt = self.gs.drone_states[id].location
        self.server.set_position(
            str(id), dronekit.LocationGlobalRelative(lat, lon, alt)
        )

    async def ping(self, id: str) -> bool:
        self.gs.ping_drone(int(id))

        while True:
            self.gs.process_messages()
            if self.gs.drone_states[int(id)].is_responsive:
                return True
            await asyncio.sleep(0)

    async def send_poll(self, id: str) -> dronekit.LocationGlobalRelative:
        self.gs.poll_drones(target_drones=(int(id),))
        await self.get_response(id, None)
        loc = self.gs.drone_states[int(id)].location
        return dronekit.LocationGlobalRelative(loc[0], loc[1], loc[2])

    async def arm_drone(self, id: str) -> bool:
        self.gs.send_arm(target_drones=(int(id),))
        return await self.get_response(id, DroneState.ARMED)

    async def dearm_drone(self, _id: str) -> None:
        pass

    async def send_takeoff(self, id: str) -> bool:
        self.gs.send_takeoff(altitude=10.0, target_drones=(int(id),))
        return await self.get_response(id, DroneState.IN_FLIGHT)

    async def send_step(self, id: str) -> None:
        self.gs.send_frame_step(0, (int(id),))
        await self.get_response(id, None)

    async def send_landing(self, id: str) -> None:
        self.gs.send_land((int(id),))
        await self.get_response(id, None)

    async def send_halt(self, id: str) -> None:
        self.gs.send_halt((int(id),))
        await self.get_response(id, None)

    async def get_response(self, id: str, state: DroneState | None) -> bool:
        while True:
            self.gs.process_messages()
            if self.gs.drone_states[int(id)].pending_confirmation is None:
                return self.gs.drone_states[int(id)].state == state
            await asyncio.sleep(0)

    async def tick(self) -> None:
        self.gs.process_messages()
