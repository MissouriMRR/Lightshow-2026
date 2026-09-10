import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from enum import Enum
from tkinter import messagebox

import dronekit

from common.drone_state import DroneState
from drone.json_parser import ConfigParser
from station.station_connection import StationConnection


class Message(Enum):
    ARM = 0
    TAKEOFF = 1
    STEP = 2
    LAND = 3
    HALT = 4


class StationServer:
    config: ConfigParser
    connection: StationConnection
    drones: dict[str, DroneState]
    show_index: int

    frames: list[list[dronekit.LocationGlobalRelative]]
    lifted: int
    altitude_index: int
    add: int
    current_message: Message | None

    drone_listener: Callable[[str], None]
    arm_listener: Callable[[], None]
    drone_position_listener: Callable[[], None]

    @property
    def armed(self) -> bool:
        return not len(list(filter(lambda x: not x.armed, self.drones.values())))

    def __init__(self, connection: StationConnection | None = None) -> None:
        self.config = ConfigParser("./Models/Example jsons/example_config.json")
        self.config.set_self_id("0")

        drone_frames = self.config.get_all_drone_frames()  # TODO not this
        drone_values = list(drone_frames.values())
        self.frames = [[] for _ in range(len(drone_values[0]))]
        for drone_index, frame_names in enumerate(drone_values):
            for frame_index, name in enumerate(frame_names):
                location = self.config.get_frame_location(str(drone_index + 1), name)
                if location is None:
                    raise ValueError(
                        f"Frame {name!r} for drone {drone_index + 1} has no coordinates"
                    )
                self.frames[frame_index].append(location)

        if connection is None:
            self.connection = StationConnection(self.config)
        else:
            self.connection = connection
        self.connection.set_server(self)

        for frame in self.frames:
            frame.sort(key=lambda loc: -loc.alt)
        self.drones = {}
        self.show_index = 0

        self.lifted = 0
        self.altitude_index = 0

        self.add = 0

        self.current_message = None

        # No-op until the GUI registers real listeners (see set_drone_listener etc.)
        self.drone_listener = lambda _drone_id: None
        self.arm_listener = lambda: None
        self.drone_position_listener = lambda: None

    async def run(self) -> None:
        await asyncio.gather(self.initial_connect(), self.process_messages())

    async def process_messages(self) -> None:
        while True:
            await self.connection.tick()

            match self.current_message:
                case Message.ARM:
                    await self._arm()
                case Message.TAKEOFF:
                    await self._takeoff()
                case Message.STEP:
                    await self._step()
                case Message.LAND:
                    await self._land()
                case Message.HALT:
                    await self._halt()
                case _:
                    pass

            self.current_message = None
            await asyncio.sleep(0)

    def set_drone_listener(
        self, drone_listener: Callable[[str], None], arm_listener: Callable[[], None]
    ) -> None:
        self.drone_listener = drone_listener
        self.arm_listener = arm_listener

    def set_drone_position_listener(
        self, drone_position_listener: Callable[[], None]
    ) -> None:
        self.drone_position_listener = drone_position_listener

    async def initial_connect(self) -> None:
        ids = self.config.get_drone_ids()[1:]

        async def connect(drone_id: str) -> None:
            with contextlib.suppress(Exception):
                async with asyncio.timeout(2):
                    await self.connection.ping(drone_id)
                    self.drone_listener(drone_id)
                    self.drones[drone_id] = DroneState()
                    await self.connection.send_poll(drone_id)

        while len(ids) > len(self.drones):
            await asyncio.gather(
                *[connect(drone_id) for drone_id in ids if drone_id not in self.drones]
            )

    def set_position(self, id: str, pos: dronekit.LocationGlobalRelative) -> None:
        if id in self.drones:
            self.drones[id].pos = pos
            self.drone_position_listener()

    def get_frame(self, num: int) -> list[dronekit.LocationGlobalRelative]:
        return self.frames[num]

    def current_frame(self) -> list[dronekit.LocationGlobalRelative]:
        return self.get_frame(self.show_index)

    def get_drone_positions(self) -> list[dronekit.LocationGlobalRelative]:
        return [drone.pos for drone in self.drones.values()]

    def get_drone_confirmeds(self) -> list[bool]:
        return [drone.confirmed for drone in self.drones.values()]

    def set_show_index(self, show_index: int) -> None:
        self.show_index = show_index

    async def dearm(self) -> None:
        dearmeds: list[Awaitable[object]] = []
        for drone_id in self.drones:
            dearmeds.append(self.connection.dearm_drone(drone_id))
            self.drones[drone_id].armed = False
        await asyncio.gather(*dearmeds)
        self.arm_listener()

    def arm(self) -> None:
        self.current_message = Message.ARM

    async def _arm(self) -> None:
        if len(self.drones) != len(
            self.config.get_for_all_drones(self.config.get_drone_connection)
        ):
            messagebox.showerror("Error", "Not all drones connected")
            return

        async def and_set(drone_id: str) -> bool:
            out = await self.connection.arm_drone(drone_id)
            self.drones[drone_id].armed = True
            return out

        for result in await asyncio.gather(*[and_set(d) for d in self.drones]):
            if not result:
                messagebox.showerror("Error", "Arming failed")
                await self.dearm()
                return

        self.arm_listener()

    def takeoff(self) -> None:
        self.current_message = Message.TAKEOFF

    async def _takeoff(self) -> None:
        if not self.armed:
            messagebox.showerror("Error", "Drones not armed")
            return
        elif list(filter(lambda x: x.frame != -1, self.drones.values())):
            messagebox.showerror("Error", "Drones already taken off")
            return

        lift_order = list(zip(self.drones.keys(), self.frames[0], strict=False))
        lift_order.sort(key=lambda pair: -pair[1].alt)
        for drone_id, _ in lift_order:
            self.drones[drone_id].confirmed = False
            self.drone_position_listener()
            await self.connection.send_takeoff(drone_id)
            self.drones[drone_id].confirmed = True
            self.drones[drone_id].frame = 0
            await self.connection.send_poll(drone_id)
            self.drone_position_listener()

    def step(self) -> None:
        self.current_message = Message.STEP

    async def _step(self) -> None:
        if list(filter(lambda x: x.frame == -1, self.drones.values())):
            messagebox.showerror("Error", "Drones not taken off")
        elif list(filter(lambda x: not x.confirmed, self.drones.values())):
            messagebox.showerror("Error", "Frame transition in progress")
        elif len(self.frames) <= self.show_index + 1:
            messagebox.showerror("Error", "No frames left to step")
        else:

            async def send(drone_id: str) -> None:
                self.drones[drone_id].confirmed = False
                self.drone_position_listener()
                await self.connection.send_step(drone_id)
                self.drones[drone_id].confirmed = True
                self.drones[drone_id].frame = self.show_index
                await self.connection.send_poll(drone_id)
                self.drone_position_listener()

            self.show_index += 1
            await asyncio.gather(*[send(d) for d in self.drones])

    def land(self) -> None:
        self.current_message = Message.LAND

    async def _land(self) -> None:
        if list(filter(lambda x: not x.confirmed, self.drones.values())):
            messagebox.showerror("Error", "Frame transition in progress")
            return

        lift_order = list(
            zip(self.drones.keys(), self.frames[self.show_index], strict=False)
        )
        lift_order.sort(key=lambda pair: pair[1].alt)

        self.show_index = 0

        for drone_id, _ in lift_order:
            self.drones[drone_id].confirmed = False
            await self.connection.send_landing(drone_id)
            self.drones[drone_id].confirmed = True
            self.drones[drone_id].frame = -1
            self.drones[drone_id].armed = False
            await self.connection.send_poll(drone_id)

        self.arm_listener()

    def halt(self) -> None:
        self.current_message = Message.HALT

    async def _halt(self) -> None:
        await asyncio.gather(*[self.connection.send_halt(d) for d in self.drones])
        self.arm_listener()
