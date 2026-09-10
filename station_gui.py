"""Ground-station GUI entry point.

Launches the Tk window (:class:`~station.window.StationFrame`) backed by a
:class:`~station.station_server.StationServer`. By default the server runs its
real networking loop on a background thread; pass ``--null`` to run the GUI with
no networking at all (:class:`~station.null_station_connection.NullStationConnection`).
"""

import argparse
import asyncio
import threading
import tkinter

from station.null_station_connection import NullStationConnection
from station.station_server import StationServer
from station.window import StationFrame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--null",
        action="store_true",
        help="run with no networking (NullStationConnection)",
    )
    args = parser.parse_args()

    connection = NullStationConnection() if args.null else None
    station_server = StationServer(connection)

    root = tkinter.Tk()
    StationFrame(root, station_server)

    if not args.null:
        threading.Thread(
            target=lambda: asyncio.run(station_server.run()), daemon=True
        ).start()

    root.mainloop()


if __name__ == "__main__":
    main()
