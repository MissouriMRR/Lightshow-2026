"""Temporary type stub for the not-yet-ported ``Station`` package.

Only the ``Point3d`` surface consumed by ``common.utils`` is declared here, so the
common port type-checks without pulling in the ``Station`` package, which lands in
a later PR. Delete this stub in the PR that ports ``Station/point.py``.
"""

class Point3d:
    x: float
    y: float
    z: float
    def __init__(self, x: float, y: float, z: float) -> None: ...
