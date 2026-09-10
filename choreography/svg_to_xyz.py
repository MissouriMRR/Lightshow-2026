import math
import os
from pathlib import Path
from typing import Any
from xml.dom import minidom

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray
from svgpathtools import Arc, CubicBezier, Line, parse_path

from choreography.resize_images import resize_image_txt
from choreography.svg_tag_convertor import convert_to_paths

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

Point = tuple[float, float]


def svg_to_xyz(svg_file: str, txt_path: str) -> None:
    """Convert SVG paths to XYZ coordinates and write them to ``txt_path``."""

    density = 0.02

    all_points: list[Point] = []
    doc = minidom.parse(svg_file)

    if not doc.getElementsByTagName("path"):
        print("No <path> tags found. Converting <g> tags to <path> tags...")
        convert_to_paths(svg_file)
        doc = minidom.parse(svg_file)
    else:
        print("Path tags found.")

    for ipath, path in enumerate(doc.getElementsByTagName("path")):
        print(f"Path {ipath}:")
        d = path.getAttribute("d")
        parsed_path = parse_path(d)

        print(f"Objects:\n{parsed_path}\n{'-' * 40}")

        for obj in parsed_path:
            start: Point = (obj.start.real, obj.start.imag)
            end: Point = (obj.end.real, obj.end.imag)
            all_points.extend([start, end])

            coords_str = f"(({round(start[0], 3)}, {round(start[1], 3)}), ({round(end[0], 3)}, {round(end[1], 3)}))"
            print(f"{type(obj).__name__} start/end coords: {coords_str}", end=" ")
            if isinstance(obj, CubicBezier):
                c1, c2 = obj.control1, obj.control2
                print(
                    f"Control points: control1/control2 (({round(c1.real, 3)}, {round(c1.imag, 3)}), ({round(c2.real, 3)}, {round(c2.imag, 3)}))"
                )

                bezier_points = get_cubic_bezier_points(
                    obj.start, c1, c2, obj.end, density=density
                )
                all_points.extend(bezier_points)
            elif isinstance(obj, Line):
                all_points.extend(get_line_points(obj.start, obj.end, spacing=density))
                print("Control points: control1/control2 ((N/A, N/A), (N/A, N/A))")
            elif isinstance(obj, Arc):
                radius_str = (
                    f"({round(obj.radius.real, 3)}, {round(obj.radius.imag, 3)})"
                )
                print(f"Arc start/end coords: {coords_str} radius: {radius_str}")
                all_points.extend(
                    calculate_circle_points(
                        obj.start, obj.end, obj.radius.real, spacing=density
                    )
                )
            else:
                all_points.extend([start, end])

        print("-" * 40)
    doc.unlink()

    if all_points:
        xy_coords = np.array(all_points)
        output_txt(xy_coords, txt_path)
        graph_points(xy_coords)


def output_txt(xyz_points: NDArray[Any], txt_filepath: str) -> bool:
    xyz_list: list[list[float]] = xyz_points.tolist()
    print(xyz_list)
    try:
        with open(txt_filepath, "w") as txt_file:
            txt_file.writelines(f"{x} {-y}\n" for x, y in xyz_list)
            print(f"Created -> {txt_filepath}")
            return True
    except OSError as e:
        print(f"Error: Could not write to .txt file at {txt_filepath}")
        print(e)
        return False


def graph_points(xyz_points: NDArray[Any], color: str = "black") -> None:
    """Graph the XYZ points in 2D."""

    plt.plot(xyz_points[:, 0], xyz_points[:, 1], ".-", color=color)
    plt.title("SVG Path Points")
    plt.axis("equal")

    ax = plt.gca()
    ax.invert_yaxis()

    plt.show()


def get_cubic_bezier_points(
    p0: complex, p1: complex, p2: complex, p3: complex, density: float
) -> list[Point]:
    """Generate points along a cubic Bezier curve."""

    points: list[Point] = []
    num_segments = get_cubic_bezier_point_density(p0, p1, p2, p3, density)
    print(f"Generating {num_segments} segments for Bezier curve from {p0} to {p3}")

    for i in range(num_segments):
        t = i / num_segments

        term0 = (1 - t) ** 3
        term1 = 3 * (1 - t) ** 2 * t
        term2 = 3 * (1 - t) * t**2
        term3 = t**3

        x = term0 * p0.real + term1 * p1.real + term2 * p2.real + term3 * p3.real
        y = term0 * p0.imag + term1 * p1.imag + term2 * p2.imag + term3 * p3.imag

        points.append((x, y))

    return points


def get_cubic_bezier_point_density(
    p0: complex, p1: complex, p2: complex, p3: complex, spacing: float
) -> int:
    length = CubicBezier(p0, p1, p2, p3).length()
    return math.floor((length or 0.0) * spacing)


def get_line_points(p0: complex, p1: complex, spacing: float) -> list[Point]:
    length = abs(p1 - p0)
    num_segments = max(1, math.floor(length * spacing))

    points: list[Point] = []
    for i in range(num_segments + 1):
        t = i / num_segments
        x = (1 - t) * p0.real + t * p1.real
        y = (1 - t) * p0.imag + t * p1.imag
        points.append((x, y))

    return points


def calculate_circle_points(
    start: complex, end: complex, radius: float, spacing: float
) -> list[Point]:
    center = (start + end) / 2

    points: list[Point] = []

    num_segments = max(3, int((2 * math.pi * radius) * spacing))

    for i in range(num_segments + 1):
        theta = (i / num_segments) * 2 * math.pi
        x = center.real + radius * math.cos(theta)
        y = center.imag + radius * math.sin(theta)
        points.append((x, y))

    return points


def svg_to_xyz_run(base_frames_path: str, file_name: str) -> None:
    svg_path = str(MODELS_DIR / "2D Source" / f"{file_name}.svg")

    output_path = os.path.join(base_frames_path, "TXT Files")

    print(output_path)

    if not os.path.isdir(output_path):
        os.mkdir(output_path)

    txt_path = os.path.join(output_path, f"{file_name}.txt")

    svg_to_xyz(svg_path, txt_path)
    resize_image_txt()
