cmake_minimum_required(VERSION 3.23)
project(Station)

add_library(source_lib OBJECT)

set_target_properties(source_lib PROPERTIES
    POSITION_INDEPENDENT_CODE ON
)

target_include_directories(source_lib
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(source_lib
    INTERFACE
        freetype 
        assimp 
        glfw 
        GL 
        m 
        X11 
        pthread 
        Xi 
        Xrandr 
        dl 
        z 
        bz2 
        png 
        brotlidec
)

target_sources(source_lib
    PRIVATE
        mainloop.cpp
        button.cpp
        color.cpp
        mesh.cpp
        quader.cpp
        shader.cpp
        utils.cpp
        glad.c
        stbi_image.cpp
        drone.cpp
        ground.cpp
)

add_executable(Station)

target_link_libraries(Station
    PRIVATE
        source_lib
)

target_sources(Station
    PRIVATE
        main.cpp
)

add_library(opengl_station SHARED)

execute_process(
    COMMAND uv run python3 -m pybind11 --includes
    OUTPUT_VARIABLE PYBIND_INCLUDES_RAW
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
string(REPLACE "-I" "" PYBIND_INCLUDES_CLEAN "${PYBIND_INCLUDES_RAW}")
separate_arguments(PYBIND_INCLUDES NATIVE_COMMAND "${PYBIND_INCLUDES_CLEAN}")

execute_process(
    COMMAND python3-config --extension-suffix
    OUTPUT_VARIABLE PYTHON_EXTENSION_SUFFIX
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

set_target_properties(opengl_station PROPERTIES
    POSITION_INDEPENDENT_CODE ON
    OUTPUT_NAME "opengl_station"
    PREFIX ""
    SUFFIX "${PYTHON_EXTENSION_SUFFIX}"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/.."
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/.."
)

target_include_directories(opengl_station
    PRIVATE
        ${PYBIND_INCLUDES}
)

target_link_libraries(opengl_station
    PRIVATE
        source_lib
)

target_sources(opengl_station
    PRIVATE
        bindings.cpp
)

