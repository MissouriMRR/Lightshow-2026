#include "drone.h"
#include <catch2/catch_test_macros.hpp>

SCENARIO("Drones can be selected") {
    GIVEN("Model") {
        Drone drone;
        drone.droneDatas.push_back(DroneData());
        drone.droneDatas.push_back(DroneData());
        drone.droneDatas.push_back(DroneData());
        drone.droneDatas.push_back(DroneData());

        THEN("Nothing is selected") { REQUIRE(drone.currentDrones.size() == 0); }

        WHEN("Nothing is held") {
            drone.setCurrentDrone(0, false, false);
            REQUIRE(drone.currentDrones.size() == 1);
            REQUIRE(drone.currentDrones[0] == 0);

            drone.setCurrentDrone(0, false, false);
            REQUIRE(drone.currentDrones.size() == 1);
            REQUIRE(drone.currentDrones[0] == 0);

            drone.setCurrentDrone(2, false, false);
            REQUIRE(drone.currentDrones.size() == 1);
            REQUIRE(drone.currentDrones[0] == 2);
        }

        WHEN("Shift is held") {
            drone.setCurrentDrone(0, true, false);
            REQUIRE(drone.currentDrones.size() == 1);
            REQUIRE(drone.currentDrones[0] == 0);

            drone.setCurrentDrone(1, true, false);
            REQUIRE(drone.currentDrones.size() == 2);
            REQUIRE(drone.currentDrones[0] == 0);
            REQUIRE(drone.currentDrones[1] == 1);

            drone.setCurrentDrone(1, true, false);
            REQUIRE(drone.currentDrones.size() == 1);
            REQUIRE(drone.currentDrones[0] == 0);
        }

        WHEN("Ctrl is held going down") {
            drone.setCurrentDrone(0, false, true);
            REQUIRE(drone.currentDrones.size() == 1);
            REQUIRE(drone.currentDrones[0] == 0);

            drone.setCurrentDrone(2, false, true);
            REQUIRE(drone.currentDrones.size() == 3);
            REQUIRE(drone.currentDrones[0] == 0);
            REQUIRE(drone.currentDrones[1] == 1);
            REQUIRE(drone.currentDrones[2] == 2);

            drone.setCurrentDrone(3, false, true);
            REQUIRE(drone.currentDrones.size() == 2);
            REQUIRE(drone.currentDrones[0] == 2);
            REQUIRE(drone.currentDrones[1] == 3);
        }

        WHEN("Ctrl is held going up") {
            drone.setCurrentDrone(3, false, true);
            REQUIRE(drone.currentDrones.size() == 1);
            REQUIRE(drone.currentDrones[0] == 3);

            drone.setCurrentDrone(1, false, true);
            REQUIRE(drone.currentDrones.size() == 3);
            REQUIRE(drone.currentDrones[0] == 1);
            REQUIRE(drone.currentDrones[1] == 2);
            REQUIRE(drone.currentDrones[2] == 3);

            drone.setCurrentDrone(0, false, true);
            REQUIRE(drone.currentDrones.size() == 2);
            REQUIRE(drone.currentDrones[0] == 0);
            REQUIRE(drone.currentDrones[1] == 1);
        }

        WHEN("Ctrl and shift are held") {
            drone.setCurrentDrone(0, true, true);
            REQUIRE(drone.currentDrones.size() == 1);
            REQUIRE(drone.currentDrones[0] == 0);

            drone.setCurrentDrone(2, true, true);
            REQUIRE(drone.currentDrones.size() == 3);
            REQUIRE(drone.currentDrones[0] == 0);
            REQUIRE(drone.currentDrones[1] == 1);
            REQUIRE(drone.currentDrones[2] == 2);

            drone.setCurrentDrone(1, true, false);
            REQUIRE(drone.currentDrones.size() == 2);
            REQUIRE(drone.currentDrones[0] == 0);
            REQUIRE(drone.currentDrones[1] == 2);

            drone.setCurrentDrone(3, true, true);
            REQUIRE(drone.currentDrones.size() == 4);
            REQUIRE(drone.currentDrones[0] == 0);
            REQUIRE(drone.currentDrones[1] == 2);
            REQUIRE(drone.currentDrones[2] == 1);
            REQUIRE(drone.currentDrones[3] == 3);

            drone.setCurrentDrone(1, false, false);
            REQUIRE(drone.currentDrones.size() == 1);
            REQUIRE(drone.currentDrones[0] == 1);
        }
    }
}
