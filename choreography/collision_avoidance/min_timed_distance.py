import numpy as np
from numpy.typing import NDArray

Vector3 = NDArray[np.float32]


def findMinDist(
    Drone1_initial: Vector3,
    Drone1_final: Vector3,
    Drone2_initial: Vector3,
    Drone2_final: Vector3,
    Drone1_velocity: float,
    Drone2_velocity: float,
) -> tuple[float, float]:
    """
    Takes two drone paths and outputs the minimum distance and the time of that
    minimum distance.

    Inputs:
        Drone1_initial = a 3D vector of the initial coordinates of drone 1.
        Drone1_final = a 3D vector of the final coordinates of drone 1.
        Drone2_initial = a 3D vector of the initial coordinates of drone 2.
        Drone2_final = a 3D vector of the initial coordinates of drone 2.
        Drone1_velocity = a scalar value containing the velocity of drone 1.
        Drone2_velocity = a scalar value containing the velocity of drone 2.

    Returns:
        A pair (t_min, min_distance) with the minimum distance and the time that
        minimum distance occurs.
    """
    # The final time each drone will reach its destination
    t1_final = np.linalg.norm(Drone1_final - Drone1_initial) / Drone1_velocity
    t2_final = np.linalg.norm(Drone2_final - Drone2_initial) / Drone2_velocity

    # unit vectors in the direction of pointx_i -> pointx_f
    v1_dir = (Drone1_final - Drone1_initial) / np.linalg.norm(
        Drone1_final - Drone1_initial
    )
    v2_dir = (Drone2_final - Drone2_initial) / np.linalg.norm(
        Drone2_final - Drone2_initial
    )

    # velocity vectors
    v1 = Drone1_velocity * v1_dir
    v2 = Drone2_velocity * v2_dir

    # Calculate r and v vectors for finding t_min.
    r = Drone1_initial - Drone2_initial
    v = v1 - v2

    bottom = np.dot(v, v)
    if np.linalg.norm(bottom) == 0:
        return (0.0, float(np.linalg.norm(r)))

    t_min = float(-np.dot(r, v) / bottom)

    # Clamp t_min to the valid time interval [0, max(t1_final, t2_final)]
    t_limit = float(max(t1_final, t2_final))
    t_min = min(max(t_min, 0.0), t_limit)

    # Drone locations at t = t_min
    Drone1_t_min = Drone1_initial + v1 * t_min
    Drone2_t_min = Drone2_initial + v2 * t_min

    # Find the distance at the minimum time
    min_dist = float(np.linalg.norm(Drone2_t_min - Drone1_t_min))
    return (t_min, min_dist)
