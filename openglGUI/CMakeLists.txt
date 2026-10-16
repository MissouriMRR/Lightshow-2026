cmake_minimum_required(VERSION 3.23)
project(Station)

set(CMAKE_BUILD_TYPE "DEBUG")

find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets OpenGL OpenGLWidgets)

set(VENV_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../.venv/lib/python3.12/site-packages")
list(APPEND CMAKE_PREFIX_PATH "${VENV_DIR}/shiboken6/lib/cmake/Shiboken6")
list(APPEND CMAKE_PREFIX_PATH "${VENV_DIR}/shiboken6_generator/lib/cmake/Shiboken6Tools")
list(APPEND CMAKE_PREFIX_PATH "${VENV_DIR}/PySide6/lib/cmake/PySide6")

find_package(Shiboken6Tools REQUIRED)

shiboken_generator_create_binding(
    EXTENSION_TARGET opengl_station
    GENERATED_SOURCES 
        "${CMAKE_CURRENT_BINARY_DIR}/opengl_station/opengl_station_module_wrapper.cpp"
        "${CMAKE_CURRENT_BINARY_DIR}/opengl_station/guireadyevent_wrapper.cpp"
        "${CMAKE_CURRENT_BINARY_DIR}/opengl_station/gui_wrapper.cpp"
    HEADERS "${CMAKE_CURRENT_SOURCE_DIR}/glmKiller.h"
    TYPESYSTEM_FILE "${CMAKE_CURRENT_SOURCE_DIR}/typesystem.xml"
    SHIBOKEN_EXTRA_OPTIONS 
        "-I${CMAKE_CURRENT_SOURCE_DIR}/include"
    LIBRARY_TARGET source_lib
    QT_MODULES
        "Core"
        "Gui"
        "Widgets"
        "OpenGL"
        "OpenGLWidgets"
)

set_target_properties(opengl_station PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/..")

add_library(source_lib OBJECT)

set_target_properties(source_lib PROPERTIES
    POSITION_INDEPENDENT_CODE ON
)

target_include_directories(source_lib
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(source_lib
    PUBLIC
        freetype 
        assimp 
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
        Qt6::Core
        Qt6::Gui
        Qt6::Widgets
        Qt6::OpenGL
        Qt6::OpenGLWidgets
)

target_sources(source_lib
    PRIVATE
        mainloop.cpp
        button.cpp
        mesh.cpp
        quader.cpp
        shader.cpp
        utils.cpp
        glad.c
        stbi_image.cpp
        drone.cpp
        ground.cpp
        gui.cpp
)

target_compile_definitions(source_lib
    PRIVATE
        ASSET_DIR=\"${CMAKE_CURRENT_SOURCE_DIR}/../assets/\"
)

add_executable(Station)
target_compile_options(Station PRIVATE -fPIC)

target_link_libraries(Station
    PRIVATE
        source_lib
)

target_sources(Station
    PRIVATE
        main.cpp
)

file(GLOB_RECURSE FILES_TO_FORMAT
    "*.cpp"
    "*.h")

set(IGNORE_FILE "${CMAKE_CURRENT_SOURCE_DIR}/.clang-format-ignore")

file(STRINGS ${IGNORE_FILE} IGNORE_LINES)

set(FILTER_REGEX "")
foreach(LINE IN LISTS IGNORE_LINES)
    string(STRIP "${LINE}" LINE)
    if(NOT LINE MATCHES "^#" AND NOT LINE STREQUAL "")
        if(FILTER_REGEX STREQUAL "")
            set(FILTER_REGEX "(${LINE})")
        else()
            set(FILTER_REGEX "${FILTER_REGEX}|(${LINE})")
        endif()
    endif()
endforeach()

list(FILTER FILES_TO_FORMAT EXCLUDE REGEX "${FILTER_REGEX}")

add_custom_target(check-format
    COMMAND clang-format --dry-run --Werror -style=file ${FILES_TO_FORMAT}
    VERBATIM)
