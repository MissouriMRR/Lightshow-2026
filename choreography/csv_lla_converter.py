"""
Converts all 'Drone [#].csv' files from the Skybrush_CSV folder with relative coordinates into real world
lat/lon/altitude coordinates. Only the rows nearest to the Blender keyframes listed in keyframes.csv
are kept, plus extra keyframes generated for each rotation listed in rotations.csv.
Outputs into the Skybrush_LLA folder.
"""

import csv
import itertools
import math
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

KEYFRAME_FILE = "keyframes.csv"
ROTATION_FILE = "rotations.csv"
FRAME_RATE = 24  # Blender frames per second
START_FRAME = 1  # Blender frame that Skybrush exports as time 0

# Rotation keyframe generation
MAX_STEP_DEG = 25.0  # Most rotation allowed between two keyframes
TOLERANCE_M = 0.3  # Most a drone may stray from its Skybrush path between keyframes

Point = tuple[float, ...]


def frame_to_ms(frame: int) -> float:
    """Convert a Blender frame number to show time in milliseconds."""
    return (frame - START_FRAME) / FRAME_RATE * 1000


def load_drone_points(input_filepath: str) -> list[Point]:
    """
    Read a Skybrush CSV into (time, x, y, z, r, g, b) tuples.
    """
    points: list[Point] = []
    with open(input_filepath, mode="r", newline="", encoding="utf-8") as infile:
        reader = csv.reader(infile)

        next(reader)

        for row in reader:
            time = float(row[0])
            x, y, z = (float(v) for v in row[1:4])
            r, g, b = (float(v) for v in row[4:])
            points.append((time, x, y, z, r, g, b))

    return points


def load_keyframes(keyframe_filepath: str) -> list[tuple[float, str]]:
    """
    Read Blender keyframes from a CSV with a header row, the frame number in
    the first column and an optional name in the second. Returns
    (show time in milliseconds, name) pairs; unnamed keyframes are named
    after their frame number.
    """
    keyframes: list[tuple[float, str]] = []
    with open(keyframe_filepath, mode="r", newline="", encoding="utf-8") as infile:
        reader = csv.reader(infile)

        next(reader)

        for row in reader:
            if not row or not row[0].strip():
                continue
            frame = int(row[0])
            name = row[1].strip() if len(row) > 1 and row[1].strip() else ""
            keyframes.append((frame_to_ms(frame), name or f"frame{frame}"))

    return keyframes


def load_rotations(rotation_filepath: str) -> list[tuple[int, int, float]]:
    """
    Read rotations from a CSV with a header row and the columns
    start_frame, end_frame, degrees. Returns an empty list if the file doesn't exist.
    """
    rotations: list[tuple[int, int, float]] = []
    try:
        with open(rotation_filepath, mode="r", newline="", encoding="utf-8") as infile:
            reader = csv.reader(infile)

            next(reader)

            for row in reader:
                if not row or not row[0].strip():
                    continue
                rotations.append((int(row[0]), int(row[1]), float(row[2])))
    except FileNotFoundError:
        pass

    return rotations


def nearest_index(row_times: list[float], time: float) -> int:
    """Index of the row closest in time to the given time."""
    return min(range(len(row_times)), key=lambda i: abs(row_times[i] - time))


def segment_error(points: list[Point], start: int, end: int) -> float:
    """
    Largest distance, in meters, between where a drone really is during
    rows start..end and where it would be flying a straight line between
    them at constant speed.
    """
    t0, x0, y0, z0 = points[start][:4]
    t1, x1, y1, z1 = points[end][:4]
    worst = 0.0
    for p in points[start + 1 : end]:
        f = (p[0] - t0) / (t1 - t0)
        expected = (x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, z0 + (z1 - z0) * f)
        worst = max(worst, math.dist(p[1:4], expected))
    return worst


def swarm_segment_error(all_points: list[list[Point]], start: int, end: int) -> float:
    """Worst segment_error across every drone."""
    return max(segment_error(points, start, end) for points in all_points)


def split_segment(all_points: list[list[Point]], start: int, end: int) -> list[int]:
    """
    Row indices to add between start and end so that no drone strays more
    than TOLERANCE_M from its path. Halves the segment until it fits.
    """
    if end - start < 2 or swarm_segment_error(all_points, start, end) <= TOLERANCE_M:
        return []
    middle = (start + end) // 2
    return (
        split_segment(all_points, start, middle)
        + [middle]
        + split_segment(all_points, middle, end)
    )


def rotation_keyframe_indices(
    all_points: list[list[Point]],
    row_times: list[float],
    start_frame: int,
    end_frame: int,
    degrees: float,
) -> list[int]:
    """
    Pick keyframe rows for one rotation: evenly spaced so each step turns at
    most MAX_STEP_DEG, then split further wherever the data shows a drone
    straying more than TOLERANCE_M (from easing or multi-axis rotation).
    """
    start_ms = frame_to_ms(start_frame)
    end_ms = frame_to_ms(end_frame)
    steps = max(1, math.ceil(abs(degrees) / MAX_STEP_DEG))

    planned = sorted(
        {
            nearest_index(row_times, start_ms + (end_ms - start_ms) * i / steps)
            for i in range(steps + 1)
        }
    )

    indices = list(planned)
    for start, end in itertools.pairwise(planned):
        indices += split_segment(all_points, start, end)
    indices.sort()

    worst = max(
        (
            swarm_segment_error(all_points, start, end)
            for start, end in itertools.pairwise(indices)
        ),
        default=0.0,
    )
    added = len(indices) - len(planned)
    print(
        f"Rotation frames {start_frame}-{end_frame} ({degrees:g} deg): "
        + f"{len(planned)} planned, {added} added by check, worst error {worst:.2f} m"
    )
    return indices


# Generate lat/lon/alt coordinates
def points_to_gps_csv(
    points: list[Point],
    output_csv: str,
    reference_lat: float,
    reference_lon: float,
    reference_alt: float,
    scale: float = 1.0,
) -> None:
    R_earth = 6378137  # Earth radius (m)

    gps_points: list[Point] = []
    for p in points:
        x, y, z = p[1:4]
        x *= scale
        y *= scale
        z *= scale

        delta_lat = (y / R_earth) * (180 / math.pi)
        delta_lon = (x / (R_earth * math.cos(math.radians(reference_lat)))) * (
            180 / math.pi
        )

        lat = reference_lat + delta_lat
        lon = reference_lon + delta_lon
        alt = reference_alt + z

        gps_points.append((p[0], lat, lon, alt, p[4], p[5], p[6]))

    # Write CSV
    with open(output_csv, "w") as csv_file:
        csv_file.write("time [msec],latitude,longitude,altitude,R,G,B\n")
        for time, lat, lon, alt, r, g, b in gps_points:
            csv_file.write(f"{time},{lat},{lon},{alt},{r},{g},{b}\n")

    print(f"GPS CSV written -> {output_csv}")


def write_formation_txt(
    all_points: list[list[Point]], row_index: int, output_txt: str
) -> None:
    """
    Write every drone's position at one row as 'x y z r g b' lines, one per
    drone in drone order, in the format txt_to_lla.py reads.
    """
    with open(output_txt, "w") as txt_file:
        for points in all_points:
            _, x, y, z, r, g, b = points[row_index]
            txt_file.write(f"{x} {y} {z} {int(r)} {int(g)} {int(b)}\n")

    print(f"Formation TXT written -> {output_txt}")


def main() -> None:
    input_dir = MODELS_DIR / "Skybrush_CSV"
    output_dir = MODELS_DIR / "Skybrush_LLA"
    output_dir.mkdir(parents=True, exist_ok=True)
    # txt_to_lla.py reads its input from this folder
    txt_dir = MODELS_DIR / "Sample Frames" / "TXT Files"

    # Only match drone files so the keyframe and rotation lists aren't converted as drones.
    # Sorted by drone number (not as text) so Drone 2 comes before Drone 10.
    input_files = sorted(
        input_dir.glob("Drone *.csv"), key=lambda path: int(path.stem.split()[-1])
    )
    if not input_files:
        print(f"No CSV files found in {input_dir}")
        return

    keyframe_path = input_dir / KEYFRAME_FILE
    try:
        keyframes = load_keyframes(str(keyframe_path))
    except FileNotFoundError:
        print(f"Error: keyframe file not found at {keyframe_path}")
        return
    print(f"Loaded {len(keyframes)} keyframe(s) at {FRAME_RATE} fps")

    # Every drone is loaded up front because rotation keyframes are checked
    # against the whole swarm at once.
    all_points = [load_drone_points(str(path)) for path in input_files]
    row_times = [p[0] for p in all_points[0]]
    for path, points in zip(input_files, all_points, strict=True):
        if [p[0] for p in points] != row_times:
            print(
                f"Error: {path.name} has different timestamps than {input_files[0].name}"
            )
            return

    indices = {nearest_index(row_times, t) for t, _ in keyframes}
    for start_frame, end_frame, degrees in load_rotations(
        str(input_dir / ROTATION_FILE)
    ):
        indices.update(
            rotation_keyframe_indices(
                all_points, row_times, start_frame, end_frame, degrees
            )
        )
    keyframe_indices = sorted(indices)
    print(f"{len(keyframe_indices)} keyframe(s) total")

    # One shared reference point for every drone's file -- using a different
    # reference per file would break the formation's relative positioning.
    default_coords = input(
        "Use default coordinates for S&T golf course? (y/n): "
    ).lower()
    if default_coords == "y":
        reference_lat = 37.948557
        reference_lon = -91.783716
        reference_alt = 0
    else:
        reference_lat = float(input("Center latitude (e.g., 37.950177): "))
        reference_lon = float(input("Center longitude (e.g., -91.780905): "))
        reference_alt = float(input("Base altitude (meters): "))
    scale = 1.0

    print(f"Converting {len(input_files)} drone show file(s)...")
    for input_path, points in zip(input_files, all_points, strict=True):
        # "Drone 5.csv" -> "drone5.csv"
        drone_number = input_path.stem.split()[-1]
        output_path = output_dir / f"drone{drone_number}.csv"
        points_to_gps_csv(
            [points[i] for i in keyframe_indices],
            str(output_path),
            reference_lat,
            reference_lon,
            reference_alt,
            scale,
        )

    # One TXT per named keyframe so each formation can be checked in Google Earth
    print(f"Writing {len(keyframes)} formation file(s)...")
    for time, name in keyframes:
        write_formation_txt(
            all_points,
            nearest_index(row_times, time),
            str(txt_dir / f"skybrush_{name}.txt"),
        )


if __name__ == "__main__":
    main()
