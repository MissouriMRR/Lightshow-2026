"""Drone-node entry point.

Runs the low-level networking loop for a single drone: connects to the mesh,
processes inbound commands via :class:`~drone.drone_command_handler.DroneCommandHandler`,
and sends periodic heartbeats. Pass ``--id`` to override the self id from the
config file.
"""

import argparse
import queue
import threading
import time

from drone.drone_command_handler import DroneCommandHandler
from drone.json_parser import ConfigParser
from interdrone.message_types import Message, MessageType
from interdrone.networking_interface import NetworkingInterface
from interdrone.networking_thread import NetworkingThread


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--id", help="Self ID", type=str)
    args = parser.parse_args()

    json_config_data = ConfigParser("./models/Example jsons/example_config.json")

    if args.id is not None:
        drone_id = str(args.id)
        json_config_data.set_self_id(drone_id)
    else:
        self_id = json_config_data.get_self_id()
        if self_id is None:
            raise SystemExit("No self id in config; pass --id")
        drone_id = self_id

    print(f"[Drone {drone_id}] Starting...")

    networking_thread_class = NetworkingThread()
    resources_ready: queue.Queue[NetworkingInterface] = queue.Queue(maxsize=1)

    networking_thread = threading.Thread(
        target=networking_thread_class.run_networking_thread,
        args=(resources_ready, json_config_data),
        daemon=True,
    )
    networking_thread.start()

    networking = resources_ready.get()
    print(f"[Drone {drone_id}] Networking interface ready")

    # Initialize command handler
    command_handler = DroneCommandHandler(drone_id=int(drone_id), networking=networking)

    # Ping GS on startup to verify connectivity
    command_handler.send_ping(target_id=0)

    start_time = time.time()
    last_heartbeat = time.time()
    heartbeat_interval = 5.0

    try:
        while True:
            # Process incoming commands and check for completion
            command_handler.process_commands()

            # Send periodic heartbeat
            current_time = time.time()
            if current_time - last_heartbeat >= heartbeat_interval:
                heartbeat_message = Message.create(
                    id=MessageType.HEARTBEAT,
                    dronesToSendData=(),
                    data={
                        "senderId": int(drone_id),
                        "payload": f"Heartbeat from Drone {drone_id}",
                    },
                )
                networking.queue_client_message(heartbeat_message)
                last_heartbeat = current_time

            time.sleep(0.05)

    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\n[Drone {drone_id}] Program ran for {elapsed:.2f} seconds")
        print("Shutting down...")


if __name__ == "__main__":
    main()
