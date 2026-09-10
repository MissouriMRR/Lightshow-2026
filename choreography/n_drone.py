import os
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray

MIN_DRONES = 4

Points = NDArray[Any]


def load_points(input_file: str) -> Points:
    points: list[list[float]] = []
    with open(input_file) as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            parts = line.split()
            try:
                coords = [float(p) for p in parts]
            except ValueError as e:
                raise ValueError(
                    f"Could not parse line to floats: '{line}' in file {input_file}"
                ) from e

            points.append(coords)
    return np.array(points)


def remove_duplicates(points: Points) -> Points:
    checked: set[tuple[int, ...]] = set()

    unique_points: list[tuple[Any, ...]] = []
    for p in map(tuple, points):
        rounded_point = tuple(round(v) for v in p)
        if rounded_point not in checked:
            checked.add(rounded_point)
            unique_points.append(p)
    return np.array(unique_points)


def downsample(points: Points, drone_count: int) -> Points:
    points = remove_duplicates(points)
    old_total = len(points)

    if drone_count >= old_total:
        return points

    step = old_total / drone_count
    indices = (np.arange(drone_count) * step).astype(int)
    indices = np.clip(indices, 0, old_total - 1)
    return points[indices]


def save_points(points: Points, output_file: str) -> None:
    with open(output_file, "w") as f:
        f.writelines(" ".join(str(v) for v in p) + "\n" for p in points)


def n_drone_run(base_frames_path: str, file_name: str) -> None:
    # Read and validate drone count
    raw_drone_count = input("Enter the desired number of drones: ")
    try:
        drone_count = int(raw_drone_count)
        if drone_count <= 0:
            raise ValueError("drone count must be a positive integer")
    except ValueError as e:
        raise SystemExit(f"Invalid drone count '{raw_drone_count}': {e}") from e

    path = os.path.join(base_frames_path, "TXT Files")

    input_path = os.path.join(path, f"resized_{file_name}.txt")
    output_path = os.path.join(path, "Reduced TXT Files", f"reduced_{file_name}.txt")

    points = load_points(input_path)

    if drone_count < MIN_DRONES and len(points) > MIN_DRONES:
        print(
            f"Using specified drone count {drone_count} is less than minimum {MIN_DRONES}, setting to minimum."
        )
        drone_count = MIN_DRONES

    reduced = downsample(points, drone_count)
    save_points(reduced, output_path)

    print(f"Reduced: {len(points)} -> {len(reduced)} points as '{output_path}'")
    plot_points(points, reduced)


def plot_points(original: Points, reduced: Points) -> None:
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    orig_x, orig_y = original[:, 0], original[:, 1]
    red_x, red_y = reduced[:, 0], reduced[:, 1]

    # matplotlib infers Axes3D.scatter's `zs` as a scalar from its default; it
    # accepts arrays at runtime, so call it untyped.
    ax_any: Any = ax
    ax_any.scatter(
        np.zeros(len(original)), orig_x, orig_y, label="Original Points", alpha=0.3
    )
    ax_any.scatter(
        np.zeros(len(reduced)), red_x, red_y, label="Reduced Points", marker="o"
    )

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    ax.legend()
    plt.show()
