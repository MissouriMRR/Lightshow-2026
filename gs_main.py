"""Ground-station entry point (headless).

Runs a fixed example mission sequence against the connected swarm: wait for
drones, ping, take off, step to frame 1, poll, land, then idle processing
messages. This is a demo script with hard-coded wait loops -- adjust or replace
for real missions. For the GUI, use ``station_gui.py``.
"""

import queue
import threading
import time

from drone.json_parser import ConfigParser
from interdrone.networking_interface import NetworkingInterface
from interdrone.networking_thread import NetworkingThread
from station.ground_station_controller import GroundStationController


def main() -> None:
    print("[GS] Ground Station Starting...\n")

    config = ConfigParser("./models/Example jsons/example_config.json")
    config.set_self_id("0")  # GS is always drone ID 0

    gs = GroundStationController(config)

    networking_thread_class = NetworkingThread()
    resources_ready: queue.Queue[NetworkingInterface] = queue.Queue(maxsize=1)

    networking_thread = threading.Thread(
        target=networking_thread_class.run_networking_thread,
        args=(resources_ready, config),
        daemon=True,
    )
    networking_thread.start()

    gs.networking = resources_ready.get()
    print("[GS] Networking interface ready\n")

    start_time = time.time()

    try:
        # Give drones time to connect
        print("[GS] Waiting for drones to connect...\n")
        for _ in range(50):
            gs.process_messages()
            time.sleep(0.1)

        # Ping all drones to check connectivity
        print("[GS] Pinging drones...\n")
        for drone_id in [int(d) for d in config.get_drone_ids() if d != "0"]:
            gs.ping_drone(drone_id)

        for _ in range(20):
            gs.process_messages()
            time.sleep(0.1)

        gs.print_swarm_status()

        print("[GS] === MISSION START ===\n")

        print("[GS] Commanding drones to take off...\n")
        gs.send_takeoff(altitude=10.0)
        for _ in range(60):
            gs.process_messages()
            time.sleep(0.1)
        gs.print_swarm_status()

        print("[GS] Commanding drones to move to frame 1...\n")
        gs.send_frame_step(frame_id=1)
        for _ in range(40):
            gs.process_messages()
            time.sleep(0.1)
        gs.print_swarm_status()

        print("[GS] Polling drones for status...\n")
        gs.poll_drones()
        for _ in range(20):
            gs.process_messages()
            time.sleep(0.1)

        print("[GS] Commanding drones to land...\n")
        gs.send_land()
        for _ in range(50):
            gs.process_messages()
            time.sleep(0.1)
        gs.print_swarm_status()

        print("[GS] === MISSION COMPLETE ===\n")
        print("[GS] Ground Station active. Processing messages...\n")

        while True:
            gs.process_messages()
            time.sleep(0.05)

    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\n[GS] Ground Station ran for {elapsed:.2f} seconds")
        gs.shutdown()
        print("[GS] Shutting down...")


if __name__ == "__main__":
    main()
