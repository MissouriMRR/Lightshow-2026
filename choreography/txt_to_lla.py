import math
import os
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

Point = tuple[float, ...]


# Generate lat/lon/alt coordinates and a spreadsheet with coordinates plus a
# Google Earth (KML) visualization.
def txt_to_gps_centered_rgb(
    input_filepath: str,
    output_csv: str,
    output_kml: str,
    reference_lat: float,
    reference_lon: float,
    reference_alt: float,
    add_label: bool,
    scale: float = 1.0,
) -> None:
    R_earth = 6378137  # Earth radius (m)
    points: list[Point] = []
    has_rgb = False

    # Read input file
    try:
        with open(input_filepath) as infile:
            for line in infile:
                parts = line.split()
                if len(parts) == 2:
                    y, z = (float(v) for v in parts[:2])
                    points.append((0.0, y, z))
                elif len(parts) == 3:
                    x, y, z = (float(v) for v in parts[:3])
                    points.append((x, y, z))
                # A line with 6 fields carries per-point RGB: x y z r g b
                elif len(parts) == 6:
                    x, y, z = (float(v) for v in parts[:3])
                    r, g, b = (int(v) for v in parts[3:6])
                    points.append((x, y, z, r, g, b))
                    has_rgb = True

    except FileNotFoundError:
        print(f"Error: file not found at {input_filepath}")
        return

    if not points:
        print("No valid points found in file.")
        return

    # Compute centroid of the 3d model
    centroid_x = sum(p[0] for p in points) / len(points)
    centroid_y = sum(p[1] for p in points) / len(points)
    centroid_z = sum(p[2] for p in points) / len(points)
    print(
        f"Model centered around ({centroid_x:.3f}, {centroid_y:.3f}, {centroid_z:.3f})"
    )

    gps_points: list[Point] = []
    for p in points:
        x, y, z = p[:3]
        x -= centroid_x
        y -= centroid_y
        z -= centroid_z
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

        if has_rgb:
            gps_points.append((lat, lon, alt, p[3], p[4], p[5]))
        else:
            gps_points.append((lat, lon, alt))

    # Write CSV
    with open(output_csv, "w") as csv_file:
        if has_rgb:
            csv_file.write("latitude,longitude,altitude,R,G,B\n")
            for lat, lon, alt, r, g, b in gps_points:
                csv_file.write(f"{lat},{lon},{alt},{r},{g},{b}\n")
        else:
            csv_file.write("latitude,longitude,altitude\n")
            for lat, lon, alt in gps_points:
                csv_file.write(f"{lat},{lon},{alt}\n")
    print(f"GPS CSV written -> {output_csv}")

    # Write KML
    with open(output_kml, "w") as kmlfile:
        kmlfile.write("<?xml version='1.0' encoding='UTF-8'?>\n")
        kmlfile.write("<kml xmlns='http://www.opengis.net/kml/2.2'>\n")
        kmlfile.write("  <Document>\n")
        kmlfile.write(f"    <name>{os.path.basename(output_kml)}</name>\n")

        for i, pt in enumerate(gps_points):
            if has_rgb:
                lat, lon, alt, r, g, b = pt
                color = f"ff{int(b):02x}{int(g):02x}{int(r):02x}"  # KML uses AABBGGRR
            else:
                lat, lon, alt = pt
                color = "ff0000ff"  # red default

            kmlfile.write("    <Placemark>\n")
            if add_label:
                kmlfile.write(f"      <name>Drone {i + 1}</name>\n")
            kmlfile.write("      <Style>\n")
            kmlfile.write("        <IconStyle>\n")
            kmlfile.write(f"          <color>{color}</color>\n")
            kmlfile.write("          <scale>0.6</scale>\n")
            kmlfile.write("          <Icon>\n")
            kml_icon = "http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png"
            kmlfile.write(f"            <href>{kml_icon}</href>\n")
            kmlfile.write("          </Icon>\n")
            kmlfile.write("        </IconStyle>\n")
            kmlfile.write("      </Style>\n")
            kmlfile.write("      <Point>\n")
            kmlfile.write("        <altitudeMode>absolute</altitudeMode>\n")
            kmlfile.write(f"        <coordinates>{lon},{lat},{alt}</coordinates>\n")
            kmlfile.write("      </Point>\n")
            kmlfile.write("    </Placemark>\n")

        kmlfile.write("  </Document>\n</kml>\n")

    print(f"KML written -> {output_kml}")


def main() -> None:
    txt_file = input("Enter input .txt file name: ").strip()
    base_name = os.path.splitext(txt_file)[0]

    frames_dir = MODELS_DIR / "Sample Frames"
    txt_path = str(frames_dir / "TXT Files" / txt_file)

    # Use proper output extensions (avoid writing KML/CSV back into the source TXT)
    csv_file = str(frames_dir / "CSV Files" / f"{base_name}.csv")
    kml_file = str(frames_dir / "KML Files" / f"{base_name}.kml")

    # Safety: if outputs would overwrite the input file, pick alternate names and warn.
    if os.path.abspath(csv_file) == os.path.abspath(txt_file) or (
        os.path.abspath(kml_file) == os.path.abspath(txt_file)
    ):
        csv_file = f"{base_name}_out.csv"
        kml_file = f"{base_name}_out.kml"
        print(
            f"Warning: output filenames would overwrite input '{txt_file}'. Using '{csv_file}' and '{kml_file}' instead."
        )

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
    scale = float(input("Scale (meters per XYZ unit, e.g., 1.0): "))
    add_label = input("Add drone labels? (y/n): ").lower() == "y"

    txt_to_gps_centered_rgb(
        txt_path,
        csv_file,
        kml_file,
        reference_lat,
        reference_lon,
        reference_alt,
        add_label,
        scale,
    )


if __name__ == "__main__":
    main()
