#!/bin/bash

cd Station
cmake -S . -B build
cmake --build build -t opengl_station
cd ..

