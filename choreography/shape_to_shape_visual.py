import json
from pathlib import Path
from typing import Any

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D

# NOTE: the old repo imported ``min_skew_distance``, which no longer exists.
# The 4-arg ``findMinDist`` call below matches ``min_linear_distance``, so this
# points there. Confirm with whoever wrote the original before relying on it.
from choreography.collision_avoidance import min_linear_distance as msd

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def open_json(file_path: str) -> dict[str, Any]:
    with open(file_path) as f:
        data = json.load(f)
    return data["coordinates"]


def visualize_all_paths(path: str) -> None:
    coordinates = open_json(path)

    fig = plt.figure(figsize=(8, 6))
    if fig.canvas.manager is not None:
        fig.canvas.manager.set_window_title("Drone Path Visualization")

    for drone_id in coordinates:
        points = [
            coordinates[drone_id][stage]
            for stage in sorted(coordinates[drone_id].keys())
        ]

        x, y, _ = zip(*points, strict=False)
        plt.plot(x, y, marker="o", label=f"Drone {drone_id}")

    plt.title("Drone Paths Across Stages")
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.legend()
    plt.grid(True)
    plt.show()


def visualize_separate_paths(path: str, loop: bool = False) -> None:
    coordinates = open_json(path)

    drone1_initial = np.array(coordinates["1"]["stage 1"], dtype=np.float32)
    drone1_final = np.array(coordinates["1"]["stage 5"], dtype=np.float32)
    drone2_initial = np.array(coordinates["4"]["stage 1"], dtype=np.float32)
    drone2_final = np.array(coordinates["4"]["stage 5"], dtype=np.float32)

    print(msd.findMinDist(drone1_initial, drone1_final, drone2_initial, drone2_final))

    drone_ids: list[str] = list(coordinates.keys())
    first_drone_id: str = drone_ids[0]
    stages: list[str] = sorted(coordinates[first_drone_id].keys())

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_title("Drone Path Visualization")
    if fig.canvas.manager is not None:
        fig.canvas.manager.set_window_title("Drone Path Visualization")

    # Create a line object for each drone
    scatters: dict[str, Line2D] = {}
    for drone_id in drone_ids:
        scatters[drone_id] = ax.plot([], [], marker="o", label=f"Drone {drone_id}")[0]

    # Set up the plot
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.legend()
    plt.grid(True)

    all_xs: list[float] = []
    all_ys: list[float] = []

    for d in drone_ids:
        for s in stages:
            x, y, _ = coordinates[d][s]
            all_xs.append(x)
            all_ys.append(y)

    # Set axis limits based on all coordinates to keep view stable
    ax.set_xlim(min(all_xs) - 0.00001, max(all_xs) + 0.00001)
    ax.set_ylim(min(all_ys) - 0.00001, max(all_ys) + 0.00001)

    def update(frame: int) -> list[Line2D]:
        for drone_id in drone_ids:
            # Get all points up to the current stage
            current_stage = stages[: frame + 1]
            points = [coordinates[drone_id][s] for s in current_stage]
            x, y, _ = zip(*points, strict=False)

            # Update the line for this drone
            scatters[drone_id].set_data(x, y)
        ax.set_title(f"Drone Positions at Stage: {stages[frame]}")

        return list(scatters.values())

    # Keep a reference so the animation is not garbage-collected before show().
    _ani = FuncAnimation(
        fig, update, frames=len(stages), interval=1000, blit=False, repeat=loop
    )

    plt.show()


def main() -> None:
    config = MODELS_DIR / "Example jsons" / "example_x_config.json"
    visualize_separate_paths(str(config), loop=True)


if __name__ == "__main__":
    main()
