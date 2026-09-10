# ground_station_controller.py

import queue
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from drone.json_parser import ConfigParser
from interdrone.message_types import Message, MessageType
from interdrone.networking_interface import NetworkingInterface
from interdrone.networking_thread import NetworkingThread


class DroneState(Enum):
    """Drone operational states"""

    UNKNOWN = "unknown"
    IDLE = "idle"
    ARMED = "armed"
    TAKING_OFF = "taking_off"
    IN_FLIGHT = "in_flight"
    LANDING = "landing"
    LANDED = "landed"
    EMERGENCY_HALT = "emergency_halt"


@dataclass
class DroneStatus:
    """Track status of a drone"""

    drone_id: int
    state: DroneState = DroneState.UNKNOWN
    location: tuple[float, float, float] = (0.0, 0.0, 0.0)
    last_heartbeat: float = field(default_factory=time.time)
    is_responsive: bool = False
    pending_confirmation: MessageType | None = None
    pending_confirmation_time: float = 0.0


class GroundStationController:
    """
    Ground Station Controller for commanding drone swarms.
    Sends commands to drones and tracks their status.
    """

    config: ConfigParser
    networking: NetworkingInterface | None
    drone_states: dict[int, DroneStatus]
    _shutdown: bool
    _networking_thread: threading.Thread | None
    confirmation_timeout: float
    heartbeat_timeout: float
    on_set_location: Callable[[int], None]

    def __init__(self, config: ConfigParser) -> None:
        self.config = config
        self.networking = None

        # Drone tracking
        self.drone_states = {}
        self._initialize_drone_states()

        # Threading
        self._shutdown = False
        self._networking_thread = None

        # Timeouts
        self.confirmation_timeout = 30.0
        self.heartbeat_timeout = 10.0

        self.on_set_location = lambda _drone_id: None

    def set_location_hook(self, on_set_location: Callable[[int], None]) -> None:
        self.on_set_location = on_set_location

    def _initialize_drone_states(self) -> None:
        """Initialize tracking for all drones (excluding GS at ID 0)"""
        all_drone_ids = self.config.get_drone_ids()
        for drone_id in all_drone_ids:
            if str(drone_id) != "0":
                self.drone_states[int(drone_id)] = DroneStatus(drone_id=int(drone_id))

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
        self._shutdown = True
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
                if drone_id in self.drone_states:
                    self.drone_states[
                        drone_id
                    ].pending_confirmation = self._get_confirmation_type(command_type)
                    self.drone_states[drone_id].pending_confirmation_time = time.time()
        else:
            # Broadcast
            for drone_status in self.drone_states.values():
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
                if drone_id in self.drone_states:
                    self.drone_states[
                        drone_id
                    ].pending_confirmation = MessageType.ARM_RESPONSE
                    self.drone_states[drone_id].pending_confirmation_time = time.time()
        else:
            for drone_status in self.drone_states.values():
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

    def poll_drones(
        self,
        target_drones: tuple[int, ...] = (),
    ) -> None:
        """Poll drones for location/status. Not yet wired up; see commented body."""
        del target_drones
        # self.send_command_to_drones(
        #     MessageType.POLL_DRONE,
        #     target_drones=target_drones,
        # )
        #
        # if target_drones:
        #     for drone_id in target_drones:
        #         if drone_id in self.drone_states:
        #             self.drone_states[drone_id].pending_confirmation = (
        #                 MessageType.POLL_DRONE_RESPONSE
        #             )
        #             self.drone_states[drone_id].pending_confirmation_time = (
        #                 time.time()
        #             )
        # else:
        #     for drone_status in self.drone_states.values():
        #         drone_status.pending_confirmation = MessageType.POLL_DRONE_RESPONSE
        #         drone_status.pending_confirmation_time = time.time()

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

    def process_messages(self) -> None:
        """
        Process incoming messages from drones.
        Should be called regularly in main loop.
        """
        if not self.networking:
            return

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

    def _handle_server_message(self, message: Message) -> None:
        """Handle messages from drones"""
        match message.id:
            case MessageType.HEARTBEAT:
                sender_id = message.data.get("senderId")
                if sender_id in self.drone_states:
                    self.drone_states[sender_id].last_heartbeat = time.time()
                    self.drone_states[sender_id].is_responsive = True
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

        if drone_id not in self.drone_states:
            return

        drone_status = self.drone_states[drone_id]
        drone_status.pending_confirmation = None
        drone_status.pending_confirmation_time = 0.0

        if status == "success":
            print(f"[GS] Drone {drone_id} ✓ {message.id.name}")

            # Update state based on confirmation
            match message.id:
                case MessageType.ARM_RESPONSE:
                    drone_status.state = DroneState.ARMED
                case MessageType.TAKEOFF_CONFIRMATION:
                    drone_status.state = DroneState.IN_FLIGHT
                case MessageType.LAND_CONFIRMATION:
                    drone_status.state = DroneState.LANDED
                case MessageType.HALT_CONFIRMATION:
                    drone_status.state = DroneState.IDLE
                case _:
                    pass
        else:
            print(f"[GS] Drone {drone_id} ✗ {message.id.name} failed")

    def _handle_arm_response(self, message: Message) -> None:
        """Handle ARM_RESPONSE from a drone"""
        drone_id = message.data.get("senderId")
        status = message.data.get("payload", "failed")

        if drone_id not in self.drone_states:
            return

        drone_status = self.drone_states[drone_id]
        drone_status.pending_confirmation = None
        drone_status.pending_confirmation_time = 0.0

        if status == "success":
            drone_status.state = DroneState.ARMED
            print(f"[GS] Drone {drone_id} ✓ ARMED successfully")
        else:
            print(f"[GS] Drone {drone_id} ✗ ARM failed: {status}")

    def _handle_poll_response(self, message: Message) -> None:
        """Handle drone location/status poll response"""
        drone_id = message.data.get("droneId")
        status = message.data.get("status", "unknown")

        if drone_id not in self.drone_states:
            return

        drone_status = self.drone_states[drone_id]
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

        if sender_id in self.drone_states:
            self.drone_states[sender_id].is_responsive = True
            self.drone_states[sender_id].last_heartbeat = time.time()

    def _check_confirmations_timeout(self) -> None:
        """Check for pending confirmations that timed out"""
        current_time = time.time()

        for drone_id, drone_status in self.drone_states.items():
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

        for drone_id, drone_status in self.drone_states.items():
            elapsed = current_time - drone_status.last_heartbeat

            if elapsed > self.heartbeat_timeout and drone_status.is_responsive:
                print(f"[GS] Drone {drone_id} heartbeat timeout")
                drone_status.is_responsive = False

    def get_swarm_status(self) -> dict[int, DroneStatus]:
        """Get status of all drones"""
        return {
            drone_id: drone_status
            for drone_id, drone_status in self.drone_states.items()
        }

    def get_drone_status(self, drone_id: int) -> DroneStatus | None:
        """Get status of a specific drone"""
        return self.drone_states.get(drone_id)

    def print_swarm_status(self) -> None:
        """Print current swarm status"""
        lines = ["\n" + "=" * 60, "SWARM STATUS", "=" * 60]
        for drone_id, status in self.drone_states.items():
            responsive = "✓" if status.is_responsive else "✗"
            pending = (
                f"(pending: {status.pending_confirmation.name})"
                if status.pending_confirmation
                else ""
            )
            lines.append(
                f"Drone {drone_id}: {responsive} {status.state.value} {pending} {status.location}"
            )
        lines.append("=" * 60 + "\n")
        print("\n".join(lines))

    def is_all_drones_responsive(self) -> bool:
        """Check if all drones are responsive"""
        return all(status.is_responsive for status in self.drone_states.values())

    def is_all_drones_idle(self) -> bool:
        """Check if all drones are idle"""
        return all(
            status.state == DroneState.IDLE for status in self.drone_states.values()
        )

    def parse_location(self, message: Message) -> None:
        sender_id = int(message.data.get("senderId", -1))
        if sender_id not in self.drone_states:
            return
        location = str(message.data.get("location", ""))
        x, y, z = [float(v) for v in location[1:-1].split(",")]
        self.drone_states[sender_id].location = (x, y, z)
        self.on_set_location(sender_id)
        # print(f"[GS] Drone {sender_id} location: {(x, y, z)}")
