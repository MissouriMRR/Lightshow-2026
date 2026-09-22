import argparse
import asyncio

from drone.drone import Drone


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--id", help="Self ID", type=str)
    args = parser.parse_args()

    drone = Drone(args.id)

    while True:
        asyncio.run(drone.tick())

if __name__ == "__main__":
    main()
