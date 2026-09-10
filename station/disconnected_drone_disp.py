import tkinter

from common.utils import partition
from station.station_server import StationServer


class DisconnectedDroneDisp(tkinter.Frame):
    desired_drones: list[str]
    connected_drones: list[str]
    station_server: StationServer
    connection_text: tkinter.Text

    def __init__(self, master: tkinter.Misc, station_server: StationServer) -> None:
        super().__init__(master)

        self.connected_drones = []

        self.station_server = station_server
        station_server.set_drone_listener(self.on_drone, self.on_arm)
        self.desired_drones = station_server.config.get_drone_ids()[1:]

        # height as a really large number because expand doesn't seem to work for some reason
        self.connection_text = tkinter.Text(self, width=14, height=10000000)

        self.connection_text.tag_configure("red", foreground="red")
        self.connection_text.tag_configure("yellow", foreground="#e6b907")
        self.connection_text.tag_configure("green", foreground="green")
        self.connection_text.pack()

        self.redraw()

    def redraw(self) -> None:
        self.connection_text.delete("1.0", "end")

        disconnected, connected = partition(
            lambda x: x not in self.connected_drones, self.desired_drones
        )
        armed, connected = partition(
            lambda x: (
                x in self.station_server.drones and self.station_server.drones[x].armed
            ),
            connected,
        )

        self.draw_connections(disconnected, "red")
        self.draw_connections(connected, "yellow")
        self.draw_connections(armed, "green")

    def draw_connections(self, ids: list[str], color: str) -> None:
        for drone_id in ids:
            connection = self.station_server.config.get_drone_connection(drone_id)
            if connection is None:
                continue
            self.connection_text.insert(
                "end", connection[0] + ":" + connection[1] + "\n", color
            )

    def on_drone(self, new_drone: str) -> None:
        self.connected_drones.append(new_drone)
        self.redraw()

    def on_arm(self) -> None:
        self.redraw()
