"""Ground-station entry point (headless).

Runs the whole show against the connected swarm: wait for drones, ping, take
off to the first show frame, step through every remaining frame (waiting for
every responsive drone to confirm each one), poll, land, then idle processing
messages. For the GUI, use ``station_gui.py``.
"""

import queue
import threading
import time

from common.config import NETWORK_CONFIG_PATH, SHOW_PATH
from drone.json_parser import ConfigParser
from interdrone.networking_interface import NetworkingInterface
from interdrone.networking_thread import NetworkingThread
from station.ground_station_controller import GroundStationController


def wait_for_confirmations(gs: GroundStationController) -> None:
    """
    Process messages until no responsive drone is waiting on a confirmation.
    Drones that never connected are ignored; drones that don't answer are
    dropped by the controller's confirmation timeout.
    """
    while any(
        status.is_responsive and status.pending_confirmation is not None
        for status in gs.drone_states.values()
    ):
        gs.process_messages()
        time.sleep(0.01)


def count_frame_steps(config: ConfigParser) -> int | None:
    """
    Number of FRAME_STEPs in the show (frames after the one takeoff goes to),
    or None if the drones in the network config don't all have the same count.
    """
    counts = {
        drone_id: len(config.get_flight_frame_names(drone_id))
        for drone_id in config.get_drone_ids()
        if drone_id != "0"
    }
    if len(set(counts.values())) != 1 or 0 in counts.values():
        print(f"[GS] Error: drones have different or empty shows: {counts}")
        return None
    return next(iter(counts.values())) - 1


def main() -> None:
    print("[GS] Ground Station Starting...\n")

    config = ConfigParser(NETWORK_CONFIG_PATH, SHOW_PATH)
    config.set_self_id("0")  # GS is always drone ID 0

    num_steps = count_frame_steps(config)
    if num_steps is None:
        return
    print(f"[GS] Show has {num_steps + 1} frames ({num_steps} steps after takeoff)\n")

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

        # Drones climb to their own first show frame; the altitude payload is unused
        print("[GS] Commanding drones to take off...\n")
        gs.send_takeoff(altitude=10.0)
        wait_for_confirmations(gs)
        gs.print_swarm_status()

        for step in range(1, num_steps + 1):
            print(f"[GS] Step {step}/{num_steps} -> frame {step + 1}")
            gs.send_frame_step(frame_id=step + 1)
            wait_for_confirmations(gs)

        print("[GS] Polling drones for status...\n")
        gs.poll_drones()
        for _ in range(20):
            gs.process_messages()
            time.sleep(0.1)
        gs.print_swarm_status()

        print("[GS] Commanding drones to land...\n")
        gs.send_land()
        wait_for_confirmations(gs)
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


if __name__ == "__main__":
    main()
