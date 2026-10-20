"""
Converts the 'drone[#].csv' keyframe files in the Skybrush_LLA folder (made by
csv_lla_converter.py) into the show JSON the drones and ground station load.
Outputs models/show.json.
"""

import csv
import json
import math
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

INPUT_DIR = MODELS_DIR / "Skybrush_LLA"
OUTPUT_PATH = MODELS_DIR / "show.json"

R_EARTH = 6378137  # Earth radius (m), same as csv_lla_converter.py

Frame = tuple[float, float, float, float, int, int, int]


def load_frames(input_filepath: str) -> list[Frame]:
    """
    Read a Skybrush_LLA CSV into (time in seconds, lat, lon, alt, r, g, b) tuples.
    """
    frames: list[Frame] = []
    with open(input_filepath, mode="r", newline="", encoding="utf-8") as infile:
        reader = csv.reader(infile)

        next(reader)

        for row in reader:
            time_ms, lat, lon, alt = (float(v) for v in row[:4])
            r, g, b = (int(float(v)) for v in row[4:7])
            frames.append((time_ms / 1000, lat, lon, alt, r, g, b))

    return frames


def distance_m(a: Frame, b: Frame) -> float:
    """
    Straight-line distance in meters between two frames. Uses the same flat
    earth approximation csv_lla_converter.py used to make the coordinates.
    """
    north = math.radians(b[1] - a[1]) * R_EARTH
    east = math.radians(b[2] - a[2]) * R_EARTH * math.cos(math.radians(a[1]))
    return math.hypot(north, east, b[3] - a[3])


def build_show(frames: list[Frame]) -> dict[str, dict[str, object]]:
    """
    Build one drone's frames for the show JSON. Each frame's flight_speed is
    the speed needed to arrive from the previous frame exactly on time.
    """
    show: dict[str, dict[str, object]] = {}
    for i, frame in enumerate(frames):
        time, lat, lon, alt, r, g, b = frame
        if i == 0:
            time_delay = 0.0
            flight_speed = 0.0
        else:
            time_delay = time - frames[i - 1][0]
            flight_speed = (
                distance_m(frames[i - 1], frame) / time_delay if time_delay else 0.0
            )

        show[f"frame {i + 1}"] = {
            # 8 decimal places of a degree is ~1 mm
            "coordinates": [round(lat, 8), round(lon, 8), round(alt, 3)],
            "time": round(time, 3),
            "time_delay": round(time_delay, 3),
            "flight_speed": round(flight_speed, 3),
            "color": [r, g, b],
        }
    return show


def write_show_json(
    show: dict[str, dict[str, dict[str, object]]], output_path: str
) -> None:
    """
    Write the show JSON with one frame per line. Keeps the file small enough
    for the large-file pre-commit check while staying readable and diffable.
    """
    drone_blocks: list[str] = []
    for drone_id, frames in show.items():
        frame_lines = ",\n".join(
            f"    {json.dumps(name)}: {json.dumps(frame)}"
            for name, frame in frames.items()
        )
        drone_blocks.append(f"  {json.dumps(drone_id)}: {{\n{frame_lines}\n  }}")

    with open(output_path, "w") as outfile:
        outfile.write('{"show": {\n' + ",\n".join(drone_blocks) + "\n}}\n")


def main() -> None:
    # Sorted by drone number (not as text) so drone2 comes before drone10
    input_files = sorted(
        INPUT_DIR.glob("drone*.csv"),
        key=lambda path: int(path.stem.removeprefix("drone")),
    )
    if not input_files:
        print(f"No drone CSV files found in {INPUT_DIR}")
        return

    show: dict[str, dict[str, dict[str, object]]] = {}
    fastest = (0.0, "", "")
    for path in input_files:
        drone_id = path.stem.removeprefix("drone")
        show[drone_id] = build_show(load_frames(str(path)))

        for frame_name, frame in show[drone_id].items():
            speed = frame["flight_speed"]
            assert isinstance(speed, float)
            if speed > fastest[0]:
                fastest = (speed, drone_id, frame_name)

    frame_counts = {len(frames) for frames in show.values()}
    if len(frame_counts) != 1:
        print(f"Error: drones have different numbers of frames: {sorted(frame_counts)}")
        return

    write_show_json(show, str(OUTPUT_PATH))

    print(f"Show JSON written -> {OUTPUT_PATH}")
    print(f"{len(show)} drone(s), {frame_counts.pop()} frame(s) each")
    print(
        f"Fastest flight_speed: {fastest[0]:.2f} m/s "
        + f"(drone {fastest[1]}, {fastest[2]})"
    )


if __name__ == "__main__":
    main()
