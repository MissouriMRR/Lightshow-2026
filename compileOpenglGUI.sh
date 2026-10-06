#!/bin/bash

cd openglGUI
cmake -S . -B build
cmake --build build -t opengl_station
cd ..

