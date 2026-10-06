"""
Converts all 'Drone [#].csv' files from the Skybrush_CSV folder with relative coordinates into real world
lat/lon/altitude coordinates. Outputs into the Skybrush_LLA folder.
"""

import csv
import math
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

Point = tuple[float, ...]


# Generate lat/lon/alt coordinates
def txt_to_gps_centered_rgb(
    input_filepath: str,
    output_csv: str,
    reference_lat: float,
    reference_lon: float,
    reference_alt: float,
    scale: float = 1.0,
) -> None:
    R_earth = 6378137  # Earth radius (m)
    points: list[Point] = []

    # Read input file
    try:
        with open(input_filepath, mode="r", newline="", encoding="utf-8") as infile:
            reader = csv.reader(infile)

            next(reader)

            for row in reader:
                time = float(row[0])
                x, y, z = (float(v) for v in row[1:4])
                r, g, b = (float(v) for v in row[4:])
                points.append((time, x, y, z, r, g, b))

    except FileNotFoundError:
        print(f"Error: file not found at {input_filepath}")
        return

    if not points:
        print("No valid points found in file.")
        return

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


def main() -> None:
    input_dir = MODELS_DIR / "Skybrush_CSV"
    output_dir = MODELS_DIR / "Skybrush_LLA"
    output_dir.mkdir(parents=True, exist_ok=True)

    input_files = sorted(input_dir.glob("*.csv"))
    if not input_files:
        print(f"No CSV files found in {input_dir}")
        return

    # One shared reference point for every drone's file -- using a different
    # reference per file would break the formation's relative positioning.
    default_coords = input(
        "Use default coordinates for S&T golf course? (y/n): "
    ).lower()
    if default_coords == "y":
        reference_lat = 37.948557
        reference_lon = -91.783716
        reference_alt = 400.0
    else:
        reference_lat = float(input("Center latitude (e.g., 37.950177): "))
        reference_lon = float(input("Center longitude (e.g., -91.780905): "))
        reference_alt = float(input("Base altitude (meters): "))
    scale = 1.0

    print(f"Converting {len(input_files)} drone show file(s)...")
    for input_path in input_files:
        output_path = output_dir / input_path.name
        txt_to_gps_centered_rgb(
            str(input_path),
            str(output_path),
            reference_lat,
            reference_lon,
            reference_alt,
            scale,
        )


if __name__ == "__main__":
    main()
