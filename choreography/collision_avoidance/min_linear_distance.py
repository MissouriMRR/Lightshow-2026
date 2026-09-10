import numpy as np
from numpy.typing import NDArray

EPSILON = 0.0001

Vector3 = NDArray[np.float32]


def _require_3d_vector(v: object, name: str) -> None:
    """
    Validates that the input is a 3D numpy vector.

    Args:
        v: The vector to validate.
        name: The name of the vector.

    Raises:
        TypeError: If v is not a numpy ndarray.
        ValueError: If v does not have shape (3,).
    """

    if not isinstance(v, np.ndarray):
        raise TypeError(f"{name} must be a numpy ndarray, but got type {type(v)}")
    if v.shape != (3,):
        raise ValueError(
            f"{name} must be a 3D vector (shape (3,)), but got shape {v.shape}"
        )


def findMinDist(
    Drone1_initial: Vector3,
    Drone1_final: Vector3,
    Drone2_initial: Vector3,
    Drone2_final: Vector3,
) -> float:
    """
    Function that takes two drone paths and outputs the minimum distance.
    https://math.stackexchange.com/questions/2213165/find-shortest-distance-between-lines-in-3d

    Inputs:
        Drone1_initial = a 3D vector of the initial coordinates of drone 1.
        Drone1_final = a 3D vector of the final coordinates of drone 1.
        Drone2_initial = a 3D vector of the initial coordinates of drone 2.
        Drone2_final = a 3D vector of the initial coordinates of drone 2.
    Returns:
        The minimum distance between the two drone paths.
    """

    # Shape validation
    _require_3d_vector(Drone1_initial, "Drone1_initial")
    _require_3d_vector(Drone1_final, "Drone1_final")
    _require_3d_vector(Drone2_initial, "Drone2_initial")
    _require_3d_vector(Drone2_final, "Drone2_final")

    # vectors in the direction of pointx_i -> pointx_f
    # These are used to define functions f1 and f2 in the form:
    # f1(t) = drone1_initial + t * drone1_dir
    # f2(t) = drone2_initial + s * drone2_dir
    # These functions are parametric functions of time, with t=0 -> Dronex_initial,
    # and t=1 -> Dronex_final
    v1_dir = Drone1_final - Drone1_initial
    v2_dir = Drone2_final - Drone2_initial

    n = np.cross(v1_dir, v2_dir)

    # find difference between the initial positions
    initial_diff = Drone2_initial - Drone1_initial

    # If lines are parallel, find the point distance
    if np.linalg.norm(n) < EPSILON:
        top = np.linalg.norm(np.cross(initial_diff, v1_dir))
        return float(top / np.linalg.norm(v1_dir))

    # t and s values for points that give minimum distance between lines
    t1 = np.dot(np.cross(v2_dir, n), initial_diff) / np.dot(n, n)
    t2 = np.dot(np.cross(v1_dir, n), initial_diff) / np.dot(n, n)

    # 0 < t < 1. Clamp time values down into acceptable range
    t1 = np.clip(t1, 0, 1)
    t2 = np.clip(t2, 0, 1)

    # Use time values to find the point locations
    p1 = Drone1_initial + t1 * v1_dir
    p2 = Drone2_initial + t2 * v2_dir

    # Find the length of the distance between the two points and return it.
    return float(np.linalg.norm(p2 - p1))
