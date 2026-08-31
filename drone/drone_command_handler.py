# drone_command_handler.py

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import dronekit

from interdrone.message_types import Message, MessageType
from interdrone.networking_interface import NetworkingInterface

CommandCallback = Callable[[Message], object]


class CommandState(Enum):
    """States for command execution"""

    IDLE = "idle"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PendingCommand:
    """Represents a command being executed"""

    message: Message
    start_time: float
    duration: float  # How long the command takes to execute
    completed: bool = False
    state: CommandState = CommandState.EXECUTING


class DroneCommandHandler:
    """
    Handles incoming drone commands, executes them, and sends confirmations.
    Simulates command execution with configurable delays.
    """

    def __init__(
        self,
        drone_id: int,
        networking: NetworkingInterface,
        command_callbacks: dict[MessageType, CommandCallback] | None = None,
    ) -> None:
        self.drone_id: int = drone_id
        self.networking: NetworkingInterface = networking

        # Execution times (in seconds) for each command
        self.command_durations: dict[MessageType, float] = {
            MessageType.TAKEOFF: 0.3,
            MessageType.FRAME_STEP: 1.0,
            MessageType.LAND: 2.0,
            MessageType.HALT: 0.5,
            MessageType.POLL_DRONE: 0.1,
            MessageType.ARM: 2.0,
        }

        # DroneKit vehicle reference (set externally when available)
        self.vehicle: dronekit.Vehicle | None = None

        # Currently executing command
        self.pending_command: PendingCommand | None = None

        # Optional callbacks when commands are received
        self.command_callbacks: dict[MessageType, CommandCallback] = (
            command_callbacks or {}
        )

        # Drone state for polling
        self.drone_location: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.drone_status: str = "idle"

        # Target altitude for the most recent takeoff command
        self.altitude: str = "10"

    def process_commands(self) -> None:
        """
        Main loop to process incoming commands.
        Should be called regularly in your main loop.
        """
        if self.pending_command is not None:
            self._check_command_completion()

        # Check for incoming commands
        server_msg = self.networking.try_get_server_message(timeout=0.01)
        if server_msg is not None:
            # Handle command synchronously
            self._handle_command_sync(server_msg)

        # Check if pending command is done
        if self.pending_command is not None:
            self._check_command_completion()

    def _handle_command_sync(self, message: Message) -> None:
        """Handle incoming command message (sync version)"""
        if message.id in self.command_callbacks:
            self.command_callbacks[message.id](message)

        match message.id:
            case MessageType.HEARTBEAT:
                # Heartbeats are just keep-alive messages, ignore them
                pass

            # Confirmations/responses are not commands - ignore them
            case (
                MessageType.TAKEOFF_CONFIRMATION
                | MessageType.FRAME_STEP_CONFIRMATION
                | MessageType.HALT_CONFIRMATION
                | MessageType.LAND_CONFIRMATION
                | MessageType.POLL_DRONE_RESPONSE
                | MessageType.ARM_RESPONSE
            ):
                pass

            case MessageType.TAKEOFF:
                self._handle_takeoff(message)

            case MessageType.FRAME_STEP:
                self._handle_frame_step(message)

            case MessageType.LAND:
                self._handle_land(message)

            case MessageType.HALT:
                self._handle_halt(message)

            case MessageType.POLL_DRONE:
                self._handle_poll_drone(message)

            case MessageType.ARM:
                self._handle_arm(message)

            case MessageType.EMERGENCY_HALT:
                self._handle_emergency_halt(message)

            case MessageType.PING:
                self._handle_ping(message)

            case MessageType.PING_RESPONSE:
                self._handle_ping_response(message)

            case _:
                print(f"[Drone {self.drone_id}] Unknown command: {message.id.name}")

    def _handle_takeoff(self, message: Message) -> None:
        """Handle TAKEOFF command"""
        if self.pending_command is not None:
            print(
                f"[Drone {self.drone_id}] ✗ Already executing command, ignoring takeoff"
            )
            return

        self.altitude = message.data.get("payload", "10")
        print(f"[Drone {self.drone_id}] → Executing TAKEOFF to {self.altitude}m")

        self.pending_command = PendingCommand(
            message=message,
            start_time=time.time(),
            duration=self.command_durations[MessageType.TAKEOFF],
        )
        self.drone_status = "taking_off"

    def _handle_frame_step(self, message: Message) -> None:
        """Handle FRAME_STEP command"""
        if self.pending_command is not None:
            msg = "Already executing command, ignoring frame step"
            print(f"[Drone {self.drone_id}] ✗ {msg}")
            return

        frame_id = message.data.get("payload", "1")
        print(f"[Drone {self.drone_id}] → Executing FRAME_STEP to frame {frame_id}")

        self.pending_command = PendingCommand(
            message=message,
            start_time=time.time(),
            duration=self.command_durations[MessageType.FRAME_STEP],
        )
        self.drone_status = "moving_to_frame"

    def _handle_land(self, message: Message) -> None:
        """Handle LAND command"""
        if self.pending_command is not None:
            print(f"[Drone {self.drone_id}] ✗ Already executing command, ignoring land")
            return

        print(f"[Drone {self.drone_id}] → Executing LAND")

        self.pending_command = PendingCommand(
            message=message,
            start_time=time.time(),
            duration=self.command_durations[MessageType.LAND],
        )
        self.drone_status = "landing"

    def _handle_halt(self, message: Message) -> None:
        """Handle HALT command - cancel current movement and hover in place"""
        print(f"[Drone {self.drone_id}] → Executing HALT")

        self.pending_command = PendingCommand(
            message=message,
            start_time=time.time(),
            duration=self.command_durations[MessageType.HALT],
        )
        self.drone_status = "halting"

    def _handle_poll_drone(self, message: Message) -> None:
        """Handle POLL_DRONE request - send back location/status"""
        if self.pending_command is not None:
            print(f"[Drone {self.drone_id}] ✗ Already executing command, ignoring poll")
            return

        print(f"[Drone {self.drone_id}] → Responding to POLL_DRONE")

        message = Message.create(
            id=MessageType.POLL_DRONE_RESPONSE,
            dronesToSendData=(0,),
            data={
                "droneId": self.drone_id,
                "location": str(self.drone_location),
                "status": "success",
                "payload": "",
            },
        )

        self.pending_command = PendingCommand(
            message=message,
            start_time=time.time(),
            duration=self.command_durations[MessageType.POLL_DRONE],
        )

    def _handle_arm(self, message: Message) -> None:
        """Handle ARM command - arm the drone via DroneKit"""
        if self.pending_command is not None:
            print(f"[Drone {self.drone_id}] ✗ Already executing command, ignoring arm")
            return

        print(f"[Drone {self.drone_id}] → Executing ARM")

        message = Message.create(
            id=MessageType.ARM_RESPONSE,
            dronesToSendData=(0,),
            data={"senderId": self.drone_id, "payload": "success"},
        )

        self.pending_command = PendingCommand(
            message=message,
            start_time=time.time(),
            duration=self.command_durations[MessageType.ARM],
        )

    def _handle_emergency_halt(self, _message: Message) -> None:
        """Handle EMERGENCY_HALT command"""
        print(f"[Drone {self.drone_id}] EMERGENCY HALT!")

        self.pending_command = None
        self.drone_status = "emergency_halted"

    def _handle_ping(self, message: Message) -> None:
        """Handle incoming PING - respond immediately"""
        sender_id = message.data.get("senderId", 0)
        print(f"[Drone {self.drone_id}] PING received from {sender_id}, responding")

        response = Message.create(
            id=MessageType.PING_RESPONSE,
            dronesToSendData=(sender_id,),
            data={
                "senderId": self.drone_id,
                "payload": f"pong from drone {self.drone_id}",
            },
        )
        self.networking.queue_client_message(response)

    def _handle_ping_response(self, message: Message) -> None:
        """Handle incoming PING_RESPONSE"""
        sender_id = message.data.get("senderId", 0)
        print(f"[Drone {self.drone_id}] PING_RESPONSE from {sender_id}")

    def send_ping(self, target_id: int = 0) -> None:
        """Send a PING to a specific target (default: GS at ID 0)"""
        ping_message = Message.create(
            id=MessageType.PING,
            dronesToSendData=(target_id,),
            data={
                "senderId": self.drone_id,
                "payload": f"ping from drone {self.drone_id}",
            },
        )
        self.networking.queue_client_message(ping_message)
        print(f"[Drone {self.drone_id}] Sent PING to {target_id}")

    def _check_command_completion(self) -> None:
        """Check if pending command has finished executing"""
        if self.pending_command is None:
            return

        if self.pending_command.completed:
            self._complete_command()

    def _complete_command(self) -> None:
        """Send confirmation when command finishes"""
        if self.pending_command is None:
            return

        command_type = self.pending_command.message.id

        # Determine confirmation message type and data
        confirmation_type = None
        confirmation_data = {
            "droneId": self.drone_id,
            "status": "success",
            "payload": "",
        }

        match command_type:
            case MessageType.TAKEOFF:
                confirmation_type = MessageType.TAKEOFF_CONFIRMATION
                self.drone_status = "in_flight"
            case MessageType.FRAME_STEP:
                confirmation_type = MessageType.FRAME_STEP_CONFIRMATION
                self.drone_status = "in_flight"
                confirmation_data["frameId"] = int(
                    self.pending_command.message.data.get("payload", "0")
                )
            case MessageType.LAND:
                confirmation_type = MessageType.LAND_CONFIRMATION
                self.drone_status = "landed"
            case MessageType.HALT:
                confirmation_type = MessageType.HALT_CONFIRMATION
                self.drone_status = "idle"
            case MessageType.POLL_DRONE_RESPONSE:
                self.pending_command.message.data["location"] = str(self.drone_location)
            case _:
                pass

        # Send confirmation to ground station only
        if confirmation_type:
            confirmation = Message.create(
                id=confirmation_type,
                dronesToSendData=(0,),  # Send only to ground station (ID 0)
                data=confirmation_data,
            )
            self.networking.queue_client_message(confirmation)
        else:
            self.networking.queue_client_message(self.pending_command.message)

        print(
            f"[Drone {self.drone_id}] ✓ {command_type.name} completed, sent confirmation"
        )

        # Clear pending command
        self.pending_command = None

    def set_drone_location(self, x: float, y: float, z: float) -> None:
        """Update drone's current location"""
        self.drone_location = (x, y, z)

    def register_callback(
        self,
        command_type: MessageType,
        callback: CommandCallback,
    ) -> None:
        """Register a callback to be executed when command is received"""
        self.command_callbacks[command_type] = callback
