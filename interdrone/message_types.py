import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Final, cast, override


class MessageType(Enum):
    UNKNOWN = 0

    # Lightshow
    GS_TEST = 300

    POLL_DRONE = 301
    POLL_DRONE_RESPONSE = 302

    PING = 303
    PING_RESPONSE = 304

    ARM = 305
    ARM_RESPONSE = 306

    TAKEOFF = 310
    FRAME_STEP = 311
    HALT = 312
    LAND = 313

    TAKEOFF_CONFIRMATION = 320
    FRAME_STEP_CONFIRMATION = 321
    HALT_CONFIRMATION = 322
    LAND_CONFIRMATION = 323

    EMERGENCY_HALT = 399

    # Interdrone Communication
    HEARTBEAT = 504
    SERVER_DEFAULT_RESPONSE = 505
    SPEED_TEST_REQUEST = 513
    SPEED_TEST_RESPONSE = 514


type SchemaFieldType = (
    type[int | float | str | tuple[Any, ...] | dict[str, Any]] | MessageType
)

# TODO inside of here document what these different fields do
EXPECTED_SCHEMA: Final[dict[MessageType, dict[str, Any]]] = {
    MessageType.UNKNOWN: {
        "id": MessageType.UNKNOWN,
        "dronesToSendData": tuple[int, ...],  # ... allows tuple to be any length
        "data": dict[str, object],  # TODO REMOVE DATA HERE
    },
    MessageType.HEARTBEAT: {
        "id": MessageType.HEARTBEAT,
        "dronesToSendData": tuple[int, ...],
        "senderId": int,
        "payload": str,
        "location": str,
    },
    MessageType.SERVER_DEFAULT_RESPONSE: {
        "id": MessageType.SERVER_DEFAULT_RESPONSE,
        "dronesToSendData": tuple[int, ...],
        "payload": str,
    },
    # Message: SPEED_TEST_REQUEST
    # Usage: Used in network_test. Sent to other drones, their server updates the data, and it's then sent back to the client for processing. Client outputs SPEED_TEST_RESPONSE
    # Description of Data: TODO Talk to team and see if we want to include this for message documentation
    MessageType.SPEED_TEST_REQUEST: {
        "id": MessageType.SPEED_TEST_REQUEST,
        "dronesToSendData": tuple[int, ...],
        "initialUploadTime": float,
        "finalUploadTime": float,
        "initialDownloadTime": float,
        "finalDownloadTime": float,
        "senderId": int,
        "payloadSize": int,
        "payload": str,
    },
    MessageType.SPEED_TEST_RESPONSE: {
        "id": MessageType.SPEED_TEST_RESPONSE,
        "dronesToSendData": tuple[int, ...],
        "target": str,
        "uploadRttMs": float,
        "uploadThroughputKbps": float,
        "downloadRttMs": float,
        "downloadThroughputKbps": float,
    },
    # Light show messages
    MessageType.GS_TEST: {
        "id": MessageType.GS_TEST,
        "dronesToSendData": tuple[int, ...],
        "payload": str,
    },
    MessageType.POLL_DRONE: {
        "id": MessageType.POLL_DRONE,
        "dronesToSendData": tuple[int, ...],
        "payload": str,
    },
    MessageType.POLL_DRONE_RESPONSE: {
        "id": MessageType.POLL_DRONE_RESPONSE,
        "dronesToSendData": tuple[int, ...],
        "droneId": int,
        "location": str,  # JSON string or formatted string
        "status": str,
        "payload": str,
    },
    MessageType.PING: {
        "id": MessageType.PING,
        "dronesToSendData": tuple[int, ...],
        "senderId": int,
        "payload": str,
    },
    MessageType.PING_RESPONSE: {
        "id": MessageType.PING_RESPONSE,
        "dronesToSendData": tuple[int, ...],
        "senderId": int,
        "payload": str,
    },
    MessageType.ARM: {
        "id": MessageType.ARM,
        "dronesToSendData": tuple[int, ...],
        "senderId": int,
        "payload": str,
    },
    MessageType.ARM_RESPONSE: {
        "id": MessageType.ARM_RESPONSE,
        "dronesToSendData": tuple[int, ...],
        "senderId": int,
        "payload": str,
    },
    MessageType.TAKEOFF: {
        "id": MessageType.TAKEOFF,
        "dronesToSendData": tuple[int, ...],
        "payload": str,
    },
    MessageType.FRAME_STEP: {
        "id": MessageType.FRAME_STEP,
        "dronesToSendData": tuple[int, ...],
        "payload": str,
    },
    MessageType.LAND: {
        "id": MessageType.LAND,
        "dronesToSendData": tuple[int, ...],
        "payload": str,
    },
    MessageType.HALT: {
        "id": MessageType.HALT,
        "dronesToSendData": tuple[int, ...],
        "payload": str,
    },
    # Confirmation responses
    MessageType.TAKEOFF_CONFIRMATION: {
        "id": MessageType.TAKEOFF_CONFIRMATION,
        "dronesToSendData": tuple[int, ...],
        "droneId": int,
        "status": str,
        "payload": str,
    },
    MessageType.FRAME_STEP_CONFIRMATION: {
        "id": MessageType.FRAME_STEP_CONFIRMATION,
        "dronesToSendData": tuple[int, ...],
        "droneId": int,
        "frameId": int,
        "status": str,
        "payload": str,
    },
    MessageType.HALT_CONFIRMATION: {
        "id": MessageType.HALT_CONFIRMATION,
        "dronesToSendData": tuple[int, ...],
        "droneId": int,
        "status": str,
        "payload": str,
    },
    MessageType.LAND_CONFIRMATION: {
        "id": MessageType.LAND_CONFIRMATION,
        "dronesToSendData": tuple[int, ...],
        "droneId": int,
        "status": str,
        "payload": str,
    },
    # Emergency Halt
    MessageType.EMERGENCY_HALT: {
        "id": MessageType.EMERGENCY_HALT,
        "dronesToSendData": tuple[int, ...],
        "payload": str,
    },
}


@dataclass(frozen=True)
class Message:
    """Message class for interdrone communication. Provides a way to create, validate, and serialize messages."""

    # ID and dronesToSendData are required values for each message
    id: MessageType
    dronesToSendData: tuple[int, ...]
    # The data variable contains all keys and values in a schema that aren't id and dronesToSendData.
    data: dict[str, Any] = field(default_factory=dict)  # TODO long term remove any

    # When new Message object is created in code this runs to prevent errors and init
    def __post_init__(self) -> None:
        if self.id not in EXPECTED_SCHEMA:
            raise ValueError(f"Invalid message type: {self.id}")

        # Check to make sure all expected key in schema are present in new message. If not, raise an error
        expected = EXPECTED_SCHEMA[self.id]
        actual_keys = set(self.data.keys())
        expected_keys = set(expected.keys())

        expected_keys -= {"id", "dronesToSendData"}

        # Check missing/extra keys
        missing = expected_keys - actual_keys
        extra = actual_keys - expected_keys

        errors: list[str] = []
        if missing:
            errors.append(f"missing keys: {sorted(missing)}")
        if extra:
            errors.append(f"extra keys: {sorted(extra)}")
        if errors:
            raise ValueError(
                f"Invalid data for message '{self.id}': {', '.join(errors)}"
            )

        # Iterate through schema and add keys to data and check for errors
        for key, allowed_types in expected.items():
            if key not in {"id", "dronesToSendData"}:
                value = self.data[key]
                if not isinstance(value, allowed_types):
                    raise TypeError(
                        f"Field '{key}' in '{self.id}' must be one of {allowed_types}, got {type(value).__name__}"
                    )
        object.__setattr__(self, "data", FrozenKeysDict(self.data.copy()))

    @classmethod
    def create(
        cls, id: MessageType, dronesToSendData: tuple[int, ...], data: dict[str, Any]
    ) -> "Message":
        return cls(id=id, dronesToSendData=dronesToSendData, data=data.copy())


# Ensures you can't change values of keys once a message is created, only their values (prevents potential issues with networking)
class FrozenKeysDict(dict[str, Any]):
    """Normal dict, but you can't add or remove keys after creation"""

    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
        self._frozen_keys: frozenset[str] = frozenset(data.keys())

    @override
    def __setitem__(self, key: str, value: object) -> None:
        if key not in self._frozen_keys:
            raise KeyError(f"Cannot add new key '{key}' – message structure is frozen")
        super().__setitem__(key, value)

    @override
    def __delitem__(self, key: str) -> None:
        raise KeyError("Cannot delete keys from Message.data")

    @override
    def clear(self) -> None:
        raise AttributeError("Cannot clear Message.data")

    @override
    def pop(self, *args: object) -> None:
        raise AttributeError("Cannot pop from Message.data")

    @override
    def popitem(self) -> tuple[str, object]:
        raise AttributeError("Cannot popitem from Message.data")

    @override
    def setdefault(self, key: str, default: object = None) -> object:
        if key not in self._frozen_keys:
            raise KeyError(f"Cannot add new key '{key}' via setdefault()")
        return super().setdefault(key, default)

    @override
    def update(self, other: object = None, **kwargs: object) -> None:
        # Callers only ever pass dict-like data; normalize to a dict so the
        # frozen-key check and the super() call are both well typed.
        incoming: dict[str, object] = dict(kwargs)
        if other is not None:
            incoming.update(cast("dict[str, object]", other))
        for k in incoming:
            if k not in self._frozen_keys:
                raise KeyError(f"Cannot add new key '{k}' via update()")
        super().update(incoming)

    def to_json(self) -> str:
        return json.dumps(self.__dict__)
