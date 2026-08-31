"""Minimal type stub for the ``dronekit`` package.

``dronekit`` 2.9.2 (the last PyPI release, from 2015) ships no type information
and does not import on Python >= 3.10 without a shim, so this stub declares just
the surface the ported code uses. Extend it as later subsystems (``drone/``,
``Station/``) need more of the ``dronekit`` API, or delete it once the project
moves to a typed / maintained MAVLink library.
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
