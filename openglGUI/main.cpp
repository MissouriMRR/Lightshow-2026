/*
 * main.cpp
 * Test runner for GUI
 * Only included in cmake Station render target
 */

#include "mainloop.h"
#include "mesh.h"
#include <iostream>

int main() {
    setup();
    droney->setState(1, (DroneState)1);
    droney->setState(2, (DroneState)1);

    droney->setPos(1, 0, 0, 0);
    droney->setPos(2, 0, 10, 0);

    LoopReturn result;
    while (!shouldClose()) {
        result = loop();
        switch (result) {
        case LoopReturn::ARM:
            std::cout << "ARM\n";
            break;
        case LoopReturn::TAKEOFF:
            std::cout << "TAKEOFF\n";
            break;
        case LoopReturn::STEP:
            std::cout << "STEP\n";
            break;
        case LoopReturn::LAND:
            std::cout << "LAND\n";
            break;
        case LoopReturn::HALT:
            std::cout << "HALT\n";
            break;
        case LoopReturn::NOTHING:
            break;
        }
    }
    cleanup();
}
