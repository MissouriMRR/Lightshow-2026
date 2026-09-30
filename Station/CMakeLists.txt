cmake_minimum_required(VERSION 3.23)

project(Station)

add_executable(Station)

target_include_directories(Station
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(Station
    PUBLIC
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

target_sources(Station
    PRIVATE
        main.cpp
        button.cpp
        color.cpp
        mesh.cpp
        quader.cpp
        shader.cpp
        utils.cpp
        glad.c
        stbi_image.cpp
        model.cpp
        ground.cpp
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

message(STATUS "${PYTHON_EXTENSION_SUFFIX}")
set_target_properties(opengl_station PROPERTIES
    POSITION_INDEPENDENT_CODE ON
    OUTPUT_NAME "opengl_station${PYTHON_EXTENSION_SUFFIX}"
    PREFIX ""
    SUFFIX ""
    LIBRARY_OUTPUT_DIRECTORY ../..
)

message(STATUS "${PYBIND_INCLUDES}")
target_include_directories(opengl_station
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
    PRIVATE
        ${PYBIND_INCLUDES}
)

target_link_libraries(opengl_station
    PUBLIC
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

target_sources(opengl_station
    PRIVATE
        bindings.cpp
        main.cpp
        button.cpp
        color.cpp
        mesh.cpp
        quader.cpp
        shader.cpp
        utils.cpp
        glad.c
        stbi_image.cpp
        model.cpp
        ground.cpp
)

add_library(source_lib OBJECT)

target_include_directories(source_lib
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(source_lib
    PUBLIC
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
        button.cpp
        color.cpp
        mesh.cpp
        quader.cpp
        shader.cpp
        utils.cpp
        glad.c
        stbi_image.cpp
        model.cpp
        ground.cpp
)

add_subdirectory(tests)
