import re
from typing import Any

from svgpathtools import svg2paths


def path_to_tag(path_obj: Any, attributes: list[dict[str, str]]) -> str:
    d = path_obj.d()
    attr = ""

    for attribute in attributes:
        for key, value in attribute.items():
            attr += f'{key}="{value}"'

    return f'<path d="{d.strip()}" {attr}/>'


def convert_to_paths(svg: str) -> None:
    try:
        with open(svg) as file:
            svg_data = file.read()

        paths, attributes, *_ = svg2paths(svg)

        new_path_tags = [path_to_tag(p, attributes) for p in paths]

        updated_svg = re.sub(
            r"(<svg[^>]*>)(.*?)(</svg>)",
            lambda m: f"{m.group(1)}" + "\n".join(new_path_tags) + f"\n{m.group(3)}",
            svg_data,
            flags=re.DOTALL,
        )

        with open(svg, "w") as file:
            file.write(updated_svg)
    except FileNotFoundError:
        print(f"File not found: {svg}")
