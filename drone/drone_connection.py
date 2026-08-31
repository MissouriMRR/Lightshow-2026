import asyncio
import queue
import threading
import time
from typing import Protocol

from drone.drone_command_handler import DroneCommandHandler
from drone.json_parser import ConfigParser
from drone.vehicle import AnyVehicle
from interdrone.message_types import Message, MessageType
from interdrone.networking_interface import NetworkingInterface
from interdrone.networking_thread import NetworkingThread


class DroneController(Protocol):
    """The slice of ``drone.drone.Drone`` that :class:`DroneConnection` drives."""

    vehicle: AnyVehicle

    async def arm(self) -> bool: ...
    async def takeoff(self) -> None: ...
    async def step(self) -> None: ...
    async def land(self) -> None: ...
    async def halt(self) -> None: ...


class DroneConnection:
    def __init__(self, jsonConfigData: ConfigParser) -> None:
        drone_id = jsonConfigData.get_self_id()
        if drone_id is None:
            raise ValueError(
                "config is missing localInfo.selfId; call set_self_id first"
            )
        self.drone_id: str = drone_id

        networkingThreadClass = NetworkingThread()
        resourcesReady: queue.Queue[NetworkingInterface] = queue.Queue(maxsize=1)

        networkingThread = threading.Thread(
            target=networkingThreadClass.run_networking_thread,
            args=(resourcesReady, jsonConfigData),
            daemon=True,
        )
        networkingThread.start()

        self.networking: NetworkingInterface = resourcesReady.get()

        # Initialize command handler
        self.command_handler: DroneCommandHandler = DroneCommandHandler(
            drone_id=int(self.drone_id), networking=self.networking
        )

        self.lastHeartbeat: float = time.time()
        self.heartbeatInterval: float = 0.5

        self.drone: DroneController | None = None

    def register_callbacks(self, drone: DroneController) -> None:
        self.drone = drone

    def set_drone_pos(self) -> None:
        assert self.drone is not None, "register_callbacks must be called first"
        pos = self.drone.vehicle.location.global_relative_frame
        self.command_handler.set_drone_location(pos.lat, pos.lon, pos.alt)

    async def tick(self) -> None:
        assert self.drone is not None, "register_callbacks must be called first"

        # Process incoming commands and check for completion
        self.command_handler.process_commands()

        if self.command_handler.pending_command:
            match self.command_handler.pending_command.message.id:
                case MessageType.ARM:
                    await self.drone.arm()
                case MessageType.TAKEOFF:
                    await self.drone.takeoff()
                case MessageType.FRAME_STEP:
                    await self.drone.step()
                case MessageType.LAND:
                    await self.drone.land()
                case MessageType.HALT:
                    await self.drone.halt()
                case MessageType.POLL_DRONE_RESPONSE:
                    self.set_drone_pos()
                case _:
                    pass
            self.command_handler.pending_command.completed = True

        # Send periodic heartbeat
        currentTime = time.time()
        if currentTime - self.lastHeartbeat >= self.heartbeatInterval:
            self.set_drone_pos()

            heartbeatMessage = Message.create(
                id=MessageType.HEARTBEAT,
                dronesToSendData=(),
                data={
                    "senderId": int(self.drone_id),
                    "payload": f"Heartbeat from Drone {self.drone_id}",
                    "location": str(self.command_handler.drone_location),
                },
            )
            self.networking.queue_client_message(heartbeatMessage)
            self.lastHeartbeat = currentTime

        await asyncio.sleep(0.05)
