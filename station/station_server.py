import asyncio
import contextlib
from enum import Enum
import queue
import threading
import time
from tkinter import messagebox
from typing import Any

from PySide6.QtCore import QObject, Signal
import dronekit
from opengl_station import DroneStatus
from pymavlink import mavutil

from common.config import NETWORK_CONFIG_PATH, SHOW_PATH
from common.drone_state import DroneState
from drone.config_parser import ConfigParser
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

    confirmation_timeout: float
    heartbeat_timeout: float

    drone_status_changed: Signal = Signal(int, DroneStatus)
    drone_position_changed: Signal = Signal(int, dronekit.LocationGlobalRelative)
    drone_color_changed: Signal = Signal(int, int, int, int)

    prearm_passing_changed: Signal = Signal(int, bool)
    status_text_added: Signal = Signal(int, int, str)
    battery_changed: Signal = Signal(int, int)


    def __init__(self) -> None:
        super().__init__()
        self.config = ConfigParser(NETWORK_CONFIG_PATH, SHOW_PATH)
        self.config.set_self_id("0")

        self.networking = None

        # Drone tracking
        self.drones = {}
        all_drone_ids = self.config.get_drone_ids()
        for drone_id in all_drone_ids:
            if drone_id != "0":
                self.drones[int(drone_id)] = DroneState()

        # Threading
        self._networking_thread = None

        # Timeouts
        self.confirmation_timeout = 30.0
        self.heartbeat_timeout = 10.0

        self.num_frames = len(self.config.get_frame_names("1"))
        self.show_index = 0

        self.go = True
        self.current_command = None

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

    async def run(self) -> None:
        await asyncio.gather(self.connect_to_drones(), self.dispatch_current_command(), self.process_messages(), self.check_mavproxy())

    async def connect_to_drones(self) -> None:
        async def connect(drone_id: int) -> None:
            with contextlib.suppress(TimeoutError):
                async with asyncio.timeout(2):
                    self.drone_status_changed.emit(int(drone_id), DroneStatus.DISCONNECTED)
                    self.send_basic_message(drone_id, MessageType.PING)
                    while not self.drones[drone_id].is_responsive:
                        await asyncio.sleep(0)
                    self.drone_status_changed.emit(drone_id, DroneStatus.CONNECTED)
                    self.drones[drone_id] = DroneState()
                    ids.remove(drone_id)

        while self.go:
            ids = [drone_id for drone_id in self.drones if not self.drones[drone_id].is_responsive]
            while len(ids) > 0:
                await asyncio.gather(
                    *[connect(drone_id) for drone_id in ids]
                )
            else:
                await asyncio.sleep(1.0)


    async def dispatch_current_command(self):
        while self.go:
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

    async def _arm(self) -> None:
        if not self.drones_all_connected():
            messagebox.showerror("Error", "Not all drones connected")
            return

        async def curry_arm(drone_id: int):
            self.send_basic_message(drone_id, MessageType.ARM)
            await self.confirmed(drone_id)
            self.drones[drone_id].status = DroneStatus.ARMED;
            self.drone_status_changed.emit(drone_id, DroneStatus.ARMED)

        await asyncio.gather(*[curry_arm(drone_id) for drone_id in self.drones])

    async def _takeoff(self) -> None:
        if not self.drones_all_armed():
            messagebox.showerror("Error", "Drones not armed")
            return
        elif list(filter(lambda x: x.frame != -1, self.drones.values())):
            messagebox.showerror("Error", "Drones already taken off")
            return

        async def curry_takeoff(drone_id: int):
            self.send_basic_message(drone_id, MessageType.TAKEOFF)
            await self.confirmed(drone_id)
            self.drones[drone_id].frame = 0

        await asyncio.gather(*[curry_takeoff(drone_id) for drone_id in self.drones])

    async def _step(self) -> None:
        if list(filter(lambda x: x.frame == -1, self.drones.values())):
            messagebox.showerror("Error", "Drones not taken off")
        elif list(filter(lambda x: x.pending_confirmation is not None, self.drones.values())):
            messagebox.showerror("Error", "Frame transition in progress")
        elif self.show_index >= self.num_frames:
            messagebox.showerror("Error", "No frames left to step")
        else:

            async def curry_send(drone_id: int) -> None:
                self.send_basic_message(drone_id, MessageType.FRAME_STEP, str(self.show_index))
                await self.confirmed(drone_id)

                color = self.config.get_frame_color(
                    str(drone_id), "frame " + str(self.show_index)
                )
                if color is not None:
                    self.drone_color_changed.emit(drone_id, *color)

                self.drones[drone_id].frame = self.show_index

            self.show_index += 1
            await asyncio.gather(*[curry_send(d) for d in self.drones])

    async def _land(self) -> None:
        if list(filter(lambda x: x.pending_confirmation is not None, self.drones.values())):
            messagebox.showerror("Error", "Frame transition in progress")
            return

        self.show_index = 0

        async def curry_land(drone_id: int) -> None:
            self.send_basic_message(drone_id, MessageType.LAND)
            await self.confirmed(drone_id)
            self.drones[drone_id].frame = -1
            self.drones[drone_id].status = DroneStatus.CONNECTED
            self.drone_status_changed.emit(drone_id, DroneStatus.CONNECTED)

        await asyncio.gather(*[curry_land(drone_id) for drone_id in self.drones])

    async def _halt(self) -> None:
        async def curry_halt(drone_id: int):
            self.send_basic_message(drone_id, MessageType.HALT)
            await self.confirmed(drone_id)
            self.drone_status_changed.emit(drone_id, DroneStatus.CONNECTED)

        await asyncio.gather(*[curry_halt(drone_id) for drone_id in self.drones])

    async def confirmed(self, drone_id: int):
        while self.drones[drone_id].pending_confirmation is not None:
            await asyncio.sleep(0)

    def drones_all_connected(self) -> bool:
        return all([x.is_responsive for x in self.drones.values()])

    def drones_all_armed(self) -> bool:
        return all([x.status == DroneStatus.ARMED for x in self.drones.values()])

    def send_basic_message(
        self,
        drone_id: int,
        message_type: MessageType,
        payload: str = ""
    ):
        if self.networking is None:
            raise RuntimeError("Networking not initialized. Call start() first.")

        self.networking.queue_client_message(Message.create(
            id=message_type,
            dronesToSendData=(drone_id,),
            data={
                "payload": payload,
            },
        ))

        self.drones[drone_id].pending_confirmation = self._get_confirmation_type(message_type)
        self.drones[drone_id].pending_confirmation_time = time.time()

        print(f"[GS] sending {message_type.name} to drone {drone_id}")


    async def process_messages(self) -> None:
        """
        Process incoming messages from drones.
        Should be called regularly in main loop.
        """
        if not self.networking:
            raise RuntimeError("Networking not initialized. Call start() first.")

        while self.go:
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
                return MessageType.ARM_CONFIRMATION
            case _:
                return None


    def _handle_server_message(self, message: Message) -> None:
        """Handle messages from drones"""
        match message.id:
            case MessageType.HEARTBEAT:
                sender_id = message.data.get("senderId")
                if sender_id in self.drones:
                    self.drones[sender_id].last_heartbeat = time.time()
                    self.drones[sender_id].is_responsive = True
                    self.parse_location(message)

            case MessageType.PING_RESPONSE:
                self._handle_ping_response(message)

            case (
                MessageType.TAKEOFF_CONFIRMATION
                | MessageType.FRAME_STEP_CONFIRMATION
                | MessageType.HALT_CONFIRMATION
                | MessageType.LAND_CONFIRMATION
                | MessageType.ARM_CONFIRMATION
            ):
                self._handle_confirmation(message)

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
                | MessageType.ARM_CONFIRMATION
            ):
                self._handle_confirmation(message)

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
                case MessageType.ARM_CONFIRMATION:
                    drone_status.state = DroneStatus.ARMED
                case MessageType.LAND_CONFIRMATION:
                    drone_status.state = DroneStatus.CONNECTED
                case MessageType.HALT_CONFIRMATION:
                    drone_status.state = DroneStatus.CONNECTED
                case _:
                    pass
        else:
            print(f"[GS] Drone {drone_id} ✗ {message.id.name} failed")

    def _handle_ping_response(self, message: Message) -> None:
        """Handle PING_RESPONSE from a drone"""
        sender_id = message.data.get("droneId", -1)
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
                    self.drone_status_changed.emit(drone_id, DroneStatus.DISCONNECTED)

    def _check_heartbeat_timeout(self) -> None:
        """Check for drones that haven't heartbeated recently"""
        current_time = time.time()

        for drone_id, drone_status in self.drones.items():
            elapsed = current_time - drone_status.last_heartbeat

            if elapsed > self.heartbeat_timeout and drone_status.is_responsive:
                print(f"[GS] Drone {drone_id} heartbeat timeout")
                drone_status.is_responsive = False
                self.drone_status_changed.emit(drone_id, DroneStatus.DISCONNECTED)

    def parse_location(self, message: Message) -> None:
        sender_id = int(message.data.get("senderId", -1))
        if sender_id not in self.drones:
            return
        location = str(message.data.get("location", ""))
        x, y, z = [float(v) for v in location[1:-1].split(",")]
        self.drones[sender_id].pos = dronekit.LocationGlobalRelative(x, y, z)
        self.drone_position_changed.emit(sender_id, self.drones[sender_id].pos)

    def stop(self):
        self.go = False

    async def check_mavproxy(self):
        connection = mavutil.mavlink_connection("udpin:127.0.0.1:5505")

        while self.go:
            msg: Any = connection.recv_match(type=["SYS_STATUS", "STATUSTEXT", "BATTERY_STATUS"], blocking=False)
            if msg is not None:
                drone_id = int(msg.get_srcSystem())

                match msg.get_type():
                    case "SYS_STATUS":
                        prearm_bit = mavutil.mavlink.MAV_SYS_STATUS_PREARM_CHECK
                        prearm_passing = bool(msg.onboard_control_sensors_health & prearm_bit)
                        if prearm_passing != self.drones[drone_id].prearm_passing:
                            self.prearm_passing_changed.emit(drone_id, prearm_passing)
                        self.drones[drone_id].prearm_passing = prearm_passing 
                    case "STATUSTEXT":
                        status_text = (msg.severity, msg.text)
                        self.drones[drone_id].add_line(status_text)
                        self.status_text_added.emit(drone_id, *status_text)
                    case "BATTERY_STATUS":
                        battery_changed = msg.battery_remaining != self.drones[drone_id].battery
                        self.drones[drone_id].battery = msg.battery_remaining
                        if battery_changed:
                            self.battery_changed.emit(drone_id, msg.battery_remaining)
                    case _:
                        pass
            await asyncio.sleep(0)

