import dronekit

from station.station_connection import PositionReceiver


class NullStationConnection:
    """No-op stand-in for :class:`~station.station_connection.StationConnection`.

    Lets the ground station GUI run with no swarm / no networking: every command
    is accepted and does nothing.
    """

    server: PositionReceiver | None = None

    def set_server(self, server: PositionReceiver) -> None:
        self.server = server

    async def ping(self, _id: str) -> bool:
        return True

    async def send_poll(self, _id: str) -> dronekit.LocationGlobalRelative:
        return dronekit.LocationGlobalRelative(0, 0, 0)

    async def arm_drone(self, _id: str) -> bool:
        return True

    async def dearm_drone(self, _id: str) -> None:
        pass

    async def send_takeoff(self, _id: str) -> bool:
        return True

    async def send_step(self, _id: str) -> None:
        pass

    async def send_landing(self, _id: str) -> None:
        pass

    async def send_halt(self, _id: str) -> None:
        pass

    async def tick(self) -> None:
        pass
