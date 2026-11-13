import asyncio
import queue
import threading

from opengl_station import DroneStatus

from common.drone_state import DroneState
from drone.json_parser import ConfigParser
from interdrone.networking_interface import NetworkingInterface
from interdrone.networking_thread import NetworkingThread
from station.ground_station_controller import GroundStationController


class StationConnection:

    def __init__(self, config: ConfigParser) -> None:
        self.gs: GroundStationController = GroundStationController(config)


    async def ping(self, id: int) -> bool:
        self.gs.ping_drone(id)

        while True:
            self.gs.process_messages()
            if self.gs.drone_states[id].is_responsive:
                return True
            await asyncio.sleep(0)

    async def arm_drone(self, id: int) -> bool:
        self.gs.send_arm(target_drones=(id,))
        return await self.get_response(id, DroneStatus.ARMED)

    async def dearm_drone(self, _id: int) -> None:
        pass

    async def send_takeoff(self, id: int) -> bool:
        self.gs.send_takeoff(altitude=10.0, target_drones=(id,))
        return await self.get_response(id, DroneStatus.ARMED)

    async def send_step(self, id: int) -> None:
        self.gs.send_frame_step(0, (id,))
        await self.get_response(id, None)

    async def send_landing(self, id: int) -> None:
        self.gs.send_land((id,))
        await self.get_response(id, None)

    async def send_halt(self, id: int) -> None:
        self.gs.send_halt((id,))
        await self.get_response(id, None)

    async def get_response(self, id: int, state: DroneStatus | None) -> bool:
        while True:
            self.gs.process_messages()
            if self.gs.drone_states[id].pending_confirmation is None:
                return self.gs.drone_states[id].state == state
            await asyncio.sleep(0)

    async def tick(self) -> None:
        self.gs.process_messages()

    def get_drones(self) -> dict[int, DroneState]:
        return self.gs.drone_states
