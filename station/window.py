import tkinter
from tkinter import ttk

from station.disconnected_drone_disp import DisconnectedDroneDisp
from station.drone_disp import DroneDisp
from station.station_server import StationServer


class StationFrame(ttk.Frame):
    station: StationServer
    disconnected_drone_disp: DisconnectedDroneDisp
    drone_disp: DroneDisp

    def __init__(self, master: tkinter.Tk, station: StationServer) -> None:
        super().__init__(master)
        self.place(relwidth=1, relheight=1)
        master.resizable(True, True)
        master.geometry("1000x600")

        self.station = station

        buttons = ttk.Frame()

        tkinter.Button(
            buttons, text="Arm Drones", command=lambda: self.station.arm()
        ).pack(side="left")

        tkinter.Button(
            buttons, text="Take Off", command=lambda: self.station.takeoff()
        ).pack(side="left")

        tkinter.Button(buttons, text="Step", command=lambda: self.station.step()).pack(
            side="left"
        )

        tkinter.Button(buttons, text="Land", command=lambda: self.station.land()).pack(
            side="left"
        )

        tkinter.Button(buttons, text="Halt", command=lambda: self.station.halt()).pack(
            side="left"
        )

        buttons.pack()

        self.disconnected_drone_disp = DisconnectedDroneDisp(self, self.station)
        self.disconnected_drone_disp.pack(side=tkinter.RIGHT)

        self.drone_disp = DroneDisp(self, self.station)
