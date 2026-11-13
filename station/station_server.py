import asyncio
import contextlib
from enum import Enum
import queue
import threading
import time
from tkinter import messagebox

from PySide6.QtCore import QObject, Signal
import dronekit
from opengl_station import DroneStatus

from common.config import NETWORK_CONFIG_PATH, SHOW_PATH
from common.drone_state import DroneState
from drone.json_parser import ConfigParser
from interdrone.message_types import Message, MessageType
from interdrone.networking_interface import NetworkingInterface
from interdrone.networking_thread import NetworkingThread


class StationCommand(Enum):
    ARM = 0,
    TAKEOFF = 1,
    STEP = 2,
    LAND = 3,
    HALT = 4,


class StationServer(QObject):
    config: ConfigParser
    drones: dict[int, DroneState]
    num_frames: int
    show_index: int

    networking: NetworkingInterface | None
    _networking_thread: threading.Thread | None
    go: bool

    current_command: StationCommand | None

    drone_status_changed: Signal = Signal(int, DroneStatus)
    drone_position_changed: Signal = Signal(int, dronekit.LocationGlobalRelative)
    drone_color_changed: Signal = Signal(int, int, int, int)

    @property
    def armed(self) -> bool:
        return all([x.status == DroneStatus.ARMED for x in self.drones.values()])

    def __init__(self) -> None:
        super().__init__()
        self.config = ConfigParser(NETWORK_CONFIG_PATH, SHOW_PATH)
        self.config.set_self_id("0")

        self.networking = None

        # Drone tracking
        self.drones = {}
        self._initialize_drones()

        # Threading
        self._networking_thread = None

        # Timeouts
        self.confirmation_timeout = 30.0
        self.heartbeat_timeout = 10.0

        self.num_frames = len(self.config.get_frame_names("1"))
        self.show_index = 0

        self.go = True
        self.current_command = None

        self.start()

    async def run(self) -> None:
        await asyncio.gather(self.initial_connect(), self.dispatch_current_command(), self.process_messages())

    def stop(self):
        self.go = False

    def arm(self):
        self.current_command = StationCommand.ARM

    def takeoff(self):
        self.current_command = StationCommand.TAKEOFF

    def step(self):
        self.current_command = StationCommand.STEP

    def land(self):
        self.current_command = StationCommand.LAND

    def halt(self):
        self.current_command = StationCommand.HALT

    async def dispatch_current_command(self):
        while True:
            match self.current_command:
                case StationCommand.ARM:
                    await self._arm()
                case StationCommand.TAKEOFF:
                    await self._takeoff()
                case StationCommand.STEP:
                    await self._step()
                case StationCommand.LAND:
                    await self._land()
                case StationCommand.HALT:
                    await self._halt()
                case _:
                    pass
            self.current_command = None
            await asyncio.sleep(0)


    async def initial_connect(self) -> None:
        ids = [int(x) for x in self.config.get_drone_ids()[1:]]

        async def connect(drone_id: int) -> None:
            self.drone_status_changed.emit(drone_id, DroneStatus.DISCONNECTED)
            with contextlib.suppress(TimeoutError):
                async with asyncio.timeout(2):
                    self.ping_drone(drone_id)
                    while not self.drones[drone_id].is_responsive:
                        await asyncio.sleep(0)
                    self.drone_status_changed.emit(drone_id, DroneStatus.CONNECTED)
                    self.drones[drone_id] = DroneState()
                    ids.remove(drone_id)

        while len(ids) > 0:
            await asyncio.gather(
                *[connect(drone_id) for drone_id in ids]
            )

    async def confirmed(self, drone_id: int):
        while self.drones[drone_id].pending_confirmation is not None:
            await asyncio.sleep(0)

    async def _arm(self) -> None:
        if len(self.drones) != len(
            self.config.get_for_all_drones(self.config.get_drone_connection)
        ):
            messagebox.showerror("Error", "Not all drones connected")
            return

        async def and_set(drone_id: int):
            self.send_arm((drone_id,))
            await self.confirmed(drone_id)
            self.drones[drone_id].status = DroneStatus.ARMED;
            self.drone_status_changed.emit(drone_id, DroneStatus.ARMED)

        await asyncio.gather(*[and_set(drone_id) for drone_id in self.drones])

    async def _takeoff(self) -> None:
        if not self.armed:
            messagebox.showerror("Error", "Drones not armed")
            return
        elif list(filter(lambda x: x.frame != -1, self.drones.values())):
            messagebox.showerror("Error", "Drones already taken off")
            return

        async def send_takeoff(drone_id: int):
            self.send_takeoff(drone_id)
            await self.confirmed(drone_id)
            self.drones[drone_id].frame = 0

        await asyncio.gather(*[send_takeoff(drone_id) for drone_id in self.drones])

    async def _step(self) -> None:
        if list(filter(lambda x: x.frame == -1, self.drones.values())):
            messagebox.showerror("Error", "Drones not taken off")
        elif list(filter(lambda x: x.pending_confirmation is not None, self.drones.values())):
            messagebox.showerror("Error", "Frame transition in progress")
        elif self.num_frames <= self.show_index + 1:
            messagebox.showerror("Error", "No frames left to step")
        else:

            async def send(drone_id: int) -> None:
                self.send_frame_step(self.show_index, (drone_id,))
                await self.confirmed(drone_id)

                color = self.config.get_frame_color(
                    str(drone_id), "frame " + str(self.show_index)
                )
                if color is not None:
                    self.drone_color_changed.emit(drone_id, *color)

                self.drones[drone_id].frame = self.show_index

            self.show_index += 1
            await asyncio.gather(*[send(d) for d in self.drones])

    async def _land(self) -> None:
        if list(filter(lambda x: x.pending_confirmation is not None, self.drones.values())):
            messagebox.showerror("Error", "Frame transition in progress")
            return

        self.show_index = 0

        async def land(drone_id: int) -> None:
            self.send_land((drone_id,))
            await self.confirmed(drone_id)
            self.drones[drone_id].frame = -1
            self.drones[drone_id].status = DroneStatus.CONNECTED
            self.drone_status_changed.emit(drone_id, DroneStatus.CONNECTED)

        await asyncio.gather(*[land(drone_id) for drone_id in self.drones])

    async def _halt(self) -> None:
        async def halt(drone_id: int):
            self.send_halt((drone_id,))
            await self.confirmed(drone_id)
            self.drone_status_changed.emit(drone_id, DroneStatus.CONNECTED)

        await asyncio.gather(*[halt(drone_id) for drone_id in self.drones])

    confirmation_timeout: float
    heartbeat_timeout: float

    def _initialize_drones(self) -> None:
        """Initialize tracking for all drones (excluding GS at ID 0)"""
        all_drone_ids = self.config.get_drone_ids()
        for drone_id in all_drone_ids:
            if str(drone_id) != "0":
                self.drones[int(drone_id)] = DroneState()

    def start(self) -> None:
        """Start the ground station networking"""
        networking_thread_class = NetworkingThread()
        resources_ready: queue.Queue[NetworkingInterface] = queue.Queue(maxsize=1)

        self._networking_thread = threading.Thread(
            target=networking_thread_class.run_networking_thread,
            args=(resources_ready, self.config),
            daemon=True,
        )
        self._networking_thread.start()

        self.networking = resources_ready.get()
        print("[GS] Networking interface ready")

    def shutdown(self) -> None:
        """Shutdown ground station"""
        print("[GS] Shutting down...")

    def send_command_to_drones(
        self,
        command_type: MessageType,
        target_drones: tuple[int, ...] = (),
        payload: str = "",
    ) -> None:
        """
        Send command to specific drones.

        Args:
            command_type: Type of command to send
            target_drones: Tuple of drone IDs. Empty = broadcast to all
            payload: Command payload (altitude, frame ID, etc.)
        """
        if not self.networking:
            raise RuntimeError("Networking not initialized. Call start() first.")

        message = Message.create(
            id=command_type,
            dronesToSendData=target_drones,
            data={"payload": payload},
        )
        self.networking.queue_client_message(message)

        # Track pending confirmations
        if target_drones:
            for drone_id in target_drones:
                if drone_id in self.drones:
                    self.drones[
                        drone_id
                    ].pending_confirmation = self._get_confirmation_type(command_type)
                    self.drones[drone_id].pending_confirmation_time = time.time()
        else:
            # Broadcast
            for drone_status in self.drones.values():
                drone_status.pending_confirmation = self._get_confirmation_type(
                    command_type
                )
                drone_status.pending_confirmation_time = time.time()

        targets = target_drones if target_drones else "all"
        print(f"[GS] Sending {command_type.name} to drones {targets}")

    def _get_confirmation_type(self, command_type: MessageType) -> MessageType | None:
        """Get the confirmation type for a command"""
        match command_type:
            case MessageType.TAKEOFF:
                return MessageType.TAKEOFF_CONFIRMATION
            case MessageType.FRAME_STEP:
                return MessageType.FRAME_STEP_CONFIRMATION
            case MessageType.LAND:
                return MessageType.LAND_CONFIRMATION
            case MessageType.HALT:
                return MessageType.HALT_CONFIRMATION
            case MessageType.ARM:
                return MessageType.ARM_RESPONSE
            case _:
                return None

    def send_takeoff(
        self,
        altitude: float = 10.0,
        target_drones: tuple[int, ...] = (),
    ) -> None:
        """Send takeoff command"""
        self.send_command_to_drones(
            MessageType.TAKEOFF,
            target_drones=target_drones,
            payload=str(altitude),
        )

    def send_frame_step(
        self,
        frame_id: int,
        target_drones: tuple[int, ...] = (),
    ) -> None:
        """Send frame step command"""
        self.send_command_to_drones(
            MessageType.FRAME_STEP,
            target_drones=target_drones,
            payload=str(frame_id),
        )

    def send_land(
        self,
        target_drones: tuple[int, ...] = (),
    ) -> None:
        """Send land command"""
        self.send_command_to_drones(
            MessageType.LAND,
            target_drones=target_drones,
        )

    def send_halt(
        self,
        target_drones: tuple[int, ...] = (),
    ) -> None:
        """Send halt command"""
        self.send_command_to_drones(
            MessageType.HALT,
            target_drones=target_drones,
        )

    def send_arm(
        self,
        target_drones: tuple[int, ...] = (),
    ) -> None:
        """Send arm command to specific drones or broadcast to all"""
        if not self.networking:
            raise RuntimeError("Networking not initialized. Call start() first.")

        message = Message.create(
            id=MessageType.ARM,
            dronesToSendData=target_drones,
            data={
                "senderId": 0,
                "payload": "",
            },
        )
        self.networking.queue_client_message(message)

        # Track pending confirmations
        if target_drones:
            for drone_id in target_drones:
                if drone_id in self.drones:
                    self.drones[
                        drone_id
                    ].pending_confirmation = MessageType.ARM_RESPONSE
                    self.drones[drone_id].pending_confirmation_time = time.time()
        else:
            for drone_status in self.drones.values():
                drone_status.pending_confirmation = MessageType.ARM_RESPONSE
                drone_status.pending_confirmation_time = time.time()

        print(f"[GS] Sending ARM to drones {target_drones if target_drones else 'all'}")

    def send_emergency_halt(
        self,
        target_drones: tuple[int, ...] = (),
    ) -> None:
        """Send emergency halt to all or specific drones"""
        self.send_command_to_drones(
            MessageType.EMERGENCY_HALT,
            target_drones=target_drones,
        )

    def ping_drone(self, drone_id: int) -> None:
        """Send a PING to a specific drone"""
        if not self.networking:
            raise RuntimeError("Networking not initialized. Call start() first.")

        ping_message = Message.create(
            id=MessageType.PING,
            dronesToSendData=(drone_id,),
            data={
                "senderId": 0,
                "payload": "ping from GS",
            },
        )
        self.networking.queue_client_message(ping_message)
        print(f"[GS] Sent PING to drone {drone_id}")

    async def process_messages(self) -> None:
        """
        Process incoming messages from drones.
        Should be called regularly in main loop.
        """
        if not self.networking:
            raise RuntimeError("Networking not initialized. Call start() first.")

        while True:
            # Check for server messages (from drones)
            server_msg = self.networking.try_get_server_message(timeout=0.01)
            if server_msg is not None:
                self._handle_server_message(server_msg)

            # Check for client responses (confirmations from drones)
            client_msg = self.networking.try_get_client_response(timeout=0.01)
            if client_msg is not None:
                self._handle_client_response(client_msg)

            # Check for timeouts
            self._check_confirmations_timeout()
            self._check_heartbeat_timeout()

            await asyncio.sleep(0)

    def _handle_server_message(self, message: Message) -> None:
        """Handle messages from drones"""
        match message.id:
            case MessageType.HEARTBEAT:
                sender_id = message.data.get("senderId")
                if sender_id in self.drones:
                    self.drones[sender_id].last_heartbeat = time.time()
                    self.drones[sender_id].is_responsive = True
                    self.parse_location(message)

            case MessageType.POLL_DRONE_RESPONSE:
                self._handle_poll_response(message)

            case MessageType.PING:
                self._handle_ping(message)

            case MessageType.PING_RESPONSE:
                self._handle_ping_response(message)

            case (
                MessageType.TAKEOFF_CONFIRMATION
                | MessageType.FRAME_STEP_CONFIRMATION
                | MessageType.HALT_CONFIRMATION
                | MessageType.LAND_CONFIRMATION
            ):
                self._handle_confirmation(message)

            case MessageType.ARM_RESPONSE:
                self._handle_arm_response(message)

            case _:
                pass

    def _handle_client_response(self, message: Message) -> None:
        """Handle confirmation messages from drones"""
        match message.id:
            case (
                MessageType.TAKEOFF_CONFIRMATION
                | MessageType.FRAME_STEP_CONFIRMATION
                | MessageType.HALT_CONFIRMATION
                | MessageType.LAND_CONFIRMATION
            ):
                self._handle_confirmation(message)

            case MessageType.ARM_RESPONSE:
                self._handle_arm_response(message)

            case _:
                pass

    def _handle_confirmation(self, message: Message) -> None:
        """Handle command completion confirmation"""
        drone_id = message.data.get("droneId")
        status = message.data.get("status", "unknown")

        if drone_id not in self.drones:
            return

        drone_status = self.drones[drone_id]
        drone_status.pending_confirmation = None
        drone_status.pending_confirmation_time = 0.0

        if status == "success":
            print(f"[GS] Drone {drone_id} ✓ {message.id.name}")

            # Update state based on confirmation
            match message.id:
                case MessageType.ARM_RESPONSE:
                    drone_status.state = DroneStatus.ARMED
                case MessageType.LAND_CONFIRMATION:
                    drone_status.state = DroneStatus.CONNECTED
                case MessageType.HALT_CONFIRMATION:
                    drone_status.state = DroneStatus.CONNECTED
                case _:
                    pass
        else:
            print(f"[GS] Drone {drone_id} ✗ {message.id.name} failed")

    def _handle_arm_response(self, message: Message) -> None:
        """Handle ARM_RESPONSE from a drone"""
        drone_id = message.data.get("senderId")
        status = message.data.get("payload", "failed")

        if drone_id not in self.drones:
            return

        drone_status = self.drones[drone_id]
        drone_status.pending_confirmation = None
        drone_status.pending_confirmation_time = 0.0

        if status == "success":
            drone_status.state = DroneStatus.ARMED
            print(f"[GS] Drone {drone_id} ✓ ARMED successfully")
        else:
            print(f"[GS] Drone {drone_id} ✗ ARM failed: {status}")

    def _handle_poll_response(self, message: Message) -> None:
        """Handle drone location/status poll response"""
        drone_id = message.data.get("droneId")
        status = message.data.get("status", "unknown")

        if drone_id not in self.drones:
            return

        drone_status = self.drones[drone_id]
        drone_status.pending_confirmation = None
        drone_status.pending_confirmation_time = 0.0

        if status == "success":
            self.parse_location(message)
        else:
            print(f"[GS] Drone {drone_id} poll failed")

    def _handle_ping(self, message: Message) -> None:
        """Handle incoming PING from a drone - respond immediately"""
        if not self.networking:
            return
        sender_id = message.data.get("senderId", -1)
        print(f"[GS] PING received from drone {sender_id}, responding")

        response = Message.create(
            id=MessageType.PING_RESPONSE,
            dronesToSendData=(sender_id,),
            data={
                "senderId": 0,
                "payload": "pong from GS",
            },
        )
        self.networking.queue_client_message(response)

    def _handle_ping_response(self, message: Message) -> None:
        """Handle PING_RESPONSE from a drone"""
        sender_id = message.data.get("senderId", -1)
        print(f"[GS] PING_RESPONSE from drone {sender_id}")

        if sender_id in self.drones:
            self.drones[sender_id].is_responsive = True
            self.drones[sender_id].last_heartbeat = time.time()

    def _check_confirmations_timeout(self) -> None:
        """Check for pending confirmations that timed out"""
        current_time = time.time()

        for drone_id, drone_status in self.drones.items():
            if drone_status.pending_confirmation is not None:
                elapsed = current_time - drone_status.pending_confirmation_time

                if elapsed > self.confirmation_timeout:
                    pending = drone_status.pending_confirmation.name
                    print(f"[GS] Drone {drone_id} confirmation timeout: {pending}")
                    drone_status.is_responsive = False
                    drone_status.pending_confirmation = None

    def _check_heartbeat_timeout(self) -> None:
        """Check for drones that haven't heartbeated recently"""
        current_time = time.time()

        for drone_id, drone_status in self.drones.items():
            elapsed = current_time - drone_status.last_heartbeat

            if elapsed > self.heartbeat_timeout and drone_status.is_responsive:
                print(f"[GS] Drone {drone_id} heartbeat timeout")
                drone_status.is_responsive = False

    def get_swarm_status(self) -> dict[int, DroneState]:
        """Get status of all drones"""
        return {
            drone_id: drone_status
            for drone_id, drone_status in self.drones.items()
        }

    def get_drone_status(self, drone_id: int) -> DroneState | None:
        """Get status of a specific drone"""
        return self.drones.get(drone_id)

    def parse_location(self, message: Message) -> None:
        sender_id = int(message.data.get("senderId", -1))
        if sender_id not in self.drones:
            return
        location = str(message.data.get("location", ""))
        x, y, z = [float(v) for v in location[1:-1].split(",")]
        self.drones[sender_id].pos = dronekit.LocationGlobalRelative(x, y, z)
        self.drone_position_changed.emit(sender_id, self.drones[sender_id].pos)
