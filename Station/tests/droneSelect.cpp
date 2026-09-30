#include <catch2/catch_test_macros.hpp>
#include "model.h"

SCENARIO("Drones can be selected") {
    GIVEN( "Model" ) {
        Model model;
        model.droneDatas.push_back(DroneData());
        model.droneDatas.push_back(DroneData());
        model.droneDatas.push_back(DroneData());
        model.droneDatas.push_back(DroneData());

        THEN( "Nothing is selected" ) {
            REQUIRE( model.currentDrones.size() == 0 );
        }

        WHEN( "Nothing is held" ) {
            model.setCurrentDrone(0, false, false);
            REQUIRE( model.currentDrones.size() == 1 );
            REQUIRE( model.currentDrones[0] == 0 );

            model.setCurrentDrone(0, false, false);
            REQUIRE( model.currentDrones.size() == 1 );
            REQUIRE( model.currentDrones[0] == 0 );

            model.setCurrentDrone(2, false, false);
            REQUIRE( model.currentDrones.size() == 1 );
            REQUIRE( model.currentDrones[0] == 2 );
        }

        WHEN( "Shift is held" ) {
            model.setCurrentDrone(0, true, false);
            REQUIRE( model.currentDrones.size() == 1 );
            REQUIRE( model.currentDrones[0] == 0 );

            model.setCurrentDrone(1, true, false);
            REQUIRE( model.currentDrones.size() == 2 );
            REQUIRE( model.currentDrones[0] == 0 );
            REQUIRE( model.currentDrones[1] == 1 );

            model.setCurrentDrone(1, true, false);
            REQUIRE( model.currentDrones.size() == 1 );
            REQUIRE( model.currentDrones[0] == 0 );
        }

        WHEN( "Ctrl is held going down" ) {
            model.setCurrentDrone(0, false, true);
            REQUIRE( model.currentDrones.size() == 1 );
            REQUIRE( model.currentDrones[0] == 0 );

            model.setCurrentDrone(2, false, true);
            REQUIRE( model.currentDrones.size() == 3 );
            REQUIRE( model.currentDrones[0] == 0 );
            REQUIRE( model.currentDrones[1] == 1 );
            REQUIRE( model.currentDrones[2] == 2 );

            model.setCurrentDrone(3, false, true);
            REQUIRE( model.currentDrones.size() == 2 );
            REQUIRE( model.currentDrones[0] == 2 );
            REQUIRE( model.currentDrones[1] == 3 );
        }

        WHEN( "Ctrl is held going up" ) {
            model.setCurrentDrone(3, false, true);
            REQUIRE( model.currentDrones.size() == 1 );
            REQUIRE( model.currentDrones[0] == 3 );

            model.setCurrentDrone(1, false, true);
            REQUIRE( model.currentDrones.size() == 3 );
            REQUIRE( model.currentDrones[0] == 1 );
            REQUIRE( model.currentDrones[1] == 2 );
            REQUIRE( model.currentDrones[2] == 3 );

            model.setCurrentDrone(0, false, true);
            REQUIRE( model.currentDrones.size() == 2 );
            REQUIRE( model.currentDrones[0] == 0 );
            REQUIRE( model.currentDrones[1] == 1 );
        }


        WHEN( "Ctrl and shift are held" ) {
            model.setCurrentDrone(0, true, true);
            REQUIRE( model.currentDrones.size() == 1 );
            REQUIRE( model.currentDrones[0] == 0 );

            model.setCurrentDrone(2, true, true);
            REQUIRE( model.currentDrones.size() == 3 );
            REQUIRE( model.currentDrones[0] == 0 );
            REQUIRE( model.currentDrones[1] == 1 );
            REQUIRE( model.currentDrones[2] == 2 );

            model.setCurrentDrone(1, true, false);
            REQUIRE( model.currentDrones.size() == 2 );
            REQUIRE( model.currentDrones[0] == 0 );
            REQUIRE( model.currentDrones[1] == 2 );

            model.setCurrentDrone(3, true, true);
            REQUIRE( model.currentDrones.size() == 4 );
            REQUIRE( model.currentDrones[0] == 0 );
            REQUIRE( model.currentDrones[1] == 2 );
            REQUIRE( model.currentDrones[2] == 1 );
            REQUIRE( model.currentDrones[3] == 3 );

            model.setCurrentDrone(1, false, false);
            REQUIRE( model.currentDrones.size() == 1 );
            REQUIRE( model.currentDrones[0] == 1 );
        }
    }
}
