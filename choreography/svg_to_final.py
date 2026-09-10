from pathlib import Path

from choreography.n_drone import n_drone_run
from choreography.svg_to_xyz import svg_to_xyz_run

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def main() -> None:
    svg_name = input("Please enter the name of the svg (without .svg): ")

    base_frames_path = str(MODELS_DIR / "Sample Frames")

    print()
    print(f"{'Convert svg to xyz':-^58}")

    svg_to_xyz_run(base_frames_path, svg_name)

    print()
    print(f"{'Number of drones':-^56}")

    n_drone_run(base_frames_path, svg_name)


if __name__ == "__main__":
    main()
