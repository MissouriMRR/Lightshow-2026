import os
from pathlib import Path
from typing import TypedDict

from matplotlib import patches
from matplotlib import pyplot as plt

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


class ImageSize(TypedDict):
    all_points_x: list[float]
    all_points_y: list[float]
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    width: float
    height: float
    aspect_ratio: float


class ResizeResult(TypedDict):
    new_points_x: list[float]
    new_points_y: list[float]
    new_height: float
    new_aspect_ratio: float
    scale: float


def resize_image_txt() -> None:
    svg_dir_path = MODELS_DIR / "Sample Frames" / "TXT Files"

    first_file = os.path.join(svg_dir_path, os.listdir(svg_dir_path)[0])
    smallest_width: float = get_image_size(first_file)["width"]
    smallest_width_file: str = ""
    for txt_file in os.listdir(svg_dir_path):
        if (
            txt_file.endswith(".txt")
            and not txt_file.startswith("reduced_")
            and not txt_file.startswith("resized_")
        ):
            txt_filepath = os.path.join(svg_dir_path, txt_file)
            size = get_image_size(txt_filepath)

            if size["width"] <= smallest_width:
                smallest_width = size["width"]
                smallest_width_file = txt_file

    plt.ion()
    for txt_file in os.listdir(svg_dir_path):
        if (
            txt_file.endswith(".txt")
            and not txt_file.startswith("reduced_")
            and not txt_file.startswith("resized_")
        ):
            txt_filepath = os.path.join(svg_dir_path, txt_file)
            size = get_image_size(txt_filepath)

            new_txt_filepath = os.path.join(svg_dir_path, f"resized_{txt_file}")

            print(f"smallest width = {smallest_width} of file {smallest_width_file}")

            new_size = resize_image(new_txt_filepath, size, smallest_width)

            show_svg_with_viewbox(
                size["all_points_x"],
                size["all_points_y"],
                size["min_x"],
                size["min_y"],
                size["width"],
                size["height"],
                plt_title=f"Original Image: {txt_file}",
            )
            show_svg_with_viewbox(
                new_size["new_points_x"],
                new_size["new_points_y"],
                size["min_x"],
                size["min_y"],
                smallest_width,
                new_size["new_height"],
                plt_title=f"Resized Image: {txt_file}",
            )
            input("Press Enter to continue...")

            plt.close("all")
    plt.ioff()


def get_image_size(txt_filepath: str) -> ImageSize:
    all_points_x: list[float] = []
    all_points_y: list[float] = []

    with open(txt_filepath) as txt_file:
        for line in txt_file:
            split_line = line.replace("\n", "").split()

            all_points_x.append(float(split_line[0]))
            all_points_y.append(float(split_line[1]))

    min_x = min(all_points_x)
    max_x = max(all_points_x)

    min_y = min(all_points_y)
    max_y = max(all_points_y)

    width = max_x - min_x
    height = max_y - min_y

    return {
        "all_points_x": all_points_x,
        "all_points_y": all_points_y,
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "width": width,
        "height": height,
        "aspect_ratio": width / height,
    }


def resize_image(
    txt_filepath: str, img_size: ImageSize, new_width: float
) -> ResizeResult:
    new_height = new_width / img_size["aspect_ratio"]
    new_aspect_ratio = new_width / new_height
    scale = new_width / img_size["width"]

    new_points: list[tuple[float, float]] = []
    for x, y in zip(img_size["all_points_x"], img_size["all_points_y"], strict=False):
        new_x = (x - img_size["min_x"]) * scale + img_size["min_x"]
        new_y = (y - img_size["min_y"]) * scale + img_size["min_y"]
        new_points.append((new_x, new_y))

    with open(txt_filepath, "w") as txt_file:
        for x, y in new_points:
            txt_file.write(f"{x} {y}\n")

    return {
        "new_points_x": [p[0] for p in new_points],
        "new_points_y": [p[1] for p in new_points],
        "new_height": new_height,
        "new_aspect_ratio": new_aspect_ratio,
        "scale": scale,
    }


def show_svg_with_viewbox(
    x_points: list[float],
    y_points: list[float],
    viewbox_min_x: float,
    viewbox_min_y: float,
    viewbox_width: float,
    viewbox_height: float,
    plt_title: str = "SVG ViewBox Visualization",
) -> None:
    _, ax = plt.subplots(figsize=(6, 6))
    ax.plot(x_points, y_points)

    viewbox = patches.Rectangle(
        (viewbox_min_x, viewbox_min_y),
        viewbox_width,
        viewbox_height,
        fill=False,
        label="ViewBox",
    )

    ax.add_patch(viewbox)

    # Draw origin
    ax.scatter([0], [0])
    ax.text(0, 0, "(0,0)", fontsize=9, ha="left", va="bottom")

    # Axes settings
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title(plt_title)
    ax.legend()

    plt.show()
