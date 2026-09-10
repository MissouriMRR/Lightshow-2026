# Lightshow Networking Commands

## Overview

The lightshow networking system enables communication between a **ground station (GS)** and multiple **drones** over TCP. All nodes are preloaded with a JSON config that maps drone IDs to IP addresses and ports.

- **Ground station** uses `GroundStationController` (in `station/ground_station_controller.py`)
- **Drones** use `DroneCommandHandler` (in `drone/drone_command_handler.py`)
- **Config** is loaded via `ConfigParser` (in `drone/json_parser.py`)

## Architecture

```
Ground Station (ID 0, port 9000)
    │
    ├── TCP ──► Drone 1 (port 5001)
    ├── TCP ──► Drone 2 (port 5002)
    └── TCP ──► Drone N (port ...)
```

Each node runs an async TCP **server** (receives messages) and **client** (sends messages) on a background thread. The main thread communicates with the networking layer through a `NetworkingInterface` using thread-safe queues.

### Message Routing

Messages use `dronesToSendData` to control where they're sent:

| `dronesToSendData` value | Destination |
|---|---|
| `()` (empty tuple) | Broadcast to ALL drones and GS |
| `(0,)` | Ground station only |
| `(1,)` | Drone 1 only |
| `(1, 2)` | Drones 1 and 2 |

---

## Configuration

### JSON Config Structure (`example_config.json`)

```json
{
  "drones": {
    "0": {
        "ip": "127.0.0.1",
        "port": "9000"
    },
    "1": {
        "ip": "127.0.0.1",
        "port": "5001"
    },
    "2": {
        "ip": "127.0.0.1",
        "port": "5002"
    }
  },
  "gs": {
    "ip": "127.0.0.1",
    "port": "9000"
  },
  "show": {
    "1": {
      "frame 1": {
        "coordinates": [37.950177, -91.780905, 1500],
        "time_delay": 0,
        "flight_speed": 5
      }
    }
  },
  "localInfo": {
    "selfId": "2",
    "speedTestKbDataSize": "16"
  }
}
```

- **`drones`**: Maps each drone ID (and GS at ID `"0"`) to an IP and port
- **`gs`**: Ground station connection info (should match drone `"0"`)
- **`show`**: Frame choreography data per drone (coordinates, timing, speed)
- **`localInfo.selfId`**: Which drone this config instance identifies as (overridden by `-i` flag or `set_self_id()`)

---

## Ground Station Commands

All commands are methods on `GroundStationController`. Every command accepts an optional `target_drones` tuple to send to specific drones. If omitted or empty, the command broadcasts to all drones.

### Setup

```python
from drone.json_parser import ConfigParser
from station.ground_station_controller import GroundStationController

config = ConfigParser("./models/Example jsons/example_config.json")
config.set_self_id("0")  # GS must identify as ID 0

gs = GroundStationController(config)
gs.start()  # Starts networking thread and blocks until ready
```

Or manually, if you need access to the thread object:

```python
from drone.json_parser import ConfigParser
from station.ground_station_controller import GroundStationController
from interdrone.networking_thread import NetworkingThread
import queue, threading

config = ConfigParser("./models/Example jsons/example_config.json")
config.set_self_id("0")

gs = GroundStationController(config)

networking_thread = NetworkingThread()
resources_ready = queue.Queue(maxsize=1)
thread = threading.Thread(
    target=networking_thread.run_networking_thread,
    args=(resources_ready, config),
    daemon=True,
)
thread.start()
gs.networking = resources_ready.get()
```

### Processing Messages

**Must be called regularly** in your main loop to receive responses, confirmations, heartbeats, and check for timeouts:

```python
while True:
    gs.process_messages()
    time.sleep(0.05)
```

### `ping_drone(drone_id)`

Send an on-demand connectivity check to a specific drone. The drone responds immediately with a `PING_RESPONSE`, which marks it as responsive.

```python
gs.ping_drone(1)  # Ping drone 1
gs.ping_drone(2)  # Ping drone 2
```

### `poll_drones(target_drones=())`

Request location and status info from drones. Drones respond with their current position and operational status.

```python
gs.poll_drones()  # Poll all drones
gs.poll_drones((1,))  # Poll drone 1 only
gs.poll_drones((1, 2))  # Poll drones 1 and 2
```

### `send_arm(target_drones=())`

Command drones to arm their motors via DroneKit. Drones send `ARM_RESPONSE` with a payload of `"success"` or `"failed"`. On success, the drone's state is updated to `ARMED`.

```python
gs.send_arm()  # Arm all drones
gs.send_arm((1,))  # Arm drone 1 only
```

### `send_takeoff(altitude=10.0, target_drones=())`

Command drones to take off to a target altitude. Drones send `TAKEOFF_CONFIRMATION` when complete.

```python
gs.send_takeoff(altitude=15.0)  # All drones, 15m
gs.send_takeoff(altitude=10.0, target_drones=(1,))  # Drone 1 only
```

### `send_frame_step(frame_id, target_drones=())`

Command drones to move to a specific frame position (defined in the config JSON). Drones send `FRAME_STEP_CONFIRMATION` when complete.

```python
gs.send_frame_step(frame_id=1)  # All drones to frame 1
gs.send_frame_step(frame_id=3, target_drones=(2,))  # Drone 2 to frame 3
```

### `send_halt(target_drones=())`

Command drones to halt in place. Drones send `HALT_CONFIRMATION` when complete.

Unlike `TAKEOFF`, `LAND`, and `FRAME_STEP`, `HALT` **overrides any in-progress command** on the drone. The interrupted command's confirmation is never sent — the GS will eventually time it out.

```python
gs.send_halt()  # Halt all drones
gs.send_halt((1,))  # Halt drone 1 only
```

### `send_land(target_drones=())`

Command drones to land. Drones send `LAND_CONFIRMATION` when complete.

```python
gs.send_land()  # Land all drones
gs.send_land((2,))  # Land drone 2 only
```

### `send_emergency_halt(target_drones=())`

Immediately halt all operations. Cancels any in-progress command on the drone. **No confirmation is sent** -- this is a fire-and-forget emergency action.

```python
gs.send_emergency_halt()  # Emergency halt all drones
gs.send_emergency_halt((1,))  # Emergency halt drone 1
```

### Status Monitoring

```python
gs.print_swarm_status()  # Print formatted status of all drones
gs.get_swarm_status()  # Returns Dict[int, DroneStatus]
gs.get_drone_status(1)  # Returns DroneStatus for drone 1
gs.is_all_drones_responsive()  # True if all drones have recent heartbeats
gs.is_all_drones_idle()  # True if all drones are in IDLE state
```

### Timeouts

| Timeout | Default | What happens |
|---|---|---|
| `confirmation_timeout` | 30.0s | If a drone doesn't confirm a command within this time, it's marked unresponsive |
| `heartbeat_timeout` | 10.0s | If a drone doesn't send a heartbeat within this time, it's marked unresponsive |

---

## Drone Commands

Drones use `DroneCommandHandler` to automatically process incoming commands and send confirmations. Most command handling is automatic -- the handler processes commands from the server queue and sends confirmations when execution completes.

### Setup

```python
from drone.json_parser import ConfigParser
from interdrone.networking_interface import NetworkingInterface
from interdrone.networking_thread import NetworkingThread
from drone.drone_command_handler import DroneCommandHandler

config = ConfigParser("./models/Example jsons/example_config.json")
config.set_self_id("1")  # Or pass -i 1 via command line

# Start networking thread (same pattern as GS)
networking_thread = NetworkingThread()
resources_ready = queue.Queue(maxsize=1)
thread = threading.Thread(
    target=networking_thread.run_networking_thread,
    args=(resources_ready, config),
    daemon=True,
)
thread.start()
networking = resources_ready.get()

command_handler = DroneCommandHandler(drone_id=1, networking=networking)
```

### Processing Commands

**Must be called regularly** in your main loop. This reads incoming messages from the server queue, executes commands, and sends confirmations when complete:

```python
while True:
    command_handler.process_commands()
    time.sleep(0.05)
```

### `send_ping(target_id=0)`

Send a connectivity check to the GS or another drone:

```python
command_handler.send_ping()  # Ping GS (default)
command_handler.send_ping(target_id=2)  # Ping drone 2
```

### `set_drone_location(x, y, z)`

Update the drone's reported location (returned when the GS polls):

```python
command_handler.set_drone_location(37.95, -91.78, 1500)
```

### `register_callback(command_type, callback)`

Register a callback function to be called when a specific command type is received:

```python
def on_takeoff(message):
    print("Takeoff command received!")


command_handler.register_callback(MessageType.TAKEOFF, on_takeoff)
```

### Automatic Behaviors

When the drone receives commands from the GS, the handler automatically:

| Command Received | Action | Confirmation Sent |
|---|---|---|
| `ARM` | Arms motors via DroneKit (or simulates if no vehicle), sets status to `armed` | `ARM_RESPONSE` |
| `TAKEOFF` | Executes for 3.0s, sets status to `taking_off` → `in_flight` | `TAKEOFF_CONFIRMATION` |
| `FRAME_STEP` | Executes for 1.0s, sets status to `moving_to_frame` → `in_flight` | `FRAME_STEP_CONFIRMATION` |
| `LAND` | Executes for 2.0s, sets status to `landing` → `landed` | `LAND_CONFIRMATION` |
| `HALT` | Executes for 0.5s, sets status to `halted` → `idle` | `HALT_CONFIRMATION` |
| `POLL_DRONE` | Responds immediately with location and status | `POLL_DRONE_RESPONSE` |
| `EMERGENCY_HALT` | Cancels pending command immediately, sets status to `emergency_halted` | None |
| `PING` | Responds immediately | `PING_RESPONSE` |

All confirmations are sent to the GS only (drone ID 0). Execution durations are configurable via `command_handler.command_durations`.

### Sending Heartbeats

Heartbeats are not sent automatically by the handler -- send them from your main loop:

```python
heartbeat = Message.create(
    id=MessageType.HEARTBEAT,
    dronesToSendData=(),  # Broadcast to all
    data={
        "senderId": drone_id,
        "payload": f"Heartbeat from Drone {drone_id}",
    },
)
networking.queue_client_message(heartbeat)
```

---

## Message Types Reference

| Type | ID | Direction | Purpose |
|---|---|---|---|
| `POLL_DRONE` | 301 | GS → Drone | Request location/status |
| `POLL_DRONE_RESPONSE` | 302 | Drone → GS | Location/status response |
| `PING` | 303 | GS ↔ Drone | On-demand connectivity check |
| `PING_RESPONSE` | 304 | GS ↔ Drone | Response to PING |
| `ARM` | 305 | GS → Drone | Command to arm motors |
| `ARM_RESPONSE` | 306 | Drone → GS | Arm result (success/failed) |
| `TAKEOFF` | 310 | GS → Drone | Command to take off |
| `FRAME_STEP` | 311 | GS → Drone | Command to move to frame |
| `HALT` | 312 | GS → Drone | Command to halt |
| `LAND` | 313 | GS → Drone | Command to land |
| `TAKEOFF_CONFIRMATION` | 320 | Drone → GS | Takeoff complete |
| `FRAME_STEP_CONFIRMATION` | 321 | Drone → GS | Frame step complete |
| `HALT_CONFIRMATION` | 322 | Drone → GS | Halt complete |
| `LAND_CONFIRMATION` | 323 | Drone → GS | Landing complete |
| `EMERGENCY_HALT` | 399 | GS → Drone | Immediate emergency stop |
| `HEARTBEAT` | 504 | Broadcast | Periodic keep-alive |

---

## Running a Test

Open 3 terminals from the `Lightshow/` directory:

```bash
# Terminal 1 - Ground Station
uv run gs_main.py

# Terminal 2 - Drone 1
uv run main.py -i 1

# Terminal 3 - Drone 2
uv run main.py -i 2
```

Start the GS first, then start drones within 5 seconds. The GS runs a full mission sequence automatically: ping → takeoff → frame step → poll → land.

---

## Drone State Lifecycle

```
UNKNOWN ──► ARMED ──► TAKING_OFF ──► IN_FLIGHT ──► LANDING ──► LANDED
                                         │
                                         ├── HALT ──► IDLE
                                         │
                                         └── EMERGENCY_HALT
```

> **Note:** These are the `DroneState` enum values tracked by the GS (`ground_station_controller.py`). The drone's internal `drone_status` string uses lowercase equivalents and has a transient `"halted"` value during HALT execution, but the GS never sees a `HALTED` state — it transitions directly to `IDLE` upon receiving `HALT_CONFIRMATION`.
