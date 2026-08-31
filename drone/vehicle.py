"""Vehicle type shared by the drone code.

``AnyVehicle`` covers both the real :class:`dronekit.Vehicle` and the in-process
:class:`~drone.sim_vehicle.SimVehicle` fake, so movement / pathfinding helpers
accept either without caring which is in use.
"""

import dronekit

from drone.sim_vehicle import SimVehicle

type AnyVehicle = dronekit.Vehicle | SimVehicle
