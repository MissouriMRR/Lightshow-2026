import os
import sys


def obj_to_txt(obj_filepath: str, txt_filepath: str) -> bool:
    vertices: list[str] = []
    try:
        with open(obj_filepath) as obj_file:
            for line in obj_file:
                if line.startswith("v "):
                    parts = line.split()
                    x, y, z = map(float, parts[1:4])
                    vertices.append(f"{x} {y} {z}")
    except FileNotFoundError:
        print(f"Error: .obj file not found at {obj_filepath}")
        return False

    try:
        with open(txt_filepath, "w") as txt_file:
            print(vertices)
            txt_file.writelines(v + "\n" for v in vertices)
        print(f"Converted {obj_filepath} → {txt_filepath}")
        return True
    except OSError:
        print(f"Error: Could not write to .txt file at {txt_filepath}")
        return False


def main() -> None:
    input_obj = input("Enter input .obj file name: ").strip()
    input_path = input("Enter input file path: ")
    base_name = os.path.splitext(input_obj)[0]

    obj_path = os.path.join(input_path, input_obj)

    txt_file = f"{base_name}.txt"
    output_path = "./Coordinates"
    txt_path = os.path.join(output_path, txt_file)

    # OBJ -> TXT
    if not obj_to_txt(obj_path, txt_path):
        sys.exit()


if __name__ == "__main__":
    main()
