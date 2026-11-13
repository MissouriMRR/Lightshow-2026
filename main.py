"""Drone entry point: runs a Drone that flies the show.

Uses the in-process SimVehicle by default. Pass ``--sitl`` to fly this drone's
ArduPilot SITL instance instead, or ``--connect`` to give a flight controller
connection string directly.
"""

import argparse
import asyncio

from drone.drone import Drone

SITL_BASE_PORT = 5750
"""SITL instance (-I N-1) listens on 5760 + 10*(N-1)
i.e. 5750 + 10*N for drone N.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--id", help="Self ID", type=str)
    vehicle_group = parser.add_mutually_exclusive_group()
    vehicle_group.add_argument(
        "-s",
        "--sitl",
        action="store_true",
        help="Connect to ArduPilot SITL instance",
    )
    vehicle_group.add_argument(
        "-c",
        "--connect",
        type=str,
        help="Flight controller connection string, e.g. tcp:127.0.0.1:5760",
    )
    args = parser.parse_args()

    connection_string: str | None = args.connect
    if args.sitl:
        if args.id is None:
            parser.error("--sitl needs --id to pick the SITL port")
        connection_string = f"tcp:127.0.0.1:{SITL_BASE_PORT + 10 * int(args.id)}"

    drone = Drone(
        args.id,
        use_test_vehicle=connection_string is None,
        vehicle_connection_string=connection_string or "",
    )

    while True:
        asyncio.run(drone.tick())


if __name__ == "__main__":
    main()
