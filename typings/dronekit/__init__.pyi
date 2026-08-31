"""Minimal type stub for the ``dronekit`` package.

``dronekit`` 2.9.2 (the last PyPI release, from 2015) ships no type information
and does not import on Python >= 3.10 without a shim (see ``common/_compat.py``),
so this stub declares just the surface the ported code uses. Extend it as later
subsystems need more of the ``dronekit`` API, or delete it once the project moves
to a typed / maintained MAVLink library.
"""

class LocationGlobalRelative:
    lat: float
    lon: float
    alt: float
    def __init__(self, lat: float, lon: float, alt: float = ...) -> None: ...

class LocationGlobal:
    lat: float
    lon: float
    alt: float
    def __init__(self, lat: float, lon: float, alt: float = ...) -> None: ...

class SystemStatus:
    state: str
    def __init__(self, state: str) -> None: ...

class VehicleMode:
    name: str
    def __init__(self, name: str) -> None: ...

class Locations:
    global_relative_frame: LocationGlobalRelative
    global_frame: LocationGlobal

class Vehicle:
    is_armable: bool
    armed: bool
    mode: VehicleMode
    location: Locations
    home_location: LocationGlobal
    def simple_takeoff(self, alt: float) -> None: ...
    def simple_goto(
        self,
        location: LocationGlobalRelative,
        airspeed: float | None = ...,
        groundspeed: float | None = ...,
    ) -> None: ...

def connect(
    ip: str,
    _initialize: bool = ...,
    wait_ready: bool | list[str] | None = ...,
    timeout: float = ...,
    baud: int = ...,
) -> Vehicle: ...
