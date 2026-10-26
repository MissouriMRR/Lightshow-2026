#!/bin/bash

export Qt6_DIR=${PWD}/6.12.0/gcc_64/lib/cmake/Qt6

cd openglGUI
cmake -S . -B build
cmake --build build -t opengl_station -j 4
cd ..

