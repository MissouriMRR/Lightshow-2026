"""In-process fake of :class:`dronekit.Vehicle` for running without a flight
controller. Selected by ``Drone(use_test_vehicle=True)`` (the default).
"""

from random import random

import dronekit


class SimVehicle:
    class Location:
        global_relative_frame: dronekit.LocationGlobalRelative

        def __init__(self, location: dronekit.LocationGlobalRelative) -> None:
            self.global_relative_frame = location

    speed: float = 1
    home_location: dronekit.LocationGlobal
    location: "SimVehicle.Location"
    is_armable: bool
    armed: bool
    _mode: dronekit.VehicleMode

    def __init__(self) -> None:
        self.home_location = dronekit.LocationGlobal(0, 0, 0)

        def rand_offset() -> float:
            spread = 50
            return random() * spread - spread / 2

        self.location = self.Location(
            dronekit.LocationGlobalRelative(rand_offset(), rand_offset(), 0)
        )
        self.is_armable = True
        self.armed = False
        self._mode = dronekit.VehicleMode("WAIT")

    @property
    def mode(self) -> dronekit.VehicleMode:
        return self._mode

    @mode.setter
    def mode(self, value: dronekit.VehicleMode) -> None:
        if value == dronekit.VehicleMode("LAND"):
            self.location.global_relative_frame.alt = 0
        self._mode = value

    def simple_goto(
        self,
        location: dronekit.LocationGlobalRelative,
        airspeed: float | None = None,
        groundspeed: float | None = None,
    ) -> None:
        # airspeed / groundspeed accepted for dronekit API parity; the sim ignores them.
        del airspeed, groundspeed
        self.location = self.Location(location)

    def simple_takeoff(self, alt: float) -> None:
        self.location.global_relative_frame.alt = alt
